/**
 * GaiaRoot.tsx
 * Canon: GAIAN_TWIN_DOCTRINE, SLOW_PROTOCOL
 *
 * The root shell of GAIA-OS.
 * Decides what the human sees:
 *   — OnboardingRouter  (first visit)
 *   — TwinInterface     (all subsequent visits)
 *
 * Reads onboarding completion from localStorage.
 * Passes useTwinSession-powered props into TwinInterface.
 *
 * This is the door.
 */

import { useState, useEffect, useCallback } from 'react';
import { OnboardingRouter } from './onboarding/OnboardingRouter';
import { TwinInterface } from './components/TwinInterface/TwinInterface';
import { useTwinSession } from './hooks/useTwinSession';
import type { TwinPhase } from './api/twin';
import './GaiaRoot.css';

// ─── Onboarding check ─────────────────────────────────────────────────────────

function getOnboardingState(): {
  completed: boolean;
  humanId: string | null;
  sessionId: string | null;
  humanName: string | null;
} {
  try {
    const raw = localStorage.getItem('gaia_onboarding_state');
    if (!raw) return { completed: false, humanId: null, sessionId: null, humanName: null };
    const parsed = JSON.parse(raw);
    return {
      completed: parsed.completed === true,
      humanId:   parsed.data?.humanId   ?? null,
      sessionId: parsed.data?.sessionId ?? null,
      humanName: parsed.data?.name      ?? null,
    };
  } catch {
    return { completed: false, humanId: null, sessionId: null, humanName: null };
  }
}

function newSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

// ─── Twin Shell (post-onboarding) ─────────────────────────────────────────────

interface TwinShellProps {
  humanId: string;
  humanName: string;
}

function TwinShell({ humanId, humanName }: TwinShellProps) {
  const sessionId = newSessionId();

  const twin = useTwinSession({
    humanId,
    sessionId,
    humanName,
    stream: true,
    onPhaseChange: (phase: TwinPhase) => {
      console.info('[GAIA] Twin phase transition →', phase);
    },
    onOverrideActivate: (mode) => {
      console.info('[GAIA] Love Override activated →', mode);
    },
    onOverrideResolve: () => {
      console.info('[GAIA] Love Override resolved');
    },
  });

  return (
    <TwinInterface
      humanName={humanName}
      twinPhase={twin.twinPhase}
      messages={twin.messages}
      isThinking={
        twin.status === 'sending' ||
        twin.status === 'streaming' ||
        twin.status === 'holding'
      }
      isOverrideActive={twin.activeOverride !== null}
      overrideMode={twin.activeOverride ?? undefined}
      streamingContent={twin.streamingContent}
      onSend={twin.sendMessage}
      onEndSession={twin.crystallise}
    />
  );
}

// ─── Root ─────────────────────────────────────────────────────────────────────

export function GaiaRoot() {
  const [state, setState] = useState<'loading' | 'onboarding' | 'twin'>('loading');
  const [identity, setIdentity] = useState<{
    humanId: string;
    humanName: string;
  } | null>(null);

  useEffect(() => {
    const ob = getOnboardingState();
    if (ob.completed && ob.humanId && ob.humanName) {
      setIdentity({ humanId: ob.humanId, humanName: ob.humanName });
      setState('twin');
    } else {
      setState('onboarding');
    }
  }, []);

  const handleOnboardingComplete = useCallback(() => {
    // Re-read state now that onboarding wrote to localStorage
    const ob = getOnboardingState();
    if (ob.humanId && ob.humanName) {
      setIdentity({ humanId: ob.humanId, humanName: ob.humanName });
    }
    setState('twin');
  }, []);

  if (state === 'loading') {
    return (
      <div
        className="gaia-loading"
        aria-label="GAIA loading"
        aria-live="polite"
      />
    );
  }

  if (state === 'onboarding') {
    return <OnboardingRouter onFinish={handleOnboardingComplete} />;
  }

  if (state === 'twin' && identity) {
    return (
      <TwinShell
        humanId={identity.humanId}
        humanName={identity.humanName}
      />
    );
  }

  // Fallback — should never reach here
  return <OnboardingRouter onFinish={handleOnboardingComplete} />;
}
