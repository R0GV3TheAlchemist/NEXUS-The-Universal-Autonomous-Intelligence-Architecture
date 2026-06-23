"""BIOPHOTON_07: Microtubule Entanglement Detection Simulation
GAIA-OS Simulation Series | 2026-06-23
Authors: R0GV3 + GAIA

Simulates quantum entanglement detection across a 20nm synaptic cleft.
Models:
  - 13-node tryptophan qubit ring (per microtubule cross-section)
  - Bell CHSH inequality test at body temperature vs cryogenic
  - Water Josephson quantum filter (JQF) transmission fidelity
  - Decoherence envelope at 310K and 4K
  - Detection method sensitivity and feasibility scoring

See canon/BIOPHOTON_07 for full documentation.
"""

import numpy as np

rng = np.random.default_rng(42)

# Physical constants
HBAR = 1.0545718e-34
KB   = 1.380649e-23

# System parameters
N_TUBULIN           = 13
N_TRYPTOPHAN        = 8
N_QUBITS            = N_TUBULIN * N_TRYPTOPHAN  # 104
CLEFT_WIDTH_NM      = 20
WATER_FILTER_FIDELITY = 0.87
TAU_BODY_PS         = 10.0
TAU_CRYO_PS         = 1e6
BELL_CLASSICAL      = 2.0
BELL_TSIRELSON      = 2 * np.sqrt(2)  # ~2.828

t_ps = np.arange(300, dtype=float)


def decoherence_factor(t_ps_val, tau_ps, temp_K):
    thermal_floor = min((KB * temp_K) / (HBAR * 613e12 * 1e-12) * 1e-15, 0.15)
    return np.exp(-t_ps_val / tau_ps) * (1 - thermal_floor) + thermal_floor * 0.1


def chsh_correlation(angle_a, angle_b, fidelity, noise):
    return fidelity * (-np.cos(angle_a - angle_b)) + (1 - fidelity) * noise * rng.normal()


def bell_S(fidelity, noise=0.08):
    a1, a2, b1, b2 = 0, np.pi/4, np.pi/8, 3*np.pi/8
    return (chsh_correlation(a1,b1,fidelity,noise) - chsh_correlation(a1,b2,fidelity,noise)
            + chsh_correlation(a2,b1,fidelity,noise) + chsh_correlation(a2,b2,fidelity,noise))


def entanglement_matrix(n=13, nn_strength=0.91, nnn_strength=0.72, filter_fidelity=0.87):
    M = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                diff = min(abs(i-j), n-abs(i-j))
                if diff == 1:
                    M[i,j] = nn_strength * filter_fidelity
                elif diff == 2:
                    M[i,j] = nnn_strength * filter_fidelity
    return M


if __name__ == '__main__':
    print(f'Tryptophan qubits per MT ring: {N_QUBITS}')
    print(f'Water JQF fidelity:            {WATER_FILTER_FIDELITY:.2%}')
    print(f'Tsirelson bound:               {BELL_TSIRELSON:.4f}')

    S_body = [bell_S(WATER_FILTER_FIDELITY * decoherence_factor(t, TAU_BODY_PS, 310), 0.08)
              for t in t_ps]
    S_cryo = [bell_S(decoherence_factor(t, TAU_CRYO_PS, 4), 0.024)
              for t in t_ps]

    window = int(TAU_BODY_PS * 3)
    viol_body = np.mean(np.abs(S_body[:window]) > BELL_CLASSICAL)
    viol_cryo = np.mean(np.abs(S_cryo) > BELL_CLASSICAL)

    print(f'Quantum violation rate (body): {viol_body:.2%}')
    print(f'Quantum violation rate (cryo): {viol_cryo:.2%}')

    M = entanglement_matrix()
    print(f'NN entanglement strength:      {M[0,1]:.4f}')
    print(f'NNN entanglement strength:     {M[0,2]:.4f}')
    print('Simulation complete. See BIOPHOTON_07 canon for interpretation.')
