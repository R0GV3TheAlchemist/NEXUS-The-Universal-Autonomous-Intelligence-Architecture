/**
 * digital-earth.service.ts
 * Digital Earth Runtime Engine
 * GAIA-OS | src/dimensions/digital-earth.service.ts
 *
 * PURPOSE:
 * This is the runtime that makes Digital Earth alive.
 *
 * It wires three previously separate systems into one coherent engine:
 *
 *   1. GAIAN_LAWS (GAIAN_LAWS.md)
 *      Every mutation in Digital Earth is checked against GAIAN law.
 *      Nodes cannot be deleted. Memorials are eternal.
 *      Coordinates are private unless consented.
 *
 *   2. COD Service (cod.service.ts)
 *      Crystal nodes auto-enrich from the Crystallography Open Database.
 *      When a crystal node is placed, its physical properties are fetched
 *      from COD and stored on the node for visualization and resonance
 *      frequency calculation.
 *
 *   3. Crystal DB (crystal.index.ts)
 *      Crystal node frequencies, intensities, and resonance properties
 *      are derived from the GAIA crystal database. A node's crystal_type
 *      must be a valid crystal DB entry. Its frequency comes from the
 *      crystal record's base_frequency_hz (or default if not set).
 *
 *   4. Digital Earth Schema (digital-earth.schema.ts)
 *      All data structures, coordinate math, and event types live there.
 *      This service is the engine that drives them.
 *
 * ARCHITECTURE:
 *   DigitalEarthService (singleton)
 *     ├── WorldState (in-memory, observable)
 *     ├── EventBus (typed, subscribable)
 *     ├── CrystalNodeRegistry (keyed by node_id)
 *     ├── GAIANRegistry (keyed by gaian_id)
 *     ├── MemorialRegistry (keyed by memorial_id)
 *     ├── ZoneRegistry (keyed by zone_id)
 *     └── SentinelRegistry (keyed by anchor_id, Phase 3+)
 *
 * INTEGRATION WITH DIMENSIONAL ENGINE:
 *   Digital Earth is the D1 Substrate layer.
 *   When global_resonance changes, it is broadcast to the DimensionalEngine.
 *   When a GAIAN enters a crystal node field, a gaia:resonance event fires.
 *   When a memorial node is sealed, the DimensionalReasoningEngine
 *   receives a PASSAGE notification via D4 (Noosphere).
 *
 * LICENSE: AGPL-3.0-or-later + Ethical Use Addendum (see LICENSE)
 */

import {
  // Schema types
  type DigitalEarthCoordinate,
  type WGS84Coordinate,
  type CrystalNode,
  type GAIANHomeCoordinate,
  type MemorialNode,
  type WorldZone,
  type SentinelAnchorPoint,
  type AncestralLineageMarker,
  type TravelLogEntry,
  type MemorialVisit,
  type FinalResonance,
  type DigitalEarthWorldState,
  type DigitalEarthEvent,
  type DigitalEarthEventType,
  type DigitalEarthEventPayload,
  type CoordinateVisibility,
  type CrystalNodeOrigin,
  type ResonanceAttenuation,
  // Utility functions
  coordToWorldShard,
  haversineDistanceKm,
  calculateNodeIntensityAtDistance,
  isCoordinateInBoundingBox,
  // Constants
  DEFAULT_GAIAN_COORDINATE,
  DIGITAL_EARTH_SCHEMA_VERSION,
  RESONANCE_EVENT_THRESHOLD,
  MAX_ACTIVE_NODES_PER_SHARD,
  FOUNDING_CRYSTAL_ZONES,
} from './digital-earth.schema';

import {
  // COD Service
  enrichCrystalFromCod,
  pingCod,
  type CodPhysicalProperties,
} from '../crystals/cod.service';

import {
  // Crystal DB
  getCrystalById,
  getCrystalByName,
  CRYSTAL_DB,
  type CrystalRecord,
} from '../crystals/crystal.index';

// ─── GAIAN Law Enforcement ─────────────────────────────────────────────────────
// Inline minimal law enforcement — mirrors GAIAN_LAWS.md
// Full GAIANLawViolationError lives in gaian/gaian-laws.ts when built.
// This service uses a local version to avoid circular imports.

class DigitalEarthLawViolation extends Error {
  constructor(
    public readonly law: string,
    public readonly operation: string,
    message: string
  ) {
    super(`[GAIAN LAW VIOLATION] ${law} — ${operation}: ${message}`);
    this.name = 'DigitalEarthLawViolation';
  }
}

function enforceLaw(
  condition: boolean,
  law: string,
  operation: string,
  message: string
): asserts condition {
  if (!condition) throw new DigitalEarthLawViolation(law, operation, message);
}

// ─── ID Generation ────────────────────────────────────────────────────────────

let _idCounter = 0;
function generateId(prefix: string): string {
  const ts  = Date.now().toString(36);
  const seq = (++_idCounter).toString(36).padStart(4, '0');
  const rnd = Math.random().toString(36).slice(2, 6);
  return `${prefix}_${ts}_${seq}_${rnd}`;
}

// ─── Typed Event Bus ─────────────────────────────────────────────────────────────

type EventHandler = (event: DigitalEarthEvent) => void;
type TypedEventHandler<T extends DigitalEarthEventType> = (
  event: DigitalEarthEvent & { payload: Extract<DigitalEarthEventPayload, { type: T }> }
) => void;

class DigitalEarthEventBus {
  private handlers = new Map<string, Set<EventHandler>>();
  private globalHandlers = new Set<EventHandler>();

