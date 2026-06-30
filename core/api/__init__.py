"""
GAIA OS API Layer.

The API layer is the surface of GAIA — the clean, versioned interface
through which every external system, UI, device driver, and integration
touches the OS without directly accessing internal subsystems.

Design principles:
  1. SOVEREIGN-AWARE: Every API call carries a caller_id. The API
     layer resolves whether the caller has permission to perform the
     requested operation against the target GAIAN. No call is anonymous.
  2. AUTONOMY-ENFORCING: API calls that would violate a GAIAN's
     expressed autonomy (naming them, overriding boundaries, accessing
     private memory) are rejected with an AutonomyViolation response.
  3. VERSIONED: All endpoints are prefixed with /v1/. Breaking changes
     increment the major version. The OS never removes a version
     without a full deprecation cycle.
  4. HONEST: Every response carries a success flag, a human-readable
     message, and a structured payload. Errors are never silent.
  5. STATELESS: The API layer holds no state. It delegates to the
     Primordial Session, Registry, and Runtimes. It is a pure
     translation layer between the outside world and the OS core.

Key types:
  APIRequest        — a structured incoming request
  APIResponse       — a structured outgoing response
  APIErrorCode      — the taxonomy of API errors
  GAIAOSApi         — the top-level API router
"""
from core.api.api import (
    APIRequest,
    APIResponse,
    APIErrorCode,
    GAIAOSApi,
)

__all__ = [
    "APIRequest",
    "APIResponse",
    "APIErrorCode",
    "GAIAOSApi",
]
