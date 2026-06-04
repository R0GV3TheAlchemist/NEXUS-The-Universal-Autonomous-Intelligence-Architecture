// src/trust/policy-engine.ts
// GAIA-OS Trust & Permission Policy Engine
// Canon ref: C01 (Gaian Sovereignty), SOVEREIGNTY.md
// Issue: #229

export enum TrustTier {
  Safe = 0,      // Read-only, no side effects — auto-approved
  Guarded = 1,   // Writes, API calls, state changes — session trust required
  Sensitive = 2, // External comms, deletes, identity ops — explicit approval
  Critical = 3,  // OS-level, data export, boot config — biometric + explicit
}

export enum SessionTrustLevel {
  Minimal = "minimal",     // Tier 0 only
  Standard = "standard",   // Tier 0-1
  Elevated = "elevated",   // Tier 0-2
  Sovereign = "sovereign", // Tier 0-3 (requires biometric/passphrase)
}

export enum PolicyDecision {
  Approved = "approved",
  Denied = "denied",
  Pending = "pending",
}

export interface ToolPolicy {
  tool: string;
  tier: TrustTier;
  scope: string[];
  requires_session_trust: SessionTrustLevel;
  audit: boolean;
  description: string;
}

export interface PolicyRequest {
  tool: string;
  input_summary: string;
  context?: Record<string, unknown>;
}

export interface PolicyResult {
  decision: PolicyDecision;
  tier: TrustTier;
  tool: string;
  reason: string;
  requires_approval_prompt?: string;
  timestamp: string;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  tool: string;
  tier: TrustTier;
  decision: PolicyDecision;
  session_trust: SessionTrustLevel;
  gaian_override: boolean;
  input_summary: string;
  context_summary: string;
}

const DEFAULT_POLICIES: Record<string, ToolPolicy> = {
  "memory.read": { tool: "memory.read", tier: TrustTier.Safe, scope: ["memory:read"], requires_session_trust: SessionTrustLevel.Minimal, audit: false, description: "Read from persistent memory store" },
  "rag.query": { tool: "rag.query", tier: TrustTier.Safe, scope: ["rag:read"], requires_session_trust: SessionTrustLevel.Minimal, audit: false, description: "Query the RAG knowledge base" },
  "files.list": { tool: "files.list", tier: TrustTier.Safe, scope: ["files:read"], requires_session_trust: SessionTrustLevel.Minimal, audit: false, description: "List files in a directory" },
  "files.read": { tool: "files.read", tier: TrustTier.Safe, scope: ["files:read"], requires_session_trust: SessionTrustLevel.Minimal, audit: false, description: "Read file contents" },
  "github.create_issue": { tool: "github.create_issue", tier: TrustTier.Guarded, scope: ["repo:write"], requires_session_trust: SessionTrustLevel.Standard, audit: true, description: "Create a new GitHub issue" },
  "github.push_files": { tool: "github.push_files", tier: TrustTier.Guarded, scope: ["repo:write"], requires_session_trust: SessionTrustLevel.Standard, audit: true, description: "Push files to a GitHub repository" },
  "github.merge_pr": { tool: "github.merge_pr", tier: TrustTier.Sensitive, scope: ["repo:admin"], requires_session_trust: SessionTrustLevel.Elevated, audit: true, description: "Merge a pull request" },
  "memory.write": { tool: "memory.write", tier: TrustTier.Guarded, scope: ["memory:write"], requires_session_trust: SessionTrustLevel.Standard, audit: true, description: "Write to persistent memory store" },
  "memory.delete": { tool: "memory.delete", tier: TrustTier.Sensitive, scope: ["memory:delete"], requires_session_trust: SessionTrustLevel.Elevated, audit: true, description: "Delete a memory entry" },
  "files.write": { tool: "files.write", tier: TrustTier.Guarded, scope: ["files:write"], requires_session_trust: SessionTrustLevel.Standard, audit: true, description: "Write or create a local file" },
  "files.delete": { tool: "files.delete", tier: TrustTier.Sensitive, scope: ["files:delete"], requires_session_trust: SessionTrustLevel.Elevated, audit: true, description: "Delete a local file" },
  "external.api_call": { tool: "external.api_call", tier: TrustTier.Sensitive, scope: ["external:write"], requires_session_trust: SessionTrustLevel.Elevated, audit: true, description: "Call an external third-party API" },
  "os.config_change": { tool: "os.config_change", tier: TrustTier.Critical, scope: ["os:admin"], requires_session_trust: SessionTrustLevel.Sovereign, audit: true, description: "Modify OS-level configuration" },
  "data.export": { tool: "data.export", tier: TrustTier.Critical, scope: ["data:export"], requires_session_trust: SessionTrustLevel.Sovereign, audit: true, description: "Export Gaian data outside the system" },
};

const TRUST_LEVEL_MAX_TIER: Record<SessionTrustLevel, TrustTier> = {
  [SessionTrustLevel.Minimal]: TrustTier.Safe,
  [SessionTrustLevel.Standard]: TrustTier.Guarded,
  [SessionTrustLevel.Elevated]: TrustTier.Sensitive,
  [SessionTrustLevel.Sovereign]: TrustTier.Critical,
};

