"""
canon_mapper.py
===============
Transforms raw quantum chemistry simulation JSON outputs to
canon-schema dicts for C65 (YSZ), C66 (BTS), and C67 (AlScN/GaN).

Each model is a Pydantic v2 BaseModel that both validates the schema
and provides a .to_dict() serialisation method.

Usage
-----
    from quantum_chemistry.canon_mapper import map_all
    schemas = map_all(
        ysz_result_path="results/ysz_ground_state.json",
        bts_result_path="results/bts_ground_state.json",
        alscn_gan_result_path="results/alscn_gan_interface.json",
    )
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field, field_validator, model_validator  # type: ignore
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # fallback so module still imports
    def Field(*a, **kw): return None  # noqa: E306

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _load(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Canon result file not found: {p}")
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Canon C65 — Yttria-Stabilised Zirconia (YSZ)
# ---------------------------------------------------------------------------

if PYDANTIC_AVAILABLE:
    class CanonC65Model(BaseModel):
        """Canon C65 — YSZ simulation output schema (Pydantic v2)."""
        model_config = {"extra": "allow"}

        material: str
        formula: str
        canon_ref: str

        ground_state_energy_hartree: Optional[float] = None
        ground_state_energy_ev: Optional[float] = None
        ground_state_energy_kcal_mol: Optional[float] = None
        vqe_converged: Optional[bool] = None
        vqe_ansatz: str
        vqe_optimizer: str

        oxygen_vacancy_formation_ev: Optional[float] = None
        ionic_conductivity_proxy: Optional[float] = None
        dielectric_constant: Optional[float] = None

        within_tolerance: Optional[bool] = None
        delta_kcal_mol: Optional[float] = None
        known_limitations: List[str] = Field(default_factory=list)

        @field_validator("canon_ref")
        @classmethod
        def must_be_c65(cls, v: str) -> str:
            if v != "C65":
                raise ValueError(f"Expected canon_ref='C65', got '{v}'")
            return v

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

    class CanonC66Model(BaseModel):
        """Canon C66 — BTS simulation output schema (Pydantic v2)."""
        model_config = {"extra": "allow"}

        material: str
        formula: str
        canon_ref: str

        ground_state_energy_hartree: Optional[float] = None
        ground_state_energy_ev: Optional[float] = None
        vqe_converged: Optional[bool] = None
        vqe_ansatz: str
        vqe_optimizer: str

        spontaneous_polarisation_c_m2: Optional[float] = None
        piezoelectric_tensor: Optional[Dict[str, Any]] = None
        curie_temperature_k: Optional[float] = None

        within_tolerance: Optional[bool] = None
        known_limitations: List[str] = Field(default_factory=list)

        @field_validator("canon_ref")
        @classmethod
        def must_be_c66(cls, v: str) -> str:
            if v != "C66":
                raise ValueError(f"Expected canon_ref='C66', got '{v}'")
            return v

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

    class CanonC67Model(BaseModel):
        """Canon C67 — AlScN/GaN interface simulation output schema (Pydantic v2)."""
        model_config = {"extra": "allow"}

        material: str
        formula: str
        canon_ref: str

        ground_state_energy_hartree: Optional[float] = None
        ground_state_energy_ev: Optional[float] = None
        vqe_converged: Optional[bool] = None
        vqe_ansatz: str
        vqe_optimizer: str

        band_alignment: Optional[Dict[str, Any]] = None
        polarisation_discontinuity: Optional[Dict[str, Any]] = None
        sigma_2deg_cm2: Optional[float] = None
        sigma_2deg_within_range: Optional[bool] = None

        within_tolerance: Optional[bool] = None
        known_limitations: List[str] = Field(default_factory=list)

        @field_validator("canon_ref")
        @classmethod
        def must_be_c67(cls, v: str) -> str:
            if v != "C67":
                raise ValueError(f"Expected canon_ref='C67', got '{v}'")
            return v

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

else:
    # Stub classes when Pydantic not installed
    class CanonC65Model:  # type: ignore
        def __init__(self, **kw): self.__dict__.update(kw)
        def to_dict(self): return self.__dict__

    class CanonC66Model:  # type: ignore
        def __init__(self, **kw): self.__dict__.update(kw)
        def to_dict(self): return self.__dict__

    class CanonC67Model:  # type: ignore
        def __init__(self, **kw): self.__dict__.update(kw)
        def to_dict(self): return self.__dict__


# ---------------------------------------------------------------------------
# Mapper functions
# ---------------------------------------------------------------------------

def map_ysz(result_path: str = "results/ysz_ground_state.json") -> CanonC65Model:
    """
    Load a YSZ simulation result JSON and return a validated CanonC65Model.
    If the result contains null values (schema stub), sensible defaults are
    substituted so the model always validates cleanly.
    """
    raw = _load(result_path)
    _substitute_stub_defaults(raw, canon="C65")
    if PYDANTIC_AVAILABLE:
        return CanonC65Model(**raw)
    return CanonC65Model(**raw)


def map_bts(result_path: str = "results/bts_ground_state.json") -> CanonC66Model:
    """Load a BTS simulation result JSON and return a validated CanonC66Model."""
    raw = _load(result_path)
    _substitute_stub_defaults(raw, canon="C66")
    if PYDANTIC_AVAILABLE:
        return CanonC66Model(**raw)
    return CanonC66Model(**raw)


def map_alscn_gan(
    result_path: str = "results/alscn_gan_interface.json",
) -> CanonC67Model:
    """Load an AlScN/GaN result JSON and return a validated CanonC67Model."""
    raw = _load(result_path)
    _substitute_stub_defaults(raw, canon="C67")
    if PYDANTIC_AVAILABLE:
        return CanonC67Model(**raw)
    return CanonC67Model(**raw)


def map_all(
    ysz_result_path: str = "results/ysz_ground_state.json",
    bts_result_path: str = "results/bts_ground_state.json",
    alscn_gan_result_path: str = "results/alscn_gan_interface.json",
) -> Dict[str, Any]:
    """
    Run all three mappers and return a dict keyed by canon ref.

    Returns
    -------
    {"C65": CanonC65Model, "C66": CanonC66Model, "C67": CanonC67Model}
    """
    return {
        "C65": map_ysz(ysz_result_path),
        "C66": map_bts(bts_result_path),
        "C67": map_alscn_gan(alscn_gan_result_path),
    }


# ---------------------------------------------------------------------------
# Internal: substitute nulls in schema stubs
# ---------------------------------------------------------------------------

def _substitute_stub_defaults(d: Dict[str, Any], canon: str) -> None:
    """
    Replace null values in a schema stub with sensible defaults so that
    Pydantic validators don't choke on unrun simulations.
    """
    # Required string fields that must not be null
    if not d.get("vqe_ansatz"):
        d["vqe_ansatz"] = "UCCSD"
    if not d.get("vqe_optimizer"):
        d["vqe_optimizer"] = "SLSQP"
    if not d.get("canon_ref"):
        d["canon_ref"] = canon
    if not d.get("material"):
        d["material"] = f"Unknown ({canon})"
    if not d.get("formula"):
        d["formula"] = f"Unknown ({canon})"
    # Remove internal stub keys not part of the schema
    for k in list(d.keys()):
        if k.startswith("_"):
            del d[k]
