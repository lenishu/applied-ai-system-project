"""
Tests for src/guardrails.py
"""

import pytest
from pydantic import ValidationError
from src.guardrails import (
    GuardrailError,
    IntentSchema,
    RecommendRequest,
    validate_input_length,
    validate_section_mood,
    apply_low_confidence_fallback,
    clamp_prefs,
    MAX_INPUT_LENGTH,
    MIN_CONFIDENCE,
)


class TestGuardrailError:
    """Test the GuardrailError exception."""

    def test_guardrail_error_layer_and_message(self):
        err = GuardrailError("input_length", "text too long")
        assert err.layer == "input_length"
        assert err.message == "text too long"
        assert "[input_length]" in str(err)


class TestValidateInputLength:
    """Test Layer 1: input length cap."""

    def test_validate_input_length_short_text_ok(self):
        short = "hello world"
        result = validate_input_length(short)
        assert result == short

    def test_validate_input_length_empty_ok(self):
        result = validate_input_length("")
        assert result == ""

    def test_validate_input_length_max_ok(self):
        text = "x" * MAX_INPUT_LENGTH
        result = validate_input_length(text)
        assert result == text

    def test_validate_input_length_exceeds_max_raises(self):
        text = "x" * (MAX_INPUT_LENGTH + 1)
        with pytest.raises(GuardrailError) as exc_info:
            validate_input_length(text)
        assert exc_info.value.layer == "input_length"


class TestValidateSectionMood:
    """Test Layer 2: activity allowlist."""

    def test_validate_section_mood_valid_student_exam_cram(self):
        section, mood = validate_section_mood("student", "exam_cram")
        assert section == "student"
        assert mood == "exam_cram"

    def test_validate_section_mood_valid_work_deep_focus(self):
        section, mood = validate_section_mood("work", "deep_focus_coding")
        assert section == "work"
        assert mood == "deep_focus_coding"

    def test_validate_section_mood_invalid_section_raises(self):
        with pytest.raises(GuardrailError) as exc_info:
            validate_section_mood("invalid", "exam_cram")
        assert exc_info.value.layer == "activity_allowlist"

    def test_validate_section_mood_invalid_mood_raises(self):
        with pytest.raises(GuardrailError) as exc_info:
            validate_section_mood("student", "invalid_mood")
        assert exc_info.value.layer == "activity_allowlist"


class TestLowConfidenceFallback:
    """Test Layer 2b: low confidence fallback to safe default."""

    def test_no_fallback_above_threshold(self):
        section, mood, fallback_used, reason = apply_low_confidence_fallback("student", "exam_cram", 0.50)
        assert section == "student"
        assert mood == "exam_cram"
        assert fallback_used is False
        assert reason is None

    def test_fallback_below_threshold(self):
        section, mood, fallback_used, reason = apply_low_confidence_fallback("work", "creative_brainstorm", 0.10)
        assert section == "work"
        assert mood == "email_triage"  # default fallback
        assert fallback_used is True
        assert reason is not None
        assert "below threshold" in reason

    def test_fallback_exactly_at_threshold(self):
        section, mood, fallback_used, reason = apply_low_confidence_fallback("personal", "chill_unwind", MIN_CONFIDENCE)
        # At or above threshold, no fallback
        assert fallback_used is False


class TestClampPrefs:
    """Test Layer 4: numeric range clamp."""

    def test_clamp_prefs_in_range_unchanged(self):
        prefs = {
            "target_energy": 0.50,
            "target_valence": 0.60,
            "target_danceability": 0.40,
            "target_acousticness": 0.75,
        }
        result = clamp_prefs(prefs)
        assert result["target_energy"] == 0.50
        assert result["target_valence"] == 0.60

    def test_clamp_prefs_exceeds_one_clamped(self):
        prefs = {
            "target_energy": 1.5,
            "target_valence": 2.0,
            "target_danceability": 0.40,
            "target_acousticness": 0.75,
        }
        result = clamp_prefs(prefs)
        assert result["target_energy"] == 1.0
        assert result["target_valence"] == 1.0

    def test_clamp_prefs_below_zero_clamped(self):
        prefs = {
            "target_energy": -0.5,
            "target_valence": -1.0,
            "target_danceability": 0.40,
            "target_acousticness": 0.75,
        }
        result = clamp_prefs(prefs)
        assert result["target_energy"] == 0.0
        assert result["target_valence"] == 0.0

    def test_clamp_prefs_string_number_converted(self):
        prefs = {
            "target_energy": "0.50",
            "target_valence": "0.60",
            "target_danceability": 0.40,
            "target_acousticness": 0.75,
        }
        result = clamp_prefs(prefs)
        assert isinstance(result["target_energy"], float)
        assert result["target_energy"] == 0.50

    def test_clamp_prefs_invalid_string_defaults_to_half(self):
        prefs = {
            "target_energy": "invalid",
            "target_valence": 0.60,
            "target_danceability": 0.40,
            "target_acousticness": 0.75,
        }
        result = clamp_prefs(prefs)
        assert result["target_energy"] == 0.5


class TestIntentSchema:
    """Test Pydantic schema for validated intent."""

    def test_intent_schema_valid(self):
        intent = IntentSchema(
            section="student",
            mood="exam_cram",
            confidence=0.85,
            free_text="cramming for final",
        )
        assert intent.section == "student"
        assert intent.mood == "exam_cram"
        assert intent.confidence == 0.85

    def test_intent_schema_invalid_section_raises(self):
        with pytest.raises(ValidationError):
            IntentSchema(
                section="invalid",
                mood="exam_cram",
                confidence=0.85,
            )

    def test_intent_schema_confidence_ge_zero(self):
        with pytest.raises(ValidationError):
            IntentSchema(
                section="student",
                mood="exam_cram",
                confidence=-0.1,
            )

    def test_intent_schema_confidence_le_one(self):
        with pytest.raises(ValidationError):
            IntentSchema(
                section="student",
                mood="exam_cram",
                confidence=1.1,
            )

    def test_intent_schema_free_text_capped(self):
        long_text = "x" * (MAX_INPUT_LENGTH + 1)
        with pytest.raises(ValidationError):
            IntentSchema(
                section="student",
                mood="exam_cram",
                confidence=0.85,
                free_text=long_text,
            )


class TestRecommendRequest:
    """Test Pydantic schema for API request."""

    def test_recommend_request_minimal(self):
        req = RecommendRequest(free_text="studying")
        assert req.free_text == "studying"
        assert req.language == "English"
        assert req.era == "2026"
        assert req.use_lastfm is True
        assert req.k == 5

    def test_recommend_request_with_explicit_section_mood(self):
        req = RecommendRequest(
            section="work",
            mood="deep_focus_coding",
            language="Nepali",
        )
        assert req.section == "work"
        assert req.mood == "deep_focus_coding"
        assert req.language == "Nepali"

    def test_recommend_request_k_bounds(self):
        req = RecommendRequest(k=1)
        assert req.k == 1

        req = RecommendRequest(k=20)
        assert req.k == 20

        with pytest.raises(ValidationError):
            RecommendRequest(k=0)

        with pytest.raises(ValidationError):
            RecommendRequest(k=21)