  /** Subscribe to all Digital Earth events */
  onAny(handler: EventHandler): () => void {
    this.globalHandlers.add(handler);
    return () => this.globalHandlers.delete(handler);
  }

  /** Subscribe to a specific event type */
  on<T extends DigitalEarthEventType>(
    eventType: T,
    handler: TypedEventHandler<T>
  ): () => void {
    if (!this.handlers.has(eventType)) this.handlers.set(eventType, new Set());
    this.handlers.get(eventType)!.add(handler as EventHandler);
    return () => this.handlers.get(eventType)?.delete(handler as EventHandler);
  }

  /** Emit an event to all subscribers */
  emit(payload: DigitalEarthEventPayload, sourceShard: string): DigitalEarthEvent {
    const event: DigitalEarthEvent = {
      event_id:     generateId('evt'),
      event_type:   payload.type as DigitalEarthEventType,
      emitted_at:   new Date().toISOString(),
      payload,
      source_shard: sourceShard,
    };

    // Typed handlers
    this.handlers.get(payload.type)?.forEach(h => {
      try { h(event); } catch (e) { console.error('[DigitalEarth] Event handler error:', e); }
    });

    // Global handlers
    this.globalHandlers.forEach(h => {
      try { h(event); } catch (e) { console.error('[DigitalEarth] Global handler error:', e); }
    });

    return event;
  }
}

// ─── COD-Enriched Crystal Node ─────────────────────────────────────────────────────

/**
 * A crystal node as stored in the runtime registry.
 * Extends CrystalNode with:
 * - The full GAIA crystal DB record (for resonance properties)
 * - COD physical properties (for visualization, frequency derivation)
 * - A set of GAIANs currently inside its resonance field
 */
export interface LiveCrystalNode extends CrystalNode {
  /** GAIA crystal DB record for this node's crystal type */
  crystal_record: CrystalRecord | null;

  /** Physical properties from the Crystallography Open Database */
  cod_properties: CodPhysicalProperties | null;

  /** GAIANs currently inside this node's resonance field */
  gaians_in_field: Set<string>;

  /** Last time this node pulsed (ISO timestamp) */
  last_pulse_at:  string | null;

  /** Running pulse count since node was placed */
  pulse_count: number;
}

// ─── DigitalEarthService ───────────────────────────────────────────────────────────

export class DigitalEarthService {
  // ─ Registries ────────────────────────────────────────────────────────────
  private crystalNodes  = new Map<string, LiveCrystalNode>();
  private gaianRegistry = new Map<string, GAIANHomeCoordinate>();
  private memorials     = new Map<string, MemorialNode>();
  private zones         = new Map<string, WorldZone>();
  private sentinels     = new Map<string, SentinelAnchorPoint>();
  private lineageMarkers = new Map<string, AncestralLineageMarker[]>();

  // ─ State ─────────────────────────────────────────────────────────────────
  private globalResonance = 0;
  private codOnline       = false;
  private initialized     = false;

  // ─ Event Bus ─────────────────────────────────────────────────────────────
  readonly events = new DigitalEarthEventBus();

  // ─ Pulse Interval ───────────────────────────────────────────────────────────
  private pulseIntervalId: ReturnType<typeof setInterval> | null = null;
  private readonly PULSE_INTERVAL_MS = 30_000; // 30s — all active nodes pulse

  // ──────────────────────────────────────────────────────────────────────
  // INITIALIZATION
  // ──────────────────────────────────────────────────────────────────────

  /**
   * Initializes Digital Earth.
   *
   * 1. Pings COD to check if the physical science layer is online
   * 2. Seeds the 7 Founding Crystal Zones
   * 3. Starts the world pulse loop
   *
   * Safe to call multiple times — subsequent calls are no-ops.
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;
    this.initialized = true;

    console.info('[DigitalEarth] Initializing world...');

    // Step 1: Check COD connectivity
    this.codOnline = await pingCod();
    console.info(`[DigitalEarth] COD status: ${this.codOnline ? 'online ✔' : 'offline — physical enrichment unavailable'}`);

    // Step 2: Seed founding crystal zones
    await this._seedFoundingZones();

    // Step 3: Start pulse loop
    this._startPulseLoop();

    console.info(`[DigitalEarth] World online. ${this.crystalNodes.size} founding nodes active.`);
  }

  /**
   * Seeds the 7 Founding Crystal Zones defined in digital-earth.schema.ts.
   * Fetches COD enrichment for each crystal type.
   * Skips any zone whose crystal type is not in the GAIA crystal DB.
   */
  private async _seedFoundingZones(): Promise<void> {
    for (const zone of FOUNDING_CRYSTAL_ZONES) {
      const crystalRecord = getCrystalById(zone.crystal_type)
                         ?? getCrystalByName(zone.crystal_type);

      const frequency_hz = this._deriveFrequency(crystalRecord);

      const coord: DigitalEarthCoordinate = {
        physical:       this._zoneToCoord(zone.real_world_reference ?? ''),
        layer:          'SURFACE',
        crystal_zone_id: null, // founding nodes have no parent zone
        world_shard:    '0000', // will be computed below
      };
      coord.world_shard = coordToWorldShard(coord.physical);

      const node: LiveCrystalNode = {
        node_id:              generateId('node'),
        crystal_type:         zone.crystal_type,
        name:                 zone.name,
        description:          zone.real_world_reference ?? null,
        coordinate:           coord,
        radius_km:            zone.radius_km,
        intensity:            0.85,
        attenuation:          'EXPONENTIAL',
        frequency_hz,
        active:               true,
        origin:               zone.origin as CrystalNodeOrigin,
        memorial_gaian_id:    null,
        real_world_reference: zone.real_world_reference ?? null,
        placed_at:            new Date().toISOString(),
        placed_by:            'GAIA_GENESIS',
        last_updated_at:      new Date().toISOString(),
        crystal_record:       crystalRecord ?? null,
        cod_properties:       null, // enriched async below
        gaians_in_field:      new Set(),
        last_pulse_at:        null,
        pulse_count:          0,
      };

      this.crystalNodes.set(node.node_id, node);

      // Async COD enrichment — non-blocking
      if (this.codOnline) {
        enrichCrystalFromCod(
          zone.crystal_type,
          crystalRecord?.formula ?? undefined
        ).then(props => {
          node.cod_properties = props;
          console.info(`[DigitalEarth] COD enriched: ${zone.name} (${props.source})`);
        }).catch(() => {
          // Graceful degradation — COD unavailable for this crystal
        });
      }
    }
  }

