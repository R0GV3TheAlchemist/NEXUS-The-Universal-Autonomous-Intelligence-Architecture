# DELETED — merged into core/synergy_engine.py (Sprint G-8 completion).
# This file is intentionally left as a one-line tombstone so any stale
# import of `patch_synergy_engine` or `SynergyEngineBridgeMixin` raises
# a clear ImportError rather than a silent AttributeError.
#
# Remove this file entirely once all import sites have been updated.
raise ImportError(
    "core.synergy_engine_patch has been merged into core.synergy_engine. "
    "Import SynergyEngine directly from core.synergy_engine instead."
)
