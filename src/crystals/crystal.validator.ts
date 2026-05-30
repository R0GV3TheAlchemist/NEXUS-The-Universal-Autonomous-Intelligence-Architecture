/**
 * src/crystals/crystal.validator.ts
 * GAIA-OS Crystal Intelligence Engine — Intake Guard
 *
 * This module is the validation layer for the crystal database.
 * It runs against every CrystalRecord before a batch is committed,
 * ensuring schema contracts are upheld and data quality is maintained.
 *
 * ─── DESIGN PHILOSOPHY ────────────────────────────────────────────────────────
 *
 * The validator is OPINIONATED but GRADUATED.
 * Not every problem is an error — some are warnings that require human review.
 * The severity system has three tiers:
 *
 *   ERROR    — record cannot be safely used; must be fixed before commit
 *   WARNING  — data gap or inconsistency that degrades reasoning quality
 *   INFO     — advisory note; does not block commit
 *
 * The validator NEVER throws on data problems. It collects all issues and
 * returns them in a structured ValidationResult. Only `assertRecord()` throws,
 * and only for use in test suites that want fast-fail behaviour.
 *
 * ─── CHECKS PERFORMED ─────────────────────────────────────────────────────────
 *
 * Domain A — GAIA Resonance
 *   A1  gaia_resonance parses to at least one valid GAIAModule            ERROR
 *   A2  no unknown tokens in gaia_resonance string                        WARNING
 *   A3  primary module consistent with CHAKRA_MODULE_MAP                  WARNING
 *       (intentional overrides are valid — this flags them for review)
 *
 * Domain B — Angel Number
 *   B1  angel_number is a registered AngelNumber value or null            ERROR
 *   B2  angel_number gaia_module matches primary resolved module          WARNING
 *
 * Domain C — Safety Coherence
 *   C1  safe_for_water=false requires non-null safety_warning             ERROR
 *   C2  safe_for_hardware=false requires non-null safety_warning          ERROR
 *   C3  CRITICAL/HIGH RiskTier requires safety_warning present            ERROR
 *   C4  safety_warning present on a NONE-tier record                      WARNING
 *       (may indicate the warning text was too mild to elevate the tier,
 *        or it is an unnecessary warning — either way needs a human eye)
 *
 * Domain D — Physical Consistency
 *   D1  hardness_min <= hardness_max when both non-null                   ERROR
 *   D2  specific_gravity_min <= specific_gravity_max when both non-null   ERROR
 *   D3  ri_min <= ri_max when both non-null                               ERROR
 *
 * ─── EXPORTS ──────────────────────────────────────────────────────────────────
 *
 *   validateRecord(record)         — full validation, returns ValidationResult
 *   validateBatch(records, label)  — validates array, returns BatchReport
 *   assertRecord(record)           — throws ValidationError on first ERROR
 *
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-30
 * Schema: CrystalRecord v1.3
 */

import type { CrystalRecord, AngelNumber } from './db/crystal.schema';
import {
  ANGEL_NUMBER_MAP,
  CHAKRA_MODULE_MAP,
} from './db/metaphysical.data';
import {
  resolveGAIAResonance,
  getSafetyProfile,
} from './crystal.theory';

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

/** Severity of a single validation issue */
export type IssueSeverity = 'ERROR' | 'WARNING' | 'INFO';

/**
 * A single validation issue found on a CrystalRecord.
 * Every issue is self-describing so it can be rendered in CI logs,
 * UI review tools, or GAIA's internal reasoning without additional context.
 */
export interface ValidationIssue {
  /** Rule code — matches the Domain+Number scheme in the file header */
  code:     string;
  severity: IssueSeverity;
  /** Human-readable description of the problem */
  message:  string;
  /** The field path that failed (dot-notation, e.g. "metaphysical.gaia_resonance") */
  field:    string;
  /** The actual value that triggered the issue (stringified) */
  actual:   string;
  /** What the value should be, or what would fix it */
  expected: string;
}