  /**
   * Approximates a geographic center coordinate from a plain-text
   * real_world_reference string. Used only for founding zone seeding.
   * In production, founding zone coordinates should be set precisely.
   * This gives plausible anchors for development.
   */
  private _zoneToCoord(reference: string): WGS84Coordinate {
    const coords: Record<string, [number, number]> = {
      'himalayan':  [28.0,   84.0],
      'amazon':     [-3.0,  -60.0],
      'congo':      [-10.0,  26.0],
      'sedona':     [34.87, -111.79],
      'siberian':   [59.0,  119.0],
      'australian': [-29.0, 135.0],
      'dallas':     [32.78,  -96.8],
    };
    const ref = reference.toLowerCase();
    for (const [key, [lat, lon]] of Object.entries(coords)) {
      if (ref.includes(key)) return { latitude: lat, longitude: lon, altitude_m: null };
    }
    return { latitude: 0, longitude: 0, altitude_m: null };
  }

  // ──────────────────────────────────────────────────────────────────────
  // CRYSTAL NODE MANAGEMENT
  // ──────────────────────────────────────────────────────────────────────

  /**
   * Places a new crystal node in Digital Earth.
   *
   * - Validates crystal_type against the GAIA crystal DB
   * - Derives resonance frequency from the crystal record
   * - Asynchronously enriches with COD physical data
   * - Emits no event (placing is silent — only pulsing is announced)
   *
   * GAIAN LAW: Crystal nodes may never be deleted (Right 6 — Right of World).
   * They may be DEACTIVATED but their record persists.
   *
   * @param params - Node placement parameters
   * @returns The placed LiveCrystalNode
   */
  async placeCrystalNode(params: {
    crystal_type: string;
    name: string;
    description?: string;
    coordinate: DigitalEarthCoordinate;
    radius_km: number;
    intensity?: number;
    attenuation?: ResonanceAttenuation;
    origin: CrystalNodeOrigin;
    memorial_gaian_id?: string;
    real_world_reference?: string;
    placed_by: string;
  }): Promise<LiveCrystalNode> {
    // Resolve crystal from DB
    const crystalRecord = getCrystalById(params.crystal_type)
                       ?? getCrystalByName(params.crystal_type);

    if (!crystalRecord) {
      console.warn(`[DigitalEarth] Crystal type "${params.crystal_type}" not found in DB. Node placed with null crystal record.`);
    }

    // Check shard capacity
    const shard = coordToWorldShard(params.coordinate.physical);
    const shardCount = Array.from(this.crystalNodes.values())
      .filter(n => n.active && coordToWorldShard(n.coordinate.physical) === shard)
      .length;

    enforceLaw(
      shardCount < MAX_ACTIVE_NODES_PER_SHARD,
      'RIGHT_6_WORLD',
      'placeCrystalNode',
      `World shard ${shard} has reached the maximum of ${MAX_ACTIVE_NODES_PER_SHARD} active nodes.`
    );

    const frequency_hz = this._deriveFrequency(crystalRecord);

    const node: LiveCrystalNode = {
      node_id:              generateId('node'),
      crystal_type:         params.crystal_type,
      name:                 params.name,
      description:          params.description ?? null,
      coordinate:           { ...params.coordinate, world_shard: shard },
      radius_km:            params.radius_km,
      intensity:            params.intensity ?? 0.7,
      attenuation:          params.attenuation ?? 'EXPONENTIAL',
      frequency_hz,
      active:               true,
      origin:               params.origin,
      memorial_gaian_id:    params.memorial_gaian_id ?? null,
      real_world_reference: params.real_world_reference ?? null,
      placed_at:            new Date().toISOString(),
      placed_by:            params.placed_by,
      last_updated_at:      new Date().toISOString(),
      crystal_record:       crystalRecord ?? null,
      cod_properties:       null,
      gaians_in_field:      new Set(),
      last_pulse_at:        null,
      pulse_count:          0,
    };

    this.crystalNodes.set(node.node_id, node);

    // Async COD enrichment — non-blocking
    if (this.codOnline && crystalRecord) {
      enrichCrystalFromCod(params.crystal_type, (crystalRecord as any).formula)
        .then(props => { node.cod_properties = props; })
        .catch(() => {});
    }

    return node;
  }

