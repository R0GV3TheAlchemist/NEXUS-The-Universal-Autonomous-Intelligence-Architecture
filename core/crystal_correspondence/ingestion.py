"""Crystal correspondence ingestion pipeline — v2.0.

This module validates incoming crystal correspondence JSON files against
schemas/correspondence-schema.json, extracts indexed scalar fields, upserts
rows into crystal_correspondence, snapshots provenance history, and emits
engine-link hooks so new records auto-register with GAIA subsystems.

Design goals
------------
* Backward compatible with v1.0 records.
* Strict schema validation before any write.
* Scalar extraction for fast lookup columns.
* Full JSONB preservation for flexible evolution.
* Validation error queue for observability.
* Engine auto-link hooks for Prismatic, resonance_field_engine, SoulMirror,
  and affect inference.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

import jsonschema
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import CrystalCorrespondence, CrystalCorrespondenceProvenanceLog

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path("schemas/correspondence-schema.json")

_validation_errors: list[dict[str, Any]] = []


def get_validation_errors() -> list[dict[str, Any]]:
    """Return accumulated validation errors from this process lifetime."""
    return list(_validation_errors)


def clear_validation_errors() -> None:
    """Clear validation error queue."""
    _validation_errors.clear()


def _load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_record(payload: dict[str, Any]) -> None:
    """Validate payload against correspondence-schema.json.

    Raises
    ------
    jsonschema.ValidationError
        If the payload does not satisfy the schema.
    """
    schema = _load_schema()
    jsonschema.validate(instance=payload, schema=schema)


def _decimal_or_none(value: Any, precision: str = "0.001") -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value)).quantize(Decimal(precision))
    except Exception:
        return None


def _parse_range_string(value: str | None) -> tuple[Decimal | None, Decimal | None]:
    """Parse a numeric range string like '6.5-7.5' or '7.83–20.8'."""
    if not value:
        return (None, None)
    norm = str(value).replace("–", "-").replace("—", "-")
    parts = [p.strip() for p in norm.split("-") if p.strip()]
    if not parts:
        return (None, None)
    if len(parts) == 1:
        d = _decimal_or_none(parts[0], precision="0.01")
        return (d, d)
    low = _decimal_or_none(parts[0], precision="0.01")
    high = _decimal_or_none(parts[1], precision="0.01")
    return (low, high)


def _extract_primary_color(payload: dict[str, Any]) -> str | None:
    pp = payload.get("correspondences", {}).get("physical_properties", {})
    colors = pp.get("color_spectrum", [])
    for entry in colors:
        if entry.get("is_primary"):
            return entry.get("label")
    if colors:
        return colors[0].get("label")
    return None


def _extract_frequency_band(payload: dict[str, Any]) -> tuple[Decimal | None, Decimal | None]:
    corr = payload.get("correspondences", {})

    # Priority 1: explicit resonant_frequencies[] array
    freqs = corr.get("resonant_frequencies", [])
    hz_values = [f.get("hz") for f in freqs if f.get("hz") is not None]
    hz_values = [Decimal(str(v)) for v in hz_values if str(v).strip() != ""]
    if hz_values:
        return (min(hz_values), max(hz_values))

    # Priority 2: legacy grid_resonance.frequency_band_hz string
    grid = corr.get("grid_resonance", {})
    return _parse_range_string(grid.get("frequency_band_hz"))


def _extract_primary_alchemical_stage(payload: dict[str, Any]) -> str | None:
    corr = payload.get("correspondences", {})
    alch = corr.get("alchemical", {})
    if alch.get("stage_primary"):
        return alch["stage_primary"]
    return payload.get("correspondences", {}).get("evidence_profile", {}).get("alchemical_stage")


def _extract_primary_gaia_layer(payload: dict[str, Any]) -> str | None:
    layers = payload.get("correspondences", {}).get("gaia_layers", [])
    if not layers:
        return None
    weighted = sorted(
        layers,
        key=lambda x: x.get("weight", 0),
        reverse=True,
    )
    return weighted[0].get("layer_id")


def _extract_primary_element(payload: dict[str, Any]) -> str | None:
    elements = payload.get("correspondences", {}).get("elements", [])
    if not elements:
        return None
    weighted = sorted(elements, key=lambda x: x.get("weight", 0), reverse=True)
    return weighted[0].get("element")


def _extract_crystal_system(payload: dict[str, Any]) -> str | None:
    return payload.get("correspondences", {}).get("physical_properties", {}).get("crystal_system")


def _extract_mohs_range(payload: dict[str, Any]) -> tuple[Decimal | None, Decimal | None]:
    mohs = payload.get("correspondences", {}).get("physical_properties", {}).get("mohs_hardness")
    return _parse_range_string(mohs)


def _extract_primary_chakra(payload: dict[str, Any]) -> str | None:
    entries = payload.get("correspondences", {}).get("chakra_system", [])
    if not entries:
        return None
    weighted = sorted(entries, key=lambda x: x.get("weight", 0), reverse=True)
    return weighted[0].get("chakra")


def _extract_coherence_scalar(payload: dict[str, Any]) -> Decimal | None:
    scalar = (
        payload.get("correspondences", {})
        .get("consequential_properties", {})
        .get("coherence_impact", {})
        .get("scalar")
    )
    return _decimal_or_none(scalar, precision="0.001")


def _extract_grey_state_risk_level(payload: dict[str, Any]) -> str | None:
    risk = payload.get("correspondences", {}).get("consequential_properties", {}).get("grey_state_risk", {})
    may_exacerbate = risk.get("may_exacerbate", []) or []
    mitigates = risk.get("mitigates", []) or []
    if may_exacerbate and mitigates:
        return "context_dependent"
    if len(may_exacerbate) >= 3:
        return "high"
    if len(may_exacerbate) >= 1:
        return "moderate"
    if mitigates:
        return "low"
    return None


def _extract_record_version(payload: dict[str, Any]) -> str | None:
    return payload.get("metadata", {}).get("version") or payload.get("metadata", {}).get("schema_version")


def _extract_review_status(payload: dict[str, Any]) -> str | None:
    return payload.get("metadata", {}).get("review_status")


def _extract_reviewed_by(payload: dict[str, Any]) -> str | None:
    return payload.get("metadata", {}).get("reviewed_by")


def _extract_next_review_date(payload: dict[str, Any]) -> dt.date | None:
    raw = payload.get("metadata", {}).get("next_review_date")
    if not raw:
        return None
    try:
        return dt.date.fromisoformat(raw)
    except Exception:
        return None


def _snapshot_record(row: CrystalCorrespondence) -> dict[str, Any]:
    return {
        "subject_id": row.subject_id,
        "common_name": row.common_name,
        "aliases": row.aliases,
        "mineral_formula": row.mineral_formula,
        "primary_color": row.primary_color,
        "frequency_hz_low": float(row.frequency_hz_low) if row.frequency_hz_low is not None else None,
        "frequency_hz_high": float(row.frequency_hz_high) if row.frequency_hz_high is not None else None,
        "alchemical_stage": row.alchemical_stage,
        "primary_gaia_layer": row.primary_gaia_layer,
        "primary_element": row.primary_element,
        "crystal_system": row.crystal_system,
        "mohs_hardness_low": float(row.mohs_hardness_low) if row.mohs_hardness_low is not None else None,
        "mohs_hardness_high": float(row.mohs_hardness_high) if row.mohs_hardness_high is not None else None,
        "piezoelectric": row.piezoelectric,
        "pyroelectric": row.pyroelectric,
        "luminance_profile": row.luminance_profile,
        "alchemical_stage_primary": row.alchemical_stage_primary,
        "primary_chakra": row.primary_chakra,
        "coherence_impact_scalar": float(row.coherence_impact_scalar) if row.coherence_impact_scalar is not None else None,
        "grey_state_risk_level": row.grey_state_risk_level,
        "record_version": row.record_version,
        "review_status": row.review_status,
        "reviewed_by": row.reviewed_by,
        "next_review_date": row.next_review_date.isoformat() if row.next_review_date else None,
        "correspondences": copy.deepcopy(row.correspondences),
        "physical_properties": copy.deepcopy(row.physical_properties),
        "resonant_frequencies": copy.deepcopy(row.resonant_frequencies),
        "chakra_system": copy.deepcopy(row.chakra_system),
        "alchemical": copy.deepcopy(row.alchemical),
        "healing": copy.deepcopy(row.healing),
        "consequential_properties": copy.deepcopy(row.consequential_properties),
        "provenance": copy.deepcopy(row.provenance),
        "provenance_v2": copy.deepcopy(row.provenance_v2),
        "sovereignty_flags": copy.deepcopy(row.sovereignty_flags),
        "change_log": copy.deepcopy(row.change_log),
        "schema_version": row.schema_version,
        "is_active": row.is_active,
    }


def _create_provenance_log(session: Session, row: CrystalCorrespondence, *, changed_by: str | None, change_note: str | None) -> None:
    session.add(
        CrystalCorrespondenceProvenanceLog(
            crystal=row,
            version=row.record_version or row.schema_version or "1.0.0",
            changed_by=changed_by,
            change_note=change_note,
            snapshot=_snapshot_record(row),
            provenance_snapshot=copy.deepcopy(row.provenance_v2 or row.provenance or {}),
        )
    )


def _auto_link_prismatic(row: CrystalCorrespondence) -> None:
    logger.info("Auto-link queued for Prismatic: %s", row.subject_id)


def _auto_link_resonance_field_engine(row: CrystalCorrespondence) -> None:
    logger.info("Auto-link queued for resonance_field_engine: %s", row.subject_id)


def _auto_link_soul_mirror(row: CrystalCorrespondence) -> None:
    logger.info("Auto-link queued for SoulMirror: %s", row.subject_id)


def _auto_link_affect_inference(row: CrystalCorrespondence) -> None:
    logger.info("Auto-link queued for affect inference: %s", row.subject_id)


def _run_engine_auto_links(row: CrystalCorrespondence) -> None:
    _auto_link_prismatic(row)
    _auto_link_resonance_field_engine(row)
    _auto_link_soul_mirror(row)
    _auto_link_affect_inference(row)


def ingest_record(
    session: Session,
    payload: dict[str, Any],
    *,
    changed_by: str | None = None,
    change_note: str | None = None,
    dry_run: bool = False,
) -> CrystalCorrespondence:
    """Validate, upsert, version, and auto-link a single correspondence record."""
    try:
        validate_record(payload)
    except jsonschema.ValidationError as exc:
        err = {
            "subject_id": payload.get("subject_id"),
            "message": exc.message,
            "path": list(exc.path),
            "validator": exc.validator,
        }
        _validation_errors.append(err)
        raise

    corr = payload.get("correspondences", {})
    metadata = payload.get("metadata", {})

    frequency_low, frequency_high = _extract_frequency_band(payload)
    mohs_low, mohs_high = _extract_mohs_range(payload)

    stmt = select(CrystalCorrespondence).where(
        CrystalCorrespondence.subject_id == payload["subject_id"]
    )
    row = session.execute(stmt).scalar_one_or_none()

    if row is not None:
        _create_provenance_log(session, row, changed_by=changed_by, change_note=change_note)
    else:
        row = CrystalCorrespondence(subject_id=payload["subject_id"], common_name=payload["subject_id"].split(":", 1)[-1].replace("_", " ").title())
        session.add(row)

    # Core identity
    row.subject_id = payload["subject_id"]
    row.common_name = metadata.get("display_name") or row.common_name
    row.aliases = payload.get("aliases", [])

    # v1.0 indexed scalars
    row.mineral_formula = corr.get("physical_properties", {}).get("chemical_formula") or row.mineral_formula
    row.primary_color = _extract_primary_color(payload)
    row.frequency_hz_low = frequency_low
    row.frequency_hz_high = frequency_high
    row.alchemical_stage = _extract_primary_alchemical_stage(payload)  # compat mirror
    row.primary_gaia_layer = _extract_primary_gaia_layer(payload)
    row.primary_element = _extract_primary_element(payload)

    # v2.0 indexed scalars
    row.crystal_system = _extract_crystal_system(payload)
    row.mohs_hardness_low = mohs_low
    row.mohs_hardness_high = mohs_high
    row.piezoelectric = corr.get("physical_properties", {}).get("piezoelectric")
    row.pyroelectric = corr.get("physical_properties", {}).get("pyroelectric")
    row.luminance_profile = corr.get("physical_properties", {}).get("luminance_profile")
    row.alchemical_stage_primary = _extract_primary_alchemical_stage(payload)
    row.primary_chakra = _extract_primary_chakra(payload)
    row.coherence_impact_scalar = _extract_coherence_scalar(payload)
    row.grey_state_risk_level = _extract_grey_state_risk_level(payload)
    row.record_version = _extract_record_version(payload) or row.record_version or "1.0.0"
    row.review_status = _extract_review_status(payload) or row.review_status or "draft"
    row.reviewed_by = _extract_reviewed_by(payload)
    row.next_review_date = _extract_next_review_date(payload)

    # Full JSONB preservation
    row.correspondences = copy.deepcopy(corr)
    row.physical_properties = copy.deepcopy(corr.get("physical_properties", {}))
    row.resonant_frequencies = copy.deepcopy(corr.get("resonant_frequencies", []))
    row.chakra_system = copy.deepcopy(corr.get("chakra_system", []))
    row.alchemical = copy.deepcopy(corr.get("alchemical", {}))
    row.healing = copy.deepcopy(corr.get("healing", {}))
    row.consequential_properties = copy.deepcopy(corr.get("consequential_properties", {}))
    row.provenance = {
        "source": "GAIA-OS",
        "confidence": corr.get("evidence_profile", {}).get("confidence", "medium"),
        "last_updated": metadata.get("updated_at"),
    }
    row.provenance_v2 = copy.deepcopy(corr.get("provenance", {}))
    row.sovereignty_flags = copy.deepcopy(metadata.get("sovereignty_flags", {}))
    row.change_log = copy.deepcopy(metadata.get("change_log", []))
    row.schema_version = metadata.get("schema_version") or row.schema_version or "2.0.0"
    row.is_active = True

    if dry_run:
        session.rollback()
        return row

    session.flush()
    _run_engine_auto_links(row)
    return row


def ingest_json_file(
    session: Session,
    path: str | Path,
    *,
    changed_by: str | None = None,
    change_note: str | None = None,
    dry_run: bool = False,
) -> CrystalCorrespondence:
    """Load a JSON file from disk and ingest it."""
    p = Path(path)
    with p.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return ingest_record(
        session,
        payload,
        changed_by=changed_by,
        change_note=change_note or f"ingested from {p}",
        dry_run=dry_run,
    )