/** The complete validation result for a single CrystalRecord */
export interface ValidationResult {
  /** Crystal display name */
  crystal_name: string;
  /** True only if no ERROR-severity issues are present */
  valid: boolean;
  /** All issues found across all domains */
  issues: ValidationIssue[];
  /** Convenience counts per severity */
  counts: {
    errors:   number;
    warnings: number;
    info:     number;
  };
}

/** Aggregate report for a full batch validation run */
export interface BatchReport {
  /** Label identifying the batch (e.g. "BATCH_A1", "BATCH_B3") */
  label:          string;
  /** ISO 8601 timestamp of when the validation was run */
  run_at:         string;
  /** Total records validated */
  total:          number;
  /** Records with zero ERROR issues */
  passed:         number;
  /** Records with at least one ERROR issue */
  failed:         number;
  /** True if every record passed */
  batch_valid:    boolean;
  /** Per-record results, failed records first */
  results:        ValidationResult[];
  /** Flat list of all ERROR issues across all records, for CI output */
  all_errors:     ValidationIssue[];
  /** Total counts across all records */
  totals: {
    errors:   number;
    warnings: number;
    info:     number;
  };
}

/**
 * Thrown by `assertRecord()` when a record has ERROR-severity issues.
 * Contains the full ValidationResult for programmatic inspection.
 */
export class ValidationError extends Error {
  constructor(
    public readonly result: ValidationResult
  ) {
    const errorList = result.issues
      .filter(i => i.severity === 'ERROR')
      .map(i => `[${i.code}] ${i.message}`)
      .join('; ');
    super(
      `Crystal validation failed for "${result.crystal_name}": ${errorList}`
    );
    this.name = 'ValidationError';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// INTERNAL HELPERS
// ─────────────────────────────────────────────────────────────────────────────

/** Shorthand factory for a ValidationIssue */
function issue(
  code:     string,
  severity: IssueSeverity,
  message:  string,
  field:    string,
  actual:   string,
  expected: string
): ValidationIssue {
  return { code, severity, message, field, actual, expected };
}

/** All legal AngelNumber values as a Set for O(1) membership tests */
const LEGAL_ANGEL_NUMBERS: Set<number | null> = new Set<number | null>([
  null,
  1, 2, 3, 4, 5, 6, 7, 8, 9,
  11, 22, 33,
  23, 44, 55, 66, 77, 88, 99,
  111, 222, 333, 444, 555, 666, 777, 888, 999,
]);

// ─────────────────────────────────────────────────────────────────────────────
// DOMAIN A — GAIA RESONANCE
// ─────────────────────────────────────────────────────────────────────────────

function checkResonanceDomain(record: CrystalRecord): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const resonance = resolveGAIAResonance(record);
  const rawField  = 'metaphysical.gaia_resonance';
  const rawValue  = record.metaphysical.gaia_resonance ?? '<null>';

  // A1 — must resolve to at least one valid module
  if (resonance.has_unknown_token && resonance.all_modules.length === 0) {
    issues.push(issue(
      'A1', 'ERROR',
      `gaia_resonance "${rawValue}" contains no recognisable GAIAModule ids. ` +
      `Valid ids: ClarusLens, AnchorPrism, SomnusVeil, SovereignCore, ViriditasHeart, Noosphere, QuantumNexus.`,
      rawField,
      rawValue,
      'At least one valid GAIAModule id'
    ));
  }

  // A2 — unknown tokens present (warning, not error — could be a new module in draft)
  if (resonance.has_unknown_token && resonance.unknown_tokens.length > 0) {
    issues.push(issue(
      'A2', 'WARNING',
      `gaia_resonance contains unrecognised token(s): ${resonance.unknown_tokens.join(', ')}. ` +
      `These will be ignored by the reasoning engine.`,
      rawField,
      resonance.unknown_tokens.join(', '),
      'Only valid GAIAModule ids'
    ));
  }

  // A3 — primary module consistency with chakra map
  const expectedModule = CHAKRA_MODULE_MAP[record.metaphysical.chakra_primary];
  const actualPrimary  = resonance.primary_module;
  if (expectedModule && actualPrimary !== expectedModule) {
    issues.push(issue(
      'A3', 'WARNING',
      `Primary module "${actualPrimary}" does not match the canonical ` +
      `CHAKRA_MODULE_MAP assignment for chakra "${record.metaphysical.chakra_primary}" ` +
      `(expected "${expectedModule}"). This may be an intentional override — verify.`,
      rawField,
      actualPrimary,
      expectedModule
    ));
  }

  return issues;
}

// ─────────────────────────────────────────────────────────────────────────────
// DOMAIN B — ANGEL NUMBER
// ─────────────────────────────────────────────────────────────────────────────

function checkAngelNumberDomain(record: CrystalRecord): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const angelNumber = record.metaphysical.angel_number as number | null;
  const field       = 'metaphysical.angel_number';

