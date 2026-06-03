<template>
  <div class="telemetry-hub">
    <!-- Header -->
    <div class="hub-header">
      <span class="hub-title">🔬 Agent Telemetry Hub</span>
      <div class="hub-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="hub-status">
        <span :class="['conn-dot', connected ? 'green' : 'red']" />
        {{ connected ? 'Live' : 'Reconnecting…' }}
      </div>
    </div>

    <!-- Live Event Stream -->
    <div v-if="activeTab === 'stream'" class="event-stream">
      <div
        v-for="event in visibleEvents"
        :key="event.id"
        :class="['event-row', riskClass(event)]"
      >
        <span class="ev-time">{{ formatTime(event.timestamp) }}</span>
        <span class="ev-icon">{{ eventIcon(event) }}</span>
        <span class="ev-skill">{{ event.skill_id || event.source }}</span>
        <span class="ev-type">{{ event.event_type }}</span>
        <span v-if="event.duration_ms" class="ev-dur">{{ event.duration_ms }}ms</span>
        <span v-if="event.dq_score !== null" class="ev-dq">DQ: {{ event.dq_score?.toFixed(2) }}</span>
        <span v-if="event.degraded" class="ev-badge degraded">FALLBACK</span>
        <span v-if="event.risk_tier === 'RED'" class="ev-badge red">RED</span>
        <span v-if="event.risk_tier === 'YELLOW'" class="ev-badge yellow">YELLOW</span>
      </div>
      <div v-if="visibleEvents.length === 0" class="empty-state">
        No events yet — waiting for GAIA activity…
      </div>
    </div>

    <!-- Skill Health Panel -->
    <div v-if="activeTab === 'skills'" class="skill-health">
      <div
        v-for="skill in skillHealth"
        :key="skill.skill_id"
        :class="['skill-row', skill.circuit_state.toLowerCase()]"
      >
        <span class="skill-id">{{ skill.skill_id }}</span>
        <span :class="['circuit-badge', skill.circuit_state.toLowerCase()]">
          {{ skill.circuit_state }}
        </span>
        <span class="skill-stat">error rate: {{ (skill.error_rate * 100).toFixed(0) }}%</span>
        <span class="skill-stat">avg: {{ skill.avg_duration_ms.toFixed(0) }}ms</span>
        <span v-if="skill.last_failure_at" class="skill-stat dim">
          last fail: {{ relativeTime(skill.last_failure_at) }}
        </span>
      </div>
      <div v-if="skillHealth.length === 0" class="empty-state">No skill health data yet.</div>
    </div>

    <!-- DQ + OE Trends (placeholder for charts — wired in #190) -->
    <div v-if="activeTab === 'quality'" class="quality-panel">
      <div class="oe-summary" v-if="oe">
        <div class="oe-stat">
          <span class="oe-label">OE Score</span>
          <span class="oe-value">{{ oe.oe_score?.toFixed(3) ?? '—' }}</span>
        </div>
        <div class="oe-stat">
          <span class="oe-label">Avg DQ</span>
          <span class="oe-value">{{ oe.avg_dq_score?.toFixed(2) ?? '—' }}</span>
        </div>
        <div class="oe-stat">
          <span class="oe-label">Tasks ({{ oe.window }})</span>
          <span class="oe-value">{{ oe.successful_tasks }} / {{ oe.total_tasks }}</span>
        </div>
        <div class="oe-stat">
          <span class="oe-label">Degraded</span>
          <span class="oe-value">{{ (oe.degraded_fraction * 100).toFixed(0) }}%</span>
        </div>
        <div class="oe-stat">
          <span class="oe-label">Avg Latency</span>
          <span class="oe-value">{{ oe.avg_total_latency_s?.toFixed(2) }}s</span>
        </div>
      </div>
      <div class="dq-list">
        <div v-for="r in dqHistory" :key="r.session_id + r.timestamp" class="dq-row">
          <span class="dq-time">{{ formatTime(r.timestamp) }}</span>
          <span class="dq-intent">{{ r.intent_class || '—' }}</span>
          <span :class="['dq-score', dqClass(r.dq_score)]">{{ r.dq_score?.toFixed(3) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

const TELEMETRY_SSE_URL = '/api/telemetry/stream'
const SKILL_IDS = ['synergy_orchestrator', 'research_desk', 'crystal_graphrag', 'planetary_hub', 'biometric_engine']

type TelemetryEvent = Record<string, any>
type SkillHealth = Record<string, any>
type OE = Record<string, any>

const activeTab = ref<'stream' | 'skills' | 'quality'>('stream')
const tabs = [
  { id: 'stream', label: '📊 Live Stream' },
  { id: 'skills', label: '🔗 Skill Health' },
  { id: 'quality', label: '🎯 DQ / OE' },
]

const events = ref<TelemetryEvent[]>([])
const skillHealth = ref<SkillHealth[]>([])
const dqHistory = ref<any[]>([])
const oe = ref<OE | null>(null)
const connected = ref(false)

const visibleEvents = computed(() => events.value.slice(0, 200))

let evtSource: EventSource | null = null
let healthInterval: ReturnType<typeof setInterval> | null = null

function connectSSE() {
  evtSource = new EventSource(TELEMETRY_SSE_URL)
  evtSource.onopen = () => { connected.value = true }
  evtSource.onmessage = (e) => {
    try {
      const ev = JSON.parse(e.data)
      events.value.unshift(ev)
      if (events.value.length > 500) events.value.length = 500
    } catch { /* ignore parse errors */ }
  }
  evtSource.onerror = () => {
    connected.value = false
    evtSource?.close()
    setTimeout(connectSSE, 3000)
  }
}

async function fetchSkillHealth() {
  const results = await Promise.all(
    SKILL_IDS.map(id =>
      fetch(`/api/telemetry/skill/${id}`)
        .then(r => r.ok ? r.json() : null)
        .catch(() => null)
    )
  )
  skillHealth.value = results.filter(Boolean)
}

async function fetchQuality() {
  try {
    const [dqRes, oeRes] = await Promise.all([
      fetch('/api/telemetry/dq?limit=50').then(r => r.json()),
      fetch('/api/telemetry/oe?window=24h').then(r => r.json()),
    ])
    dqHistory.value = dqRes.records ?? []
    oe.value = oeRes
  } catch { /* swallow */ }
}

function formatTime(ts: string): string {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function relativeTime(ts: string): string {
  const diff = Math.round((Date.now() - new Date(ts).getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`
  return `${Math.round(diff / 3600)}h ago`
}

function eventIcon(ev: TelemetryEvent): string {
  if (ev.event_type === 'job_failed') return '🔴'
  if (ev.degraded) return '⚠️'
  if (ev.risk_tier === 'RED') return '🔴'
  if (ev.risk_tier === 'YELLOW') return '🟡'
  if (ev.event_type === 'action_gate_triggered') return '🔐'
  if (ev.event_type === 'circuit_broken') return '⛔'
  if (ev.source === 'healing') return '🔁'
  if (ev.source === 'biometric') return '💚'
  if (ev.source === 'planetary') return '🌍'
  return '✅'
}

function riskClass(ev: TelemetryEvent): string {
  if (ev.risk_tier === 'RED' || ev.event_type === 'job_failed') return 'risk-red'
  if (ev.risk_tier === 'YELLOW' || ev.degraded) return 'risk-yellow'
  return ''
}

function dqClass(score: number): string {
  if (score >= 0.85) return 'dq-high'
  if (score >= 0.65) return 'dq-mid'
  return 'dq-low'
}

onMounted(() => {
  connectSSE()
  fetchSkillHealth()
  fetchQuality()
  healthInterval = setInterval(() => {
    fetchSkillHealth()
    fetchQuality()
  }, 15000)
})

onUnmounted(() => {
  evtSource?.close()
  if (healthInterval) clearInterval(healthInterval)
})
</script>

<style scoped>
.telemetry-hub {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--gaia-surface, #0d0e14);
  color: var(--gaia-text, #e2e8f0);
  font-family: var(--gaia-mono, 'JetBrains Mono', monospace);
  font-size: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.hub-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--gaia-surface-2, #161820);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.hub-title { font-size: 13px; font-weight: 600; color: var(--gaia-teal, #4f98a3); }

.hub-tabs { display: flex; gap: 4px; }
.tab-btn {
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--gaia-text-dim, #94a3b8);
  cursor: pointer;
  font-size: 11px;
  transition: all 0.15s;
}
.tab-btn.active {
  background: rgba(79, 152, 163, 0.15);
  border-color: rgba(79, 152, 163, 0.4);
  color: var(--gaia-teal, #4f98a3);
}

.hub-status { margin-left: auto; display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--gaia-text-dim, #94a3b8); }
.conn-dot { width: 7px; height: 7px; border-radius: 50%; }
.conn-dot.green { background: #437a22; box-shadow: 0 0 4px #437a22; }
.conn-dot.red   { background: #a13544; }

/* Event stream */
.event-stream { flex: 1; overflow-y: auto; padding: 4px 0; }
.event-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background 0.1s;
}
.event-row:hover { background: rgba(255,255,255,0.03); }
.event-row.risk-red    { background: rgba(161,53,68,0.08); }
.event-row.risk-yellow { background: rgba(209,153,0,0.06); }

.ev-time  { color: var(--gaia-text-dim, #94a3b8); min-width: 72px; }
.ev-icon  { min-width: 18px; }
.ev-skill { color: var(--gaia-teal, #4f98a3); min-width: 140px; font-weight: 500; }
.ev-type  { color: var(--gaia-text, #e2e8f0); flex: 1; }
.ev-dur   { color: var(--gaia-text-dim, #94a3b8); min-width: 60px; text-align: right; }
.ev-dq    { color: #437a22; min-width: 72px; text-align: right; }

.ev-badge {
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
}
.ev-badge.degraded { background: rgba(209,153,0,0.2); color: #d19900; }
.ev-badge.red      { background: rgba(161,53,68,0.3); color: #f87171; }
.ev-badge.yellow   { background: rgba(209,153,0,0.2); color: #d19900; }

/* Skill health */
.skill-health { flex: 1; overflow-y: auto; padding: 8px 16px; display: flex; flex-direction: column; gap: 4px; }
.skill-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.05);
}
.skill-id { font-weight: 600; color: var(--gaia-teal, #4f98a3); min-width: 160px; }
.circuit-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
}
.circuit-badge.closed    { background: rgba(67,122,34,0.2); color: #437a22; }
.circuit-badge.open      { background: rgba(161,53,68,0.2); color: #f87171; }
.circuit-badge.half_open { background: rgba(209,153,0,0.2); color: #d19900; }
.skill-stat { color: var(--gaia-text-dim, #94a3b8); font-size: 11px; }
.skill-stat.dim { opacity: 0.6; }

/* Quality panel */
.quality-panel { flex: 1; overflow-y: auto; padding: 12px 16px; }
.oe-summary {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  padding: 12px 16px;
  background: rgba(79,152,163,0.07);
  border: 1px solid rgba(79,152,163,0.2);
  border-radius: 8px;
  margin-bottom: 12px;
}
.oe-stat { display: flex; flex-direction: column; gap: 2px; }
.oe-label { font-size: 10px; color: var(--gaia-text-dim, #94a3b8); text-transform: uppercase; letter-spacing: 0.08em; }
.oe-value { font-size: 18px; font-weight: 700; color: var(--gaia-teal, #4f98a3); }

.dq-list { display: flex; flex-direction: column; gap: 2px; }
.dq-row { display: flex; gap: 10px; padding: 4px 0; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.03); }
.dq-time   { color: var(--gaia-text-dim, #94a3b8); min-width: 72px; font-size: 11px; }
.dq-intent { flex: 1; color: var(--gaia-text, #e2e8f0); }
.dq-score  { font-weight: 700; min-width: 60px; text-align: right; }
.dq-high { color: #437a22; }
.dq-mid  { color: #d19900; }
.dq-low  { color: #a13544; }

.empty-state { padding: 32px; text-align: center; color: var(--gaia-text-dim, #94a3b8); opacity: 0.5; }
</style>
