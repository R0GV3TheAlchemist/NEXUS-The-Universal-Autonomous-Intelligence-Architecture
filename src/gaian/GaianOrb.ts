/**
 * GaianOrb.ts
 * Living Earth avatar — Three.js WebGL renderer.
 *
 * Features:
 *  - Realistic land/ocean sphere with texture
 *  - Animated scrolling cloud layer
 *  - Fresnel atmosphere glow shader
 *  - GLSL aurora effect at the poles
 *  - Real-time day/night terminator line
 *  - GSAP-driven mood transitions
 *  - WebSocket listener for /mood events from the Python backend
 *  - setParams(OrbParams) — Crystal Core 8-field visual contract (C-CC01)
 *  - setProfileParams(GAIANProfile) — profile-driven override layer (M2, Issue #756)
 *  - Coherence ring canvas overlay
 *
 * Usage:
 *   const orb = new GaianOrb(document.getElementById('orb-canvas') as HTMLCanvasElement);
 *   orb.start();
 *   orb.setMood('joyful');             // legacy mood API (still works)
 *   orb.setParams(orbParams);          // Crystal Core API (preferred)
 *   orb.setProfileParams(profile);     // Profile override API (M2)
 *   orb.dispose(); // cleanup on unmount
 *
 * Profile override precedence (M2):
 *   setProfileParams() derives a base OrbParams from profile.lciBaseline via
 *   orbParamsFromPsi(), then overrides primaryColor with profile.avatarColor
 *   and secondaryColor with the crystal resonance tint for
 *   profile.preferredCrystal.  The result is passed into setParams() so the
 *   existing GSAP animation path handles all transitions.
 *
 *   When the Crystal Core sidecar is live, its setParams() calls take
 *   precedence over the profile baseline — the sidecar represents real-time
 *   Ψ state, the profile represents the architect's persistent identity.
 *   The profile layer is re-applied on session init (before the first sidecar
 *   tick) and whenever the profile is mutated.
 */

// three and gsap are declared as external globals loaded via CDN at runtime.
declare const THREE: typeof import('three');
declare const gsap: typeof import('gsap').gsap;

import { gaianMood, GaianMoodState, MoodProfile, MOOD_PROFILES } from './GaianMood';
import type { GAIANProfile } from './GAIANProfile';
import { OrbParams, orbParamsFromPsi } from './OrbParams';

// ── GLSL Shaders ──────────────────────────────────────────────────────

const ATMOSPHERE_VERT = /* glsl */`
  varying vec3 vNormal;
  varying vec3 vPosition;
  void main() {
    vNormal   = normalize(normalMatrix * normal);
    vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const ATMOSPHERE_FRAG = /* glsl */`
  uniform vec3  uGlowColor;
  uniform float uGlowIntensity;
  varying vec3  vNormal;
  varying vec3  vPosition;

  void main() {
    vec3  viewDir  = normalize(-vPosition);
    float rim      = 1.0 - max(dot(viewDir, vNormal), 0.0);
    float glow     = pow(rim, 3.5) * uGlowIntensity;
    gl_FragColor   = vec4(uGlowColor * glow, glow * 0.85);
  }
