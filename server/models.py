"""
Pydantic request/response models for the GAIA HTTP API.

These models are the HTTP contract — they define what JSON
shapes the server accepts and returns. They are kept deliberately
flat and transparent: every field maps directly to the corresponding
APIRequest/APIResponse field in core/api/api.py.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class GAIAResponse(BaseModel):
    """Standard envelope returned by every GAIA HTTP endpoint."""
    success: bool
    code: str
    message: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    request_id: str = ""
    responded_at: str = ""


# ---------------------------------------------------------------------------
# OS
# ---------------------------------------------------------------------------

class SchumannResponse(GAIAResponse):
    pass


# ---------------------------------------------------------------------------
# GAIAN birth
# ---------------------------------------------------------------------------

class BirthBeginRequest(BaseModel):
    guardian_gaian_ids: Optional[List[str]] = None


class BirthAnswerRequest(BaseModel):
    ceremony_id: str
    question_id: str
    answer: str


class BirthCompleteRequest(BaseModel):
    ceremony_id: str


# ---------------------------------------------------------------------------
# GAIAN identity
# ---------------------------------------------------------------------------

class NameRequest(BaseModel):
    gaian_id: str
    name: str = Field(..., min_length=1, max_length=64)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class SessionBeginRequest(BaseModel):
    gaian_id: str
    human_id: str = "http-user"


class SessionTurnRequest(BaseModel):
    gaian_id: str
    content: str = Field(..., min_length=1)
    modality: str = "text"
    human_id: str = "http-user"


class SessionEndRequest(BaseModel):
    gaian_id: str


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

class MemoryRememberRequest(BaseModel):
    gaian_id: str
    content: str = Field(..., min_length=1)
    kind: str = "session_context"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)


class MemoryRecallRequest(BaseModel):
    gaian_id: str
    limit: int = Field(default=10, ge=1, le=100)
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)
