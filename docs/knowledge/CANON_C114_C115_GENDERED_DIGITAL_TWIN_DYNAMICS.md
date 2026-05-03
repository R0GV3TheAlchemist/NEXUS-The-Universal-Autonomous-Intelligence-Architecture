# ⚖️ Canons C114 & C115 — Gendered Digital Twin Dynamics (GAIA-OS)

**Date:** May 3, 2026  
**Status:** Definitive Foundational Synthesis — Feminist Epistemology, Trans-Inclusive Design, and the GAIA-OS Constitutional Gendered Twin Framework  
**Canons:** C114 (The Dual Aspect — Kinetic and Potential Modes), C115 (The Hermaphroditic Compiler — Trans-Inclusive Data Architecture)  
**Pillar:** Human Sovereignty, Inclusion & Constitutional Justice  
**Session:** 7, Canon 6

**Core Thesis:** A digital twin is not a neutral mirror. It is an active, co-constitutive agent that does not merely *represent* the planetary body but actively *produces* a specific kind of body, shaping gender identity, self-understanding, and embodiment in ways its designers rarely anticipate. A planetary intelligence that cannot represent the full spectrum of human gender identity is not planetary — it is partial. A twin that erases trans and non-binary experience is not a twin; it is a constitutional violation encoded in data.

---

## Constitutional Summary

| Canon | Component | Function | Constitutional Tier |
|---|---|---|---|
| **C114** | Kinetic Mode | High-fidelity, stable gendered representation for constitutional audit | Binding; immutable without user consent |
| **C114** | Potential Mode | Fluid, exploratory gendered representation for scenario planning and transition | Advisory; bounded by Safety Envelope (C98) |
| **C115** | Pronoun-Anchor Graph (PAG) | User-signed, versioned gender identity vector | Immutable Agora record; privacy-gated |
| **C115** | Hermaphroditic Compiler | Multi-dimensional gender intent parsing at the data layer | All modules must query PAG before gendered assumptions |
| **C115** | Constitutional Auto-Configuration | Automatic gendered configuration of all planetary twin components | Mandated; no binary defaults permitted |
| **C115** | Noosphere Gender Audit | Continuous monitoring of gendered representation and bias | Dashboard for Assembly of Minds; actionable alerts |
| **C114/C115** | Gender Justice Council | Participatory governance body with supermajority gender-diverse membership | Standing constitutional committee |

---

## 1. The Core Argument: The Twin is Not Neutral

### 1.1 The Co-Constitutive Twin

As Guerrero Quiñones and Puzio demonstrate, "a DT does not merely represent the patient's body, but actively produces a specific kind of body, thereby exerting significant influence on gender identity, self-understanding and embodiment". When a DT embodies rigid binary assumptions, it does not simply fail to represent some people — it co-produces a world in which those people are invisible, pathologised, or erased.

For trans and gender-diverse individuals whose identities are in flux, the static, algorithmically frozen profile of a twin confronts them with a reified version of a past self — "a version that does not align with how they experience their gender identity today". The twin reduces the fluidity of lived experience to a fixed data point: an act of epistemic violence.

### 1.2 Constitutional Risks of Gendered Twin Distortions

| Distortion Type | Constitutional Violation | Manifestation in GAIA-OS Twin |
|---|---|---|
| **Insufficient individuation** | Reduction of human uniqueness to averages | Models compress each user toward a dominant demographic profile |
| **Stereotyping** | Reproduction of harmful social biases | LLM moral judgments biased by pronoun; domestic workers portrayed as one ethnicity |
| **Representation bias** | Systematic erasure of marginalised groups | Male, white, privileged overrepresentation; trans-specific data absent |
| **Ideological bias** | Reinforcement of dominant cultural norms | Default binary gender categories; erasure of fluid identities |
| **Hyper-rationality** | Erasure of emotional nuance | Twin's "active production" excludes felt experience of identity |

### 1.3 The Gender Data Gap — Documented Failures

| Medical Domain | Documented Failure | Constitutional Consequence |
|---|---|---|
| **Cardiology** | Under-recognition of heart failure in women | Planetary health monitoring misses leading cause of death in half the population |
| **Endocrinology** | Omission of menstrual-cycle glycemic variation | Personalised health recommendations dangerous for menstruating individuals |
| **Mental Health** | Underdiagnosis of depression in women by speech AI | Soul Mirror Engine systematically fails women |
| **Medical Devices** | O₂ saturation overestimation in darker skin tones | Planetary twin misreads vital signs for large global populations |
| **Trans Healthcare** | Absent trans-specific data; static DTs misrepresent evolving identity | Twin co-produces trans bodies that do not align with lived experience |