`;

const AURORA_VERT = /* glsl */`
  varying vec2 vUv;
  varying vec3 vNormal;
  void main() {
    vUv        = uv;
    vNormal    = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const AURORA_FRAG = /* glsl */`
  uniform float uTime;
  uniform float uIntensity;
  varying vec2  vUv;
  varying vec3  vNormal;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }

  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(hash(i), hash(i + vec2(1,0)), f.x),
      mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x),
      f.y
    );
  }

  void main() {
    float lat       = abs(vUv.y - 0.5) * 2.0;
    float poleMask  = smoothstep(0.55, 0.85, lat);
    float n  = noise(vec2(vUv.x * 6.0 + uTime * 0.3, vUv.y * 4.0 + uTime * 0.15));
    float n2 = noise(vec2(vUv.x * 12.0 - uTime * 0.2, vUv.y * 8.0));
    float band = smoothstep(0.35, 0.65, n) * smoothstep(0.4, 0.6, n2);
    vec3  color = mix(vec3(0.0, 0.9, 0.6), vec3(0.5, 0.1, 0.9), n2);
    float alpha = poleMask * band * uIntensity * 0.75;
    gl_FragColor = vec4(color, alpha);
  }
`;

// ── Crystal resonance → secondary color tint ─────────────────────────────────

/**
 * Maps preferredCrystal to a secondary atmosphere tint.
 * These are the canonical crystal colors for the 9 GAIAN crystals (ADR-FE-006).
 */
const CRYSTAL_SECONDARY_COLORS: Record<string, string> = {
  'amethyst':          '#7b4fa6',
  'clear-quartz':      '#e8f4f8',
  'citrine':           '#e8b84b',
  'obsidian':          '#2a2a2a',
  'labradorite':       '#4a7a9b',
  'rose-quartz':       '#e8a0b0',
  'selenite':          '#f0f0f0',
  'black-tourmaline':  '#1a1a2e',
  'lapis-lazuli':      '#26619c',
};

/**
 * Derives an OrbParams override from a GAIANProfile.
 * Uses orbParamsFromPsi(lciBaseline) as the structural base, then
 * overrides primaryColor with profile.avatarColor and secondaryColor
 * with the crystal resonance tint.
 */
export function orbParamsFromProfile(profile: GAIANProfile): OrbParams {
  const base = orbParamsFromPsi(profile.lciBaseline);
  const crystalSecondary = CRYSTAL_SECONDARY_COLORS[profile.preferredCrystal] ?? base.secondaryColor;
  return {
    ...base,
    primaryColor:   profile.avatarColor || base.primaryColor,
    secondaryColor: crystalSecondary,
  };
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function hexToColor(hex: string): import('three').Color {
  return new THREE.Color(hex);
}

function sunDirection(): import('three').Vector3 {
  const now    = new Date();
  const hours  = now.getUTCHours() + now.getUTCMinutes() / 60;
  const sunLon = ((hours / 24) * 2 * Math.PI) - Math.PI;
  const sunLat = 0;
  return new THREE.Vector3(
    Math.cos(sunLat) * Math.cos(sunLon),
    Math.sin(sunLat),
    Math.cos(sunLat) * Math.sin(sunLon),
  ).normalize();
}

// ── GaianOrb class ───────────────────────────────────────────────────────────

export class GaianOrb {
  private canvas:     HTMLCanvasElement;
  private renderer:   import('three').WebGLRenderer;
  private scene:      import('three').Scene;
  private camera:     import('three').PerspectiveCamera;
  private clock:      import('three').Clock;

  private earthMesh:   import('three').Mesh;
  private cloudMesh:   import('three').Mesh;
  private atmMesh:     import('three').Mesh;
  private auroraMesh:  import('three').Mesh;

  private atmMat:    import('three').ShaderMaterial;
  private auroraMat: import('three').ShaderMaterial;
  private cloudMat:  import('three').MeshStandardMaterial;

  private sunLight: import('three').DirectionalLight;

  private _raf:       number | null = null;
  private _ws:        WebSocket | null = null;
  private _moodUnsub: (() => void) | null = null;

  private _ringCanvas:  HTMLCanvasElement | null = null;
  private _ringCtx:     CanvasRenderingContext2D | null = null;
  private _ringOpacity: number = 0;
  private _ringColor:   string = '#4f98a3';

  private _live = {
    rotationSpeed:   MOOD_PROFILES.calm.rotationSpeed,
    glowIntensity:   MOOD_PROFILES.calm.glowIntensity,
    cloudOpacity:    MOOD_PROFILES.calm.cloudOpacity,
    auroraIntensity: MOOD_PROFILES.calm.auroraIntensity,
    pulseFrequency:  MOOD_PROFILES.calm.pulseFrequency,
    pulseAmplitude:  MOOD_PROFILES.calm.pulseAmplitude,
    atmScale:        1.18,
    pulsePhase:      0,
    scale:           1,
  };

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);

    this.scene  = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, canvas.clientWidth / canvas.clientHeight, 0.1, 100);
    this.camera.position.z = 2.8;
    this.clock  = new THREE.Clock();

    const ambient = new THREE.AmbientLight(0x111122, 0.6);
    this.scene.add(ambient);

    this.sunLight = new THREE.DirectionalLight(0xfff5e0, 1.4);
    this.sunLight.position.copy(sunDirection()).multiplyScalar(5);
    this.scene.add(this.sunLight);

    const sphere = new THREE.SphereGeometry(1, 64, 64);

    const earthMat = new THREE.MeshStandardMaterial({ color: 0x1a4a7a, roughness: 0.85, metalness: 0.05 });
    const loader = new THREE.TextureLoader();
    loader.load('/assets/earth-day.jpg',    (t: import('three').Texture) => { earthMat.map = t; earthMat.needsUpdate = true; });
    loader.load('/assets/earth-normal.jpg', (t: import('three').Texture) => { earthMat.normalMap = t; earthMat.needsUpdate = true; });
    this.earthMesh = new THREE.Mesh(sphere, earthMat);
    this.scene.add(this.earthMesh);

    this.cloudMat = new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: this._live.cloudOpacity, depthWrite: false });
    loader.load('/assets/earth-clouds.jpg', (t: import('three').Texture) => { this.cloudMat.alphaMap = t; this.cloudMat.needsUpdate = true; });
    this.cloudMesh = new THREE.Mesh(new THREE.SphereGeometry(1.008, 64, 64), this.cloudMat);
    this.scene.add(this.cloudMesh);

    this.atmMat = new THREE.ShaderMaterial({
      vertexShader:   ATMOSPHERE_VERT,
      fragmentShader: ATMOSPHERE_FRAG,
      uniforms: {
        uGlowColor:     { value: hexToColor(MOOD_PROFILES.calm.glowColor) },
        uGlowIntensity: { value: MOOD_PROFILES.calm.glowIntensity },
      },
      side:        THREE.BackSide,
      transparent: true,
      blending:    THREE.AdditiveBlending,
      depthWrite:  false,
    });
    this.atmMesh = new THREE.Mesh(new THREE.SphereGeometry(1.18, 64, 64), this.atmMat);
    this.scene.add(this.atmMesh);

    this.auroraMat = new THREE.ShaderMaterial({
      vertexShader:   AURORA_VERT,
      fragmentShader: AURORA_FRAG,
      uniforms: {
        uTime:      { value: 0 },
        uIntensity: { value: MOOD_PROFILES.calm.auroraIntensity },
      },
      transparent: true,
      blending:    THREE.AdditiveBlending,
      depthWrite:  false,
      side:        THREE.FrontSide,
    });
    this.auroraMesh = new THREE.Mesh(new THREE.SphereGeometry(1.01, 64, 64), this.auroraMat);
    this.scene.add(this.auroraMesh);

    this._initRingCanvas();
    new ResizeObserver(() => this._onResize()).observe(canvas);
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  start(): void {
    this._moodUnsub = gaianMood.onChange((_state, profile) => this._transitionToProfile(profile));
    this._connectWebSocket();
    this._loop();
  }

  setMood(mood: GaianMoodState): void {
    gaianMood.set(mood);
  }

  setParams(p: OrbParams): void {
    const target = hexToColor(p.primaryColor);
    gsap.to(this.atmMat.uniforms['uGlowColor'].value, {
      duration: 2.0, ease: 'power2.inOut',
      r: target.r, g: target.g, b: target.b,
    });
    gsap.to(this._live, {
      duration:        2.0,
      ease:            'power2.inOut',
      rotationSpeed:   p.rotationSpeed,
      glowIntensity:   0.2 + ((p.glowRadius - 0.8) / 0.6) * 0.8,
      cloudOpacity:    0.4 + (1 - (p.auroraIntensity / 0.95)) * 0.3,
      auroraIntensity: p.auroraIntensity,
      pulseFrequency:  p.pulseRate,
      pulseAmplitude:  0.008 + p.pulseRate * 0.04,
      atmScale:        p.glowRadius,
    });
    gsap.to(this.atmMesh.scale, {
      duration: 2.0, ease: 'power2.inOut',
      x: p.glowRadius, y: p.glowRadius, z: p.glowRadius,
    });
    this._ringOpacity = p.coherenceRingOpacity;
    this._ringColor   = p.primaryColor;
  }

  /**
   * Profile override API (M2 — Issue #756).
   * Derives OrbParams from the architect's GAIANProfile and applies via setParams().
   * Call at session init and on any profile mutation.
   */
  setProfileParams(profile: GAIANProfile): void {
    this.setParams(orbParamsFromProfile(profile));
  }

  dispose(): void {
    if (this._raf)       cancelAnimationFrame(this._raf);
    if (this._ws)        this._ws.close();
    if (this._moodUnsub) this._moodUnsub();
    this.renderer.dispose();
    this._ringCanvas?.remove();
  }

  // ── Render loop ─────────────────────────────────────────────────────────────

  private _loop(): void {
    this._raf = requestAnimationFrame(() => this._loop());
    const elapsed = this.clock.getElapsedTime();
    void this.clock.getDelta();

    this.earthMesh.rotation.y  += this._live.rotationSpeed;
    this.cloudMesh.rotation.y  += this._live.rotationSpeed * 1.15;
    this.auroraMesh.rotation.y += this._live.rotationSpeed * 0.5;

    const breathe = 1 + Math.sin(elapsed * this._live.pulseFrequency * Math.PI * 2) * this._live.pulseAmplitude;
    this.earthMesh.scale.setScalar(breathe);
    this.cloudMesh.scale.setScalar(breathe * 1.008);

    this.atmMat.uniforms['uGlowIntensity'].value = this._live.glowIntensity;
    this.auroraMat.uniforms['uTime'].value       = elapsed;
    this.auroraMat.uniforms['uIntensity'].value  = this._live.auroraIntensity;
    this.cloudMat.opacity                        = this._live.cloudOpacity;

    if (Math.floor(elapsed) % 60 === 0) {
      this.sunLight.position.copy(sunDirection()).multiplyScalar(5);
    }

    this.renderer.render(this.scene, this.camera);
    this._drawRing(elapsed);
  }

  // ── Coherence ring ────────────────────────────────────────────────────────────

  private _initRingCanvas(): void {
    const ring = document.createElement('canvas');
    ring.className = 'gaian-orb__ring';
    ring.setAttribute('aria-hidden', 'true');
    ring.width  = this.canvas.clientWidth;
    ring.height = this.canvas.clientHeight;
    this.canvas.insertAdjacentElement('afterend', ring);
    this._ringCanvas = ring;
    this._ringCtx    = ring.getContext('2d');
  }

  private _drawRing(elapsed: number): void {
    const ctx = this._ringCtx;
    const cvs = this._ringCanvas;
    if (!ctx || !cvs || this._ringOpacity <= 0.01) return;
    ctx.clearRect(0, 0, cvs.width, cvs.height);
    const cx = cvs.width / 2;
    const cy = cvs.height / 2;
    const r  = Math.min(cx, cy) * 0.62;
    const dashOffset = (elapsed * 12) % (Math.PI * 2);
    ctx.save();
    ctx.globalAlpha    = this._ringOpacity * 0.85;
    ctx.strokeStyle    = this._ringColor;
    ctx.lineWidth      = 1.5;
    ctx.setLineDash([6, 10]);
    ctx.lineDashOffset = -dashOffset * 20;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  // ── Mood transition (legacy) ───────────────────────────────────────────────────

  private _transitionToProfile(profile: MoodProfile): void {
    gsap.to(this._live, {
      duration:        1.4, ease: 'power2.inOut',
      rotationSpeed:   profile.rotationSpeed,
      glowIntensity:   profile.glowIntensity,
      cloudOpacity:    profile.cloudOpacity,
      auroraIntensity: profile.auroraIntensity,
      pulseFrequency:  profile.pulseFrequency,
      pulseAmplitude:  profile.pulseAmplitude,
    });
    const target = hexToColor(profile.glowColor);
    gsap.to(this.atmMat.uniforms['uGlowColor'].value, {
      duration: 1.4, ease: 'power2.inOut',
      r: target.r, g: target.g, b: target.b,
    });
  }

  // ── WebSocket ─────────────────────────────────────────────────────────────

  private _connectWebSocket(): void {
    const WS_URL = 'ws://localhost:8008/ws/mood';
    try {
      this._ws = new WebSocket(WS_URL);
      this._ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data as string) as { mood?: GaianMoodState; sentiment?: number };
          if (data.mood)                               gaianMood.set(data.mood);
          else if (typeof data.sentiment === 'number') gaianMood.fromSentiment(data.sentiment);
        } catch { /* malformed — ignore */ }
      };
      this._ws.onclose = () => { setTimeout(() => this._connectWebSocket(), 3000); };
      this._ws.onerror = () => { this._ws?.close(); };
    } catch { /* backend not running — silent fail */ }
  }

  // ── Resize ──────────────────────────────────────────────────────────────────

  private _onResize(): void {
    const w = this.canvas.clientWidth;
    const h = this.canvas.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
    if (this._ringCanvas) {
      this._ringCanvas.width  = w;
      this._ringCanvas.height = h;
    }
  }
}
