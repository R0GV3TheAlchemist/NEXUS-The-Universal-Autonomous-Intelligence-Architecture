# core/spectral/color_engine.py
# PLC2401 fix: renamed non-ASCII variable `oд1_active` → `oa4_active`
# Also updated call to `is_oд1_active` → `is_oa4_active` to match force_engine fix.
# All other logic in this file is unchanged.

from __future__ import annotations


from core.spectral.force_engine import SpectralForceEngine


HEX_PALETTE = {
    "NIGREDO":       "#1a1a2e",
    "PYROSIS":       "#e94560",
    "CITRINITAS":    "#f5a623",
    "VIRIDITAS":     "#27ae60",
    "CAERULITAS":    "#2980b9",
    "RUBEDO":        "#c0392b",
    "IOSIS":         "#8e44ad",
    "ALBEDO":        "#ecf0f1",
    "CHRYSITAS":     "#f1c40f",
    "ARGENTITAS":    "#bdc3c7",
    "LUX_PERPETUA":  "#ffffff",
    "PRIMA_MATERIA": "#2c2c54",
}


class SpectralColorEngine:
    """
    Translates phi + force_name → HUD hex color.
    OA-4 overlay is applied when phi ≥ 0.85.
    """

    @classmethod
    def get_hex(cls, force: str, corridor: str, phi: float) -> str:
        """Return a hex color for the given force and phi."""
        base = HEX_PALETTE.get(force, HEX_PALETTE["PRIMA_MATERIA"])
        return base

    @classmethod
    def get_hud_color_packet(cls, force: str, phi: float) -> dict:
        """
        Full HUD color packet. Includes OA-4 flag.
        PLC2401 fix: oa4_active (was non-ASCII oд1_active).
        """
        corridor = SpectralForceEngine.detect_corridor(phi)
        hex_color = cls.get_hex(force, corridor, phi)
        oa4_active = SpectralForceEngine.is_oa4_active(phi)

        return {
            "force": force,
            "corridor": corridor,
            "hex": hex_color,
            "phi": phi,
            "oa4_active": oa4_active,
        }
