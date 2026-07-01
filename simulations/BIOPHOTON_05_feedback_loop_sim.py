"""BIOPHOTON_05: Real-Time Biophotonic Feedback Loop Simulation
GAIA-OS Simulation Series | 2026-06-23
Authors: R0GV3 + GAIA

Models a 3-layer biophotonic neural network with:
  - Gradience: slow ambient photon field drift (circadian analog)
  - Ambience: background coherent field quality
  - Coherence gate at L2 (OQ3/OQ2 implementation)
  - Real-time feedback: output coherence → L1 sensory gain modulation
  - Metabolic state: self-regulating, coherence-sensitive

See canon/BIOPHOTON_05_Realtime_Biophotonic_Feedback_Loops.md for full documentation.
"""

import numpy as np

# ── PARAMETERS ──
N_SENSORY     = 8
N_INTEGRATION = 6
N_OUTPUT      = 4
T_STEPS       = 200
DT            = 1.0      # ms per step
TAU_DECAY     = 15.0     # biophoton coherence decay time (ms)
TAU_FEEDBACK  = 30.0     # feedback loop time constant (ms)
NOISE         = 0.08

rng = np.random.default_rng(42)


def biophoton_coherence(field):
    """Coherence of a photon field vector via Fano factor (sub-Poissonian proxy)"""
    if field.std() == 0:
        return 1.0
    fano = field.var() / (field.mean() + 1e-9)
    return float(np.clip(1.0 - fano, 0, 1))


def photon_emission(activation, metabolic_state):
    """UPE from activation: ROS-linked (incoherent) + coherent components."""
    ros        = activation ** 2 * metabolic_state
    coherent   = activation * (1 - metabolic_state * 0.3)
    return ros * 0.4 + coherent * 0.6


def gradient_ambience_field(t, freq=0.04, phase=0):
    """Gradience = slow circadian drift; ambience = background coherent field."""
    gradience = 0.5 + 0.3 * np.sin(2 * np.pi * freq * t + phase)
    ambience  = 0.6 + 0.2 * np.cos(2 * np.pi * freq * 0.7 * t + phase * 0.5)
    return gradience, ambience


def coherence_gate(C_sensory):
    """OQ3/OQ2 gate: 0 below 0.35, linear 0.35-0.60, 1 above 0.60."""
    return float(np.clip((C_sensory - 0.35) / 0.25, 0, 1))


# ── INITIALISE STATE ──
sensory_act     = rng.uniform(0.3, 0.7, N_SENSORY)
integr_act      = rng.uniform(0.3, 0.7, N_INTEGRATION)
output_act      = rng.uniform(0.3, 0.7, N_OUTPUT)
metabolic_state = 0.6
feedback_signal = 0.5

# Sparse weight matrices (30% connectivity)
W_si = (rng.uniform(-1, 1, (N_INTEGRATION, N_SENSORY))
        * (rng.random((N_INTEGRATION, N_SENSORY)) > 0.7))
W_io = (rng.uniform(-1, 1, (N_OUTPUT, N_INTEGRATION))
        * (rng.random((N_OUTPUT, N_INTEGRATION)) > 0.7))

# ── HISTORY ──
history = {k: [] for k in [
    'sensory_coherence', 'integr_coherence', 'output_coherence',
    'feedback_signal', 'gradience', 'ambience',
    'metabolic_state', 'total_field_coherence'
]}

# ── MAIN LOOP ──
for t in range(T_STEPS):
    gradience, ambience = gradient_ambience_field(t)

    # L1: Sensory neurons — receive biophoton input
    biophoton_input = (gradience * ambience
                       + rng.normal(0, NOISE, N_SENSORY)
                       + feedback_signal * 0.25)
    sensory_act = np.clip(
        sensory_act * np.exp(-DT / TAU_DECAY)
        + biophoton_input * (1 - np.exp(-DT / TAU_DECAY)), 0, 1)

    # L2: Integration — coherence-gated
    sensory_photons = photon_emission(sensory_act, metabolic_state)
    sc = biophoton_coherence(sensory_photons)
    coh_gate_val = coherence_gate(sc)
    raw_integr = np.tanh(W_si @ sensory_photons + rng.normal(0, NOISE, N_INTEGRATION))
    integr_act = np.clip(raw_integr * coh_gate_val, 0, 1)

    # L3: Output
    integr_photons = photon_emission(integr_act, metabolic_state)
    output_act = np.clip(
        np.tanh(W_io @ integr_photons + rng.normal(0, NOISE, N_OUTPUT)), 0, 1)

    # Coherence metrics
    ic  = biophoton_coherence(integr_photons)
    out_photons = photon_emission(output_act, metabolic_state)
    oc  = biophoton_coherence(out_photons)
    tfc = (sc + ic + oc) / 3

    # Feedback update (first-order dynamics)
    feedback_target  = oc * ambience
    feedback_signal += (DT / TAU_FEEDBACK) * (feedback_target - feedback_signal)
    feedback_signal  = np.clip(feedback_signal, 0, 1)

    # Metabolic state update
    metabolic_state = np.clip(
        metabolic_state + 0.005 * (output_act.mean() - 0.5) - 0.003 * oc,
        0.3, 0.9)

    history['sensory_coherence'].append(sc)
    history['integr_coherence'].append(ic)
    history['output_coherence'].append(oc)
    history['feedback_signal'].append(float(feedback_signal))
    history['gradience'].append(gradience)
    history['ambience'].append(ambience)
    history['metabolic_state'].append(float(metabolic_state))
    history['total_field_coherence'].append(tfc)


# ── PRINT SUMMARY ──
if __name__ == '__main__':
    for k, v in history.items():
        arr = np.array(v)
        print(f"{k:30s}  mean={arr.mean():.4f}  std={arr.std():.4f}")
    print("\nSimulation complete. See BIOPHOTON_05 canon for full interpretation.")