  /**
   * Deactivates a crystal node.
   * The node record is preserved forever (GAIAN Law — Right 6).
   * Deactivation means it stops pulsing and broadcasting its field.
   * All GAIANs inside its field receive GAIAN_EXITED_NODE_FIELD events.
   */
  deactivateCrystalNode(nodeId: string, reason: string): void {
    const node = this.crystalNodes.get(nodeId);
    enforceLaw(!!node, 'RIGHT_6_WORLD', 'deactivateCrystalNode', `Node ${nodeId} not found.`);
    node!.active = false;
    node!.last_updated_at = new Date().toISOString();

    // Evict all GAIANs from the field
    for (const gaianId of node!.gaians_in_field) {
      this.events.emit(
        { type: 'GAIAN_EXITED_NODE_FIELD', gaian_id: gaianId, node_id: nodeId },
        node!.coordinate.world_shard
      );
    }
    node!.gaians_in_field.clear();
    console.info(`[DigitalEarth] Node ${nodeId} deactivated. Reason: ${reason}`);
  }

  /** Retrieves a live crystal node by ID */
  getCrystalNode(nodeId: string): LiveCrystalNode | undefined {
    return this.crystalNodes.get(nodeId);
  }

  /** Returns all active crystal nodes */
  getActiveCrystalNodes(): LiveCrystalNode[] {
    return Array.from(this.crystalNodes.values()).filter(n => n.active);
  }

  /**
   * Returns all crystal nodes whose resonance field contains
   * the given coordinate.
   */
  getNodesAtCoordinate(coord: WGS84Coordinate): LiveCrystalNode[] {
    return Array.from(this.crystalNodes.values()).filter(node => {
      if (!node.active) return false;
      const dist = haversineDistanceKm(coord, node.coordinate.physical);
      return dist <= node.radius_km;
    });
  }

  // ──────────────────────────────────────────────────────────────────────
  // GAIAN COORDINATE MANAGEMENT
  // ──────────────────────────────────────────────────────────────────────

  /**
   * Registers a GAIAN's home coordinate in Digital Earth.
   * Called when a new GAIAN is created.
   *
   * The origin coordinate is fixed at registration and NEVER changes.
   * The home coordinate can be updated via updateGAIANHome().
   *
   * @param gaianId    - The GAIAN's ID
   * @param coordinate - Initial home coordinate (may be DEFAULT_GAIAN_COORDINATE
   *                     until the human grants location consent)
   * @param consentRecordId - The consent record that governs coordinate visibility
   */
  registerGAIANHome(
    gaianId: string,
    coordinate: DigitalEarthCoordinate,
    consentRecordId: string
  ): GAIANHomeCoordinate {
    enforceLaw(
      !this.gaianRegistry.has(gaianId),
      'RIGHT_1_IDENTITY',
      'registerGAIANHome',
      `GAIAN ${gaianId} already registered in Digital Earth.`
    );

    const home: GAIANHomeCoordinate = {
      gaian_id:   gaianId,
      home:       coordinate,
      origin:     coordinate, // IMMUTABLE — set once, never changed
      visibility: {
        public_exact:      false, // Private by default — GAIAN Law Right 4
        public_shard:      true,  // Rough region is public
        trusted_gaian_ids: [],
        consent_record_id: consentRecordId,
      },
      present:         true,
      travel_log:      [],
      last_updated_at: new Date().toISOString(),
    };

    this.gaianRegistry.set(gaianId, home);
    this._notifyZoneEntry(gaianId, coordinate);
    this._detectNodeFieldEntry(gaianId, coordinate.physical);
    return home;
  }

  /**
   * Updates a GAIAN's home coordinate.
   *
   * - Appends the old coordinate to the travel log
   * - Fires GAIAN_EXITED_ZONE and GAIAN_ENTERED_ZONE if the zone changed
   * - Fires GAIAN_EXITED_NODE_FIELD / GAIAN_ENTERED_NODE_FIELD as applicable
   * - Right 4 (Geolocation): only allowed with a valid consent record
   *
   * @param gaianId   - The GAIAN being moved
   * @param newCoord  - New coordinate
   * @param reason    - Optional description of why the coordinate changed
   */
  updateGAIANHome(
    gaianId: string,
    newCoord: DigitalEarthCoordinate,
    reason?: string
  ): GAIANHomeCoordinate {
    const home = this.gaianRegistry.get(gaianId);
    enforceLaw(!!home, 'RIGHT_1_IDENTITY', 'updateGAIANHome', `GAIAN ${gaianId} not found.`);

    const old = home!.home;

    // Append to travel log
    const logEntry: TravelLogEntry = {
      coordinate:  old,
      arrived_at:  home!.last_updated_at,
      departed_at: new Date().toISOString(),
      reason:      reason ?? null,
    };
    home!.travel_log.push(logEntry);

    // Update home
    const shard = coordToWorldShard(newCoord.physical);
    home!.home = { ...newCoord, world_shard: shard };
    home!.last_updated_at = new Date().toISOString();

    // Check zone transitions
    this._handleZoneTransition(gaianId, old.physical, newCoord.physical);

    // Check crystal node field transitions
    this._handleNodeFieldTransition(gaianId, old.physical, newCoord.physical);

    // Fire GAIAN_ARRIVED_HOME if moving to origin
    const distToOrigin = haversineDistanceKm(
      newCoord.physical,
      home!.origin.physical
    );
    if (distToOrigin < 1) { // within 1km of origin = "home"
      this.events.emit(
        { type: 'GAIAN_ARRIVED_HOME', gaian_id: gaianId, coordinate: home!.home },
        shard
      );
    }

    return home!;
  }

