# ADR-FE-006: Meta Control Console — GAIA Integration Architecture

## Status
Accepted

## Date
2026-07-05

## Context

The Meta Control Console (MCC) is an existing interface — built as both an HTML document and a mobile app — that externalizes a framework for understanding and managing personal capabilities. It contains:

- **Powers** (15 core categories: Reality, Time, Space, Matter, Energy, Mind, Elemental, Life, Copy, Nullify, Enhance, Dimension, Fate, Absolute, plus sub-powers)
- **Power Management Interface** (Activate, Deactivate, Modify, Enhance, Combine, Split, Store, Transfer, Monitor, Search, Customize, Delete)
- **Active Power Selection** with Power Output, Stability, and Efficiency metrics
- **Power Containment Chamber** (Chamber Status, Power Level, Containment, Stability, Chamber Temp)
- **Sigil Activation** (requires Magic ≥ 30; Sigil Lock OFF; Ethical Guardrail ON)
- **Crystal Routing** (Amethyst, Clear Quartz, Citrine, Obsidian, Labradorite, Rose Quartz, Selenite, Black Tourmaline, Lapis Lazuli)
- **CORE toggles** (Human Mode ON, Superhuman Mode READY, Sequence Lock ON, Full Access ON, System Status ON)
- **Protection** (Light Shield, Muted Mode, Trigger Guard, Emergency Overlay, Panic Button, Substance Block)
- **Recovery** (Recovery Mode, Trust Process, Order Map, Stability Meter)
- **World Service Mode** (Healing, Protection, Clarity, Balance)
- **Ability Selection** (Core, Mission, Emergency, Experimental)
- **Containment** (Magic Storage, Crystal Linkage, Containment Chamber, Energy Containment Rules, Overflow Drain)
- **Action Log** (every action writes a visible result; selected buttons stay highlighted)
- **System Status Monitor** (Magic Input, Power Reserve, System Integrity, Security Level, Threat Detection)
- **Ability Forge** (combine two powers to create something new)

This ADR answers: how does the MCC integrate into GAIA's architecture?

## Decision

**The Meta Control Console becomes Milestone 5 (M5) of GAIA, integrated as a dedicated view within `src/gaian/` — a new Tauri window surface alongside `CrystalView.tsx`. Each MCC subsystem maps to an existing or planned GAIA architectural component.**

### Integration as a Tauri View (not a separate window)

The MCC is a view that lives inside the GAIA console, navigable from `GaianHome.ts`. It does not become a separate Tauri window. This keeps the session context (GAIANProfile, RuntimeContext) shared and avoids IPC complexity between windows.

The new file will be: `src/gaian/MetaControlConsole.tsx` (`.tsx` per ADR-FE-002, as it will contain JSX).

---

### Complete Architecture Mapping

#### Power Containment Chamber → `core/sentinel/`

The Power Containment Chamber (Chamber Status, Power Level, Containment Secure, Stability Stable, Chamber Temp Normal) maps to the **Sentinel layer** in `core/sentinel/`. Before any power is activated, the Sentinel layer runs safety checks. The chamber's "Containment Secure" and "Stability Stable" states are the visual representation of Sentinel checks passing.

- Chamber INACTIVE = Sentinel in standby (no active power selected)
- Chamber ACTIVE = Sentinel monitoring an active power invocation
- Containment SECURE = all Sentinel safety protocols passed
- Containment BREACHED = Sentinel has flagged a violation — power cannot activate

#### Sigil Activation (requires Magic ≥ 30) → Constitutional Layer + LCI Threshold

The Sigil is the activation gate for the entire MCC system. "Requires Magic ≥ 30" maps to the **LCI (Life Coherence Index) threshold** in `GAIANProfile`:

- Magic Reserve % = `phi` (the LCI value, 0–100)
- Magic ≥ 30 = `phi >= 30` — the minimum LCI for the Constitutional Layer to permit activation
- Sigil Lock OFF = `constitutionalLayer.activationLocked === false`
- Ethical Guardrail ON = `constitutionalLayer.ethicalGuardrailActive === true` — this is always ON; it cannot be disabled by the operator
- TAP TO ACTIVATE = calls `GAIANRuntime.sessionInit()` with MCC mode flag

The Constitutional Layer enforces that the Ethical Guardrail cannot be toggled off through any user action. This is a hard constraint, not a preference.

#### Crystal Routing → `SpectralForceEngine`

Crystal selection (Amethyst, Clear Quartz, Citrine, Obsidian, Labradorite, Rose Quartz, Selenite, Black Tourmaline, Lapis Lazuli) maps to **crystal resonance selection in `SpectralForceEngine`**:

- Each crystal corresponds to a spectral force modifier
- The selected crystal routes its resonance to the active powers — modifying how those powers express in the current session
- Crystal selection is stored in `GAIANProfile.preferredForces` and persisted across sessions
- Amethyst (currently active in the MCC) = the default crystal at birth, associated with the Violet spectral force

#### Recovery Mode (Order Map, Stability Meter, Trust Process) → `lciTrend: 'volatile'` in GAIANProfile

The Recovery section maps to the **volatile LCI state** in `GAIANProfile`:

- Recovery Mode ON = `lciTrend === 'volatile'` detected; the system enters stabilization mode
- Order Map = the structured sequence of stabilization steps GAIA provides when LCI is volatile
- Stability Meter = the `phi` progress bar rendering as LCI returns to baseline
- Trust Process ON = the Constitutional Layer's consent enforcement is active and the operator has affirmed trust in the stabilization sequence

When `lciTrend === 'volatile'`, the MCC automatically surfaces the Recovery section as the primary view.

