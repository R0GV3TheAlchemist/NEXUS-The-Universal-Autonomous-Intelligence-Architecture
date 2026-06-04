// tests/trust/policy-engine.test.ts
// GAIA-OS Trust & Permission Policy Engine — Unit Tests
// Issue: #229

import { PolicyEngine, PolicyDecision, SessionTrustLevel, TrustTier } from "../../src/trust/policy-engine";

describe("PolicyEngine", () => {
  let engine: PolicyEngine;

  beforeEach(() => { engine = new PolicyEngine(SessionTrustLevel.Standard); });

  describe("Tier 0 (Safe)", () => {
    it("auto-approves memory.read at Minimal trust", () => {
      engine.setSessionTrust(SessionTrustLevel.Minimal);
      const result = engine.evaluate({ tool: "memory.read", input_summary: "reading session prefs" });
      expect(result.decision).toBe(PolicyDecision.Approved);
      expect(result.tier).toBe(TrustTier.Safe);
    });
    it("auto-approves rag.query at any trust level", () => {
      const result = engine.evaluate({ tool: "rag.query", input_summary: "query crystal compendium" });
      expect(result.decision).toBe(PolicyDecision.Approved);
    });
  });

  describe("Tier 1 (Guarded)", () => {
    it("approves github.create_issue at Standard trust", () => {
      const result = engine.evaluate({ tool: "github.create_issue", input_summary: "create sprint issue" });
      expect(result.decision).toBe(PolicyDecision.Approved);
    });
    it("denies github.create_issue at Minimal trust", () => {
      engine.setSessionTrust(SessionTrustLevel.Minimal);
      const result = engine.evaluate({ tool: "github.create_issue", input_summary: "create issue" });
      expect(result.decision).toBe(PolicyDecision.Denied);
    });
  });

  describe("Tier 2 (Sensitive)", () => {
    it("returns Pending with approval prompt at Elevated trust", () => {
      engine.setSessionTrust(SessionTrustLevel.Elevated);
      const result = engine.evaluate({ tool: "files.delete", input_summary: "delete old logs" });
      expect(result.decision).toBe(PolicyDecision.Pending);
      expect(result.requires_approval_prompt).toBeDefined();
    });
    it("denies files.delete at Standard trust", () => {
      const result = engine.evaluate({ tool: "files.delete", input_summary: "delete logs" });
      expect(result.decision).toBe(PolicyDecision.Denied);
    });
    it("resolves approval when Gaian approves", () => {
      engine.setSessionTrust(SessionTrustLevel.Elevated);
      const pending = engine.evaluate({ tool: "files.delete", input_summary: "delete logs" });
      const approvalId = pending.requires_approval_prompt?.match(/Approval ID: (approval-[\\w-]+)/)?.[1];
      expect(approvalId).toBeDefined();
      const resolved = engine.resolve(approvalId!, true);
      expect(resolved.decision).toBe(PolicyDecision.Approved);
    });
    it("denies when Gaian rejects", () => {
      engine.setSessionTrust(SessionTrustLevel.Elevated);
      const pending = engine.evaluate({ tool: "files.delete", input_summary: "delete logs" });
      const approvalId = pending.requires_approval_prompt?.match(/Approval ID: (approval-[\\w-]+)/)?.[1];
      const resolved = engine.resolve(approvalId!, false);
      expect(resolved.decision).toBe(PolicyDecision.Denied);
    });
  });

  describe("Unregistered tools", () => {
    it("denies any unregistered tool", () => {
      const result = engine.evaluate({ tool: "unknown.tool", input_summary: "do something" });
      expect(result.decision).toBe(PolicyDecision.Denied);
      expect(result.reason).toContain("not registered");
    });
  });

  describe("Audit log", () => {
    it("records Tier 1 actions", () => {
      engine.evaluate({ tool: "github.create_issue", input_summary: "create issue" });
      const log = engine.getAuditLog();
      expect(log.length).toBeGreaterThan(0);
      expect(log[0].tool).toBe("github.create_issue");
    });
  });
});
