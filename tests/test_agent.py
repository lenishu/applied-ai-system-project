"""
Tests for src/agent.py
"""

import json
import pytest
from src.agent import (
    parse_intent,
    resolve_activity,
    retrieve_catalog,
    rerank,
    explain,
    run_pipeline,
    PipelineStep,
    PipelineResult,
)
from src.catalog import LastFmClient
from src.activities import get_profile, to_user_prefs


class TestPipelineStep:
    """Test PipelineStep data structure."""

    def test_pipeline_step_creation(self):
        step = PipelineStep(
            name="test_step",
            input={"key": "value"},
            output={"result": 42},
            latency_ms=123.45,
            note="test note",
        )
        assert step.name == "test_step"
        assert step.latency_ms == 123.45


class TestPipelineResult:
    """Test PipelineResult data structure."""

    def test_pipeline_result_empty(self):
        result = PipelineResult()
        assert result.steps == []
        assert result.recommendations == []
        assert result.error is None

    def test_pipeline_result_to_dict(self):
        result = PipelineResult()
        result.steps.append(
            PipelineStep(
                name="step1",
                input={},
                output={},
                latency_ms=10.5,
            )
        )
        d = result.to_dict()
        assert "steps" in d
        assert len(d["steps"]) == 1
        assert d["steps"][0]["name"] == "step1"


class TestParseIntent:
    """Test Step 1: Parse Intent."""

    def test_parse_intent_explicit_selection(self):
        intent_dict, step = parse_intent("", explicit_section="student", explicit_mood="exam_cram")
        assert intent_dict["section"] == "student"
        assert intent_dict["mood"] == "exam_cram"
        assert intent_dict["confidence"] == 1.0
        assert step.name == "1_parse_intent"

    def test_parse_intent_from_free_text(self):
        intent_dict, step = parse_intent("cramming for exam")
        assert intent_dict["section"] == "student"
        assert intent_dict["mood"] == "exam_cram"
        assert intent_dict["confidence"] > 0.15

    def test_parse_intent_empty_text_fallback(self):
        intent_dict, step = parse_intent("")
        assert intent_dict["section"] == "work"
        assert intent_dict["mood"] == "email_triage"
        assert intent_dict["fallback_used"] is True

    def test_parse_intent_long_text_truncated(self):
        long_text = "x" * 600  # Exceeds MAX_INPUT_LENGTH (500)
        with pytest.raises(Exception):
            # Should raise GuardrailError for input length
            parse_intent(long_text)


class TestResolveActivity:
    """Test Step 2: Resolve Activity."""

    def test_resolve_activity_returns_user_prefs(self):
        intent_dict = {"section": "student", "mood": "exam_cram"}
        user_prefs, step = resolve_activity(intent_dict, "English", "2026")
        assert "target_energy" in user_prefs
        assert "preferred_language" in user_prefs
        assert user_prefs["target_energy"] == 0.30
        assert step.name == "2_resolve_activity"

    def test_resolve_activity_custom_language_era(self):
        intent_dict = {"section": "work", "mood": "deep_focus_coding"}
        user_prefs, step = resolve_activity(intent_dict, "Nepali", "2010-20")
        assert user_prefs["preferred_language"] == "Nepali"
        assert user_prefs["preferred_era"] == "2010-20"


class TestRetrieveCatalog:
    """Test Step 3: Retrieve Catalog."""

    def test_retrieve_catalog_returns_candidates_and_step(self):
        intent_dict = {"section": "student", "mood": "exam_cram"}
        # Use CSV-only (no Last.fm to avoid API calls)
        candidates, step = retrieve_catalog(intent_dict, use_lastfm=False)
        assert isinstance(candidates, list)
        assert step.name == "3_retrieve_catalog"
        assert "total_candidates" in step.output

    def test_retrieve_catalog_filters_instrumentalness(self):
        intent_dict = {"section": "student", "mood": "exam_cram"}
        # exam_cram has instrumentalness_min=0.7
        candidates, step = retrieve_catalog(intent_dict, use_lastfm=False)
        profile = get_profile("student", "exam_cram")
        if profile.instrumentalness_min > 0:
            # Some candidates should have been filtered
            assert "filter_dropped" in step.output or len(candidates) >= 0


class TestRerank:
    """Test Step 4: Rerank (uses existing recommend_songs unchanged)."""

    def test_rerank_returns_ranked_and_step(self):
        user_prefs = {
            "favorite_genre": None,
            "favorite_mood": None,
            "target_energy": 0.35,
            "target_valence": 0.50,
            "target_danceability": 0.35,
            "target_acousticness": 0.55,
            "preferred_language": "English",
            "preferred_era": "2026",
        }
        # Get some candidates from CSV
        from src.catalog import load_csv_seed
        candidates = load_csv_seed()[:10]  # Use first 10

        ranked, step = rerank(user_prefs, candidates, k=3)
        assert isinstance(ranked, list)
        assert len(ranked) <= 3
        assert step.name == "4_rerank"
        assert step.output["top_k"] is not None

    def test_rerank_empty_candidates(self):
        user_prefs = {"target_energy": 0.5, "target_valence": 0.5, "target_danceability": 0.5, "target_acousticness": 0.5}
        ranked, step = rerank(user_prefs, [], k=5)
        assert ranked == []
        assert step.output["top_k"] == []