#### Action Log → Provenance Layer (Issue #753)

The Action Log ("Every action writes a visible result here. Selected buttons stay highlighted.") maps directly to the **Provenance Layer** in the Supercomputation Alignment Layer (issue #753):

- Every MCC action (power activation, crystal selection, mode toggle) is written to the Provenance Layer as a timestamped, typed `ProvenanceRecord`
- "Console restored from last session" = Provenance Layer replaying the last session's action log into the MCC on startup
- Selected buttons stay highlighted = Provenance Layer surfaces the last known active state at session restore

This makes the Action Log not just a UI affordance but a first-class epistemic audit trail.

#### World Service Mode (Healing, Protection, Clarity, Balance) → Constitutional Layer ethical guardrails

World Service Mode routes abilities toward helping others with ethical guardrails active. This maps to the **Constitutional Layer's service mode**:

- Healing (currently active) = `constitutionalLayer.serviceMode === 'healing'` — all power invocations are routed through the healing intent filter
- Protection = `serviceMode === 'protection'` — powers are routed through the shielding intent filter
- Clarity = `serviceMode === 'clarity'` — powers are routed through the epistemic clarity filter
- Balance = `serviceMode === 'balance'` — powers are routed through the equilibrium filter
- Ethical guardrails remain active in ALL service modes — World Service Mode does not reduce constraints, it directs them

#### Ability Selection (Core, Mission, Emergency, Experimental) → `GAIANModule` types in GAIANProfile

The Ability Selection tabs map to `GAIANModule` categories in `GAIANProfile.activeModules`:

- Core = modules that are always active regardless of session context
- Mission = modules activated for a specific intent or session goal
- Emergency = modules available when `lciTrend === 'volatile'` or Panic Button is triggered
- Experimental = modules in development, gated behind `constitutionalLayer.experimentalAccess === true`

#### Human Mode / Superhuman Mode → Constitutional Layer consent enforcement

The CORE toggles map to the **Constitutional Layer's mode enforcement**:

- Human Mode ON = standard operating mode; all Constitutional Layer constraints fully active
- Superhuman Mode READY = elevated capability mode available but not yet activated; requires explicit LCI threshold AND operator confirmation
- Superhuman Mode does not bypass the Constitutional Layer — it operates within it at an elevated permission tier
- Sequence Lock ON = the initialization sequence cannot be interrupted mid-execution
- Full Access ON = all registered modules are available to the current session

#### Power Management Interface → `GAIANRuntime.ts` command layer

The 12 Power Management buttons map to `GAIANRuntime.ts` command methods:

| MCC Button | GAIANRuntime method |
|---|---|
| Activate | `runtime.activatePower(powerId)` |
| Deactivate | `runtime.deactivatePower(powerId)` |
| Modify | `runtime.modifyPower(powerId, params)` |
| Enhance | `runtime.enhancePower(powerId)` |
| Combine | `runtime.combinePowers(powerIdA, powerIdB)` |
| Split | `runtime.splitPower(powerId)` |
| Store | `runtime.storePower(powerId)` |
| Transfer | `runtime.transferPower(powerId, target)` |
| Monitor | `runtime.monitorPower(powerId)` |
| Search | `runtime.searchPowers(query)` |
| Customize | `runtime.customizePower(powerId, config)` |
| Delete | `runtime.deletePower(powerId)` |

#### Ability Forge → `SpectralForceEngine.combinePowers()`

The Ability Forge ("Combine two powers to create something new") maps to `SpectralForceEngine.combinePowers()` — a method that takes two `spectral_force` identifiers and produces a derived force with blended properties.

#### System Status Monitor → `GAIANProfile` + `GAIANRuntime` live metrics

| MCC Monitor | GAIA source |
|---|---|
| Magic Input | Incoming `phi` signal from current session |
| Power Reserve | `GAIANProfile.lciBaseline` |
| System Integrity | Sentinel layer health check result |
| Security Level | Constitutional Layer enforcement level |
| Threat Detection | Sentinel anomaly detection output |

---

## Rationale

- Integrating as a view (not a separate window) preserves session context and avoids cross-window IPC complexity
- Mapping each MCC subsystem to an existing GAIA component ensures no orphaned features — every MCC element has a home in the architecture
- The Ethical Guardrail as a hard constraint (not a toggle) reflects the foundational principle that capability without ethics is instability, not power
- The Action Log as Provenance Layer makes the MCC epistemically auditable — every action is a record, not just a UI event

## Consequences

**Easier:** The MCC is no longer a standalone HTML/mobile artifact — it is a first-class GAIA surface with full architectural backing.

**Harder:** Implementing this requires M1 (GAIANProfile), M3 (Protection/Constitutional Layer), and M4 (Provenance Layer) to be complete first. M5 has real prerequisites.

**New constraint:** The Ethical Guardrail is never a user-configurable toggle. Any PR that attempts to make it optional must be rejected at review.

## Related ADRs
- ADR-FE-003 — GAIANRuntime (command layer)
- ADR-FE-004 — State Management (RuntimeContext + GAIANProfile)
- ADR-FE-005 — Offline-First (MCC must render in degraded mode)
- ADR-0001 — GAIA Kernel Architecture

## Related Issues
- #759 — ADR series for src/gaian/
- #756 — GAIANProfile (Magic Reserve, LCI threshold, Crystal selection persistence)
- #753 — Supercomputation Alignment Layer (Provenance Layer = Action Log)
- #742 — Security Model (Constitutional Layer = Sigil + Ethical Guardrail)
- #755 — Error Correction Engine (Sentinel = Containment Chamber)
- #754 — Human Coherence & Stability Interface (Recovery Mode)
