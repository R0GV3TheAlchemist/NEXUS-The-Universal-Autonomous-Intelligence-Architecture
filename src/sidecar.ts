/**
 * src/sidecar.ts — web-app branch
 * GAIA-OS Backend Health Monitor
 *
 * Web-safe replacement for the Tauri sidecar.
 * Uses only fetch() — no invoke() calls.
 *
 * Polls GET /api/health every 30 s after initial connect.
 * Dispatches 'gaia:backend-status' custom events so the shell
 * can reflect backend state without any Tauri dependency.
 *
 * On the web, GAIA cannot restart the backend process — if the
 * backend goes offline, the UI shows an offline indicator and
 * retries silently until it comes back.
 */

const HEALTH_URL       = '/api/health';
const POLL_ATTEMPTS    = 20;
const RETRY_INTERVAL   = 30_000;  // 30 s steady-state poll
const INITIAL_DELAY_MS = 300;

function dispatch(status: 'connecting' | 'online' | 'offline') {
  window.dispatchEvent(
    new CustomEvent('gaia:backend-status', { detail: { status } })
  );
}

function log(level: 'info' | 'warn' | 'error', msg: string) {
  const prefix = '[GAIA sidecar]';
  if (level === 'info')  console.info(prefix, msg);
  if (level === 'warn')  console.warn(prefix, msg);
  if (level === 'error') console.error(prefix, msg);
}

async function pollHealth(attempts = POLL_ATTEMPTS): Promise<boolean> {
  let delay = INITIAL_DELAY_MS;
  for (let i = 0; i < attempts; i++) {
    await new Promise(r => setTimeout(r, delay));
    try {
      const res = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(2000) });
      if (res.ok) {
        log('info', `Backend healthy after ${i + 1} attempt(s)`);
        return true;
      }
    } catch (_) { /* backend not up yet — keep polling */ }
    delay = Math.min(delay * 1.5, 3000);
  }
  return false;
}

/**
 * Non-blocking init — resolves immediately so the shell renders
 * without waiting for the backend. Health polling runs in background.
 */
export async function initSidecar(): Promise<void> {
  dispatch('connecting');
  log('info', 'Background health-check started');

  (async () => {
    const ready = await pollHealth();
    if (ready) {
      dispatch('online');
      log('info', 'Backend online');
      // Steady-state poll every 30 s
      setInterval(async () => {
        try {
          const res = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(2000) });
          dispatch(res.ok ? 'online' : 'offline');
        } catch {
          dispatch('offline');
        }
      }, RETRY_INTERVAL);
      return;
    }
    // Backend never came up
    dispatch('offline');
    log('error', 'Backend offline — start the Python server with: uvicorn main:app --port 8008');
  })();

  return Promise.resolve();
}

/**
 * getBackendStatus — web version.
 * Returns 'online' or 'offline' based on a live health probe.
 */
export async function getBackendStatus(): Promise<string> {
  try {
    const res = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(2000) });
    return res.ok ? 'online' : 'offline';
  } catch {
    return 'offline';
  }
}