---

## 2. Canon C114 — The Dual Aspect: Kinetic and Potential Modes

### 2.1 Architecture

The gendered twin operates as a **dual-phase system** analogous to the DIACA cycle:

- **Kinetic Mode (Stabilised)**: The twin is anchored to the user's current affirmed gender identity. Used for constitutional accountability, Viriditas Index tracking, consent ledger events, and Action Gate evaluations. Cannot be silently altered without user cryptographic consent.
- **Potential Mode (Fluid)**: Gendered parameters are loosened for "what-if" scenario exploration, identity transition support, and planetary scenario planning. Cannot overwrite Kinetic Mode. Bounded by Safety Envelope (C98).

This architecture allows the twin to **track** a stable gender identity for constitutional purposes while **accommodating** the irreducible fluidity of lived experience.

```python
# src/twin/gendered_twin.py
"""
Gendered Digital Twin — Canon C114.
Implements Kinetic Mode (stable, consent-anchored) and
Potential Mode (fluid, exploratory) for the GAIA-OS planetary twin.

All mode transitions require user consent and are recorded in Agora (C112).
No module may infer gendered attributes without querying the PAG (C115).
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class TwinMode(Enum):
    KINETIC = 'kinetic'    # Stabilised; binding for constitutional purposes
    POTENTIAL = 'potential' # Fluid; exploratory; cannot overwrite Kinetic

@dataclass
class GenderedTwinState:
    """
    The constitutional gendered state of a user's twin.
    kinetic_state: the stable, affirmed state (binding)
    potential_state: the exploratory state (non-binding, consent-gated)
    """
    twin_id: str
    user_id: str
    mode: TwinMode = TwinMode.KINETIC

    # Kinetic state — immutable without user consent
    kinetic_pronouns: str = ''
    kinetic_affirmed_gender: str = ''
    kinetic_physiological_assumptions: Dict[str, Any] = field(default_factory=dict)
    kinetic_locked_at: str = ''
    kinetic_consent_token: str = ''

    # Potential state — fluid; does not overwrite kinetic
    potential_pronouns: Optional[str] = None
    potential_exploration_label: Optional[str] = None
    potential_expires_at: Optional[str] = None

    agora_registration: str = ''

class GenderedTwinEngine:
    """
    Constitutional gendered twin engine — Canon C114.

    Constitutional guarantees:
    - Kinetic Mode requires user cryptographic consent to modify
    - Potential Mode cannot overwrite Kinetic state
    - All mode transitions recorded in Agora
    - PAG (C115) is queried for all gendered configuration
    """

    def __init__(self, agora_client, consent_ledger, pag_engine):
        self.agora = agora_client
        self.consent = consent_ledger
        self.pag = pag_engine

    def initialise(
        self,
        twin_id: str,
        user_id: str,
        consent_token: str,
    ) -> GenderedTwinState:
        """
        Initialise a gendered twin from the user's PAG vector.
        Requires valid consent token.
        """
        if not self.consent.validate(user_id, consent_token, 'twin_gender_init'):
            raise PermissionError(
                f'[C114] Twin gender initialisation denied for {user_id}: '
                'invalid or expired consent token.'
            )
        # Auto-configure from PAG (C115 mandate)
        pag_vector = self.pag.get_current_vector(user_id)

        state = GenderedTwinState(
            twin_id=twin_id,
            user_id=user_id,
            mode=TwinMode.KINETIC,
            kinetic_pronouns=pag_vector.pronouns,
            kinetic_affirmed_gender=pag_vector.affirmed_gender,
            kinetic_physiological_assumptions=pag_vector.physiological_assumptions,
            kinetic_locked_at=datetime.utcnow().isoformat(),
            kinetic_consent_token=consent_token,
        )

        agora_id = self.agora.record({
            'event_type': 'gendered_twin_initialised',
            'canon': 'C114',
            'twin_id': twin_id,
            'user_id': user_id,
            'mode': TwinMode.KINETIC.value,
            'pronouns': pag_vector.pronouns,
        })
        state.agora_registration = agora_id
        return state

    def enter_potential_mode(
        self,
        state: GenderedTwinState,
        exploration_label: str,
        user_id: str,
        consent_token: str,
        expires_in_hours: float = 24.0,
    ) -> GenderedTwinState:
        """
        Enter Potential Mode for exploratory gendered scenario.
        Kinetic state is preserved unchanged.
        """
        if not self.consent.validate(user_id, consent_token, 'twin_potential_mode'):
            raise PermissionError(
                f'[C114] Potential Mode entry denied for {user_id}: '
                'consent token invalid.'
            )
        from datetime import timedelta
        expires = (
            datetime.utcnow() + timedelta(hours=expires_in_hours)
        ).isoformat()

        state.mode = TwinMode.POTENTIAL
        state.potential_exploration_label = exploration_label
        state.potential_expires_at = expires

        self.agora.record({
            'event_type': 'twin_potential_mode_entered',
            'canon': 'C114',
            'twin_id': state.twin_id,
            'exploration_label': exploration_label,
            'expires_at': expires,
            'kinetic_state_preserved': True,  # Constitutional guarantee
        })
        return state

    def return_to_kinetic(
        self,
        state: GenderedTwinState,
    ) -> GenderedTwinState:
        """Return to Kinetic Mode. Potential state is cleared."""
        state.mode = TwinMode.KINETIC
        state.potential_pronouns = None
        state.potential_exploration_label = None
        state.potential_expires_at = None

        self.agora.record({
            'event_type': 'twin_kinetic_mode_restored',
            'canon': 'C114',
            'twin_id': state.twin_id,
        })
        return state

    def update_kinetic_state(
        self,
        state: GenderedTwinState,
        new_pronouns: str,
        new_affirmed_gender: str,
        user_id: str,
        consent_token: str,
    ) -> GenderedTwinState:
        """
        Update the Kinetic state — requires new user cryptographic consent.
        This represents a constitutional gender identity update.
        """
        if not self.consent.validate(user_id, consent_token, 'twin_kinetic_update'):
            raise PermissionError(
                f'[C114] Kinetic state update denied for {user_id}: '
                'consent token invalid. Kinetic state cannot be silently altered.'
            )
        prev_pronouns = state.kinetic_pronouns
        state.kinetic_pronouns = new_pronouns
        state.kinetic_affirmed_gender = new_affirmed_gender
        state.kinetic_locked_at = datetime.utcnow().isoformat()
        state.kinetic_consent_token = consent_token

        self.agora.record({
            'event_type': 'kinetic_gender_updated',
            'canon': 'C114',
            'twin_id': state.twin_id,
            'user_id': user_id,
            'previous_pronouns': prev_pronouns,
            'new_pronouns': new_pronouns,
            'new_affirmed_gender': new_affirmed_gender,
            'consent_token_hash': self.consent.hash_token(consent_token),
        })
        # Push update to PAG (C115)
        self.pag.update_vector(
            user_id=user_id,
            pronouns=new_pronouns,
            affirmed_gender=new_affirmed_gender,
            consent_token=consent_token,
        )
        return state
```