  // B1 — must be a registered AngelNumber value or null
  if (!LEGAL_ANGEL_NUMBERS.has(angelNumber)) {
    issues.push(issue(
      'B1', 'ERROR',
      `angel_number ${angelNumber} is not a valid AngelNumber. ` +
      `Allowed values: null, 1-9, 11, 22, 33, 23, 44-99 (sacred), 111-999 (sequences).`,
      field,
      String(angelNumber),
      'A registered AngelNumber value or null'
    ));
  }

  // B2 — angel number's gaia_module should align with primary resolved module
  if (angelNumber != null && LEGAL_ANGEL_NUMBERS.has(angelNumber)) {
    const angelDef      = ANGEL_NUMBER_MAP.get(angelNumber as AngelNumber);
    const resonance     = resolveGAIAResonance(record);
    const primaryModule = resonance.primary_module;

    if (angelDef && angelDef.gaia_module !== primaryModule) {
      issues.push(issue(
        'B2', 'WARNING',
        `angel_number ${angelNumber} ("${angelDef.name}") is associated with ` +
        `module "${angelDef.gaia_module}" in the registry, but the crystal's ` +
        `primary module resolves to "${primaryModule}". This may be intentional — verify.`,
        field,
        `${angelNumber} → ${angelDef.gaia_module}`,
        `${angelNumber} → ${primaryModule}`
      ));
    }
  }

  return issues;
}

// ─────────────────────────────────────────────────────────────────────────────
// DOMAIN C — SAFETY COHERENCE
// ─────────────────────────────────────────────────────────────────────────────

function checkSafetyDomain(record: CrystalRecord): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const { safe_for_water, safe_for_hardware } = record.physical;
  const warning = record.metaphysical.safety_warning;
  const safety  = getSafetyProfile(record);

  // C1 — water-unsafe without a warning
  if (!safe_for_water && warning == null) {
    issues.push(issue(
      'C1', 'ERROR',
      `safe_for_water is false but safety_warning is null. ` +
      `Every water-unsafe stone must carry an explicit safety_warning.`,
      'metaphysical.safety_warning',
      'null',
      'Non-null safety_warning describing the water hazard'
    ));
  }

  // C2 — hardware-unsafe without a warning
  if (!safe_for_hardware && warning == null) {
    issues.push(issue(
      'C2', 'ERROR',
      `safe_for_hardware is false but safety_warning is null. ` +
      `Every hardware-unsafe stone must carry an explicit safety_warning.`,
      'metaphysical.safety_warning',
      'null',
      'Non-null safety_warning describing the hardware hazard'
    ));
  }

  // C3 — CRITICAL/HIGH risk tier requires a warning
  if (
    (safety.risk_tier === 'CRITICAL' || safety.risk_tier === 'HIGH') &&
    warning == null
  ) {
    issues.push(issue(
      'C3', 'ERROR',
      `RiskTier is ${safety.risk_tier} but safety_warning is null. ` +
      `CRITICAL and HIGH risk stones must always carry an explicit warning.`,
      'metaphysical.safety_warning',
      'null',
      `Non-null safety_warning (RiskTier: ${safety.risk_tier})`
    ));
  }

  // C4 — NONE-tier with a warning present (advisory only)
  if (safety.risk_tier === 'NONE' && warning != null) {
    issues.push(issue(
      'C4', 'WARNING',
      `safety_warning is present but RiskTier computed as NONE. ` +
      `Either the warning text should contain keywords that elevate the tier, ` +
      `or the warning may be unnecessary. Review the warning text.`,
      'metaphysical.safety_warning',
      `"${warning.slice(0, 60)}${warning.length > 60 ? '...' : ''}"`,
      'Either elevate with hazard keywords or remove the warning'
    ));
  }

  return issues;
}

