export type GaiaMode =
  | 'discovery'
  | 'build'
  | 'validation'
  | 'reflect'
  | 'recover'
  | 'protect'
  | 'offline';

export interface GaiaState {
  system_state: GaiaMode;
  coherence: number;
  energy: number;
  stress: number;
  entropy: number;
  learning_rate: number;
  exploration_rate: number;
  conservation_rate: number;
  personal_coherence: number;
  planetary_coherence: number;
  high_risk_allowed: boolean;
  canon_write_allowed: boolean;
  last_transition_at: string;
  session_id: string;
}

export interface TalismanEffect {
  coherence_delta: number;
  energy_delta: number;
  stress_delta: number;
  entropy_delta: number;
}

export interface Talisman {
  id: string;
  name: string;
  purpose: string;
  created_by: string;
  status: 'dormant' | 'active' | 'archived';
  effect: TalismanEffect;
  created_at: string;
  last_activated_at: string | null;
  notes: string;
}
