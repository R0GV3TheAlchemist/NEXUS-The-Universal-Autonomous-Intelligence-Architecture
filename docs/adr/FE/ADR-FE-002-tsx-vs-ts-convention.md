# ADR-FE-002: Why CrystalView is .tsx and Everything Else is .ts

## Status
Accepted

## Date
2026-07-05

## Context

`CrystalView.tsx` uses the `.tsx` extension, which signals JSX/TSX syntax — the ability to write HTML-like markup directly in TypeScript. All other files in `src/gaian/` use `.ts`. This creates a visible inconsistency: `GaianChatView.ts` and `GaianHome.ts` both render UI but do not use `.tsx`.

Without a declared convention, contributors cannot tell whether `.tsx` is reserved, required, or simply inconsistently applied.

## Decision

**The `.tsx` extension is reserved for files that directly return or render JSX markup.** Files that orchestrate, configure, or control UI without directly writing JSX markup use `.ts`.

Specific rules:

1. A file uses `.tsx` if and only if it contains JSX syntax (`<Component />`, `<div>`, etc.) in its return value or render output.
2. A file uses `.ts` if it manages state, handles events, calls IPC, or composes logic — even if it ultimately causes UI to render.
3. `CrystalView.tsx` is correctly named: it returns JSX.
4. `GaianChatView.ts` and `GaianHome.ts` should be audited. If they contain JSX, rename to `.tsx`. If they do not, the current extension is correct.
5. This rule applies to all new files in `src/gaian/` going forward.

## Rationale

The `.tsx` / `.ts` distinction is the TypeScript compiler's own signal. Using it consistently means the file extension communicates intent: open a `.tsx` file and expect markup; open a `.ts` file and expect logic. This reduces cognitive overhead and makes the codebase self-documenting at the filesystem level.

Alternatives considered:
- **All files as `.tsx`:** Rejected. Unnecessary — the JSX transform has a cost and `.tsx` files have stricter parsing rules. Using `.tsx` everywhere is noise.
- **All files as `.ts`:** Rejected. Loses the signal entirely and requires opening files to understand their role.

## Consequences

**Easier:**
- File extension communicates role without opening the file
- Consistent with TypeScript community convention

**Harder:**
- `GaianChatView.ts` and `GaianHome.ts` need an audit pass
- Contributors must remember to choose extension deliberately

**New constraints:**
- New file extension must be explicitly chosen using this rule, not defaulted
- PR checklist should include: "Is the file extension correct per ADR-FE-002?"

## Related ADRs
- ADR-FE-001 (Language boundaries)
- ADR-FE-003 (GAIANRuntime as central execution loop)