// ─────────────────────────────────────────────────────────────────────────────
// DOMAIN D — PHYSICAL CONSISTENCY
// ─────────────────────────────────────────────────────────────────────────────

function checkPhysicalDomain(record: CrystalRecord): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const p = record.physical;

  // D1 — hardness range
  if (
    p.hardness_min != null && p.hardness_max != null &&
    p.hardness_min > p.hardness_max
  ) {
    issues.push(issue(
      'D1', 'ERROR',
      `hardness_min (${p.hardness_min}) is greater than hardness_max (${p.hardness_max}).`,
      'physical.hardness_min / physical.hardness_max',
      `${p.hardness_min} > ${p.hardness_max}`,
      'hardness_min ≤ hardness_max'
    ));
  }

  // D2 — specific gravity range
  if (
    p.specific_gravity_min != null && p.specific_gravity_max != null &&
    p.specific_gravity_min > p.specific_gravity_max
  ) {
    issues.push(issue(
      'D2', 'ERROR',
      `specific_gravity_min (${p.specific_gravity_min}) is greater than ` +
      `specific_gravity_max (${p.specific_gravity_max}).`,
      'physical.specific_gravity_min / physical.specific_gravity_max',
      `${p.specific_gravity_min} > ${p.specific_gravity_max}`,
      'specific_gravity_min ≤ specific_gravity_max'
    ));
  }

  // D3 — refractive index range
  if (
    p.ri_min != null && p.ri_max != null &&
    p.ri_min > p.ri_max
  ) {
    issues.push(issue(
      'D3', 'ERROR',
      `ri_min (${p.ri_min}) is greater than ri_max (${p.ri_max}).`,
      'physical.ri_min / physical.ri_max',
      `${p.ri_min} > ${p.ri_max}`,
      'ri_min ≤ ri_max'
    ));
  }

  return issues;
}

// ─────────────────────────────────────────────────────────────────────────────
// PUBLIC API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * validateRecord
 *
 * Runs all 12 validation rules across all 4 domains against a single
 * CrystalRecord. Returns a structured ValidationResult.
 *
 * Never throws — all issues are collected and returned.
 *
 * @param record — Any CrystalRecord from the database
 * @returns       ValidationResult
 */
export function validateRecord(record: CrystalRecord): ValidationResult {
  const allIssues: ValidationIssue[] = [
    ...checkResonanceDomain(record),
    ...checkAngelNumberDomain(record),
    ...checkSafetyDomain(record),
    ...checkPhysicalDomain(record),
  ];

  const errors   = allIssues.filter(i => i.severity === 'ERROR').length;
  const warnings = allIssues.filter(i => i.severity === 'WARNING').length;
  const info     = allIssues.filter(i => i.severity === 'INFO').length;

  return {
    crystal_name: record.name,
    valid:        errors === 0,
    issues:       allIssues,
    counts:       { errors, warnings, info },
  };
}

/**
 * validateBatch
 *
 * Validates an array of CrystalRecords and produces an aggregate BatchReport.
 * Failed records appear first in the results array for easy CI triage.
 *
 * @param records — Array of CrystalRecords (typically a full batch export)
 * @param label   — Identifying label for the batch (e.g. "BATCH_A1")
 * @returns         BatchReport
 */