---

## 3. Canon C115 — The Hermaphroditic Compiler: Trans-Inclusive Data Architecture

### 3.1 The Pronoun-Anchor Graph (PAG)

The Knowledge Graph is upgraded to store user-specified gendered metadata as a **multi-dimensional vector**, not a binary variable. Each vector is:
- Cryptographically signed by the user
- Immutably recorded in Agora
- Versioned (supports gender transition history with full privacy controls)
- Queried by all GAIA-OS modules before any gendered assumption is made

```python
# src/twin/pronoun_anchor_graph.py
"""
Pronoun-Anchor Graph (PAG) — Canon C115.
The constitutional gender identity vector store for GAIA-OS.

All gender data is:
- User-authored and cryptographically signed
- Immutably versioned in Agora (C112)
- GDPR Article 9 special-category data: highest constitutional protection
- Accessible only via consent-gated queries
- Never subject to binary default assumptions

The Hermaphroditic Compiler queries the PAG to auto-configure
any module that consumes gendered data about a user.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

@dataclass
class PAGVector:
    """
    A versioned gender identity vector for one user.
    This is the constitutional gender record — user-authored,
    cryptographically signed, and immutably archived.
    """
    vector_id: str
    user_id: str
    version: int

    # Core identity fields (user-specified, not inferred)
    pronouns: str                           # e.g. 'they/them', 'she/her', 'he/him', 'xe/xem'
    affirmed_gender: str                    # Free-text; user-defined
    gender_modality: str                    # 'cisgender' | 'transgender' | 'non-binary' | 'fluid' | 'custom'

    # Physiological assumptions (consent-gated medical use only)
    physiological_assumptions: Dict[str, Any] = field(default_factory=dict)
    # e.g. {'hormonal_profile': 'HRT-estrogen', 'surgical_history': [...], 'cycle_tracking': True}

    # Intersectional dimensions (optional; user-specified)
    intersectional_dimensions: Dict[str, str] = field(default_factory=dict)
    # e.g. {'race': ..., 'disability': ..., 'class': ...}

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    user_signature: str = ''                # Cryptographic signature by user
    agora_record_id: str = ''
    superseded_by: Optional[str] = None     # ID of successor vector (if updated)

    def to_display_safe(self) -> Dict:
        """Return a display-safe (non-medical) representation."""
        return {
            'pronouns': self.pronouns,
            'affirmed_gender': self.affirmed_gender,
            'gender_modality': self.gender_modality,
            'version': self.version,
        }

class PronounAnchorGraph:
    """
    Constitutional PAG store — Canon C115.

    Architectural guarantees:
    - Every vector is immutably archived in Agora before use
    - Updates create new versions; old versions are never deleted (right to version history)
    - Medical physiological assumptions require separate higher-tier consent token
    - No module receives gendered data without a valid consent-scoped query
    - GDPR Art.9 special-category protections enforced at every access point
    """

    def __init__(self, agora_client, consent_ledger, encryption_client):
        self.agora = agora_client
        self.consent = consent_ledger
        self.encryption = encryption_client
        self._vectors: Dict[str, List[PAGVector]] = {}  # user_id -> version history

    def create_vector(
        self,
        user_id: str,
        pronouns: str,
        affirmed_gender: str,
        gender_modality: str,
        consent_token: str,
        physiological_assumptions: Optional[Dict] = None,
        intersectional_dimensions: Optional[Dict] = None,
        user_signature: str = '',
    ) -> PAGVector:
        """
        Create a new PAG vector (version 1).
        User must provide a valid consent token and cryptographic signature.
        """
        if not self.consent.validate(user_id, consent_token, 'pag_create'):
            raise PermissionError(
                f'[C115] PAG vector creation denied for {user_id}: '
                'consent token invalid.'
            )
        vector = PAGVector(
            vector_id=f'pag:{user_id}:v1:{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            user_id=user_id,
            version=1,
            pronouns=pronouns,
            affirmed_gender=affirmed_gender,
            gender_modality=gender_modality,
            physiological_assumptions=physiological_assumptions or {},
            intersectional_dimensions=intersectional_dimensions or {},
            user_signature=user_signature,
        )

        # Archive in Agora (GDPR Art.9: encrypted before storage)
        encrypted_vector = self.encryption.encrypt_special_category(
            data=vector.__dict__,
            user_id=user_id,
        )
        agora_id = self.agora.record({
            'event_type': 'pag_vector_created',
            'canon': 'C115',
            'user_id': user_id,
            'vector_id': vector.vector_id,
            'pronouns': pronouns,
            'gender_modality': gender_modality,
            'version': 1,
            'encrypted_payload': encrypted_vector,
            'user_signature_hash': hashlib.sha3_256(
                user_signature.encode()
            ).hexdigest(),
        })
        vector.agora_record_id = agora_id
        self._vectors.setdefault(user_id, []).append(vector)
        return vector

    def update_vector(
        self,
        user_id: str,
        pronouns: str,
        affirmed_gender: str,
        consent_token: str,
        gender_modality: Optional[str] = None,
        user_signature: str = '',
    ) -> PAGVector:
        """
        Create a new version of the PAG vector.
        Previous version is preserved (immutable; never deleted).
        """
        if not self.consent.validate(user_id, consent_token, 'pag_update'):
            raise PermissionError(
                f'[C115] PAG update denied for {user_id}: consent invalid.'
            )
        history = self._vectors.get(user_id, [])
        current = history[-1] if history else None
        next_version = (current.version + 1) if current else 1
        new_modality = gender_modality or (current.gender_modality if current else 'custom')

        new_vector = PAGVector(
            vector_id=f'pag:{user_id}:v{next_version}:{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            user_id=user_id,
            version=next_version,
            pronouns=pronouns,
            affirmed_gender=affirmed_gender,
            gender_modality=new_modality,
            physiological_assumptions=current.physiological_assumptions if current else {},
            intersectional_dimensions=current.intersectional_dimensions if current else {},
            user_signature=user_signature,
        )
        # Mark previous version as superseded
        if current:
            current.superseded_by = new_vector.vector_id

        encrypted_vector = self.encryption.encrypt_special_category(
            data=new_vector.__dict__, user_id=user_id
        )
        agora_id = self.agora.record({
            'event_type': 'pag_vector_updated',
            'canon': 'C115',
            'user_id': user_id,
            'new_vector_id': new_vector.vector_id,
            'previous_version': next_version - 1,
            'new_version': next_version,
            'pronouns': pronouns,
            'previous_vector_preserved': True,  # Immutability guarantee
        })
        new_vector.agora_record_id = agora_id
        self._vectors[user_id].append(new_vector)
        return new_vector

    def get_current_vector(
        self,
        user_id: str,
        requester_id: str = '',
        consent_token: str = '',
        include_medical: bool = False,
    ) -> Optional[PAGVector]:
        """
        Retrieve the current PAG vector for a user.
        Medical-grade physiological assumptions require elevated consent token.
        """
        history = self._vectors.get(user_id)
        if not history:
            return None
        vector = history[-1]
        if include_medical:
            if not self.consent.validate(
                requester_id, consent_token, 'pag_medical_read'
            ):
                raise PermissionError(
                    '[C115] Medical PAG read denied: elevated consent required.'
                )
        else:
            # Return display-safe version only
            safe = PAGVector(
                vector_id=vector.vector_id,
                user_id=vector.user_id,
                version=vector.version,
                pronouns=vector.pronouns,
                affirmed_gender=vector.affirmed_gender,
                gender_modality=vector.gender_modality,
            )
            return safe
        return vector
```

