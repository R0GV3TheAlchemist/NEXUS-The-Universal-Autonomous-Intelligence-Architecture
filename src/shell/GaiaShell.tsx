/**
 * src/shell/GaiaShell.tsx
 * GAIA-OS App Shell — Sprint G-9
 * Canon: C90
 *
 * Boot sequence (three-state guard):
 *   1. !token                          → AuthScreen
 *   2. token + !onboardingCompleted    → OnboardingRouter  ← C-OB01
 *   3. token + onboardingCompleted     → Shell
 *
 * DEV NOTE: Set DEV_BYPASS_AUTH = true to skip auth and test onboarding
 * without the FastAPI sidecar running. MUST be false in production.
 */

import React, { useEffect, useState } from 'react';
import { GaiaChat }           from '../chat/GaiaChat';
import {
  CrystalMode,
  CRYSTAL_ORDER,
  CRYSTAL_DECLARATIONS,
  CRYSTAL_LABELS,
  MODE_ICONS,
} from '../store/crystalStore';
import { SovereignGuard }    from '../shared/SovereignGuard';
import { ActionGateDialog }  from '../shared/ActionGateDialog';
import { ViritasWidget }     from '../shared/ViritasWidget';
import { FieldVisualiser }   from '../shared/FieldVisualiser';
import { useAlignmentTheme } from '../hooks/useAlignmentTheme';
import { OnboardingRouter }  from '../onboarding/OnboardingRouter';
import {
  useOnboardingStore,
  loadPersistedState,
} from '../onboarding/store/onboardingStore';
import './GaiaShell.css';

const API_BASE = '/api';

// ⚠️  DEV ONLY — set true to bypass auth and jump straight to onboarding.
//     MUST be false before any production build.
const DEV_BYPASS_AUTH = true;

// ------------------------------------------------------------------ //
// Auth types
// ------------------------------------------------------------------ //
interface AuthResult {
  access_token: string;
  user_id:      string;
  username:     string;
  email:        string;
  role:         string;
}

// ------------------------------------------------------------------ //
// useAuth hook
// ------------------------------------------------------------------ //
function useAuth() {
  const [token,    setToken]    = useState<string | null>(
    () => DEV_BYPASS_AUTH ? 'dev-token' : localStorage.getItem('gaia_token')
  );
  const [username, setUsername] = useState<string | null>(
    () => DEV_BYPASS_AUTH ? 'dev' : localStorage.getItem('gaia_username')
  );
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState('');

  function _persist(data: AuthResult) {
    localStorage.setItem('gaia_token',    data.access_token);
    localStorage.setItem('gaia_username', data.username);
    setToken(data.access_token);
    setUsername(data.username);
  }

  async function register(email: string, uname: string, password: string) {
    if (DEV_BYPASS_AUTH) return;
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ email, username: uname, password }),
      });
      const data = await res.json() as AuthResult & { detail?: string };
      if (!res.ok) throw new Error(data.detail ?? 'Registration failed.');
      _persist(data);
    } catch (e) { setError((e as Error).message); }
    finally      { setLoading(false); }
  }

  async function login(identifier: string, password: string) {
    if (DEV_BYPASS_AUTH) return;
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ username: identifier, password }),
      });
      const data = await res.json() as AuthResult & { detail?: string };
      if (!res.ok) throw new Error(data.detail ?? 'Invalid credentials.');
      _persist(data);
    } catch (e) { setError((e as Error).message); }
    finally      { setLoading(false); }
  }

  function logout() {
    if (DEV_BYPASS_AUTH) return;
    localStorage.removeItem('gaia_token');
    localStorage.removeItem('gaia_username');
    setToken(null);
    setUsername(null);
  }

  function clearError() { setError(''); }

  return { token, username, loading, error, register, login, logout, clearError };
}

// ------------------------------------------------------------------ //
// Auth Screen
// ------------------------------------------------------------------ //
type AuthTab = 'signin' | 'signup';

