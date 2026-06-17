from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import datetime

@dataclass
class NumerologyNumber:
    value: int
    label: str
    meaning: str = ""

@dataclass
class NumerologyProfile:
    user_id: str
    life_path: int
    expression: int
    soul_urge: int
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)

@dataclass
class NumerologyChart:
    profile: NumerologyProfile
    numbers: list = field(default_factory=list)
    notes: Optional[str] = None