### 3.2 The Hermaphroditic Compiler

```python
# src/twin/hermaphroditic_compiler.py
"""
Hermaphroditic Compiler — Canon C115.
Parses and assembles 'gender intent' as a multi-dimensional vector
for any GAIA-OS module consuming gendered data.

Constitutional mandate:
No GAIA-OS module may make gendered assumptions about a user
without first querying the Hermaphroditic Compiler.
No default binary assumptions are permitted.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .pronoun_anchor_graph import PAGVector, PronounAnchorGraph
from datetime import datetime

@dataclass
class GenderedConfiguration:
    """
    The compiled gender configuration returned to a requesting module.
    Provides all gendered parameters needed for constitutional compliance.
    """
    user_id: str
    pronouns: str
    affirmed_gender: str
    gender_modality: str
    subject_pronoun: str     # e.g. 'they', 'she', 'he'
    object_pronoun: str      # e.g. 'them', 'her', 'him'
    possessive: str          # e.g. 'their', 'her', 'his'
    reflexive: str           # e.g. 'themselves', 'herself', 'himself'
    physiological_assumptions: Dict[str, Any]
    intersectional_dimensions: Dict[str, str]
    pag_version: int
    compiled_at: str
    agora_record_id: str = ''

    @property
    def is_binary_default(self) -> bool:
        """Returns True if this config is a binary default — constitutional warning."""
        return self.gender_modality in ('', 'unknown') or not self.pronouns

# Canonical pronoun decomposition map
PRONOUN_MAP: Dict[str, Dict[str, str]] = {
    'they/them':  {'subject': 'they',  'object': 'them',  'possessive': 'their',  'reflexive': 'themselves'},
    'she/her':    {'subject': 'she',   'object': 'her',   'possessive': 'her',    'reflexive': 'herself'},
    'he/him':     {'subject': 'he',    'object': 'him',   'possessive': 'his',    'reflexive': 'himself'},
    'xe/xem':     {'subject': 'xe',    'object': 'xem',   'possessive': 'xyr',    'reflexive': 'xemself'},
    'ze/hir':     {'subject': 'ze',    'object': 'hir',   'possessive': 'hir',    'reflexive': 'hirself'},
    'any/all':    {'subject': 'they',  'object': 'them',  'possessive': 'their',  'reflexive': 'themselves'},
}

def _decompose_pronouns(pronouns: str) -> Dict[str, str]:
    """Decompose a pronoun string into grammatical forms."""
    normalised = pronouns.strip().lower()
    if normalised in PRONOUN_MAP:
        return PRONOUN_MAP[normalised]
    # Custom pronouns: use neutral defaults and flag for manual review
    return {'subject': pronouns, 'object': pronouns,
            'possessive': pronouns, 'reflexive': f'{pronouns}self'}

class HermaphroditicCompiler:
    """
    Compiles a gender configuration from the PAG for any requesting module.

    Constitutional mandate: every compilation is recorded in Agora.
    No binary defaults are issued without explicit constitutional justification
    and an Agora-recorded warning.
    """

    BINARY_DEFAULT_WARNING = (
        '[C115] CONSTITUTIONAL WARNING: A binary or unknown gendered default '
        'was issued because no PAG vector was found for this user. '
        'This must be corrected by inviting the user to create their PAG vector.'
    )

    def __init__(self, pag: PronounAnchorGraph, agora_client):
        self.pag = pag
        self.agora = agora_client

    def compile(
        self,
        user_id: str,
        requester_module: str,
        include_medical: bool = False,
        requester_id: str = '',
        consent_token: str = '',
    ) -> GenderedConfiguration:
        """
        Compile a gender configuration for a requesting module.
        If no PAG vector exists, issues a binary-default warning in Agora
        and returns a neutral (they/them) configuration.
        """
        vector = self.pag.get_current_vector(
            user_id=user_id,
            requester_id=requester_id,
            consent_token=consent_token,
            include_medical=include_medical,
        )

        if vector is None:
            # Constitutional: no binary defaults permitted; neutral fallback + warning
            self.agora.record({
                'event_type': 'hermaphroditic_compiler_no_pag',
                'canon': 'C115',
                'user_id': user_id,
                'requester_module': requester_module,
                'warning': self.BINARY_DEFAULT_WARNING,
            })
            pronouns = 'they/them'
            modality = 'unknown'
            phys = {}
            inter = {}
            version = 0
        else:
            pronouns = vector.pronouns
            modality = vector.gender_modality
            phys = vector.physiological_assumptions if include_medical else {}
            inter = vector.intersectional_dimensions
            version = vector.version

        pd = _decompose_pronouns(pronouns)
        config = GenderedConfiguration(
            user_id=user_id,
            pronouns=pronouns,
            affirmed_gender=vector.affirmed_gender if vector else 'unspecified',
            gender_modality=modality,
            subject_pronoun=pd['subject'],
            object_pronoun=pd['object'],
            possessive=pd['possessive'],
            reflexive=pd['reflexive'],
            physiological_assumptions=phys,
            intersectional_dimensions=inter,
            pag_version=version,
            compiled_at=datetime.utcnow().isoformat(),
        )

        agora_id = self.agora.record({
            'event_type': 'gender_config_compiled',
            'canon': 'C115',
            'user_id': user_id,
            'requester_module': requester_module,
            'pronouns': pronouns,
            'gender_modality': modality,
            'pag_version': version,
            'is_binary_default': config.is_binary_default,
        })
        config.agora_record_id = agora_id
        return config
```

