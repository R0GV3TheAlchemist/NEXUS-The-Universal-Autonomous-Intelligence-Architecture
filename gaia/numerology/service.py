from __future__ import annotations
from .constants import MASTER_NUMBERS, TRAITS
from .models import NumerologyInput, NumerologyChart, CoreNumber
from .engine import (
    calc_life_path,
    calc_expression,
    calc_soul_urge,
    calc_personality,
    calc_birthday,
    normalize_name,
)


class NumerologyService:
    SYSTEM_VERSION = "1.0.0"

    def generate_chart(self, inp: NumerologyInput) -> NumerologyChart:
        lp   = CoreNumber(**calc_life_path(inp.birth_date, inp.use_master_numbers))
        exp  = CoreNumber(**calc_expression(inp.full_birth_name, inp.use_master_numbers))
        su   = CoreNumber(**calc_soul_urge(inp.full_birth_name, inp.use_master_numbers, inp.vowel_mode))
        per  = CoreNumber(**calc_personality(inp.full_birth_name, inp.use_master_numbers, inp.vowel_mode))
        bday = CoreNumber(**calc_birthday(inp.birth_date))

        master_nums = sorted({
            n for n in [
                lp.reduced_value, exp.reduced_value,
                su.reduced_value, per.reduced_value,
            ]
            if n in MASTER_NUMBERS
        })

        traits = {
            "life_path":   TRAITS.get(lp.reduced_value, {}),
            "expression":  TRAITS.get(exp.reduced_value, {}),
            "soul_urge":   TRAITS.get(su.reduced_value, {}),
            "personality": TRAITS.get(per.reduced_value, {}),
            "birthday":    TRAITS.get(bday.reduced_value, {}),
        }

        return NumerologyChart(
            subject_name=normalize_name(inp.full_birth_name),
            birth_date=inp.birth_date,
            life_path=lp,
            expression=exp,
            soul_urge=su,
            personality=per,
            birthday=bday,
            master_numbers_present=master_nums,
            traits=traits,
            config={
                "use_master_numbers": inp.use_master_numbers,
                "vowel_mode":         inp.vowel_mode,
                "chart_system":       "Pythagorean",
            },
            system_version=self.SYSTEM_VERSION,
        )
