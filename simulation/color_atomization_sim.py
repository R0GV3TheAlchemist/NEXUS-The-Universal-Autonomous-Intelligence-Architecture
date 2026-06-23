from dataclasses import dataclass
from typing import List
import csv, math, os
from statistics import mean

os.makedirs("simulation/output", exist_ok=True)

@dataclass
class ColorAtom:
    name: str
    hue_deg: float
    wavelength_nm: float
    frequency_thz: float
    positive_charge: float
    negative_charge: float
    resonance: float

    @property
    def complement_hue(self): return (self.hue_deg + 180) % 360
    @property
    def charge_magnitude(self): return math.sqrt(self.positive_charge**2 + self.negative_charge**2)
    @property
    def charge_differential(self): return abs(self.positive_charge - self.negative_charge)

COLOR_ATOMS = [
    ColorAtom("red",           0,   700, 428, 0.90, 0.20, 0.85),
    ColorAtom("red-orange",   30,   630, 476, 0.85, 0.25, 0.75),
    ColorAtom("orange",       60,   610, 492, 0.80, 0.30, 0.70),
    ColorAtom("yellow-orange",90,   590, 508, 0.75, 0.35, 0.65),
    ColorAtom("yellow",      120,   575, 521, 0.65, 0.40, 0.72),
    ColorAtom("yellow-green", 150,  555, 541, 0.45, 0.55, 0.80),
    ColorAtom("green",        180,  530, 566, 0.25, 0.80, 0.88),
    ColorAtom("blue-green",   210,  505, 594, 0.20, 0.85, 0.82),
    ColorAtom("blue",         240,  470, 638, 0.15, 0.90, 0.78),
    ColorAtom("blue-violet",  270,  450, 667, 0.20, 0.85, 0.72),
    ColorAtom("violet",       300,  420, 714, 0.30, 0.75, 0.68),
    ColorAtom("red-violet",   330,  390, 769, 0.55, 0.50, 0.74),
]

atom_map = {a.name: a for a in COLOR_ATOMS}

def angular_distance(h1, h2):
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)

def comp_score(dist): return dist / 180.0

def charge_align(a, b):
    dot = a.positive_charge * b.positive_charge + a.negative_charge * b.negative_charge
    mag = a.charge_magnitude * b.charge_magnitude
    return dot / mag if mag else 0.0

def coherence(comp, ct, res, wc=0.50, wq=0.30, wr=0.20):
    return wc * comp + wq * ct + wr * res

def classify_state(coh):
    if coh >= 0.60: return "harmonic"
    if coh >= 0.30: return "neutral"
    return "dissonant"

def force_type(a, b, dist, medium):
    align = charge_align(a, b)
    is_comp = dist >= 150
    both_loud = a.resonance >= 0.75 and b.resonance >= 0.75
    if medium == "ADDITIVE":
        if is_comp and align < 0.85:     return "ATTRACTIVE"
        if not is_comp and align > 0.95: return "REPULSIVE"
        if both_loud and align > 0.85:   return "AMPLIFYING"
        return "NEUTRAL"
    else:
        if is_comp:          return "EQUILIBRATING"
        if align > 0.95:     return "REPULSIVE"
        if both_loud:        return "AMPLIFYING"
        return "NEUTRAL"

def get_field_type(atom):
    diff = atom.charge_differential
    strength = atom.resonance * diff * 1.5
    ft = "FORCE_FIELD" if strength >= 0.50 else ("AMBIENT_FIELD" if strength >= 0.25 else "NULL_FIELD")
    if atom.positive_charge > atom.negative_charge + 0.1:   dom = "POSITIVE"
    elif atom.negative_charge > atom.positive_charge + 0.1: dom = "NEGATIVE"
    else:                                                    dom = "BALANCED"
    return ft, dom, round(strength, 4), round(diff, 4)

pair_rows = []
for a in COLOR_ATOMS:
    for b in COLOR_ATOMS:
        dist  = angular_distance(a.hue_deg, b.hue_deg)
        cs    = comp_score(dist)
        align = charge_align(a, b)
        res   = a.resonance * b.resonance
        coh   = coherence(cs, -align, res)
        pair_rows.append({
            "color_a": a.name, "color_b": b.name,
            "angular_distance": round(dist,1),
            "complementarity_score": round(cs,4),
            "charge_alignment": round(align,4),
            "charge_term": round(-align,4),
            "resonance_score": round(res,4),
            "coherence_score": round(coh,4),
            "state": classify_state(coh),
            "force_type_additive": force_type(a,b,dist,"ADDITIVE"),
            "force_type_subtractive": force_type(a,b,dist,"SUBTRACTIVE"),
        })

field_rows = []
for atom in COLOR_ATOMS:
    ft, dom, strength, diff = get_field_type(atom)
    field_rows.append({
        "name": atom.name, "hue_deg": atom.hue_deg,
        "wavelength_nm": atom.wavelength_nm, "frequency_thz": atom.frequency_thz,
        "charge_differential": diff, "field_strength": strength,
        "field_type": ft, "dominant_charge": dom,
    })

TRIADS = [
    ("red","yellow","blue"), ("red-orange","yellow-green","blue-violet"),
    ("orange","green","violet"), ("yellow-orange","blue-green","red-violet"),
    ("red","green","yellow"), ("blue","orange","red"),
    ("red","green","blue"), ("yellow","violet","orange"),
]

def pc(na, nb):
    a,b = atom_map[na], atom_map[nb]
    dist = angular_distance(a.hue_deg, b.hue_deg)
    return coherence(comp_score(dist), -charge_align(a,b), a.resonance*b.resonance)

triad_rows = []
for (na,nb,nc) in TRIADS:
    cab,cbc,cca = pc(na,nb), pc(nb,nc), pc(nc,na)
    tri = (cab+cbc+cca)/3
    state = "closed-harmonic" if tri>=0.40 else ("mixed" if tri>=0.25 else "unstable")
    triad_rows.append({"color_a":na,"color_b":nb,"color_c":nc,
        "coh_ab":round(cab,4),"coh_bc":round(cbc,4),"coh_ca":round(cca,4),
        "triadic_coherence":round(tri,4),"state":state})

bridge_rows = []
for fr,atom in zip(field_rows, COLOR_ATOMS):
    bridge_rows.append({"name":atom.name,"hue_deg":atom.hue_deg,
        "wavelength_nm":atom.wavelength_nm,"frequency_thz":atom.frequency_thz,
        "frequency_hz":int(atom.frequency_thz*1e12),
        "field_type":fr["field_type"],"dominant_charge":fr["dominant_charge"],
        "field_strength":fr["field_strength"],"resonance":atom.resonance})

def wcsv(path, rows):
    with open(path,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)

wcsv("simulation/output/color_atomization_results.csv", pair_rows)
wcsv("simulation/output/color_atomization_fields.csv",  field_rows)
wcsv("simulation/output/color_atomization_triadic.csv", triad_rows)
wcsv("simulation/output/color_atomization_bridge.csv",  bridge_rows)

print("Simulation complete. Outputs written to simulation/output/")
non_self = [r for r in pair_rows if r["color_a"] != r["color_b"]]
comp_coh  = [r["coherence_score"] for r in non_self if r["angular_distance"]>=150]
ncomp_coh = [r["coherence_score"] for r in non_self if r["angular_distance"]<150]
print(f"Complement advantage: +{mean(comp_coh)-mean(ncomp_coh):.4f}")