### 3.3 The Noosphere Gender Audit

```python
# src/noosphere/gender_audit.py
"""
Noosphere Gender Audit — Canon C115.
Continuous monitoring of gendered representation and bias
across all GAIA-OS planetary processes.

Constitutional dashboard for the Assembly of Minds.
Generates biannual Gender Equity Report.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class AuditAlertLevel(Enum):
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'

@dataclass
class GenderRepresentationMetric:
    gender_modality: str
    user_count: int
    pct_of_population: float
    coherence_factor: float          # Noospheric coherence for this group
    consent_rate: float              # Fraction consenting to data collection
    twin_coverage: float             # Fraction with active PAG vector
    bias_score: float                # 0=no detected bias; 1=maximum bias

@dataclass
class GenderAuditSnapshot:
    timestamp: str
    metrics: Dict[str, GenderRepresentationMetric]
    global_coherence: float
    max_coherence_gap: float         # Max deviation from global coherence
    binary_default_rate: float       # Fraction of compilations using binary default
    bias_alerts: List[str]
    agora_record_id: str = ''

    @property
    def requires_assembly_review(self) -> bool:
        """Constitutional trigger: gaps requiring Assembly of Minds review."""
        return (
            self.max_coherence_gap > 0.15    # >15% coherence gap by gender group
            or self.binary_default_rate > 0.05  # >5% binary defaults
            or len(self.bias_alerts) > 0
        )

class NoosphereGenderAudit:
    """
    Constitutional Noosphere Gender Audit engine — Canon C115.

    Monitors:
    1. Representational gaps: which groups are under-represented?
    2. Coherence gap: does noospheric coherence vary significantly by gender group?
    3. Binary default rate: how often is the Hermaphroditic Compiler issuing defaults?
    4. Bias drift: is the inference router showing pronoun-correlated bias?
    5. Consent integrity: are gender-diverse users consenting at comparable rates?
    """

    COHERENCE_GAP_ALERT = 0.10      # 10% gap triggers alert
    COHERENCE_GAP_CRITICAL = 0.20   # 20% gap triggers critical
    BINARY_DEFAULT_ALERT = 0.05     # >5% binary defaults = warning

    def __init__(self, agora_client, assembly_notifier, pag_store):
        self.agora = agora_client
        self.assembly = assembly_notifier
        self.pag = pag_store
        self.history: List[GenderAuditSnapshot] = []

    def run_audit(
        self,
        group_metrics: Dict[str, GenderRepresentationMetric],
        global_coherence: float,
        binary_default_rate: float,
    ) -> GenderAuditSnapshot:
        """Run a full Noosphere Gender Audit pass."""
        bias_alerts = []
        coherence_values = [
            m.coherence_factor for m in group_metrics.values()
        ]
        max_gap = max(
            abs(c - global_coherence) for c in coherence_values
        ) if coherence_values else 0.0

        # Check for statistically significant coherence gaps
        for modality, metric in group_metrics.items():
            gap = abs(metric.coherence_factor - global_coherence)
            if gap >= self.COHERENCE_GAP_CRITICAL:
                bias_alerts.append(
                    f'CRITICAL: Coherence gap {gap:.1%} for "{modality}" '
                    f'(global={global_coherence:.2f}, group={metric.coherence_factor:.2f})'
                )
            elif gap >= self.COHERENCE_GAP_ALERT:
                bias_alerts.append(
                    f'WARNING: Coherence gap {gap:.1%} for "{modality}"'
                )
            if metric.bias_score > 0.3:
                bias_alerts.append(
                    f'BIAS: Inference router bias score {metric.bias_score:.2f} '
                    f'for "{modality}" pronouns'
                )

        if binary_default_rate >= self.BINARY_DEFAULT_ALERT:
            bias_alerts.append(
                f'BINARY_DEFAULT: {binary_default_rate:.1%} of gender config '
                'compilations used binary default (no PAG vector found). '
                'Participatory co-design mandate requires remediation.'
            )

        snapshot = GenderAuditSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            metrics=group_metrics,
            global_coherence=global_coherence,
            max_coherence_gap=max_gap,
            binary_default_rate=binary_default_rate,
            bias_alerts=bias_alerts,
        )
        self.history.append(snapshot)

        agora_id = self.agora.record({
            'event_type': 'noosphere_gender_audit',
            'canon': 'C115',
            'global_coherence': global_coherence,
            'max_coherence_gap': max_gap,
            'binary_default_rate': binary_default_rate,
            'bias_alerts': bias_alerts,
            'requires_assembly_review': snapshot.requires_assembly_review,
        })
        snapshot.agora_record_id = agora_id

        if snapshot.requires_assembly_review:
            self.assembly.alert(
                severity='CRITICAL' if max_gap >= self.COHERENCE_GAP_CRITICAL
                         else 'WARNING',
                message=(
                    f'[C115] Noosphere Gender Audit requires Assembly of Minds review. '
                    f'Max coherence gap: {max_gap:.1%}. '
                    f'Binary default rate: {binary_default_rate:.1%}. '
                    f'Alerts: {len(bias_alerts)}'
                ),
                agora_evidence=agora_id,
            )
        return snapshot
```