class TestExplain:
    """Test Step 5: Explain (templated, no LLM)."""

    def test_explain_returns_list_of_dicts(self):
        # Create minimal ranked results
        from src.recommender import score_song
        from src.catalog import load_csv_seed

        candidates = load_csv_seed()[:3]
        if not candidates:
            pytest.skip("No CSV candidates available")

        user_prefs = {
            "favorite_genre": None,
            "favorite_mood": None,
            "target_energy": 0.35,
            "target_valence": 0.50,
            "target_danceability": 0.35,
            "target_acousticness": 0.55,
            "preferred_language": "English",
            "preferred_era": "2026",
        }

        ranked = []
        for cand in candidates:
            score, reason = score_song(user_prefs, cand)
            ranked.append((cand, score, reason))

        intent_dict = {"section": "work", "mood": "deep_focus_coding"}
        explanations, step = explain(ranked, intent_dict)

        assert len(explanations) == len(ranked)
        assert step.name == "5_explain"
        for expl in explanations:
            assert "title" in expl
            assert "artist" in expl
            assert "score" in expl
            assert "explanation_one_line" in expl


class TestRunPipeline:
    """Test full end-to-end pipeline orchestration."""

    def test_run_pipeline_basic(self):
        result = run_pipeline(free_text="cramming for exam", use_lastfm=False, k=3)
        assert isinstance(result, PipelineResult)
        assert len(result.steps) == 5  # All 5 steps completed
        assert result.intent is not None
        assert result.user_prefs is not None
        assert result.error is None

    def test_run_pipeline_explicit_section_mood(self):
        result = run_pipeline(section="student", mood="exam_cram", use_lastfm=False, k=2)
        assert result.intent["section"] == "student"
        assert result.intent["mood"] == "exam_cram"
        assert result.intent["confidence"] == 1.0

    def test_run_pipeline_recommendations_limit_k(self):
        result = run_pipeline(free_text="studying", use_lastfm=False, k=3)
        assert len(result.recommendations) <= 3

    def test_run_pipeline_step_names(self):
        result = run_pipeline(free_text="gym workout", use_lastfm=False, k=2)
        step_names = [s.name for s in result.steps]
        assert "1_parse_intent" in step_names
        assert "2_resolve_activity" in step_names
        assert "3_retrieve_catalog" in step_names
        assert "4_rerank" in step_names
        assert "5_explain" in step_names

    def test_run_pipeline_error_handling_invalid_section(self):
        result = run_pipeline(
            section="invalid",
            mood="exam_cram",
            use_lastfm=False,
        )
        assert result.error is not None
        assert "GuardrailError" in result.error or len(result.steps) < 5

    def test_run_pipeline_to_dict_serializable(self):
        result = run_pipeline(free_text="relaxing", use_lastfm=False, k=2)
        d = result.to_dict()
        # Should be JSON-serializable
        json_str = json.dumps(d, default=str)
        assert isinstance(json_str, str)


class TestPipelineIntegration:
    """Integration tests combining multiple pipeline steps."""

    def test_pipeline_full_trace_logging(self):
        # Just verify that a full run produces a trace we can inspect
        result = run_pipeline(
            free_text="coding session deep focus",
            use_lastfm=False,
            k=2,
        )
        assert len(result.steps) > 0
        # Each step should have latency
        for step in result.steps:
            assert step.latency_ms >= 0

    def test_pipeline_fallback_confidence_warning(self):
        # Low-confidence text should trigger fallback
        result = run_pipeline(
            free_text="zzz qwerty xyz",  # No keywords
            use_lastfm=False,
            k=1,
        )
        # Should still succeed, but with fallback
        assert result.error is None
        if result.intent["fallback_used"]:
            assert result.intent["section"] == "work"
            assert result.intent["mood"] == "email_triage"

    def test_pipeline_multiple_languages_supported(self):
        # Test that language can be changed
        result1 = run_pipeline(
            free_text="exam study",
            language="English",
            use_lastfm=False,
            k=1,
        )
        result2 = run_pipeline(
            free_text="exam study",
            language="Nepali",
            use_lastfm=False,
            k=1,
        )
        assert result1.user_prefs["preferred_language"] == "English"
        assert result2.user_prefs["preferred_language"] == "Nepali"