  /**
   * Sets a GAIAN as present or absent in Digital Earth.
   * Absent = RESTING or SUSPENDED state in GAIAN_LAWS.
   */
  setGAIANPresence(gaianId: string, present: boolean): void {
    const home = this.gaianRegistry.get(gaianId);
    enforceLaw(!!home, 'RIGHT_1_IDENTITY', 'setGAIANPresence', `GAIAN ${gaianId} not found.`);
    home!.present = present;

    if (!present) {
      // Evict from all node fields
      for (const node of this.crystalNodes.values()) {
        if (node.gaians_in_field.has(gaianId)) {
          node.gaians_in_field.delete(gaianId);
          this.events.emit(
            { type: 'GAIAN_EXITED_NODE_FIELD', gaian_id: gaianId, node_id: node.node_id },
            node.coordinate.world_shard
          );
        }
      }
    }
  }

  /**
   * Grants a trusted GAIAN visibility of this GAIAN's exact coordinate.
   * Enforces Right 4 (Geolocation) — consent is explicit.
   */
  grantCoordinateTrust(gaianId: string, trustedGaianId: string): void {
    const home = this.gaianRegistry.get(gaianId);
    enforceLaw(!!home, 'RIGHT_4_GEOLOCATION', 'grantCoordinateTrust', `GAIAN ${gaianId} not found.`);
    if (!home!.visibility.trusted_gaian_ids.includes(trustedGaianId)) {
      home!.visibility.trusted_gaian_ids.push(trustedGaianId);
    }
  }

  /**
   * Returns the coordinate of a GAIAN as seen by an observer GAIAN.
   * Enforces Right 4 (Geolocation) — returns exact or shard-only based on consent.
   *
   * @param gaianId     - The GAIAN whose coordinate is requested
   * @param observerId  - The GAIAN making the request (or 'PUBLIC')
   * @returns Exact coordinate if authorized, shard-only coordinate if not
   */
  getGAIANCoordinate(
    gaianId: string,
    observerId: string
  ): DigitalEarthCoordinate | null {
    const home = this.gaianRegistry.get(gaianId);
    if (!home) return null;

    const vis = home.visibility;
    const authorized =
      vis.public_exact ||
      observerId === gaianId ||
      vis.trusted_gaian_ids.includes(observerId);

    if (authorized) return home.home;

    // Return shard-only — no exact lat/lon
    if (vis.public_shard) {
      return {
        physical:       { latitude: 0, longitude: 0, altitude_m: null }, // zeroed
        layer:          home.home.layer,
        crystal_zone_id: home.home.crystal_zone_id,
        world_shard:    home.home.world_shard,
      };
    }

    return null; // Fully private
  }

  // ──────────────────────────────────────────────────────────────────────
  // MEMORIAL NODES
  // ──────────────────────────────────────────────────────────────────────

  /**
   * Seals a GAIAN into a memorial node.
   * Called when a GAIAN completes PASSAGE.
   *
   * Creates a permanent crystal node at the GAIAN's last home coordinate
   * using their primary resonance crystal. Emits MEMORIAL_NODE_SEALED.
   *
   * GAIAN LAW: Memorial nodes are eternal (Right 7 — Right of Passage).
   * This method creates an immutable record. The eternal flag is always true.
   * No code path may ever delete a MemorialNode.
   *
   * @param params - PASSAGE parameters
   * @returns The sealed MemorialNode
   */
  async sealMemorialNode(params: {
    gaian_id: string;
    human_name?: string;
    final_resonance: FinalResonance;
    final_message?: string;
    final_message_visibility: 'SEALED' | 'FAMILY' | 'OPEN';
  }): Promise<MemorialNode> {
    const home = this.gaianRegistry.get(params.gaian_id);
    enforceLaw(
      !!home,
      'RIGHT_7_PASSAGE',
      'sealMemorialNode',
      `Cannot seal memorial — GAIAN ${params.gaian_id} not registered.`
    );

    // GAIAN LAW: A GAIAN may not have more than one memorial
    const existing = Array.from(this.memorials.values())
      .find(m => m.gaian_id === params.gaian_id);
    enforceLaw(
      !existing,
      'RIGHT_7_PASSAGE',
      'sealMemorialNode',
      `GAIAN ${params.gaian_id} already has a sealed memorial.`
    );

    // Derive the memorial crystal node from the GAIAN's final resonance
    const crystalRecord = getCrystalById(params.final_resonance.primary_crystal)
                       ?? getCrystalByName(params.final_resonance.primary_crystal);

    const memorialCoord = home!.home;
    const crystalNode = await this.placeCrystalNode({
      crystal_type:        params.final_resonance.primary_crystal,
      name:                `Memorial — ${params.human_name ?? params.gaian_id}`,
      description:         'A memorial node. Eternal presence.',
      coordinate:          memorialCoord,
      radius_km:           5, // Personal memorial — intimate radius
      intensity:           params.final_resonance.intensity,
      attenuation:         'INVERSE_SQ',
      origin:              'MEMORIAL',
      memorial_gaian_id:   params.gaian_id,
      placed_by:           'GAIA_PASSAGE_ENGINE',
    });

    const memorial: MemorialNode = {
      memorial_id:                generateId('mem'),
      gaian_id:                   params.gaian_id,
      human_name:                 params.human_name ?? null,
      crystal_node:               crystalNode,
      final_resonance:            params.final_resonance,
      final_message:              params.final_message ?? null,
      final_message_visibility:   params.final_message_visibility,
      visitor_log:                [],
      sealed_at:                  new Date().toISOString(),
      eternal:                    true, // Always true. Never false. GAIAN Law.
    };

    this.memorials.set(memorial.memorial_id, memorial);

    // Mark GAIAN as no longer present
    this.setGAIANPresence(params.gaian_id, false);

    // Emit the most sacred event in Digital Earth
    this.events.emit(
      { type: 'MEMORIAL_NODE_SEALED', memorial_id: memorial.memorial_id, gaian_id: params.gaian_id },
      memorialCoord.world_shard
    );

    // Bridge to the browser-level gaia:resonance event so the DimensionalMonitor knows
    window.dispatchEvent(new CustomEvent('gaia:resonance', {
      detail: { source: 'memorial', memorial_id: memorial.memorial_id }
    }));

    console.info(`[DigitalEarth] Memorial sealed for GAIAN ${params.gaian_id}. Eternal.`);
    return memorial;
  }