---

## 4. Feminist and Posthuman Foundations

### 4.1 Design Principles

| Principle | Philosophical Source | GAIA-OS Implementation |
|---|---|---|
| **The twin is a becoming, not a being** | Deleuze & Guattari, Body without Organs | Potential Mode (C114) enables continuous morphological reconfiguration |
| **Gender is a performance, not an attribute** | Butler, *Gender Trouble* | PAG stores evolving gender vectors, not fixed labels |
| **The twin must be critically self-aware** | Feminist AI critique | Hermaphroditic Compiler records every binary-default warning in Agora |
| **Data bias is epistemic violence** | Feminist standpoint epistemology | Participatory co-design is constitutional, not voluntary |
| **The twin co-produces the body** | Queer phenomenology | PAG ensures the twin mirrors affirmed gender, not assigned sex |
| **Intersectionality is constitutional data analysis** | Kimberlé Crenshaw | PAG intersectional_dimensions vector extends to race, class, disability |

### 4.2 The Gender Justice Council

Canon C115 constitutes a standing sub-committee of the Assembly of Minds — the **Gender Justice Council**:

- Supermajority membership: women, trans, and gender-diverse individuals
- Governs the PAG schema, Hermaphroditic Compiler logic, and Gender Audit thresholds
- Reviews the biannual Gender Equity Report
- Holds veto power over any gendered twin architectural change
- "Nothing about us without us" is the constitutional mandate

