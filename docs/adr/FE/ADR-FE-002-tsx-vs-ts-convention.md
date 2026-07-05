# ADR-FE-002: .tsx vs .ts File Extension Convention in src/gaian/

## Status
Accepted

## Date
2026-07-05

## Context

In `src/gaian/`, all files use the `.ts` extension except `CrystalView.tsx`. This inconsistency raises the question: is `.tsx` reserved for a specific purpose, or is it accidental?

The distinction matters because:
- `.tsx` enables JSX syntax (React component markup inline with TypeScript)
- `.ts` is pure TypeScript — no JSX
- Tooling (tsc, ESLint, Vite) treats them differently
- Developers need a clear rule to know which extension to use when creating new files

Currently `GaianHome.ts`, `GaianChatView.ts`, and `AlignmentIndicator.ts` all render UI surfaces but use `.ts`. `CrystalView.tsx` renders UI and uses `.tsx`. No documented rule explains the difference.

## Decision

**`.tsx` is reserved for files that contain JSX/React component syntax.**
**.ts` is used for all other TypeScript files — including files that orchestrate or produce UI output through non-JSX means.**

Specifically:
- A file gets `.tsx` if and only if it contains JSX expressions (e.g., `return <Component />` or `<div>...</div>`)
- A file that manages UI state, triggers renders, or configures visual output without JSX syntax stays `.ts`
- `CrystalView.tsx` is correctly named — it contains JSX
- `GaianHome.ts`, `GaianChatView.ts`, `AlignmentIndicator.ts` are correctly named if they do not contain JSX — this must be verified when those files are opened for modification

**When creating a new file in `src/gaian/`:**
- Does it contain `return (<...>)` JSX syntax? → use `.tsx`
- Does it not contain JSX? → use `.ts`
- When in doubt: start with `.ts`, rename to `.tsx` only when JSX is added

## Rationale

- Consistent with standard TypeScript/React community conventions
- Prevents tooling misconfiguration (tsc will error on JSX in a `.ts` file without explicit config changes)
- Keeps the rule simple and verifiable — no judgment call required

## Consequences

**Easier:** Every new file has a clear, mechanical rule for its extension. PR review can enforce this without ambiguity.

**Harder:** Existing files may need extension review when they are modified (a `.ts` file that introduces JSX must be renamed).

**New constraint:** PR checklist must include extension verification for any new `src/gaian/` file.

## Related ADRs
- ADR-FE-001 — Language Boundaries
- ADR-FE-003 — GAIANRuntime as Central Execution Loop

## Related Issues
- #759 — ADR series for src/gaian/
- #756 — GAIANProfile (new files will be created in src/gaian/ — this rule applies)