export class PolicyEngine {
  private policies: Record<string, ToolPolicy>;
  private sessionTrust: SessionTrustLevel;
  private auditLog: AuditEntry[] = [];
  private pendingApprovals: Map<string, PolicyRequest> = new Map();

  constructor(sessionTrust: SessionTrustLevel = SessionTrustLevel.Standard, customPolicies?: Record<string, ToolPolicy>) {
    this.sessionTrust = sessionTrust;
    this.policies = { ...DEFAULT_POLICIES, ...customPolicies };
  }

  evaluate(request: PolicyRequest): PolicyResult {
    const timestamp = new Date().toISOString();
    const policy = this.policies[request.tool];

    if (!policy) {
      const result: PolicyResult = { decision: PolicyDecision.Denied, tier: TrustTier.Critical, tool: request.tool, reason: `Tool "${request.tool}" is not registered in the policy registry.`, timestamp };
      this.writeAudit(request, result, null);
      return result;
    }

    const maxAllowedTier = TRUST_LEVEL_MAX_TIER[this.sessionTrust];

    if (policy.tier === TrustTier.Safe) {
      const result: PolicyResult = { decision: PolicyDecision.Approved, tier: policy.tier, tool: request.tool, reason: "Tier 0 (Safe) — auto-approved.", timestamp };
      if (policy.audit) this.writeAudit(request, result, policy);
      return result;
    }

    if (policy.tier > maxAllowedTier) {
      const result: PolicyResult = { decision: PolicyDecision.Denied, tier: policy.tier, tool: request.tool, reason: `Session trust level "${this.sessionTrust}" does not permit Tier ${policy.tier} actions.`, timestamp };
      this.writeAudit(request, result, policy);
      return result;
    }

    if (policy.tier === TrustTier.Guarded) {
      const result: PolicyResult = { decision: PolicyDecision.Approved, tier: policy.tier, tool: request.tool, reason: `Tier 1 (Guarded) — approved at session trust "${this.sessionTrust}".`, timestamp };
      this.writeAudit(request, result, policy);
      return result;
    }

    const approvalId = `approval-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    this.pendingApprovals.set(approvalId, request);
    const result: PolicyResult = {
      decision: PolicyDecision.Pending,
      tier: policy.tier,
      tool: request.tool,
      reason: `Tier ${policy.tier} (${TrustTier[policy.tier]}) — explicit Gaian approval required.`,
      requires_approval_prompt: `⚠️ GAIA is requesting a ${TrustTier[policy.tier].toUpperCase()} action.\nTool: ${policy.tool}\nDescription: ${policy.description}\nAction: ${request.input_summary}\nApproval ID: ${approvalId}\nDo you approve? (yes / no)`,
      timestamp,
    };
    this.writeAudit(request, result, policy);
    return result;
  }

  resolve(approvalId: string, approved: boolean, gaianOverride = false): PolicyResult {
    const request = this.pendingApprovals.get(approvalId);
    const timestamp = new Date().toISOString();
    if (!request) return { decision: PolicyDecision.Denied, tier: TrustTier.Critical, tool: "unknown", reason: `No pending approval found for ID "${approvalId}".`, timestamp };
    this.pendingApprovals.delete(approvalId);
    const policy = this.policies[request.tool];
    const result: PolicyResult = { decision: approved ? PolicyDecision.Approved : PolicyDecision.Denied, tier: policy?.tier ?? TrustTier.Critical, tool: request.tool, reason: approved ? "Gaian explicitly approved." : "Gaian denied.", timestamp };
    this.writeAudit(request, result, policy ?? null, gaianOverride);
    return result;
  }

  register(policy: ToolPolicy): void { this.policies[policy.tool] = policy; }
  setSessionTrust(level: SessionTrustLevel): void { this.sessionTrust = level; }
  getSessionTrust(): SessionTrustLevel { return this.sessionTrust; }
  getAuditLog(): AuditEntry[] { return [...this.auditLog]; }
  getPendingApprovals(): Map<string, PolicyRequest> { return new Map(this.pendingApprovals); }

  private buildApprovalPrompt(policy: ToolPolicy, request: PolicyRequest, approvalId: string): string {
    return [`⚠️ GAIA is requesting a ${TrustTier[policy.tier].toUpperCase()} action.`, `Tool: ${policy.tool}`, `Description: ${policy.description}`, `Action: ${request.input_summary}`, `Approval ID: ${approvalId}`, `Do you approve? (yes / no)`].join("\n");
  }

  private writeAudit(request: PolicyRequest, result: PolicyResult, policy: ToolPolicy | null, gaianOverride = false): void {
    if (!policy?.audit && result.decision === PolicyDecision.Approved && (policy?.tier ?? 0) === 0) return;
    this.auditLog.push({ id: `audit-${Date.now()}-${Math.random().toString(36).slice(2)}`, timestamp: result.timestamp, tool: request.tool, tier: policy?.tier ?? TrustTier.Critical, decision: result.decision, session_trust: this.sessionTrust, gaian_override: gaianOverride, input_summary: request.input_summary, context_summary: JSON.stringify(request.context ?? {}) });
  }
}

export default PolicyEngine;
