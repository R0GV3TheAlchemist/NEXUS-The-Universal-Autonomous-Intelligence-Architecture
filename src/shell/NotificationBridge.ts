/**
 * src/shell/NotificationBridge.ts — web-app branch
 * GAIA-OS Proactive Notifications
 *
 * Web-safe replacement for the Tauri notification bridge.
 * Uses the standard Web Notifications API instead of
 * @tauri-apps/plugin-notification.
 *
 * Polls the backend every 5 minutes for pending notifications.
 * Click navigation uses window.dispatchEvent (custom event) instead
 * of invoke('navigate_main') — GaiaShell listens for this event
 * to switch the active mode/section.
 *
 * Browser permission is requested on init. If denied, polling
 * continues but no visible notifications are shown — the backend
 * can still mark them as delivered via the dismiss endpoint.
 */

const POLL_INTERVAL_MS = 5 * 60 * 1000;  // 5 minutes
const API_BASE         = '/api';

interface PendingNotification {
  id:      string;
  title:   string;
  body:    string;
  trigger: string;
  section: string;
}

export class NotificationBridge {
  private pollTimer:         ReturnType<typeof setInterval> | null = null;
  private permissionGranted = false;

  async init(): Promise<void> {
    this.permissionGranted = await this.ensurePermission();
    if (!this.permissionGranted) {
      console.warn('[NotificationBridge] Permission denied — notifications disabled.');
      // Still poll — backend marks delivered even without visible notifications
    }
    await this.poll();
    this.pollTimer = setInterval(() => this.poll(), POLL_INTERVAL_MS);
  }

  destroy(): void {
    if (this.pollTimer !== null) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  // ── Permission (Web Notifications API) ───────────────────────────────

  private async ensurePermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('[NotificationBridge] Web Notifications API not available.');
      return false;
    }
    if (Notification.permission === 'granted') return true;
    if (Notification.permission === 'denied')  return false;
    try {
      const result = await Notification.requestPermission();
      return result === 'granted';
    } catch (err) {
      console.error('[NotificationBridge] Permission request failed:', err);
      return false;
    }
  }

  // ── Poll ─────────────────────────────────────────────────────────────────

  private async poll(): Promise<void> {
    try {
      const res = await fetch(`${API_BASE}/notifications/pending`);
      if (!res.ok) return;
      const notification: PendingNotification | null = await res.json();
      if (!notification) return;
      await this.fire(notification);
    } catch (err) {
      console.debug('[NotificationBridge] Poll failed (backend may be starting):', err);
    }
  }

  // ── Fire ─────────────────────────────────────────────────────────────────

  private async fire(notification: PendingNotification): Promise<void> {
    try {
      // Web Notifications API
      if (this.permissionGranted && 'Notification' in window) {
        const n = new Notification(notification.title, {
          body: notification.body,
          icon: '/gaia-icon.svg',
          tag:  notification.id,   // deduplication key
        });

        // Click — dispatch a custom event instead of invoke('navigate_main')
        if (notification.trigger === 'memory') {
          n.addEventListener('click', () => {
            window.focus();
            window.dispatchEvent(
              new CustomEvent('gaia:navigate', {
                detail: { section: notification.section },
              })
            );
          });
        }
      }

      // Mark as delivered on the backend
      await fetch(`${API_BASE}/notifications/dismiss`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ notification_id: notification.id }),
      });

    } catch (err) {
      console.error('[NotificationBridge] Failed to fire notification:', err);
    }
  }
}

export const notificationBridge = new NotificationBridge();
