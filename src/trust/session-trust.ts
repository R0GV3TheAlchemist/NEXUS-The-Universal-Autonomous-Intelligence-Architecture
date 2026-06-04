// src/trust/session-trust.ts
// GAIA-OS Session Trust Level Management
// Canon ref: C01
// Issue: #229

import { SessionTrustLevel } from "./policy-engine";

export interface SessionTrustState {
  level: SessionTrustLevel;
  elevated_at?: string;
  elevated_by?: "passphrase" | "biometric" | "gaian_override";
  expires_at?: string;
}

export class SessionTrustManager {
  private state: SessionTrustState;

  constructor(initialLevel: SessionTrustLevel = SessionTrustLevel.Standard) {
    this.state = { level: initialLevel };
  }

  getLevel(): SessionTrustLevel {
    this.checkExpiry();
    return this.state.level;
  }

  elevate(level: SessionTrustLevel, method: "passphrase" | "biometric" | "gaian_override", ttlMinutes?: number): void {
    this.state = { level, elevated_at: new Date().toISOString(), elevated_by: method, expires_at: ttlMinutes ? new Date(Date.now() + ttlMinutes * 60 * 1000).toISOString() : undefined };
  }

  downgrade(level: SessionTrustLevel = SessionTrustLevel.Standard): void {
    this.state = { level };
  }

  getState(): SessionTrustState {
    this.checkExpiry();
    return { ...this.state };
  }

  private checkExpiry(): void {
    if (this.state.expires_at && new Date() > new Date(this.state.expires_at)) {
      this.state = { level: SessionTrustLevel.Standard };
    }
  }
}

export default SessionTrustManager;