export function validateBatch(
  records: CrystalRecord[],
  label: string
): BatchReport {
  const results = records.map(r => validateRecord(r));

  // Failed records first
  results.sort((a, b) => {
    if (!a.valid && b.valid)  return -1;
    if (a.valid  && !b.valid) return 1;
    return b.counts.errors - a.counts.errors;
  });

  const passed    = results.filter(r => r.valid).length;
  const failed    = results.length - passed;
  const allErrors = results.flatMap(r => r.issues.filter(i => i.severity === 'ERROR'));

  const totals = results.reduce(
    (acc, r) => ({
      errors:   acc.errors   + r.counts.errors,
      warnings: acc.warnings + r.counts.warnings,
      info:     acc.info     + r.counts.info,
    }),
    { errors: 0, warnings: 0, info: 0 }
  );

  return {
    label,
    run_at:      new Date().toISOString(),
    total:       records.length,
    passed,
    failed,
    batch_valid: failed === 0,
    results,
    all_errors:  allErrors,
    totals,
  };
}

/**
 * assertRecord
 *
 * Validates a CrystalRecord and throws a ValidationError if any ERROR-severity
 * issues are found. Intended for use in test suites that want fast-fail
 * behaviour on the first invalid record.
 *
 * @param record — Any CrystalRecord from the database
 * @throws ValidationError if the record has any ERROR-severity issues
 */
export function assertRecord(record: CrystalRecord): void {
  const result = validateRecord(record);
  if (!result.valid) {
    throw new ValidationError(result);
  }
}

/**
 * formatBatchReport
 *
 * Renders a BatchReport as a human-readable string suitable for
 * CI logs, terminal output, or GAIA's internal reasoning traces.
 *
 * @param report — BatchReport from validateBatch()
 * @returns       Formatted string
 */
export function formatBatchReport(report: BatchReport): string {
  const lines: string[] = [
    `╔${'═'.repeat(66)}`,
    `║ GAIA Crystal Validator — Batch Report`,
    `║ Batch : ${report.label}`,
    `║ Run at: ${report.run_at}`,
    `║ Result: ${
      report.batch_valid
        ? '✅ ALL RECORDS VALID'
        : `❌ ${report.failed} of ${report.total} RECORDS FAILED`
    }`,
    `║ Totals: ${report.total} records · ` +
      `${report.totals.errors} errors · ` +
      `${report.totals.warnings} warnings · ` +
      `${report.totals.info} info`,
    `╚${'═'.repeat(66)}`,
  ];

  if (!report.batch_valid) {
    lines.push('');
    lines.push('FAILED RECORDS:');
    lines.push('');

    for (const result of report.results.filter(r => !r.valid)) {
      lines.push(`  ❌ ${result.crystal_name} — ${result.counts.errors} error(s), ${result.counts.warnings} warning(s)`);
      for (const iss of result.issues) {
        const icon = iss.severity === 'ERROR' ? '✗' : iss.severity === 'WARNING' ? '⚠' : 'ℹ';
        lines.push(`      ${icon} [${iss.code}] ${iss.message}`);
        lines.push(`          field   : ${iss.field}`);
        lines.push(`          actual  : ${iss.actual}`);
        lines.push(`          expected: ${iss.expected}`);
      }
      lines.push('');
    }
  }

  if (report.totals.warnings > 0 && report.batch_valid) {
    lines.push('');
    lines.push('WARNINGS (batch passed, but review recommended):');
    lines.push('');

    for (const result of report.results.filter(r => r.counts.warnings > 0)) {
      lines.push(`  ⚠  ${result.crystal_name} — ${result.counts.warnings} warning(s)`);
      for (const iss of result.issues.filter(i => i.severity === 'WARNING')) {
        lines.push(`      ⚠ [${iss.code}] ${iss.message}`);
      }
      lines.push('');
    }
  }

  return lines.join('\n');
}
