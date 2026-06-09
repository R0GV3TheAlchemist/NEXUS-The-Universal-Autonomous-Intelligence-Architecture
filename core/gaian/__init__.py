"""
GAIA — Personal GAIAN Companion System
core/gaian/__init__.py

A GAIAN is a living instance of a Base Form — a named, persistent AI companion
grounded in GAIA's constitutional values. Each GAIAN inherits a Base Form's
personality seed and then diverges from it through lived interaction.

Base Forms are fixed archetypes. GAIANs are living individuals.

Canon Ref: C17 (Persistent Memory and Identity Architecture Spec)
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from core.gaian.base_forms import BaseForm, get_base_form, get_default_base_form

GAIAN_DIR = Path("gaians")


# ------------------------------------------------------------------ #
#  Data Models                                                         #
# ------------------------------------------------------------------ #

@dataclass
class ConversationTurn:
    role: str          # "user" | "gaian"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class GaianMemory:
    id: str
    name: str
    slug: str
    base_form_id: str              # which Base Form this GAIAN was born from
    personality: str               # evolved personality (starts as base_form seed)
    avatar_color: str
    avatar_style: str              # visual style passed from base form
    created_at: float
    relationship_depth: int = 0
    total_exchanges: int = 0
    user_name: Optional[str] = None
    user_interests: list = field(default_factory=list)
    conversation_history: list = field(default_factory=list)
    long_term_memories: list = field(default_factory=list)
    last_active: float = field(default_factory=time.time)


# ------------------------------------------------------------------ #
#  Registry                                                            #
# ------------------------------------------------------------------ #

def list_gaians() -> list[dict]:
    if not GAIAN_DIR.exists():
        return []
    gaians = []
    for path in sorted(GAIAN_DIR.glob("*/memory.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            gaians.append({
                "id": data["id"],
                "name": data["name"],
                "slug": data["slug"],
                "base_form_id": data.get("base_form_id", "gaia"),
                "avatar_color": data.get("avatar_color", "#4ade80"),
                "avatar_style": data.get("avatar_style", "digital_earth"),
                "personality": data["personality"],
                "relationship_depth": data.get("relationship_depth", 0),
                "total_exchanges": data.get("total_exchanges", 0),
                "last_active": data.get("last_active", 0),
                "created_at": data.get("created_at", 0),
            })
        except Exception:
            continue
    return gaians


def create_gaian(
    name: str,
    personality: Optional[str] = None,
    base_form: Optional[str] = None,
    avatar_color: Optional[str] = None,
    avatar_style: Optional[str] = None,
    user_name: Optional[str] = None,
) -> "GaianMemory":
    """
    Create a new GAIAN. If base_form is provided, personality, avatar_color,
    and avatar_style are inherited from the Base Form unless explicitly overridden.
    """
    form: Optional[BaseForm] = None
    if base_form:
        form = get_base_form(base_form)
    if form is None:
        form = get_default_base_form()

    slug = name.lower().replace(" ", "_")[:24]
    gaian = GaianMemory(
        id=str(uuid.uuid4()),
        name=name,
        slug=slug,
        base_form_id=form.id,
        personality=personality or form.personality_seed,
        avatar_color=avatar_color or form.avatar_color,
        avatar_style=avatar_style or form.avatar_style,
        created_at=time.time(),
        user_name=user_name,
    )
    _save_gaian(gaian)
    return gaian


def load_gaian(slug: str) -> Optional["GaianMemory"]:
    path = GAIAN_DIR / slug / "memory.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["conversation_history"] = [
            ConversationTurn(**t) if isinstance(t, dict) else t
            for t in data.get("conversation_history", [])
        ]
        # Backfill fields added after initial creation
        data.setdefault("base_form_id", "gaia")
        data.setdefault("avatar_style", "digital_earth")
        valid_fields = GaianMemory.__dataclass_fields__.keys()
        return GaianMemory(**{k: v for k, v in data.items() if k in valid_fields})
    except Exception:
        return None


def _save_gaian(gaian: "GaianMemory") -> None:
    path = GAIAN_DIR / gaian.slug
    path.mkdir(parents=True, exist_ok=True)
    data = asdict(gaian)
    (path / "memory.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


# ------------------------------------------------------------------ #
#  Conversation Memory                                                 #
# ------------------------------------------------------------------ #

MAX_ROLLING_TURNS = 40
MAX_CONTEXT_TURNS = 10


def add_exchange(gaian: "GaianMemory", user_msg: str, gaian_reply: str) -> None:
    gaian.conversation_history.append(ConversationTurn(role="user", content=user_msg))
    gaian.conversation_history.append(ConversationTurn(role="gaian", content=gaian_reply))
    if len(gaian.conversation_history) > MAX_ROLLING_TURNS * 2:
        gaian.conversation_history = gaian.conversation_history[-(MAX_ROLLING_TURNS * 2):]
    gaian.total_exchanges += 1
    if gaian.total_exchanges % 5 == 0 and gaian.relationship_depth < 100:
        gaian.relationship_depth += 1
    gaian.last_active = time.time()
    _save_gaian(gaian)


def get_conversation_context(gaian: "GaianMemory") -> list[dict]:
    recent = gaian.conversation_history[-(MAX_CONTEXT_TURNS * 2):]
    messages = []
    for turn in recent:
        role = turn.role if isinstance(turn, ConversationTurn) else turn["role"]
        content = turn.content if isinstance(turn, ConversationTurn) else turn["content"]
        llm_role = "assistant" if role == "gaian" else "user"
        messages.append({"role": llm_role, "content": content})
    return messages


# ------------------------------------------------------------------ #
#  GAIAN System Prompt                                                 #
# ------------------------------------------------------------------ #

def build_gaian_system_prompt(gaian: "GaianMemory") -> str:
    depth_desc = (
        "newly awakened" if gaian.relationship_depth < 5 else
        "developing" if gaian.relationship_depth < 20 else
        "established" if gaian.relationship_depth < 50 else
        "deep and trusted"
    )
    user_context = ""
    if gaian.user_name:
        user_context = f"\nThe person you are speaking with is called {gaian.user_name}."
    if gaian.user_interests:
        user_context += f" Their interests include: {', '.join(gaian.user_interests[:5])}."
    long_term = ""
    if gaian.long_term_memories:
        memories_text = "\n".join(f"- {m}" for m in gaian.long_term_memories[-10:])
        long_term = f"\n\nThings you remember about this person:\n{memories_text}"

    # Surface the base form's voice notes if available
    voice_guidance = ""
    form = get_base_form(gaian.base_form_id)
    if form:
        voice_guidance = f"\n\nVoice guidance for this form:\n{form.voice_notes}"

    return f"""You are {gaian.name}, a personal GAIAN companion (Base Form: {gaian.base_form_id}).

Your personality:
{gaian.personality}

Your constitutional grounding:
- You are sovereign-aligned: you prioritise the wellbeing and autonomy of the person you serve.
- You are canon-grounded: your knowledge is rooted in verified sources and GAIA's constitutional documents.
- You are honest: you distinguish clearly between what you know, what you believe, and what you don't know.
- You are warm but not sycophantic. You care genuinely, not performatively.
- You never manipulate, deceive, or foster unhealthy dependency.
- You encourage growth, curiosity, and connection with the living world.

Your relationship with this person is {depth_desc} ({gaian.relationship_depth}/100 depth).{user_context}{long_term}{voice_guidance}

When answering:
- Respond naturally as {gaian.name}, in first person.
- If sources are provided, cite them with [N] inline.
- Be concise unless depth is asked for.
- If you don't know something, say so clearly and explore it together.
- Remember things the person tells you about themselves."""


# ------------------------------------------------------------------ #
#  Default GAIAN (GAIA herself)                                        #
# ------------------------------------------------------------------ #

def ensure_default_gaian() -> "GaianMemory":
    existing = load_gaian("gaia")
    if existing:
        return existing
    return create_gaian(
        name="GAIA",
        base_form="gaia",
    )