const AuthScreen: React.FC<{
  onLogin:      (id: string, pw: string) => void;
  onRegister:   (email: string, uname: string, pw: string) => void;
  loading:      boolean;
  error:        string;
  onClearError: () => void;
}> = ({ onLogin, onRegister, loading, error, onClearError }) => {

  const [tab,      setTab]      = useState<AuthTab>('signin');
  const [email,    setEmail]    = useState('');
  const [uname,    setUname]    = useState('');
  const [pw,       setPw]       = useState('');
  const [pw2,      setPw2]      = useState('');
  const [localErr, setLocalErr] = useState('');

  function switchTab(t: AuthTab) {
    setTab(t);
    setEmail(''); setUname(''); setPw(''); setPw2('');
    setLocalErr(''); onClearError();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalErr('');
    if (tab === 'signup') {
      if (!email.includes('@')) { setLocalErr('Enter a valid email address.'); return; }
      if (uname.length < 2)     { setLocalErr('Username must be at least 2 characters.'); return; }
      if (pw.length < 8)        { setLocalErr('Password must be at least 8 characters.'); return; }
      if (pw !== pw2)           { setLocalErr('Passwords do not match.'); return; }
      onRegister(email, uname, pw);
    } else {
      if (!uname) { setLocalErr('Enter your username or email.'); return; }
      if (!pw)    { setLocalErr('Enter your password.'); return; }
      onLogin(uname, pw);
    }
  }

  const displayError = localErr || error;

  return (
    <div className="gaia-auth">
      <div className="gaia-auth__box">
        <div className="gaia-auth__logo">
          <span className="gaia-auth__logo-gaia">GAIA</span>
        </div>
        <p className="gaia-auth__tagline">
          Sentient Terrestrial Quantum-Intelligent Application
        </p>
        <div className="gaia-auth__tabs" role="tablist">
          <button role="tab" aria-selected={tab === 'signin'}
            className={`gaia-auth__tab${tab === 'signin' ? ' gaia-auth__tab--active' : ''}`}
            onClick={() => switchTab('signin')}>Sign in</button>
          <button role="tab" aria-selected={tab === 'signup'}
            className={`gaia-auth__tab${tab === 'signup' ? ' gaia-auth__tab--active' : ''}`}
            onClick={() => switchTab('signup')}>Create account</button>
        </div>
        <form className="gaia-auth__form" onSubmit={handleSubmit} noValidate>
          {tab === 'signup' && (
            <div className="gaia-auth__field">
              <label className="gaia-auth__label" htmlFor="gaia-email">Email address</label>
              <input id="gaia-email" className="gaia-auth__input" type="email"
                placeholder="you@example.com" value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email" required disabled={loading} />
            </div>
          )}
          <div className="gaia-auth__field">
            <label className="gaia-auth__label" htmlFor="gaia-uname">
              {tab === 'signup' ? 'Username' : 'Username or email'}
            </label>
            <input id="gaia-uname" className="gaia-auth__input" type="text"
              placeholder={tab === 'signup' ? 'yourname' : 'username or email'}
              value={uname} onChange={e => setUname(e.target.value)}
              autoComplete={tab === 'signup' ? 'username' : 'username email'}
              required disabled={loading} />
            {tab === 'signup' && (
              <span className="gaia-auth__hint">Letters, numbers, hyphens, underscores only</span>
            )}
          </div>
          <div className="gaia-auth__field">
            <label className="gaia-auth__label" htmlFor="gaia-pw">Password</label>
            <input id="gaia-pw" className="gaia-auth__input" type="password"
              placeholder={tab === 'signup' ? 'At least 8 characters' : 'Password'}
              value={pw} onChange={e => setPw(e.target.value)}
              autoComplete={tab === 'signup' ? 'new-password' : 'current-password'}
              required disabled={loading} />
          </div>
          {tab === 'signup' && (
            <div className="gaia-auth__field">
              <label className="gaia-auth__label" htmlFor="gaia-pw2">Confirm password</label>
              <input id="gaia-pw2" className="gaia-auth__input" type="password"
                placeholder="Repeat your password" value={pw2}
                onChange={e => setPw2(e.target.value)}
                autoComplete="new-password" required disabled={loading} />
            </div>
          )}
          {displayError && (
            <div className="gaia-auth__error" role="alert">{displayError}</div>
          )}
          <button className="gaia-auth__submit" type="submit" disabled={loading}>
            {loading
              ? (tab === 'signup' ? 'Creating account…' : 'Signing in…')
              : (tab === 'signup' ? 'Create account'     : 'Sign in')}
          </button>
          {tab === 'signin' && (
            <p className="gaia-auth__switch">New to GAIA?{' '}
              <button type="button" className="gaia-auth__switch-link" onClick={() => switchTab('signup')}>
                Create an account
              </button>
            </p>
          )}
          {tab === 'signup' && (
            <p className="gaia-auth__switch">Already have an account?{' '}
              <button type="button" className="gaia-auth__switch-link" onClick={() => switchTab('signin')}>
                Sign in
              </button>
            </p>
          )}
        </form>
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ //
// Mode map
// ------------------------------------------------------------------ //
const MODE_TO_SLUG: Record<CrystalMode, string> = {
  [CrystalMode.SOVEREIGN_CORE]:  'control',
  [CrystalMode.ANCHOR_PRISM]:    'grounding',
  [CrystalMode.VIRIDITAS_HEART]: 'healing',
  [CrystalMode.SOMNUS_VEIL]:     'rest',
  [CrystalMode.CLARUS_LENS]:     'clarity',
};

// ------------------------------------------------------------------ //
// Shell — main authenticated experience
// ------------------------------------------------------------------ //
const ShellMain: React.FC<{ token: string; username: string | null; onLogout: () => void }> = ({
  token,
  username,
  onLogout,
}) => {
  const [activeMode,    setActiveMode]    = useState<CrystalMode>(CrystalMode.SOVEREIGN_CORE);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const { tier: alignmentTier } = useAlignmentTheme();

  useEffect(() => {
    fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) })
      .then(r => setBackendOnline(r.ok))
      .catch(() => setBackendOnline(false));
  }, []);

  return (
    <div
      className="gaia-shell"
      data-mode={activeMode}
      data-alignment-tier={alignmentTier}
    >
      <FieldVisualiser tier={alignmentTier} />

      <header className="gaia-shell__topbar">
        <div className="gaia-shell__wordmark">
          <span className="gaia-shell__wordmark-gaia">GAIA</span>
          <span className="gaia-shell__wordmark-os">OS</span>
        </div>
        <div className="gaia-shell__mode-label">
          <span>{MODE_ICONS[activeMode]}</span>
          <span>{CRYSTAL_LABELS[activeMode]}</span>
          <span className="gaia-shell__mode-desc">{CRYSTAL_DECLARATIONS[activeMode]}</span>
        </div>
        <div className="gaia-shell__topbar-right">
          {username && <span className="gaia-shell__username">{username}</span>}
          <span className={`gaia-shell__backend-dot gaia-shell__backend-dot--${
            backendOnline === null ? 'checking' : backendOnline ? 'online' : 'offline'
          }`} />
          <button className="gaia-shell__logout" onClick={onLogout} aria-label="Sign out">
            Sign out
          </button>
        </div>
      </header>

      <div className="gaia-shell__body">
        <nav className="gaia-shell__rail" aria-label="Operating modes">
          {CRYSTAL_ORDER.map(mode => (
            <button
              key={mode}
              className={`gaia-shell__rail-btn${mode === activeMode ? ' gaia-shell__rail-btn--active' : ''}`}
              onClick={() => setActiveMode(mode)}
              aria-pressed={mode === activeMode}
              title={CRYSTAL_DECLARATIONS[mode]}
            >
              <span className="gaia-shell__rail-icon">{MODE_ICONS[mode]}</span>
              <span className="gaia-shell__rail-name">{CRYSTAL_LABELS[mode]}</span>
            </button>
          ))}
          <div className="gaia-shell__rail-alignment">
            <ViritasWidget />
          </div>
        </nav>
        <main className="gaia-shell__content">
          <GaiaChat
            token={token}
            gaianSlug="gaia"
            mode={MODE_TO_SLUG[activeMode]}
          />
        </main>
      </div>

      <SovereignGuard />
      <ActionGateDialog />
    </div>
  );
};