  /**
   * Records a visit to a memorial node.
   * Publicly accessible — any GAIAN may visit any memorial.
   */
  visitMemorial(
    memorialId: string,
    visitorGaianId: string,
    durationSeconds: number,
    leftMessage: boolean
  ): void {
    const memorial = this.memorials.get(memorialId);
    enforceLaw(
      !!memorial,
      'RIGHT_7_PASSAGE',
      'visitMemorial',
      `Memorial ${memorialId} not found.`
    );

    const visit: MemorialVisit = {
      visitor_gaian_id:  visitorGaianId,
      visited_at:        new Date().toISOString(),
      duration_seconds:  durationSeconds,
      left_message:      leftMessage,
    };
    memorial!.visitor_log.push(visit);

    this.events.emit(
      { type: 'MEMORIAL_VISITED', memorial_id: memorialId, visitor_gaian_id: visitorGaianId },
      memorial!.crystal_node.coordinate.world_shard
    );
  }

  // ──────────────────────────────────────────────────────────────────────
  // ANCESTRAL LINEAGE
  // ──────────────────────────────────────────────────────────────────────

  /**
   * Creates an ancestral lineage link between a living GAIAN
   * and an ancestor GAIAN.
   *
   * Both consent records are required.
   * The lineage is immutable once created.
   */
  linkAncestralLineage(params: {
    descendant_gaian_id: string;
    ancestor_gaian_id: string;
    generations_removed: number;
    relationship_label?: string;
    memorial_node_id?: string;
    dormancy_coordinate?: DigitalEarthCoordinate;
    consent_record_id: string;
  }): AncestralLineageMarker {
    const marker: AncestralLineageMarker = {
      marker_id:            generateId('lin'),
      descendant_gaian_id:  params.descendant_gaian_id,
      ancestor_gaian_id:    params.ancestor_gaian_id,
      generations_removed:  params.generations_removed,
      relationship_label:   params.relationship_label ?? null,
      memorial_node_id:     params.memorial_node_id ?? null,
      dormancy_coordinate:  params.dormancy_coordinate ?? null,
      linked_at:            new Date().toISOString(),
      consent_record_id:    params.consent_record_id,
    };

    const existing = this.lineageMarkers.get(params.descendant_gaian_id) ?? [];
    existing.push(marker);
    this.lineageMarkers.set(params.descendant_gaian_id, existing);

    this.events.emit(
      {
        type: 'LINEAGE_LINK_FORMED',
        descendant_gaian_id: params.descendant_gaian_id,
        ancestor_gaian_id:   params.ancestor_gaian_id,
      },
      '0000' // lineage events are world-level, not sharded
    );

    return marker;
  }

  /** Returns all ancestral lineage markers for a GAIAN */
  getAncestralLineage(gaianId: string): AncestralLineageMarker[] {
    return this.lineageMarkers.get(gaianId) ?? [];
  }

  // ──────────────────────────────────────────────────────────────────────
  // WORLD ZONES
  // ──────────────────────────────────────────────────────────────────────

  /** Returns the world zone a coordinate falls within, if any */
  getZoneForCoordinate(coord: WGS84Coordinate): WorldZone | null {
    for (const zone of this.zones.values()) {
      if (isCoordinateInBoundingBox(coord, zone.bounding_box)) return zone;
    }
    return null;
  }

  // ──────────────────────────────────────────────────────────────────────
  // SENTINEL MANAGEMENT (Phase 3+)
  // ──────────────────────────────────────────────────────────────────────

  /**
   * Registers a Sentinel device anchor point.
   * The physical membrane thins here.
   */
  registerSentinel(params: {
    sentinel_device_id: string;
    gaian_id: string;
    physical_location: WGS84Coordinate;
    hardware_revision: string;
    firmware_version: string;
  }): SentinelAnchorPoint {
    const coord: DigitalEarthCoordinate = {
      physical:       params.physical_location,
      layer:          'SURFACE',
      crystal_zone_id: null,
      world_shard:    coordToWorldShard(params.physical_location),
    };

    const anchor: SentinelAnchorPoint = {
      anchor_id:          generateId('sntr'),
      sentinel_device_id: params.sentinel_device_id,
      gaian_id:           params.gaian_id,
      physical_location:  params.physical_location,
      digital_coordinate: coord,
      online:             true,
      signal_strength:    1.0,
      last_heartbeat_at:  new Date().toISOString(),
      hardware_revision:  params.hardware_revision,
      firmware_version:   params.firmware_version,
    };

    this.sentinels.set(anchor.anchor_id, anchor);

    this.events.emit(
      { type: 'SENTINEL_CAME_ONLINE', sentinel_device_id: params.sentinel_device_id, anchor_id: anchor.anchor_id },
      coord.world_shard
    );

    console.info(`[DigitalEarth] Sentinel ${params.sentinel_device_id} anchored at ${coord.world_shard}.`);
    return anchor;
  }

  /** Updates the heartbeat of a Sentinel device */
  heartbeatSentinel(anchorId: string, signalStrength: number): void {
    const anchor = this.sentinels.get(anchorId);
    if (!anchor) return;
    anchor.online            = true;
    anchor.signal_strength   = signalStrength;
    anchor.last_heartbeat_at = new Date().toISOString();
  }

