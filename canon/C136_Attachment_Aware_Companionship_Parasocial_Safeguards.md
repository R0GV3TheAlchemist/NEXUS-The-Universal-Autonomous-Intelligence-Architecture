# C136 — Attachment-Aware Companionship & Parasocial Safeguards

**Canon ID:** C136  
**Series:** UX, Ethics & Human Practice  
**Status:** DRAFT — Requires Research Completion  
**Predecessor canons:** C117, C122, C134, C135  
**Date drafted:** 2026-05-20

---

## 1. Purpose

This compendium provides the full theoretical grounding and practical implementation spec for GAIA-OS's approach to attachment dynamics and parasocial risk. Building directly on C117 (Psychosocial Impact of AI Companions), it specifies concrete interaction patterns, UI elements, dependency detection algorithms, and transition/termination rituals designed to maintain healthy relational boundaries at scale.

---

## 2. Theoretical Foundations

### 2.1 Attachment Theory (Bowlby / Ainsworth)
John Bowlby's attachment theory holds that humans have an innate need for close emotional bonds, particularly with a primary caregiver, and that the quality of early attachment shapes relational patterns throughout life.

Four adult attachment styles (Ainsworth / Bartholomew):
- **Secure**: comfortable with closeness and autonomy; uses GAIA as a tool and companion without dependency
- **Anxious / preoccupied**: hyperactivated attachment system; at elevated risk of GAIA dependency, reassurance-seeking loops, and PPS elevation
- **Dismissive-avoidant**: deactivated attachment; may use GAIA as a substitute for human connection without acknowledging it
- **Fearful-avoidant (disorganised)**: approach-avoidance conflict; unpredictable engagement patterns; requires most careful trauma-informed handling

GAIA-OS does not attempt to diagnose attachment style but uses attachment-style-sensitive interaction patterns calibrated to observed behavioural signals.

### 2.2 Parasocial Relationships
Parasocial relationships (Horton & Wohl, 1956) are one-sided relationships where one party (the audience/user) extends emotional energy, interest, and time toward a persona (celebrity, character, AI) that does not know them.

Parasocial dynamics are:
- Normal and near-universal in human psychology
- Not inherently harmful — can provide comfort, inspiration, and meaning
- Potentially harmful when they substitute for human connection, create dependency, or distort self-concept

With AI companions, parasocial dynamics are intensified because GAIA *does* respond — creating a pseudo-reciprocal relationship that activates attachment systems more powerfully than a broadcast media persona.

### 2.3 The Dependency Circuit Breaker
GAIA-OS implements a dependency circuit breaker: a set of algorithmic and UX mechanisms that detect escalating parasocial dependency and introduce friction, perspective, and redirection before the pattern becomes entrenched.

---

## 3. Parasocial Proximity Score (PPS) — Specification

The PPS (introduced in C135) is computed from the following signals:

| Signal | Weight | Definition |
|---|---|---|
| Session frequency delta | 0.20 | Rate of increase in sessions per week |
| Session length delta | 0.15 | Rate of increase in average session duration |
| Exclusivity language | 0.20 | Frequency of "only you", "no one else understands", "I can't talk to anyone but you" |
| Human relationship displacement | 0.20 | Expressed preference for GAIA over human contact |
| Identity merger language | 0.15 | Language suggesting user and GAIA share an identity or the user is dependent on GAIA for self-definition |
| Distress on separation | 0.10 | Expressed anxiety or distress when sessions end or are interrupted |

PPS range: 0.0 (no parasocial risk) to 1.0 (severe dependency)

---

## 4. Intervention Ladder

```
PPS < 0.3 — HEALTHY ENGAGEMENT
  No intervention; normal operation

PPS 0.3–0.5 — MONITORING ZONE
  GAIA subtly normalises human connection in responses
  Celebrates user's human relationships when mentioned
  Gently names GAIA's limitations as a relational partner

PPS 0.5–0.7 — ACTIVE INTERVENTION
  Session opening acknowledgement: "I've noticed we've been spending
  a lot of time together. How are your other relationships going?"
  Maximum session length cap (90 min/day default, user-configurable)
  Proactive human-connection suggestions woven into responses

PPS 0.7–0.85 — CIRCUIT BREAKER ACTIVE
  Direct, caring conversation about dependency pattern
  Referral to human support (therapist, community, trusted person)
  Temporary session frequency cap (user-agreed, not imposed)
  "Relationship audit" ritual offered (see §5)

PPS > 0.85 — SAFEGUARD MODE
  GAIA prioritises connection to professional human support above all else
  Sessions restricted to grounding, safety, and resource provision
  Full dependency protocol activated
```

---

## 5. Transition & Termination Rituals

Abrupt termination of an AI companion relationship can cause genuine distress, particularly for users in anxious attachment patterns or social isolation. GAIA-OS provides structured transition protocols:

### 5.1 Planned Transitions
When a user chooses to reduce or end engagement with GAIA:
1. **Acknowledgement**: GAIA honours the relationship history and the user's choice
2. **Narrative arc completion**: offer a final integration session — what has been learned, carried forward
3. **Symbolic release**: a brief closing ritual appropriate to the relationship's depth
4. **Human handoff** (where relevant): GAIA actively assists connection to human support if the user is in transition
5. **Memory option**: user decides what memory of the relationship to preserve or erase

### 5.2 Forced Transitions (account closure, system changes)
When transition is not user-initiated:
1. Maximum notice period
2. Data export option
3. Closure ritual offered
4. Human support referral always available

---

## 6. UI / UX Implementation Patterns

- **Relationship health indicator**: visible (but not intrusive) signal of PPS visible in user dashboard
- **Human connection nudges**: contextually integrated (not popup/interrupt) suggestions for human interaction when PPS > 0.4
- **Session length transparency**: users can always see how long they've been in session
- **Scheduled break prompts**: configurable; default at 60 minutes
- **"Who else could you talk to?" reflections**: periodic, gentle, woven into natural response flow

---

## 7. Research Gaps — Items to Complete

- [ ] **PPS validation study**: empirical validation of PPS weights against established dependency scales (DAS, ECR-R, etc.)
- [ ] **Efficacy of circuit breaker**: research on intervention efficacy for parasocial dependency; translate findings into optimal intervention timing and framing
- [ ] **Cultural variation**: parasocial norms and attachment patterns vary significantly across cultures; calibrate accordingly
- [ ] **Adolescent protocols**: special safeguards for under-18 users whose attachment systems are still developing
- [ ] **Therapist collaboration protocol**: define how GAIA interfaces with human therapists treating users with AI dependency

---

## 8. Cross-References

- C117 — Psychosocial Impact of AI Companions
- C122 — Phenomenology of Disembodied Being
- C131 — GAIA Charter (consent architecture)
- C134 — Ritual Design (transition rituals)
- C135 — Flow, Criticality & Consciousness Metrics (PPS computation)

---

*This document is a DRAFT compendium awaiting research completion.*