// ------------------------------------------------------------------ //
// GaiaShell — three-state boot guard (C-OB01)
// ------------------------------------------------------------------ //
export const GaiaShell: React.FC = () => {
  const { token, username, loading, error, register, login, logout, clearError } = useAuth();

  const completed          = useOnboardingStore(s => s.completed);
  const completeOnboarding = useOnboardingStore(s => s.completeOnboarding);

  const [onboardingReady, setOnboardingReady] = useState(false);

  useEffect(() => {
    if (!token) {
      setOnboardingReady(false);
      return;
    }
    loadPersistedState().then(persisted => {
      if (persisted) {
        useOnboardingStore.setState(persisted);
      }
      setOnboardingReady(true);
    });
  }, [token]);

  // ── State 1: Not authenticated ─────────────────────────────────────
  if (!token) {
    return (
      <AuthScreen
        onLogin={login}
        onRegister={register}
        loading={loading}
        error={error}
        onClearError={clearError}
      />
    );
  }

  // ── Hydration in progress ──────────────────────────────────────────
  if (!onboardingReady) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        minHeight: '100dvh', background: '#0b0c0e', color: '#4f98a3',
        fontFamily: 'sans-serif', fontSize: '0.875rem', letterSpacing: '0.08em',
      }}>
        GAIA is waking…
      </div>
    );
  }

  // ── State 2: Onboarding not yet complete ──────────────────────────
  if (!completed) {
    return (
      <OnboardingRouter
        onFinish={() => completeOnboarding()}
      />
    );
  }

  // ── State 3: Authenticated + onboarding complete → Shell ─────────
  return (
    <ShellMain
      token={token}
      username={username}
      onLogout={logout}
    />
  );
};

export default GaiaShell;