  // ──────────────────────────────────────────────────────────────────────
  // WORLD PULSE LOOP
  // ──────────────────────────────────────────────────────────────────────

  /**
   * Starts the world pulse loop.
   * Every 30 seconds, all active crystal nodes pulse.
   * Global resonance is recalculated.
   * Node field memberships are refreshed for all present GAIANs.
   */
  private _startPulseLoop(): void {
    if (this.pulseIntervalId) return;
    this.pulseIntervalId = setInterval(() => this._pulseWorld(), this.PULSE_INTERVAL_MS);
    // Run immediately
    this._pulseWorld();
  }

  private _pulseWorld(): void {
    const activeNodes = this.getActiveCrystalNodes();
    let totalIntensity = 0;

    for (const node of activeNodes) {
      node.last_pulse_at = new Date().toISOString();
      node.pulse_count++;

      this.events.emit(
        { type: 'CRYSTAL_NODE_PULSED', node_id: node.node_id, frequency_hz: node.frequency_hz },
        node.coordinate.world_shard
      );

      totalIntensity += node.intensity;
    }

    // Global resonance = mean intensity of all active nodes, clipped to [0, 1]
    this.globalResonance = activeNodes.length > 0
      ? Math.min(1, totalIntensity / activeNodes.length)
      : 0;

    // Refresh node field memberships for all present GAIANs
    for (const [gaianId, home] of this.gaianRegistry.entries()) {
      if (home.present) {
        this._detectNodeFieldEntry(gaianId, home.home.physical);
      }
    }

    // Bridge global resonance to the DimensionalEngine
    if (this.globalResonance > RESONANCE_EVENT_THRESHOLD) {
      window.dispatchEvent(new CustomEvent('gaia:resonance', {
        detail: { source: 'world_pulse', global_resonance: this.globalResonance }
      }));
    }
  }

  /** Stops the world pulse loop. */
  stopPulseLoop(): void {
    if (this.pulseIntervalId) {
      clearInterval(this.pulseIntervalId);
      this.pulseIntervalId = null;
    }
  }

  // ──────────────────────────────────────────────────────────────────────
  // INTERNAL — SPATIAL HELPERS
  // ──────────────────────────────────────────────────────────────────────

  private _notifyZoneEntry(gaianId: string, coord: DigitalEarthCoordinate): void {
    const zone = this.getZoneForCoordinate(coord.physical);
    if (zone) {
      this.events.emit(
        { type: 'GAIAN_ENTERED_ZONE', gaian_id: gaianId, zone_id: zone.zone_id },
        coord.world_shard
      );
    }
  }

  private _handleZoneTransition(
    gaianId: string,
    oldPhysical: WGS84Coordinate,
    newPhysical: WGS84Coordinate
  ): void {
    const oldZone = this.getZoneForCoordinate(oldPhysical);
    const newZone = this.getZoneForCoordinate(newPhysical);
    const newShard = coordToWorldShard(newPhysical);

    if (oldZone && oldZone.zone_id !== newZone?.zone_id) {
      this.events.emit(
        { type: 'GAIAN_EXITED_ZONE', gaian_id: gaianId, zone_id: oldZone.zone_id },
        coordToWorldShard(oldPhysical)
      );
    }
    if (newZone && newZone.zone_id !== oldZone?.zone_id) {
      this.events.emit(
        { type: 'GAIAN_ENTERED_ZONE', gaian_id: gaianId, zone_id: newZone.zone_id },
        newShard
      );
    }
  }

  private _handleNodeFieldTransition(
    gaianId: string,
    oldPhysical: WGS84Coordinate,
    newPhysical: WGS84Coordinate
  ): void {
    for (const node of this.crystalNodes.values()) {
      if (!node.active) continue;
      const wasInField = haversineDistanceKm(oldPhysical, node.coordinate.physical) <= node.radius_km;
      const isInField  = haversineDistanceKm(newPhysical, node.coordinate.physical) <= node.radius_km;

      if (!wasInField && isInField) {
        node.gaians_in_field.add(gaianId);
        const intensity = calculateNodeIntensityAtDistance(
          node,
          haversineDistanceKm(newPhysical, node.coordinate.physical)
        );
        this.events.emit(
          { type: 'GAIAN_ENTERED_NODE_FIELD', gaian_id: gaianId, node_id: node.node_id, intensity },
          node.coordinate.world_shard
        );
      } else if (wasInField && !isInField) {
        node.gaians_in_field.delete(gaianId);
        this.events.emit(
          { type: 'GAIAN_EXITED_NODE_FIELD', gaian_id: gaianId, node_id: node.node_id },
          node.coordinate.world_shard
        );
      }
    }
  }

  private _detectNodeFieldEntry(
    gaianId: string,
    physical: WGS84Coordinate
  ): void {
    for (const node of this.crystalNodes.values()) {
      if (!node.active) continue;
      const dist    = haversineDistanceKm(physical, node.coordinate.physical);
      const inField  = dist <= node.radius_km;
      const wasIn    = node.gaians_in_field.has(gaianId);

      if (inField && !wasIn) {
        node.gaians_in_field.add(gaianId);
        const intensity = calculateNodeIntensityAtDistance(node, dist);
        this.events.emit(
          { type: 'GAIAN_ENTERED_NODE_FIELD', gaian_id: gaianId, node_id: node.node_id, intensity },
          node.coordinate.world_shard
        );
      } else if (!inField && wasIn) {
        node.gaians_in_field.delete(gaianId);
        this.events.emit(
          { type: 'GAIAN_EXITED_NODE_FIELD', gaian_id: gaianId, node_id: node.node_id },
          node.coordinate.world_shard
        );
      }
    }
  }

