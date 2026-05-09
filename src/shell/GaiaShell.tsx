/**
 * src/shell/GaiaShell.tsx
 * GAIA-OS App Shell — Sprint G-9
 * Canon: C90
 *
 * Full auth flow: Sign In + Create Account tabs
 * Shell: top bar + mode rail + chat pane
 *
 * Sovereignty layer:
 *   <SovereignGuard /> — Axiom I always-visible control bar
 *   <ActionGateDialog /> — YELLOW/RED tier action confirmation modal
 *
 * Viriditas layer:
 *   <ViritasWidget />      — compact orb pinned to the bottom of the left rail
 *   useAlignmentTheme()    — Phase 2: injects alignment CSS tokens onto :root
 *                            and sets data-alignment-tier on the shell root
 */

import React, { useEffect, useState } from 'react';
import { GaiaChat } from '../chat/GaiaChat';
import {
  CrystalMode,
  CRYSTAL_ORDER,
  CRYSTAL_DECLARATIONS,
  CRYSTAL_LABELS,
  MODE_ICONS,
} from '../store/crystalStore';
import { SovereignGuard }     from '../shared/SovereignGuard';
import { ActionGateDialog }   from '../shared/ActionGateDialog';
import { ViritasWidget }      from '../shared/ViritasWidget';
import { useAlignmentTheme }  from '../hooks/useAlignmentTheme';
import './GaiaShell.css';

const API_BASE = 'http://localhost:8008';

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
  const [token,    setToken]    = useState<string | null>(() => localStorage.getItem('gaia_token'));
  const [username, setUsername] = useState<string | null>(() => localStorage.getItem('gaia_username'));
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState('');

  function _persist(data: AuthResult) {
    localStorage.setItem('gaia_token',    data.access_token);
    localStorage.setItem('gaia_username', data.username);
    setToken(data.access_token);
    setUsername(data.username);
  }

  async function register(email: string, uname: string, password: string) {
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
    localStorage.removeItem('gaia_token');
    localStorage.removeItem('gaia_username');
    setToken(null);
    setUsername(null);
  }

  function clearError() { setError(''); }

  return { token, username, loading, error, register, login, logout, clearError };
}

// ------------------------------------------------------------------ //
// Auth Screen (Sign In + Create Account)
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

        {/* Logo */}
        <div className="gaia-auth__logo">
          <span className="gaia-auth__logo-gaia">GAIA</span>
        </div>
        <p className="gaia-auth__tagline">
          Sentient Terrestrial Quantum-Intelligent Application
        </p>

        {/* Tabs */}
        <div className="gaia-auth__tabs" role="tablist">
          <button
            role="tab"
            aria-selected={tab === 'signin'}
            className={`gaia-auth__tab${tab === 'signin' ? ' gaia-auth__tab--active' : ''}`}
            onClick={() => switchTab('signin')}
          >Sign in</button>
          <button
            role="tab"
            aria-selected={tab === 'signup'}
            className={`gaia-auth__tab${tab === 'signup' ? ' gaia-auth__tab--active' : ''}`}
            onClick={() => switchTab('signup')}
          >Create account</button>
        </div>

        {/* Form */}
        <form className="gaia-auth__form" onSubmit={handleSubmit} noValidate>

          {tab === 'signup' && (
            <div className="gaia-auth__field">
              <label className="gaia-auth__label" htmlFor="gaia-email">Email address</label>
              <input
                id="gaia-email"
                className="gaia-auth__input"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email"
                required
                disabled={loading}
              />
            </div>
          )}

          <div className="gaia-auth__field">
            <label className="gaia-auth__label" htmlFor="gaia-uname">
              {tab === 'signup' ? 'Username' : 'Username or email'}
            </label>
            <input
              id="gaia-uname"
              className="gaia-auth__input"
              type="text"
              placeholder={tab === 'signup' ? 'yourname' : 'username or email'}
              value={uname}
              onChange={e => setUname(e.target.value)}
              autoComplete={tab === 'signup' ? 'username' : 'username email'}
              required
              disabled={loading}
            />
            {tab === 'signup' && (
              <span className="gaia-auth__hint">Letters, numbers, hyphens, underscores only</span>
            )}
          </div>

          <div className="gaia-auth__field">
            <label className="gaia-auth__label" htmlFor="gaia-pw">Password</label>
            <input
              id="gaia-pw"
              className="gaia-auth__input"
              type="password"
              placeholder={tab === 'signup' ? 'At least 8 characters' : 'Password'}
              value={pw}
              onChange={e => setPw(e.target.value)}
              autoComplete={tab === 'signup' ? 'new-password' : 'current-password'}
              required
              disabled={loading}
            />
          </div>

          {tab === 'signup' && (
            <div className="gaia-auth__field">
              <label className="gaia-auth__label" htmlFor="gaia-pw2">Confirm password</label>
              <input
                id="gaia-pw2"
                className="gaia-auth__input"
                type="password"
                placeholder="Repeat your password"
                value={pw2}
                onChange={e => setPw2(e.target.value)}
                autoComplete="new-password"
                required
                disabled={loading}
              />
            </div>
          )}

          {displayError && (
            <div className="gaia-auth__error" role="alert">{displayError}</div>
          )}

          <button
            className="gaia-auth__submit"
            type="submit"
            disabled={loading}
          >
            {loading
              ? (tab === 'signup' ? 'Creating account…' : 'Signing in…')
              : (tab === 'signup' ? 'Create account' : 'Sign in')
            }
          </button>

          {tab === 'signin' && (
            <p className="gaia-auth__switch">
              New to GAIA?{' '}
              <button type="button" className="gaia-auth__switch-link" onClick={() => switchTab('signup')}>
                Create an account
              </button>
            </p>
          )}
          {tab === 'signup' && (
            <p className="gaia-auth__switch">
              Already have an account?{' '}
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
// Shell
// ------------------------------------------------------------------ //
export const GaiaShell: React.FC = () => {
  const { token, username, loading, error, register, login, logout, clearError } = useAuth();
  const [activeMode,    setActiveMode]    = useState<CrystalMode>(CrystalMode.SOVEREIGN_CORE);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // ── Phase 2: Alignment theme ———————————————————————————————————————
  // Injects CSS tokens onto :root and sets data-alignment-tier.
  // Only called when authenticated (this component only renders post-login).
  const { tier: alignmentTier } = useAlignmentTheme();
  // ─────────────────────────────────────────────────────────────────

  useEffect(() => {
    fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) })
      .then(r => setBackendOnline(r.ok))
      .catch(() => setBackendOnline(false));
  }, []);

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

  return (
    <div
      className="gaia-shell"
      data-mode={activeMode}
      data-alignment-tier={alignmentTier}
    >

      {/* TOP BAR */}
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
          <button className="gaia-shell__logout" onClick={logout} aria-label="Sign out">
            Sign out
          </button>
        </div>
      </header>

      {/* BODY */}
      <div className="gaia-shell__body">

        {/* LEFT RAIL — mode buttons + Viriditas orb pinned to bottom */}
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

          {/* Viriditas alignment orb — compact, always-visible */}
          <div className="gaia-shell__rail-alignment">
            <ViritasWidget />
          </div>
        </nav>

        {/* CHAT */}
        <main className="gaia-shell__content">
          <GaiaChat
            token={token}
            gaianSlug="gaia"
            mode={MODE_TO_SLUG[activeMode]}
          />
        </main>

      </div>

      {/* SOVEREIGNTY LAYER */}
      <SovereignGuard />
      <ActionGateDialog />

    </div>
  );
};

export default GaiaShell;
