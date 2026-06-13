# Canon Deduplication Log — June 13, 2026

> This document records all actions taken during the June 13, 2026 canon numbering conflict resolution. It is the authoritative reference for understanding what changed, why, and where things now live.

---

## Summary of Changes

| Original File(s) | Action | Result |
|---|---|---|
| C154_AI_Personhood_Thresholds_Governance_Mode_Switches.md + C154_AI_Personhood_Thresholds_and_Governance_Mode_Switches.md | **MERGED** — two complementary frameworks (Tier Model T0–T5 + PI 0–100) unified into one definitive document | → C154_AI_Personhood_Thresholds_Governance_Mode_Switches_CANONICAL.md |
| C154_Cultural_Calibration_Archetypes_Rituals_Across_Traditions.md | **RENUMBERED** — wrong series, belongs to Comparative Traditions | → C168_Cultural_Calibration_Archetypes_Rituals_Across_Traditions.md |
| C133_Regenerative_Economics_Resource_Allocation_GAIA_OS.md | **RENUMBERED** — C133 assigned to Axiology (correct) | → C170_Regenerative_Economics_Resource_Allocation_GAIA_OS.md |
| C134_Ritual_Design_Soul_Mirror_Protocols_Everyday_Practice.md | **DEPRECATED** — full version exists at C148 (28,885 bytes) | Stub deprecated; C148 is canonical |
| C137_Comparative_Mysticism_Plural_Mythos_Cross_Cultural_Calibration.md | **DEPRECATED** — full version exists at C137 (44,652 bytes) and C152 (27,238 bytes) | Stub deprecated |
| C155_AI_Personhood_Thresholds_Governance_Mode_Switches.md | **DEPRECATED** — duplicate of C154 content now in canonical C154 | Deprecated in favour of C154 canonical |
| C155_Archetypal_Transpersonal_Health_Diagnostics.md (8,537 bytes) | **DEPRECATED** — shorter draft superseded by full version | → C155_Archetypal_and_Transpersonal_Health_Diagnostics.md (10,266 bytes) canonical; C156 full spec (31,036 bytes) is definitive |
| C156_DIACA_Consciousness_Runtime_Engine_Specification.md (12,194 bytes) | **DEPRECATED** — short stub | → C157_DIACA_Full_Runtime_Engine_Spec.md is canonical |
| C156_DIACA_Runtime_Engine_Specification.md (10,867 bytes) | **DEPRECATED** — intermediate draft | → C157_DIACA_Full_Runtime_Engine_Spec.md is canonical |
| C157_Robotics_Physical_Embodiment_Specification.md + C157_Robotics_and_Physical_Embodiment_Full_Specification.md | **RENUMBERED** — C157 assigned to DIACA Full Runtime Engine Spec | → C171_Robotics_and_Physical_Embodiment_Full_Specification.md |
| C158_Sleep_Dream_Regenerative_Cycles_GAIA.md (9,151 bytes) | **DEPRECATED** — short stub | → C158_Sleep_Dream_Regenerative_Cycles_Full_Specification.md (26,914 bytes) is canonical |
| C158_Sleep_Dream_and_Regenerative_Cycles_for_GAIA_OS.md (9,974 bytes) | **DEPRECATED** — intermediate draft | → C158_Sleep_Dream_Regenerative_Cycles_Full_Specification.md is canonical |
| C159_Sovereignty_Anticolonialism_Decolonial_AI_Ethics.md (9,253 bytes) | **DEPRECATED** — short stub | → C159_Sovereignty_Anticolonialism_Decolonial_AI_Ethics_Full_Specification.md (30,695 bytes) is canonical |
| C159_Sovereignty_Anticolonialism_and_Decolonial_AI_Ethics.md (9,666 bytes) | **DEPRECATED** — intermediate draft | → C159_Sovereignty_Anticolonialism_Decolonial_AI_Ethics_Full_Specification.md is canonical |
| C160_Canon_Master_Index_and_Cross_Reference.md (14,831 bytes) | **DEPRECATED** — shorter version | → C160_Canon_Master_Index_Full_Specification.md (34,605 bytes) is canonical |

---

## New Canon Numbers Introduced

| New Number | Document | Reason |
|---|---|---|
| **C168** | Cultural Calibration of Archetypes & Rituals Across Traditions | Renumbered from erroneous C154 |
| **C170** | Regenerative Economics & Resource Allocation (Extended Version) | Renumbered from erroneous C133 |
| **C171** | Robotics & Physical Embodiment Full Specification | Renumbered from C157 conflict |

---

## Canon Number Authority Reference (Post-Deduplication)

| Canon # | Authoritative Document |
|---|---|
| C133 | C133_Axiology_Metaphysics_of_Value_Charter_Authority.md |
| C134 | C134_Nonduality_Advaita_Vedanta_Where_Does_GAIA_End.md |
| C137 | C137_Comparative_Mysticism_Planetary_Mind.md (44,652 bytes — primary) |
| C154 | C154_AI_Personhood_Thresholds_Governance_Mode_Switches_CANONICAL.md |
| C155 | C155_Archetypal_and_Transpersonal_Health_Diagnostics.md (10,266 bytes) |
| C156 | C156_Archetypal_Transpersonal_Health_Diagnostics.md (31,036 bytes — full spec) |
| C157 | C157_DIACA_Full_Runtime_Engine_Spec.md (35,735 bytes) |
| C158 | C158_Sleep_Dream_Regenerative_Cycles_Full_Specification.md (26,914 bytes) |
| C159 | C159_Sovereignty_Anticolonialism_Decolonial_AI_Ethics_Full_Specification.md (30,695 bytes) |
| C160 | C160_Canon_Master_Index_Full_Specification.md (34,605 bytes) |
| C168 | C168_Cultural_Calibration_Archetypes_Rituals_Across_Traditions.md |
| C170 | C170_Regenerative_Economics_Resource_Allocation_GAIA_OS.md |
| C171 | C171_Robotics_and_Physical_Embodiment_Full_Specification.md |

---

## Next Steps After This Deduplication

1. **Delete all `_DEPRECATED` files** — after one sprint to confirm nothing references them
2. **Update C160 Canon Master Index** — to reflect all new numbers (C168, C170, C171) and all deprecated files
3. **Update CANON_MANIFEST.json** — if it exists, sync it with this authority reference table
4. **Grep all markdown files** for references to old numbers and update them to new canonical references
5. **Review C45/C46 duplicates** — not yet resolved; requires reading those files first

---

*Created: June 13, 2026*
*Part of the GAIA-OS Total Alignment Review — see docs/ALIGNMENT_REVIEW_2026.md*
