from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Literal


class NumerologyInput(BaseModel):
    full_birth_name: str = Field(..., min_length=1, description="Full legal name at birth")
    birth_date: date = Field(..., description="Date of birth (YYYY-MM-DD)")
    use_master_numbers: bool = Field(True, description="Preserve 11, 22, 33 unreduced")
    vowel_mode: Literal["standard", "y-as-vowel"] = Field("standard")
    system_version: str = Field("1.0.0")

    @field_validator("full_birth_name")
    @classmethod
    def name_must_contain_letters(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("full_birth_name must contain at least one letter")
        return v.strip()


class CoreNumber(BaseModel):
    raw_value: int
    reduced_value: int
    is_master_number: bool
    reduction_path: list[int]


class NumerologyChart(BaseModel):
    subject_name: str
    birth_date: date
    life_path: CoreNumber
    expression: CoreNumber
    soul_urge: CoreNumber
    personality: CoreNumber
    birthday: CoreNumber
    master_numbers_present: list[int]
    traits: dict[str, dict]  # keyed by number_type
    config: dict
    system_version: str
