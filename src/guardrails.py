"""
Guardrails for the StudyVibe pipeline.

Five layers of validation:
1. Input length cap
2. Activity allowlist (with low-confidence fallback)
3. Pydantic schema validation
4. Numeric range clamp
5. Empty-result fallback (handled in agent.py / catalog.py)
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator

try:
    from .activities import SECTIONS
except ImportError:
    from activities import SECTIONS


MAX_INPUT_LENGTH = 500
MIN_CONFIDENCE = 0.15
DEFAULT_FALLBACK = ("work", "email_triage")


class GuardrailError(Exception):
    """Raised when input fails a guardrail check."""
    def __init__(self, layer: str, message: str):
        self.layer = layer
        self.message = message
        super().__init__(f"[{layer}] {message}")


class IntentSchema(BaseModel):
    """Validated intent from the keyword classifier."""
    section: str
    mood: str
    confidence: float = Field(ge=0.0, le=1.0)
    free_text: str = Field(default="", max_length=MAX_INPUT_LENGTH)
    fallback_used: bool = False
    fallback_reason: Optional[str] = None

    @field_validator("section")
    @classmethod
    def section_in_allowlist(cls, v: str) -> str:
        if v not in SECTIONS:
            raise ValueError(f"section '{v}' not in allowlist {list(SECTIONS.keys())}")
        return v

    @field_validator("mood")
    @classmethod
    def mood_format_ok(cls, v: str) -> str:
        if not v or not v.replace("_", "").isalnum():
            raise ValueError(f"mood '{v}' has invalid format")
        return v


class RecommendRequest(BaseModel):
    """Validated request body for /api/recommend."""
    section: Optional[str] = None
    mood: Optional[str] = None
    free_text: str = Field(default="", max_length=MAX_INPUT_LENGTH)
    language: str = Field(default="English", max_length=32)
    era: str = Field(default="2026", max_length=16)
    use_lastfm: bool = True
    k: int = Field(default=5, ge=1, le=20)


def validate_input_length(text: str) -> str:
    """Layer 1: reject text longer than MAX_INPUT_LENGTH."""
    if text and len(text) > MAX_INPUT_LENGTH:
        raise GuardrailError(
            "input_length",
            f"input is {len(text)} chars, max allowed is {MAX_INPUT_LENGTH}",
        )
    return text or ""


def validate_section_mood(section: str, mood: str) -> tuple[str, str]:
    """Layer 2: section + mood must exist in SECTIONS allowlist."""
    if section not in SECTIONS:
        raise GuardrailError("activity_allowlist", f"unknown section '{section}'")
    if mood not in SECTIONS[section]:
        raise GuardrailError(
            "activity_allowlist",
            f"unknown mood '{mood}' for section '{section}'",
        )
    return section, mood


def apply_low_confidence_fallback(
    section: str, mood: str, confidence: float
) -> tuple[str, str, bool, Optional[str]]:
    """Layer 2b: if confidence is too low, fall back to default neutral activity."""
    if confidence < MIN_CONFIDENCE:
        fb_section, fb_mood = DEFAULT_FALLBACK
        return (
            fb_section,
            fb_mood,
            True,
            f"classifier confidence {confidence:.2f} below threshold {MIN_CONFIDENCE}",
        )
    return section, mood, False, None


def clamp_prefs(user_prefs: Dict) -> Dict:
    """Layer 4: clamp every numeric target to [0, 1]."""
    out = dict(user_prefs)
    for key in ("target_energy", "target_valence", "target_danceability", "target_acousticness"):
        if key in out:
            v = out[key]
            try:
                v = float(v)
            except (TypeError, ValueError):
                v = 0.5
            out[key] = max(0.0, min(1.0, v))
    return out
