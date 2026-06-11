/**
 * src/shell/GaiaShell.tsx
 * GAIA-OS App Shell — Three-Tier UI
 * Canon: C90, C-OB01
 *
 * Navigation architecture (three principals):
 *   HUMAN  tier → My Gaian · Memory · Goals · Settings
 *   GAIA   tier → Ask GAIA · World Feed · Deep Compute · Analysis
 *   GAIAN  tier → Companion · Mood · Bond · Vitality
 *
 * Boot sequence (three-state guard):
 *   1. !token                       → AuthScreen
 *   2. token + !onboardingCompleted → OnboardingRouter  ← C-OB01
 *   3. token + onboardingCompleted  → ShellMain
 *
 * DEV: Set DEV_BYPASS_AUTH = true to skip auth during development.
 *      MUST be false before any production build.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { listen }            from '@tauri-apps/api/event';
import { GaiaChat }          from '../chat/GaiaChat';
import { SovereignGuard }    from '../shared/SovereignGuard';
import { ActionGateDialog }  from '../shared/ActionGateDialog';
import { ViritasWidget }     from '../shared/ViritasWidget';
import { FieldVisualiser }   from '../shared/FieldVisualiser';
import { useAlignmentTheme } from '../hooks/useAlignmentTheme';
import { OnboardingRouter }  from '../onboarding/OnboardingRouter';
import { EmrysPanel }        from '../crystal-view';
import {
  useOnboardingStore,
  loadPersistedState,
} from '../onboarding/store/onboardingStore';
import './GaiaShell.css';

const API_BASE = '/api';
const DEV_BYPASS_AUTH = true; // ⚠️ set false before production

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface AuthResult {
  access_token: string;
  user_id:      string;
  username:     string;
  email:        string;
  role:         string;
}

type Tier = 'human' | 'gaia' | 'gaian';

interface NavItem {
  id:      string;
  label:   string;
  icon:    string;       // SVG path data (24×24 viewBox)
  tier:    Tier;
  tooltip: string;       // plain-English description (no metaphysics)
}

// ─────────────────────────────────────────────────────────────────────────────
// Navigation definition — three tiers, plain-English labels
// Metaphysical names stay in tooltips only
// ─────────────────────────────────────────────────────────────────────────────

const NAV: NavItem[] = [
  // ── HUMAN tier ──────────────────────────────────────────────────────────
  {
    id: 'companion',
    label: 'My Gaian',
    tier: 'human',
    tooltip: 'Your personal AI companion',
    icon: 'M12 2a5 5 0 1 1 0 10A5 5 0 0 1 12 2zm0 13c-5.33 0-8 2.67-8 4v1h16v-1c0-1.33-2.67-4-8-4z',
  },
  {
    id: 'memory',
    label: 'Memory',
    tier: 'human',
    tooltip: 'Everything GAIA remembers about you — fully visible and editable',
    icon: 'M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4m0 0h18',
  },
  {
    id: 'goals',
    label: 'Goals',
    tier: 'human',
    tooltip: 'Tasks and goals you have set for GAIA to work on',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
  },
  {
    id: 'settings',
    label: 'Settings',
    tier: 'human',
    tooltip: 'Your account, consent, and system preferences',
    icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0z',
  },
  // ── GAIA tier ───────────────────────────────────────────────────────────
  {
    id: 'ask',
    label: 'Ask GAIA',
    tier: 'gaia',
    tooltip: 'Search, research, and deep Q&A powered by GAIA\'s full intelligence',
    icon: 'M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z',
  },
  {
    id: 'feed',
    label: 'World Feed',
    tier: 'gaia',
    tooltip: 'Live signals from the collective — world events, trends, resonance patterns',
    icon: 'M3.055 11H5a2 2 0 0 1 2 2v1a2 2 0 0 0 2 2 2 2 0 0 1 2 2v2.945M8 3.935V5.5A2.5 2.5 0 0 0 10.5 8h.5a2 2 0 0 1 2 2 2 2 0 0 0 4 0 2 2 0 0 1 2-2h1.064M15 20.488V18a2 2 0 0 1 2-2h3.064M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
  },
  {
    id: 'compute',
    label: 'Deep Compute',
    tier: 'gaia',
    tooltip: 'Advanced reasoning, quantum-inspired analysis, and multi-step problem solving',
    icon: 'M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4m0 0h18M9 9h.01M15 9h.01M9 15h.01M15 15h.01',
  },
  {
    id: 'analysis',
    label: 'Analysis',
    tier: 'gaia',
    tooltip: 'Multi-dimensional analysis and pattern recognition across your data',
    icon: 'M9 19v-6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2zm0 0V9a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v10m-6 0a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2m0 0V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2z',
  },
  // ── GAIAN tier ──────────────────────────────────────────────────────────
  {
    id: 'chat',
    label: 'Companion',
    tier: 'gaian',
    tooltip: 'Speak directly with your Gaian — your personal AI companion',
    icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 0 1-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  },
  {
    id: 'mood',
    label: 'Mood',
    tier: 'gaian',
    tooltip: 'Your Gaian\'s current emotional state and how they\'re feeling',
    icon: 'M14.828 14.828a4 4 0 0 1-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
  },
  {
    id: 'bond',
    label: 'Bond',
    tier: 'gaian',
    tooltip: 'The depth of your relationship with your Gaian over time',
    icon: 'M4.318 6.318a4.5 4.5 0 0 0 0 6.364L12 20.364l7.682-7.682a4.5 4.5 0 0 0-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 0 0-6.364 0z',
  },
  {
    id: 'vitality',
    label: 'Vitality',
    tier: 'gaian',
    tooltip: 'Your Gaian\'s health and well-being indicators',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
  },
];

const TIER_LABELS: Record<Tier, string> = {
  human:  'You',
  gaia:   'GAIA',
  gaian:  'Your Gaian',
};

// ─────────────────────────────────────────────────────────────────────────────
// useAuth hook
// ─────────────────────────────────────────────────────────────────────────────

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
      const res  = await fetch(`${API_BASE}/auth/register`, {
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
      const res  = await fetch(`${API_BASE}/auth/login`, {
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

  return { token, username, loading, error, register, login, logout, clearError: () => setError('') };
}

// ─────────────────────────────────────────────────────────────────────────────
// AuthScreen
// ─────────────────────────────────────────────────────────────────────────────

type AuthTab = 'signin' | 'signup';

const AuthScreen: React.FC<{
  onLogin:    (id: string, pw: string) => void;
  onRegister: (email: string, uname: string, pw: string) => void;
  loading:    boolean;
  error:      string;
  onClear:    () => void;
}> = ({ onLogin, onRegister, loading, error, onClear }) => {
  const [tab,   setTab]   = useState<AuthTab>('signin');
  const [email, setEmail] = useState('');
  const [uname, setUname] = useState('');
  const [pw,    setPw]    = useState('');
  const [pw2,   setPw2]   = useState('');
  const [local, setLocal] = useState('');

  function switchTab(t: AuthTab) {
    setTab(t); setEmail(''); setUname(''); setPw(''); setPw2('');
    setLocal(''); onClear();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setLocal('');
    if (tab === 'signup') {
      if (!email.includes('@'))  { setLocal('Enter a valid email.');         return; }
      if (uname.length < 2)      { setLocal('Username needs 2+ characters.'); return; }
      if (pw.length < 8)         { setLocal('Password needs 8+ characters.'); return; }
      if (pw !== pw2)            { setLocal('Passwords do not match.');       return; }
      onRegister(email, uname, pw);
    } else {
      if (!uname) { setLocal('Enter your username or email.'); return; }
      if (!pw)    { setLocal('Enter your password.');           return; }
      onLogin(uname, pw);
    }
  }

  const displayError = local || error;

  return (
    <div className="gs-auth">
      <div className="gs-auth__box">
        <div className="gs-auth__logo">
          <svg viewBox="0 0 48 48" width="36" height="36" fill="none" aria-hidden>
            <circle cx="24" cy="24" r="22" stroke="#4f98a3" strokeWidth="2" strokeDasharray="4 3"/>
            <circle cx="24" cy="24" r="10" fill="#4f98a3" fillOpacity="0.15" stroke="#4f98a3" strokeWidth="1.5"/>
            <circle cx="24" cy="24" r="3" fill="#4f98a3"/>
            <line x1="24" y1="2" x2="24" y2="14" stroke="#4f98a3" strokeWidth="1.5"/>
            <line x1="24" y1="34" x2="24" y2="46" stroke="#4f98a3" strokeWidth="1.5"/>
            <line x1="2" y1="24" x2="14" y2="24" stroke="#4f98a3" strokeWidth="1.5"/>
            <line x1="34" y1="24" x2="46" y2="24" stroke="#4f98a3" strokeWidth="1.5"/>
          </svg>
          <span className="gs-auth__wordmark">GAIA<span>OS</span></span>
        </div>
        <p className="gs-auth__tagline">Your intelligent operating system</p>

        <div className="gs-auth__tabs" role="tablist">
          {(['signin', 'signup'] as AuthTab[]).map(t => (
            <button key={t} role="tab" aria-selected={tab === t}
              className={`gs-auth__tab${tab === t ? ' gs-auth__tab--active' : ''}`}
              onClick={() => switchTab(t)}>
              {t === 'signin' ? 'Sign in' : 'Create account'}
            </button>
          ))}
        </div>

        <form className="gs-auth__form" onSubmit={handleSubmit} noValidate>
          {tab === 'signup' && (
            <div className="gs-auth__field">
              <label htmlFor="gs-email">Email</label>
              <input id="gs-email" type="email" placeholder="you@example.com"
                value={email} onChange={e => setEmail(e.target.value)}
                autoComplete="email" disabled={loading} />
            </div>
          )}
          <div className="gs-auth__field">
            <label htmlFor="gs-uname">{tab === 'signup' ? 'Username' : 'Username or email'}</label>
            <input id="gs-uname" type="text"
              placeholder={tab === 'signup' ? 'yourname' : 'username or email'}
              value={uname} onChange={e => setUname(e.target.value)}
              autoComplete={tab === 'signup' ? 'username' : 'username email'}
              disabled={loading} />
          </div>
          <div className="gs-auth__field">
            <label htmlFor="gs-pw">Password</label>
            <input id="gs-pw" type="password"
              placeholder={tab === 'signup' ? 'At least 8 characters' : 'Password'}
              value={pw} onChange={e => setPw(e.target.value)}
              autoComplete={tab === 'signup' ? 'new-password' : 'current-password'}
              disabled={loading} />
          </div>
          {tab === 'signup' && (
            <div className="gs-auth__field">
              <label htmlFor="gs-pw2">Confirm password</label>
              <input id="gs-pw2" type="password" placeholder="Repeat your password"
                value={pw2} onChange={e => setPw2(e.target.value)}
                autoComplete="new-password" disabled={loading} />
            </div>
          )}
          {displayError && <div className="gs-auth__error" role="alert">{displayError}</div>}
          <button className="gs-auth__submit" type="submit" disabled={loading}>
            {loading
              ? (tab === 'signup' ? 'Creating…' : 'Signing in…')
              : (tab === 'signup' ? 'Create account' : 'Sign in')}
          </button>
          <p className="gs-auth__switch">
            {tab === 'signin' ? 'New to GAIA? ' : 'Already have an account? '}
            <button type="button" onClick={() => switchTab(tab === 'signin' ? 'signup' : 'signin')}>
              {tab === 'signin' ? 'Create an account' : 'Sign in'}
            </button>
          </p>
        </form>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// SVG icon helper
// ─────────────────────────────────────────────────────────────────────────────

const Icon: React.FC<{ d: string; size?: number; 'aria-hidden'?: boolean }> = ({
  d, size = 18, 'aria-hidden': hidden = true,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="1.6"
    strokeLinecap="round" strokeLinejoin="round"
    aria-hidden={hidden}>
    {d.split(' M').map((seg, i) => (
      <path key={i} d={i === 0 ? seg : 'M' + seg} />
    ))}
  </svg>
);

// ─────────────────────────────────────────────────────────────────────────────
// PlaceholderView — for nav items without a full component yet
// ─────────────────────────────────────────────────────────────────────────────

const PlaceholderView: React.FC<{ item: NavItem }> = ({ item }) => (
  <div className="gs-placeholder">
    <div className="gs-placeholder__icon">
      <Icon d={item.icon} size={32} />
    </div>
    <h2>{item.label}</h2>
    <p>{item.tooltip}</p>
    <span className="gs-placeholder__tier" data-tier={item.tier}>
      {TIER_LABELS[item.tier]} layer
    </span>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// ShellMain — authenticated experience
// ─────────────────────────────────────────────────────────────────────────────

const ShellMain: React.FC<{
  token:    string;
  username: string | null;
  onLogout: () => void;
}> = ({ token, username, onLogout }) => {
  const [activeId,      setActiveId]      = useState<string>('ask');
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [sidebarOpen,   setSidebarOpen]   = useState(true);
  const [showEmrys,     setShowEmrys]     = useState(false);
  const { tier: alignmentTier } = useAlignmentTheme();

  // Pull current GAIAN stage for EmrysPanel context.
  // Graceful: passes undefined if currentStage isn't in the store yet.
  const currentStage = useOnboardingStore(
    s => (s as Record<string, unknown>).currentStage as string | undefined
  );

  useEffect(() => {
    fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3_000) })
      .then(r => setBackendOnline(r.ok))
      .catch(() => setBackendOnline(false));
  }, []);

  // Listen for 'gaia:navigate' Tauri events emitted by AmbientOrb.openMain().
  //
  // AmbientOrb calls mainWindow.emit('gaia:navigate', { section }) which dispatches
  // a Tauri event on this webview — NOT a DOM CustomEvent. We must use Tauri's
  // listen() API here, not window.addEventListener.
  //
  // In browser-only dev mode (no Tauri runtime), listen() may throw; the error
  // is caught silently so the button trigger still works fine.
  //
  useEffect(() => {
    let unlisten: (() => void) | undefined;
    listen<{ section: string }>('gaia:navigate', (e) => {
      if (e.payload.section === 'emrys') setShowEmrys(true);
    })
      .then(fn => { unlisten = fn; })
      .catch(() => { /* non-Tauri environment — button trigger still works */ });
    return () => { unlisten?.(); };
  }, []);

  const activeItem = NAV.find(n => n.id === activeId) ?? NAV[4]; // default: Ask GAIA

  const renderContent = useCallback(() => {
    if (activeId === 'ask' || activeId === 'chat' || activeId === 'companion') {
      return <GaiaChat token={token} gaianSlug="gaia" mode="control" />;
    }
    return <PlaceholderView item={activeItem} />;
  }, [activeId, token, activeItem]);

  return (
    <div className="gs" data-alignment-tier={alignmentTier}>
      <FieldVisualiser tier={alignmentTier} />

      {/* ── Top bar ─────────────────────────────────────────────────── */}
      <header className="gs__topbar">
        <button
          className="gs__topbar-toggle"
          onClick={() => setSidebarOpen(o => !o)}
          aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          aria-expanded={sidebarOpen}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="1.8" aria-hidden>
            <line x1="3" y1="6"  x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>

        <div className="gs__wordmark">
          <svg viewBox="0 0 32 32" width="22" height="22" fill="none" aria-hidden>
            <circle cx="16" cy="16" r="14" stroke="#4f98a3" strokeWidth="1.5" strokeDasharray="3 2"/>
            <circle cx="16" cy="16" r="6" fill="#4f98a3" fillOpacity="0.15" stroke="#4f98a3" strokeWidth="1"/>
            <circle cx="16" cy="16" r="2" fill="#4f98a3"/>
            <line x1="16" y1="2"  x2="16" y2="10" stroke="#4f98a3" strokeWidth="1"/>
            <line x1="16" y1="22" x2="16" y2="30" stroke="#4f98a3" strokeWidth="1"/>
            <line x1="2"  y1="16" x2="10" y2="16" stroke="#4f98a3" strokeWidth="1"/>
            <line x1="22" y1="16" x2="30" y2="16" stroke="#4f98a3" strokeWidth="1"/>
          </svg>
          <span>GAIA<em>OS</em></span>
        </div>

        <div className="gs__topbar-center">
          <span className="gs__active-label">{activeItem.label}</span>
          <span className="gs__active-tier" data-tier={activeItem.tier}>
            {TIER_LABELS[activeItem.tier]}
          </span>
        </div>

        <div className="gs__topbar-right">
          <ViritasWidget />

          {/* ── Emrys L2 button ──────────────────────────────────── */}
          <button
            className={`gs__emrys-btn${showEmrys ? ' gs__emrys-btn--active' : ''}`}
            onClick={() => setShowEmrys(v => !v)}
            aria-label="Open Emrys L2 vibronic bridge panel"
            aria-pressed={showEmrys}
            title="Emrys L2 (C164 · C165 · C166)"
          >
            ⚡
          </button>

          <span
            className={`gs__status-dot gs__status-dot--${
              backendOnline === null ? 'checking' : backendOnline ? 'online' : 'offline'
            }`}
            title={backendOnline === null ? 'Connecting…' : backendOnline ? 'GAIA online' : 'GAIA offline'}
          />
          {username && <span className="gs__username">{username}</span>}
          <button className="gs__logout" onClick={onLogout} aria-label="Sign out">
            Sign out
          </button>
        </div>
      </header>

      <div className="gs__body">
        {/* ── Sidebar ───────────────────────────────────────────────── */}
        <nav
          className={`gs__sidebar${sidebarOpen ? '' : ' gs__sidebar--collapsed'}`}
          aria-label="GAIA navigation"
        >
          {(['human', 'gaia', 'gaian'] as Tier[]).map(tier => (
            <div key={tier} className="gs__nav-section">
              <span className="gs__nav-tier-label">{TIER_LABELS[tier]}</span>
              {NAV.filter(n => n.tier === tier).map(item => (
                <button
                  key={item.id}
                  className={`gs__nav-item${
                    item.id === activeId ? ' gs__nav-item--active' : ''
                  }`}
                  data-tier={item.tier}
                  onClick={() => setActiveId(item.id)}
                  title={item.tooltip}
                  aria-pressed={item.id === activeId}
                >
                  <span className="gs__nav-icon">
                    <Icon d={item.icon} />
                  </span>
                  <span className="gs__nav-label">{item.label}</span>
                </button>
              ))}
            </div>
          ))}
        </nav>

        {/* ── Main content ──────────────────────────────────────────── */}
        <main className="gs__main">
          {renderContent()}
        </main>
      </div>

      <SovereignGuard />
      <ActionGateDialog />

      {/* ── Emrys L2 Panel — portal-level overlay ──────────────────── */}
      <EmrysPanel
        open={showEmrys}
        onClose={() => setShowEmrys(false)}
        gaianStage={currentStage}
        defaultTab="cold-start"
      />
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// GaiaShell — three-state boot guard
// ─────────────────────────────────────────────────────────────────────────────

export const GaiaShell: React.FC = () => {
  const { token, username, loading, error, register, login, logout, clearError } = useAuth();
  const completed          = useOnboardingStore(s => s.completed);
  const completeOnboarding = useOnboardingStore(s => s.completeOnboarding);
  const [onboardingReady, setOnboardingReady] = useState(false);

  useEffect(() => {
    if (!token) { setOnboardingReady(false); return; }
    loadPersistedState().then(persisted => {
      if (persisted) useOnboardingStore.setState(persisted);
      setOnboardingReady(true);
    });
  }, [token]);

  if (!token) {
    return <AuthScreen onLogin={login} onRegister={register}
      loading={loading} error={error} onClear={clearError} />;
  }

  if (!onboardingReady) {
    return (
      <div className="gs-waking">
        <svg viewBox="0 0 32 32" width="28" height="28" fill="none" aria-hidden>
          <circle cx="16" cy="16" r="14" stroke="#4f98a3" strokeWidth="1.5"
            strokeDasharray="3 2" style={{animationName:'gs-spin',animationDuration:'3s',animationTimingFunction:'linear',animationIterationCount:'infinite',transformOrigin:'center'}} />
          <circle cx="16" cy="16" r="2" fill="#4f98a3"/>
        </svg>
        <span>GAIA is waking…</span>
      </div>
    );
  }

  if (!completed) {
    return <OnboardingRouter onFinish={() => completeOnboarding()} />;
  }

  return <ShellMain token={token} username={username} onLogout={logout} />;
};

export default GaiaShell;
