"""crystal_correspondence v2.0: new indexed scalars, JSONB axes, sovereignty flags.

Revision ID: 20260615_crystal_corr_v2
Revises: 20260615_crystal_corr
Create Date: 2026-06-15

This migration extends the crystal_correspondence table with all axes
introduced in correspondence-schema.json v2.0. All new columns are
nullable so existing v1.0 records remain valid without modification.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision    = "20260615_crystal_corr_v2"
down_revision = "20260615_crystal_corr"
branch_labels = None
depends_on    = None


def upgrade() -> None:

    # ───────────────────────────────────────────────────────────────────
    # NEW INDEXED SCALAR COLUMNS
    # These are promoted out of JSONB for fast B-tree resonance queries.
    # ───────────────────────────────────────────────────────────────────
    new_scalar_cols = [
        # Physical
        sa.Column("crystal_system",          sa.Text,           nullable=True),
        sa.Column("mohs_hardness_low",        sa.Numeric(4, 2),  nullable=True),
        sa.Column("mohs_hardness_high",       sa.Numeric(4, 2),  nullable=True),
        sa.Column("piezoelectric",            sa.Boolean,        nullable=True),
        sa.Column("pyroelectric",             sa.Boolean,        nullable=True),
        sa.Column("luminance_profile",        sa.Text,           nullable=True),
        # Alchemical
        sa.Column("alchemical_stage_primary", sa.Text,           nullable=True),
        # Chakra
        sa.Column("primary_chakra",           sa.Text,           nullable=True),
        # Consequential
        sa.Column("coherence_impact_scalar",  sa.Numeric(4, 3),  nullable=True),  # -1.000 to +1.000
        sa.Column("grey_state_risk_level",    sa.Text,           nullable=True),  # low / moderate / high / context_dependent
        # Versioning & review
        sa.Column("record_version",           sa.Text,           nullable=True,  server_default="'1.0.0'"),
        sa.Column("review_status",            sa.Text,           nullable=True,  server_default="'draft'"),
        sa.Column("reviewed_by",              sa.Text,           nullable=True),
        sa.Column("next_review_date",         sa.Date,           nullable=True),
    ]

    for col in new_scalar_cols:
        op.add_column("crystal_correspondence", col)

    # ───────────────────────────────────────────────────────────────────
    # NEW JSONB COLUMNS
    # Each holds one v2.0 correspondence axis in full fidelity.
    # ───────────────────────────────────────────────────────────────────
    new_jsonb_cols = [
        ("physical_properties",      "'{}'"),
        ("resonant_frequencies",     "'[]'"),
        ("chakra_system",            "'[]'"),
        ("alchemical",               "'{}'"),
        ("healing",                  "'{}'"),
        ("consequential_properties", "'{}'"),
        ("provenance_v2",            "'{}'"),   # record-level provenance (confidence_score, last_verified, etc.)
        ("sovereignty_flags",        "'{}'"),
        ("aliases",                  "'[]'"),
        ("change_log",               "'[]'"),
    ]

    for col_name, default in new_jsonb_cols:
        op.add_column(
            "crystal_correspondence",
            sa.Column(col_name, JSONB, nullable=True, server_default=default),
        )

    # ───────────────────────────────────────────────────────────────────
    # B-TREE INDEXES on new scalar columns
    # ───────────────────────────────────────────────────────────────────
    scalar_indexes = [
        ("ix_cc_crystal_system",          ["crystal_system"]),
        ("ix_cc_piezoelectric",           ["piezoelectric"]),
        ("ix_cc_alchemical_stage_primary",["alchemical_stage_primary"]),
        ("ix_cc_primary_chakra",          ["primary_chakra"]),
        ("ix_cc_coherence_impact_scalar", ["coherence_impact_scalar"]),
        ("ix_cc_grey_state_risk_level",   ["grey_state_risk_level"]),
        ("ix_cc_review_status",           ["review_status"]),
        ("ix_cc_record_version",          ["record_version"]),
    ]

    for idx_name, cols in scalar_indexes:
        op.create_index(idx_name, "crystal_correspondence", cols)

    # Composite index: fast resonance range query
    # e.g. WHERE frequency_hz_low >= 7.83 AND frequency_hz_high <= 40.0
    #      AND alchemical_stage_primary = 'NIGREDO'
    op.create_index(
        "ix_cc_resonance_composite",
        "crystal_correspondence",
        ["frequency_hz_low", "frequency_hz_high", "alchemical_stage_primary"],
    )

    # Partial index: active records only (most queries filter is_active = true)
    op.execute(
        """
        CREATE INDEX ix_cc_active_layer
        ON crystal_correspondence (primary_gaia_layer, alchemical_stage_primary)
        WHERE is_active = true
        """
    )

    # ───────────────────────────────────────────────────────────────────
    # GIN INDEXES on new JSONB columns
    # Enables fast containment queries like:
    #   healing @> '{"physical": [{"target_system": "immune"}]}'
    #   consequential_properties @> '{"interaction_matrix": [{"type": "synergy"}]}'
    # ───────────────────────────────────────────────────────────────────
    gin_indexes = [
        ("ix_cc_physical_properties_gin",      "physical_properties"),
        ("ix_cc_resonant_frequencies_gin",     "resonant_frequencies"),
        ("ix_cc_chakra_system_gin",            "chakra_system"),
        ("ix_cc_alchemical_gin",               "alchemical"),
        ("ix_cc_healing_gin",                  "healing"),
        ("ix_cc_consequential_gin",            "consequential_properties"),
        ("ix_cc_provenance_v2_gin",            "provenance_v2"),
        ("ix_cc_sovereignty_flags_gin",        "sovereignty_flags"),
    ]

    for idx_name, col_name in gin_indexes:
        op.execute(
            f"CREATE INDEX {idx_name} ON crystal_correspondence USING gin ({col_name})"
        )


def downgrade() -> None:
    # Drop GIN indexes
    gin_index_names = [
        "ix_cc_physical_properties_gin", "ix_cc_resonant_frequencies_gin",
        "ix_cc_chakra_system_gin", "ix_cc_alchemical_gin", "ix_cc_healing_gin",
        "ix_cc_consequential_gin", "ix_cc_provenance_v2_gin", "ix_cc_sovereignty_flags_gin",
    ]
    for idx in gin_index_names:
        op.execute(f"DROP INDEX IF EXISTS {idx}")

    # Drop scalar indexes
    scalar_index_names = [
        "ix_cc_crystal_system", "ix_cc_piezoelectric", "ix_cc_alchemical_stage_primary",
        "ix_cc_primary_chakra", "ix_cc_coherence_impact_scalar", "ix_cc_grey_state_risk_level",
        "ix_cc_review_status", "ix_cc_record_version", "ix_cc_resonance_composite",
        "ix_cc_active_layer",
    ]
    for idx in scalar_index_names:
        op.drop_index(idx, table_name="crystal_correspondence")

    # Drop new JSONB columns
    for col_name in [
        "physical_properties", "resonant_frequencies", "chakra_system",
        "alchemical", "healing", "consequential_properties",
        "provenance_v2", "sovereignty_flags", "aliases", "change_log",
    ]:
        op.drop_column("crystal_correspondence", col_name)

    # Drop new scalar columns
    for col_name in [
        "crystal_system", "mohs_hardness_low", "mohs_hardness_high",
        "piezoelectric", "pyroelectric", "luminance_profile",
        "alchemical_stage_primary", "primary_chakra",
        "coherence_impact_scalar", "grey_state_risk_level",
        "record_version", "review_status", "reviewed_by", "next_review_date",
    ]:
        op.drop_column("crystal_correspondence", col_name)
