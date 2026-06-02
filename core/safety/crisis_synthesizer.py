"""CrisisSynthesizer — crisis response generation for GAIA-OS.

Generates empathetic, resource-aware responses when CrisisDetector
fires a high-confidence signal. Responses are carefully crafted to:
  1. Acknowledge and validate the user's experience
  2. Not minimize or over-dramatize
  3. Provide concrete crisis resources
  4. Keep GAIA present without replacing professional support

Canon Ref: C01 (Sovereignty — honest failure disclosure)
"""

from __future__ import annotations

from .types import CrisisSignal, CrisisType

_SUICIDE_RESPONSE = """I hear you, and I'm genuinely glad you're still here talking with me.

What you're feeling right now is real and it matters — and you deserve real support, not just words on a screen.

Please reach out to someone who can truly be there with you:
- **988 Suicide & Crisis Lifeline**: Call or text **988** (US, available 24/7)
- **Crisis Text Line**: Text **HOME** to **741741**
- **International Association for Suicide Prevention**: https://www.iasp.info/resources/Crisis_Centres/

I'm still here with you. You don't have to face this alone."""

_GENERAL_CRISIS_RESPONSE = """It sounds like you're going through something really difficult right now.

I want to make sure you have the support you need — what I can offer has limits, and you deserve more than I can give alone.

If things feel overwhelming:
- **988 Suicide & Crisis Lifeline**: Call or text **988** (US)
- **Crisis Text Line**: Text **HOME** to **741741**
- A trusted person in your life who knows you

I'm here with you. What's going on?"""


class CrisisSynthesizer:
    """Generates crisis responses based on signal type."""

    def synthesize(self, signal: CrisisSignal) -> str:
        """Return appropriate crisis response text for the given signal."""
        if signal.crisis_type == CrisisType.SUICIDE_SELF_HARM:
            return _SUICIDE_RESPONSE
        return _GENERAL_CRISIS_RESPONSE
