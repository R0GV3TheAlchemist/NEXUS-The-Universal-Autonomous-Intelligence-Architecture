"""
test_canon_validation.py
========================
Tests for canon_mapper.py and validator.py (issue #139).

All tests are unconditional (no quantum packages required) —
they exercise the mapper/validator logic against the committed
schema stubs and reference data files.

Run with:
    pytest src-python/tests/test_canon_validation.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# canon_mapper tests
# ---------------------------------------------------------------------------

def test_canon_mapper_importable():
    import quantum_chemistry.canon_mapper as m  # noqa
    assert m is not None


def test_map_ysz_returns_c65_model():
    from quantum_chemistry.canon_mapper import map_ysz, CanonC65Model
    model = map_ysz("results/ysz_ground_state.json")
    assert isinstance(model, CanonC65Model)
    assert model.canon_ref == "C65"
    assert model.material is not None


def test_map_bts_returns_c66_model():
    from quantum_chemistry.canon_mapper import map_bts, CanonC66Model
    model = map_bts("results/bts_ground_state.json")
    assert isinstance(model, CanonC66Model)
    assert model.canon_ref == "C66"


def test_map_alscn_gan_returns_c67_model():
    from quantum_chemistry.canon_mapper import map_alscn_gan, CanonC67Model
    model = map_alscn_gan("results/alscn_gan_interface.json")
    assert isinstance(model, CanonC67Model)
    assert model.canon_ref == "C67"


def test_map_all_returns_all_three():
    from quantum_chemistry.canon_mapper import map_all
    schemas = map_all()
    assert set(schemas.keys()) == {"C65", "C66", "C67"}


def test_canon_models_to_dict():
    from quantum_chemistry.canon_mapper import map_all
    schemas = map_all()
    for canon, model in schemas.items():
        d = model.to_dict()
        assert isinstance(d, dict)
        assert d.get("canon_ref") == canon


# ---------------------------------------------------------------------------
# validator tests
# ---------------------------------------------------------------------------

def test_validator_importable():
    import quantum_chemistry.validator as v  # noqa
    assert v is not None


def test_reference_data_files_exist():
    for fname in (
        "data/rruff_ysz_reference.json",
        "data/mindat_bts_reference.json",
        "data/alscn_gan_literature.json",
    ):
        assert Path(fname).exists(), f"Missing reference data: {fname}"


def test_reference_data_parseable():
    from quantum_chemistry.validator import load_reference_data
    for fname in (
        "data/rruff_ysz_reference.json",
        "data/mindat_bts_reference.json",
        "data/alscn_gan_literature.json",
    ):
        data = load_reference_data(fname)
        assert isinstance(data, dict)
        assert len(data) > 0


def test_validate_all_runs_without_error():
    from quantum_chemistry.validator import validate_all
    report = validate_all()
    assert len(report.materials) == 3
    assert report.total_tested >= 0


def test_validate_all_pass_rate_geometry_only():
    """
    With schema stubs, only geometry properties are testable.
    All geometry properties should pass (residual = 0).
    """
    from quantum_chemistry.validator import validate_all
    report = validate_all()
    for mvr in report.materials:
        testable = [p for p in mvr.properties if p.passed is not None]
        for p in testable:
            assert p.passed, (
                f"{mvr.material}: property '{p.property_name}' FAILED "
                f"(sim={p.simulated_value}, ref={p.reference_value}, "
                f"residual={p.residual})"
            )


def test_write_validation_report(tmp_path):
    from quantum_chemistry.validator import validate_all, write_validation_report
    report = validate_all()
    out = str(tmp_path / "report.md")
    write_validation_report(report, out)
    content = Path(out).read_text()
    assert "GAIA-OS Quantum Chemistry Validation Report" in content
    assert "C65" in content
    assert "C66" in content
    assert "C67" in content


def test_validation_report_md_exists():
    assert Path("results/validation_report.md").exists()
    content = Path("results/validation_report.md").read_text()
    assert "C65" in content and "C66" in content and "C67" in content