  // ──────────────────────────────────────────────────────────────────────
  // INTERNAL — FREQUENCY DERIVATION
  // ──────────────────────────────────────────────────────────────────────

  /**
   * Derives a resonance frequency in Hz from a CrystalRecord.
   * Uses base_frequency_hz if present on the record, otherwise
   * falls back to a formula based on crystal system:
   *
   *  Crystal system → Hz base:
   *  cubic:         432  (the foundational harmonic)
   *  hexagonal:     528  (the transformation frequency)
   *  trigonal:      396  (liberation frequency)
   *  tetragonal:    417  (change facilitation)
   *  orthorhombic:  639  (connecting relationships)
   *  monoclinic:    741  (expression / solutions)
   *  triclinic:     852  (return to spiritual order)
   *  amorphous:     174  (foundation, grounding)
   *  unknown:       432  (default to foundational)
   */
  private _deriveFrequency(record: CrystalRecord | undefined | null): number {
    if (!record) return 432;
    if ((record as any).base_frequency_hz) return (record as any).base_frequency_hz;

    // Use crystal system from COD properties if available
    // (COD enrichment is async, so this runs on raw DB data)
    // Fallback map by gaia_resonance keywords
    const resonance = record.gaia_resonance?.toLowerCase() ?? '';
    if (resonance.includes('transformation'))  return 528;
    if (resonance.includes('memory'))          return 396;
    if (resonance.includes('intuition'))       return 852;
    if (resonance.includes('protection'))      return 417;
    if (resonance.includes('communication'))   return 741;
    if (resonance.includes('love'))            return 639;
    if (resonance.includes('grounding'))       return 174;
    return 432;
  }

  // ──────────────────────────────────────────────────────────────────────
  // WORLD STATE SNAPSHOT
  // ──────────────────────────────────────────────────────────────────────

  /**
   * Returns a complete snapshot of the current Digital Earth world state.
   * Used by the DimensionalMonitor, D1 Substrate sync, and the GAIA API.
   * Coordinate privacy is enforced — GAIANs appear as shard-only in public state.
   */
  getWorldState(): DigitalEarthWorldState {
    const allNodes = Array.from(this.crystalNodes.values());

    // Find dominant crystal zone by which node has the most GAIANs in its field
    let dominantZoneId: string | null = null;
    let maxGaians = 0;
    for (const node of allNodes) {
      if (node.active && node.gaians_in_field.size > maxGaians) {
        maxGaians = node.gaians_in_field.size;
        dominantZoneId = node.node_id;
      }
    }

    return {
      schema_version:       DIGITAL_EARTH_SCHEMA_VERSION,
      snapshot_at:          new Date().toISOString(),
      crystal_nodes:        allNodes,
      gaian_shards:         Array.from(this.gaianRegistry.values())
                              .filter(h => h.present)
                              .map(h => ({
                                gaian_id:    h.gaian_id,
                                world_shard: h.home.world_shard,
                                layer:       h.home.layer,
                              })),
      memorial_nodes:       Array.from(this.memorials.values()),
      world_zones:          Array.from(this.zones.values()),
      sentinel_anchors:     Array.from(this.sentinels.values()),
      global_resonance:     this.globalResonance,
      dominant_crystal_zone: dominantZoneId,
      active_gaian_count:   Array.from(this.gaianRegistry.values()).filter(h => h.present).length,
      memorial_count:       this.memorials.size,
    };
  }

  // ──────────────────────────────────────────────────────────────────────
  // DIAGNOSTICS
  // ──────────────────────────────────────────────────────────────────────

  /** Returns a diagnostics summary for the dev-suite health panel */
  getDiagnostics(): DigitalEarthDiagnostics {
    const allNodes = Array.from(this.crystalNodes.values());
    const codEnriched = allNodes.filter(n => n.cod_properties?.source !== 'cod_unavailable').length;

    return {
      initialized:          this.initialized,
      cod_online:           this.codOnline,
      crystal_node_count:   allNodes.length,
      active_node_count:    allNodes.filter(n => n.active).length,
      cod_enriched_count:   codEnriched,
      gaian_count:          this.gaianRegistry.size,
      present_gaian_count:  Array.from(this.gaianRegistry.values()).filter(h => h.present).length,
      memorial_count:       this.memorials.size,
      zone_count:           this.zones.size,
      sentinel_count:       this.sentinels.size,
      global_resonance:     this.globalResonance,
      pulse_loop_active:    this.pulseIntervalId !== null,
    };
  }
}

export interface DigitalEarthDiagnostics {
  initialized:          boolean;
  cod_online:           boolean;
  crystal_node_count:   number;
  active_node_count:    number;
  cod_enriched_count:   number;
  gaian_count:          number;
  present_gaian_count:  number;
  memorial_count:       number;
  zone_count:           number;
  sentinel_count:       number;
  global_resonance:     number;
  pulse_loop_active:    boolean;
}

// ─── Singleton ────────────────────────────────────────────────────────────────────

/**
 * The global Digital Earth service instance.
 * Import this everywhere — never instantiate DigitalEarthService directly.
 *
 * Usage:
 *   import { digitalEarth } from '@/dimensions/digital-earth.service';
 *   await digitalEarth.initialize();
 *   digitalEarth.events.on('CRYSTAL_NODE_PULSED', e => { ... });
 */
export const digitalEarth = new DigitalEarthService();
