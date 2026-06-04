// src/trust/audit-log.ts
// GAIA-OS Immutable Audit Log with SHA-256 hash chain
// Canon ref: C01, SOVEREIGNTY.md
// Issue: #229

import { AuditEntry } from "./policy-engine";
import { createHash } from "crypto";

export interface AuditChainEntry extends AuditEntry {
  previous_hash: string;
  entry_hash: string;
}

export class AuditLog {
  private chain: AuditChainEntry[] = [];
  private static GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000";

  append(entry: AuditEntry): AuditChainEntry {
    const previous_hash = this.chain.length > 0 ? this.chain[this.chain.length - 1].entry_hash : AuditLog.GENESIS_HASH;
    const payload = JSON.stringify({ ...entry, previous_hash });
    const entry_hash = createHash("sha256").update(payload).digest("hex");
    const chainEntry: AuditChainEntry = { ...entry, previous_hash, entry_hash };
    this.chain.push(chainEntry);
    return chainEntry;
  }

  verify(): boolean {
    for (let i = 1; i < this.chain.length; i++) {
      if (this.chain[i].previous_hash !== this.chain[i - 1].entry_hash) return false;
    }
    return true;
  }

  export(): AuditChainEntry[] { return [...this.chain]; }
  getLength(): number { return this.chain.length; }
}

export default AuditLog;