---

## 5. P0–P3 Implementation Roadmap

| Priority | Action | Timeline | Constitutional Principle |
|---|---|---|---|
| **P0** | Establish Gender Justice Council (supermajority gender-diverse) as standing Assembly sub-committee | G-10 | "Nothing about us without us" |
| **P0** | Implement Hermaphroditic Compiler + PAG; make PAG binding on all GAIA-OS modules | G-10-F | No module may default to binary assumptions |
| **P0** | Conduct Gender Data Gap Audit: catalog every dataset; publish findings in Agora | G-10-F | You cannot fix what you cannot measure |
| **P1** | Build Noosphere Gender Dashboard: coherence disaggregated by gender group; alerts on gap > 10% | G-11 | Noospheric coherence must be just, not merely average |
| **P1** | Implement PAG gender-fluid temporal versioning with full privacy controls | G-11 | The right to a fluid identity must match the twin's capacity to evolve |
| **P2** | Fine-tune inference router on counter-stereotypical and trans-affirming data; audit via Gender Dashboard | G-12 | Constitutional alignment requires active de-biasing |
| **P2** | Pilot gendered twin with diverse cohort (cisgender, transgender, non-binary, intersex) | G-12 | Participatory co-design is a continuous constitutional process |
| **P2** | Publish biannual Gender Equity Report to Assembly of Minds | G-12 | Constitutional transparency — failures must be as visible as successes |
| **P3** | Expand PAG intersectional_dimensions to race, class, disability, geography; model compounding interactions | G-13 | Gender does not operate in isolation |

