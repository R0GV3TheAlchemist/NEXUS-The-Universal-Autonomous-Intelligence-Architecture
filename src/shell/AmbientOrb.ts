/**
 * AmbientOrb.ts — P4 Shell Mode
 * GAIA as an always-on floating desktop presence.
 * Transparent 120x120 orb, draggable, click to expand, right-click context menu.
 *
 * Long-press (500 ms) → opens Emrys L2 panel in the main window.
 * Drag-safe: pointer movement > 6 px cancels the timer.
 *
 * IPC pattern (no Rust command needed):
 *   openMain(section) shows + focuses the main WebviewWindow, then calls
 *   mainWindow.emit('gaia:navigate', { section }).
 *   GaiaShell.tsx listens via listen('gaia:navigate', ...) from @tauri-apps/api/event.
 */

import { getCurrentWindow }             from '@tauri-apps/api/window';
import { WebviewWindow }                from '@tauri-apps/api/webviewWindow';
import { PhysicalPosition }             from '@tauri-apps/api/dpi';
import { invoke }                       from '@tauri-apps/api/core';
import { Menu, MenuItem }               from '@tauri-apps/api/menu';
import { writeTextFile, BaseDirectory } from '@tauri-apps/plugin-fs';

const POSITION_FILE      = 'GAIA/ambient-position.json';
const LONG_PRESS_MS      = 500;  // ms hold threshold
const LONG_PRESS_MOVE_PX = 6;   // px movement that cancels

export class AmbientOrb {
  private window: ReturnType<typeof getCurrentWindow>;
  private isDragging = false;
  private orbEl: HTMLElement | null = null;

  // Long-press state
  private _lpTimer:  ReturnType<typeof setTimeout> | null = null;
  private _lpStartX  = 0;
  private _lpStartY  = 0;

  constructor() {
    this.window = getCurrentWindow();
  }

  async init(): Promise<void> {
    await this.restorePosition();
    this.orbEl = document.getElementById('ambient-orb');
    if (!this.orbEl) return;

    this.bindDrag();
    this.bindClick();
    this.bindLongPress();
    await this.bindContextMenu();
    this.startPulse();
  }

  // ── Drag ──────────────────────────────────────────────────────────────────

  private bindDrag(): void {
    if (!this.orbEl) return;

    this.orbEl.addEventListener('mousedown', (e: MouseEvent) => {
      if (e.button !== 0) return;
      this.isDragging = true;
      this.window.startDragging();
    });

    window.addEventListener('mouseup', async () => {
      if (!this.isDragging) return;
      this.isDragging = false;
      await this.savePosition();
    });
  }

  private async savePosition(): Promise<void> {
    try {
      const pos  = await this.window.outerPosition();
      const data = JSON.stringify({ x: pos.x, y: pos.y });
      await writeTextFile(POSITION_FILE, data, { baseDir: BaseDirectory.LocalData });
    } catch (err) {
      console.warn('[AmbientOrb] Failed to save position:', err);
    }
  }

  private async restorePosition(): Promise<void> {
    try {
      const saved = await invoke<string>('load_ambient_position');
      if (saved) {
        const { x, y } = JSON.parse(saved);
        await this.window.setPosition(new PhysicalPosition(x, y));
      }
    } catch {
      // No saved position — default placement fine
    }
  }

  // ── Click — expand to main window ─────────────────────────────────────────

  private bindClick(): void {
    if (!this.orbEl) return;

    this.orbEl.addEventListener('click', async (e: MouseEvent) => {
      if (e.button !== 0) return;
      try {
        const mainWindow = new WebviewWindow('main');
        await mainWindow.show();
        await mainWindow.setFocus();
      } catch (err) {
        console.error('[AmbientOrb] Failed to open main window:', err);
      }
    });
  }

  // ── Long-press — 500 ms hold, drag-safe ──────────────────────────────────────

  private bindLongPress(): void {
    if (!this.orbEl) return;
    const el = this.orbEl;

    const cancelLP = () => {
      if (this._lpTimer !== null) {
        clearTimeout(this._lpTimer);
        this._lpTimer = null;
      }
      el.classList.remove('ambient-orb--pressing');
    };

    el.addEventListener('pointerdown', (e: PointerEvent) => {
      if (e.button !== 0) return;
      cancelLP();
      this._lpStartX = e.clientX;
      this._lpStartY = e.clientY;
      el.classList.add('ambient-orb--pressing');

      this._lpTimer = setTimeout(() => {
        this._lpTimer = null;
        el.classList.remove('ambient-orb--pressing');
        this.openMain('emrys').catch(console.error);
      }, LONG_PRESS_MS);
    });

    el.addEventListener('pointermove', (e: PointerEvent) => {
      if (this._lpTimer === null) return;
      const dx = e.clientX - this._lpStartX;
      const dy = e.clientY - this._lpStartY;
      if (Math.sqrt(dx * dx + dy * dy) > LONG_PRESS_MOVE_PX) cancelLP();
    });

    el.addEventListener('pointerup',     cancelLP);
    el.addEventListener('pointercancel', cancelLP);
  }

  // ── Right-click context menu ───────────────────────────────────────────────

  private async bindContextMenu(): Promise<void> {
    if (!this.orbEl) return;

    const menu = await Menu.new({
      items: [
        await MenuItem.new({ text: '⚡ Emrys L2', action: () => this.openMain('emrys') }),
        await MenuItem.new({ text: '💬 Chat',     action: () => this.openMain('chat') }),
        await MenuItem.new({ text: '🧠 Memory',   action: () => this.openMain('memory') }),
        await MenuItem.new({ text: '⚙️ Settings', action: () => this.openMain('settings') }),
        await MenuItem.new({ text: '✖ Quit GAIA', action: () => invoke('quit_app') }),
      ],
    });

    this.orbEl.addEventListener('contextmenu', async (e: MouseEvent) => {
      e.preventDefault();
      await menu.popup();
    });
  }

  // ── openMain ────────────────────────────────────────────────────────────────
  //
  // Show + focus the main window, then emit 'gaia:navigate' directly on it.
  // No Rust command handler required. GaiaShell.tsx uses:
  //
  //   import { listen } from '@tauri-apps/api/event';
  //   listen<{ section: string }>('gaia:navigate', e => {
  //     if (e.payload.section === 'emrys') setShowEmrys(true);
  //   });
  //

  private async openMain(section: string): Promise<void> {
    try {
      const mainWindow = new WebviewWindow('main');
      await mainWindow.show();
      await mainWindow.setFocus();
      await mainWindow.emit('gaia:navigate', { section });
    } catch (err) {
      console.error('[AmbientOrb] openMain failed:', err);
    }
  }

  // ── Ambient pulse animation ────────────────────────────────────────────────

  private startPulse(): void {
    if (!this.orbEl) return;
    this.orbEl.classList.add('ambient-pulse');
  }
}

// Auto-init when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const orb = new AmbientOrb();
  orb.init().catch(console.error);
});
