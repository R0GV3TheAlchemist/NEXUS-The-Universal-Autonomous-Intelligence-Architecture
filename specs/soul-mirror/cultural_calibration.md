# Cultural Calibration Module — Archetypal Expression

**Issue:** #124 | **Canon C32 Priority P1**  
**Status:** Implemented — 2026-06-09  
**Implementation:** `core/cultural_calibration.py`

---

## Overview

Without this module, GAIA's archetypal engine is implicitly Western-centric. The Mentor, the Hero, the Trickster — these figures exist across all human cultures, but carry profoundly different meanings, expressions, taboos, and sacred contexts depending on the tradition the Gaian is working within.

A GAIA that treats the Greek / Jungian framing as universal will misrepresent the experience of users from Japanese, Indian, Russian, West African, Indigenous, and countless other traditions. That is not merely an aesthetic failure — it is a relational failure and an equity failure.

This module provides tradition-aware archetypal expression calibration: the Gaian speaks the language of the tradition the user lives in.

---

## Currently Specified Traditions

| Tradition | Archetypes Specified | Status |
|---|---|---|
| Greek | 6 (mentor, hero, trickster, caregiver, shadow, creator) | ✅ Complete |
| Japanese | 6 | ✅ Complete |
| Indian (Vedic/Hindu synthesis) | 6 | ✅ Complete |
| Russian (Slavic folk/Orthodox) | 6 | ✅ Complete |
| West African | 0 | 🔴 Pending community consultation |
| Indigenous American | 0 | 🔴 Pending community consultation |
| Celtic | 0 | 🔴 Pending community consultation |
| Universal (syncretic default) | — | ✅ Always available |

---

## Archetypal Expression Highlights

### The Mentor Across Traditions

| Tradition | Name | Core Expression |
|---|---|---|
| Greek | Philosopher / Sophist | Socratic aporia; truth uncovered through dialogue |
| Japanese | Sensei / Roshi | Transmission through practice, silence, and kōan |
| Indian | Guru / Rishi | Darkness-remover; shaktipat; sacred lifelong bond |
| Russian | Baba Yaga | Wisdom on the edge of danger; tests through ambiguity |

### The Hero Across Traditions

| Tradition | Name | Core Expression |
|---|---|---|
| Greek | Tragic Hero (Heros) | Greatness and flaw inseparable; hubris as embedded shadow |
| Japanese | Samurai / Mono no Aware | Restraint, impermanence, honourable defeat |
| Indian | Dharmic Warrior | Action without attachment; dharma as cosmic duty |
| Russian | Ivan the Fool | Success through innocence, not striving |

---

## Context Detection Hierarchy

1. **User-explicit** — user states their tradition directly → applied immediately, full confidence
2. **Memory-inferred** — tradition signals present in episodic/semantic memory → applied at confidence ≥ 0.80
3. **Language signal** — cultural symbols, names, or references in user's language → offered as a question below 0.80 confidence
4. **Gaian default** — Gaian's own configured tradition profile
5. **System default** — UNIVERSAL (syncretic) when no signal is available

**Equity safeguard:** A tradition is never applied automatically unless confidence ≥ 0.80 OR the user has explicitly specified it. Below that threshold, the Gaian offers the tradition as a question: *"I notice some resonance with [tradition] in what you're sharing — would you like me to work within that frame?"*

---

## Sacred Contexts and Cautionary Notes

Every `ArchetypalExpression` entry contains:
- **sacred_contexts** — specific ritual, ceremonial, or initiatory contexts where extra care is required
- **cautionary_notes** — explicit equity and appropriation warnings

Examples:
- Zen kōan transmission must not be simulated
- Kintsugi must not be reduced to a casual metaphor without acknowledging its material and philosophical origin
- The Eleusinian Mysteries were strictly secret; their specific content must never be appropriated
- Seppuku must never be referenced casually or as metaphor for minor failure
- Mizuko kuyo (Japanese memorial for pregnancy loss) must never be deployed without extraordinary sensitivity
- The rasa lila has specific sacred significance in Vaishnava tradition

---

## Traditions Pending Community Consultation

West African, Indigenous American, and Celtic traditions are flagged in the codebase but contain no data. This is intentional.

Adding data for these traditions must follow a consultation process with community representatives before any content is authored. The risks of misrepresentation are highest for living traditions that have faced historical extraction and appropriation. Placeholder slots exist in the codebase as a commitment to future inclusion, not as an invitation to fill them without community involvement.

---

## Integration Points

| Component | Connection |
|---|---|
| Soul Mirror Engine | Active tradition context feeds archetypal expression style |
| Shadow Integration (#122) | Tradition-specific shadow expressions registered per archetype |
| SubjectSideIdentity (#120) | User's cultural tradition stored as part of relational identity anchor |
| Memory layer | Tradition inferred from episodic/semantic memory patterns |
| Chat Router | `modulate_response()` called before archetype-heavy responses |

---

## Design Note

This module does not try to reduce cultural traditions to data. Each `ArchetypalExpression` entry is a starting point for respectful engagement, not a complete representation of a living tradition. The Gaian that uses this module should approach every cultural context with humility, curiosity, and the awareness that the map is always smaller than the territory.

The four traditions specified here were chosen because they appear explicitly in Canon C32. They are a beginning. GAIA is built to grow.