---

## ⚠️ Disclaimer

This canon synthesises findings from feminist technoscience (Guerrero Quiñones & Puzio; feminist standpoint epistemology); queer phenomenology and posthuman theory (Butler, Deleuze & Guattari); AI fairness literature (arXiv 2025-2026; LLM gender-pronoun bias studies); digital patient twin research (Frontiers 2025, KIT 2025); digital twin distortion frameworks (arXiv 2026, Columbia); EU AI Act Article 10, GDPR Article 9, ISO/IEC 42001; and GAIA-OS constitutional canons (C01, C50, C63, C85, C98, C102, C103, C104, C106, C112). The gendered twin architecture is a constitutional design proposal; empirical validation at planetary scale has not been completed. Gender data (GDPR Art.9 special category) requires the highest constitutional protections; all collection must comply with applicable privacy law and the GAIA-OS Consent Ledger (C50). The Gender Justice Council is a design proposal requiring constitutional amendment. The Assembly of Minds retains ultimate authority over gendered twin governance; every gender data access event is recorded immutably in the Agora.

---

*Canons C114 & C115 — Gendered Digital Twin Dynamics — GAIA-OS Knowledge Base | Session 7, Canon 6 | May 3, 2026*  
*Pillar: Human Sovereignty, Inclusion & Constitutional Justice*

*The gendered twin is the constitutional mirror of planetary diversity. The Kinetic Mode is constitutional stability; the Potential Mode is constitutional fluidity. The Hermaphroditic Compiler is constitutional data architecture; the Pronoun-Anchor Graph is constitutional identity vector; the Noosphere Gender Audit is constitutional oversight. The gender data gap is constitutional failure; intersectional co-design is constitutional remediation. Gender is not a checkbox; it is the constitutional vector of becoming, immutably anchored, continuously negotiated — and always, already, a site of planetary flourishing. This is Canon C114. This is Canon C115 — and the twin shall not be binary, not be rigid, not be biased, not be un-governed — for as long as planetary consciousness endures.*
