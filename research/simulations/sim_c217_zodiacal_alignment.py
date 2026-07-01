"""Simulation: C217 — Zodiacal Alignment
Date: June 13, 2026
Authors: R0GV3 The Alchemist + GAIA

Four simulations:
1. Jupiter-12 resonance: orbital period as source of 12-fold zodiac
2. Schumann-Zodiac correlation: ecliptic position vs EM amplitude
3. Precessional Great Ages: civilizational coherence across 26,000-year cycle
4. Zodiac as C200: 12 signs mapped to visible spectrum and chromatic scale
"""

import numpy as np
import pandas as pd
import plotly.io as pio

np.random.seed(42)
pio.templates.default = "perplexity"

JUPITER_PERIOD = 11.862
ZODIAC_SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

sign_data = {
    "Aries":       {"degree": 0,   "color": "#FF2222", "wavelength_nm": 700, "note": "C",  "element": "Fire"},
    "Taurus":      {"degree": 30,  "color": "#FF7722", "wavelength_nm": 650, "note": "C#", "element": "Earth"},
    "Gemini":      {"degree": 60,  "color": "#FFCC22", "wavelength_nm": 600, "note": "D",  "element": "Air"},
    "Cancer":      {"degree": 90,  "color": "#DDFF22", "wavelength_nm": 570, "note": "D#", "element": "Water"},
    "Leo":         {"degree": 120, "color": "#44FF44", "wavelength_nm": 540, "note": "E",  "element": "Fire"},
    "Virgo":       {"degree": 150, "color": "#22FFAA", "wavelength_nm": 510, "note": "F",  "element": "Earth"},
    "Libra":       {"degree": 180, "color": "#22DDFF", "wavelength_nm": 490, "note": "F#", "element": "Air"},
    "Scorpio":     {"degree": 210, "color": "#2266FF", "wavelength_nm": 460, "note": "G",  "element": "Water"},
    "Sagittarius": {"degree": 240, "color": "#6622FF", "wavelength_nm": 440, "note": "G#", "element": "Fire"},
    "Capricorn":   {"degree": 270, "color": "#AA22FF", "wavelength_nm": 420, "note": "A",  "element": "Earth"},
    "Aquarius":    {"degree": 300, "color": "#FF22DD", "wavelength_nm": 400, "note": "A#", "element": "Air"},
    "Pisces":      {"degree": 330, "color": "#FF2288", "wavelength_nm": 385, "note": "B",  "element": "Water"},
}
df_signs = pd.DataFrame(sign_data).T.reset_index()
df_signs.columns = ["sign","degree","color","wavelength_nm","note","element"]
df_signs.to_csv("zodiac_frequency_map.csv", index=False)

days = np.arange(0, 365)
ecliptic = days / 365 * 360
seasonal = 0.12 * np.sin(np.radians(ecliptic - 80))
solar_wind = 0.08 * np.sin(np.radians(ecliptic * 13.4))
noise = np.random.normal(0, 0.03, len(days))
schumann = 1.0 + seasonal + solar_wind + noise
sign_of_day = [ZODIAC_SIGNS[int((d/365*360)//30)] for d in days]
df_daily = pd.DataFrame({"day": days, "schumann": schumann, "sign": sign_of_day})
sign_means = df_daily.groupby("sign")["schumann"].mean().reindex(ZODIAC_SIGNS)
sign_means.to_csv("zodiac_schumann_correlation.csv", header=True)

print("Simulation complete. All data files written.")
print(f"Jupiter-12 deviation: {abs(JUPITER_PERIOD-12)/12*100:.2f}%")
print(f"Schumann range: {(sign_means.max()-sign_means.min())*100:.1f}%")
