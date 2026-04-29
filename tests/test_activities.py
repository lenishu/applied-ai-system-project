"""
Tests for src/activities.py
"""

import pytest
from src.activities import (
    SECTIONS,
    ACTIVITY_LOOKUP,
    AudioFeatureTarget,
    get_profile,
    to_user_prefs,
    all_section_mood_pairs,
    classify,
)


class TestActivitiesStructure:
    """Test that SECTIONS dict is properly structured."""

    def test_sections_has_three_top_levels(self):
        assert set(SECTIONS.keys()) == {"student", "work", "personal"}

    def test_student_section_has_five_moods(self):
        assert len(SECTIONS["student"]) == 5
        expected = {"exam_cram", "deep_study", "light_reading", "group_brainstorm", "pre_exam_pump"}
        assert set(SECTIONS["student"].keys()) == expected

    def test_work_section_has_six_moods(self):
        assert len(SECTIONS["work"]) == 6
        expected = {"deep_focus_coding", "email_triage", "creative_brainstorm", "meeting_prep", "energizing_break", "commute"}
        assert set(SECTIONS["work"].keys()) == expected

    def test_personal_section_has_six_moods(self):
        assert len(SECTIONS["personal"]) == 6
        expected = {"workout_gym", "chill_unwind", "happy_celebrate", "sad_reflective", "romantic", "sleep_winddown"}
        assert set(SECTIONS["personal"].keys()) == expected

    def test_all_profiles_are_audio_feature_targets(self):
        for section, moods in SECTIONS.items():
            for mood, target in moods.items():
                assert isinstance(target, AudioFeatureTarget)
                assert 0 <= target.target_energy <= 1
                assert 0 <= target.target_valence <= 1
                assert 0 <= target.target_danceability <= 1
                assert 0 <= target.target_acousticness <= 1
                assert 0 <= target.instrumentalness_min <= 1


class TestActivityLookup:
    """Test the flat ACTIVITY_LOOKUP dict."""

    def test_activity_lookup_has_all_moods(self):
        total = sum(len(moods) for moods in SECTIONS.values())
        assert len(ACTIVITY_LOOKUP) == total

    def test_activity_lookup_keys_are_section_dot_mood(self):
        for key in ACTIVITY_LOOKUP.keys():
            assert "." in key
            section, mood = key.split(".", 1)
            assert section in SECTIONS
            assert mood in SECTIONS[section]


class TestGetProfile:
    """Test get_profile() lookup function."""

    def test_get_profile_exam_cram(self):
        prof = get_profile("student", "exam_cram")
        assert isinstance(prof, AudioFeatureTarget)
        assert prof.target_energy == 0.30
        assert prof.target_acousticness == 0.70

    def test_get_profile_deep_focus_coding(self):
        prof = get_profile("work", "deep_focus_coding")
        assert prof.target_energy == 0.35
        assert prof.instrumentalness_min == 0.6

    def test_get_profile_workout_gym(self):
        prof = get_profile("personal", "workout_gym")
        assert prof.target_energy == 0.90
        assert prof.target_danceability == 0.85

    def test_get_profile_nonexistent_raises_keyerror(self):
        with pytest.raises(KeyError):
            get_profile("student", "nonexistent")

        with pytest.raises(KeyError):
            get_profile("invalid", "exam_cram")


class TestToUserPrefs:
    """Test conversion of activity profile to user preferences dict."""

    def test_to_user_prefs_default_era(self):
        prof = get_profile("student", "exam_cram")
        prefs = to_user_prefs(prof)
        assert prefs["target_energy"] == 0.30
        assert prefs["target_valence"] == 0.50
        assert prefs["preferred_language"] == "English"
        assert prefs["preferred_era"] == "2026"

    def test_to_user_prefs_custom_language_era(self):
        prof = get_profile("work", "email_triage")
        prefs = to_user_prefs(prof, language="Nepali", era="2010-20")
        assert prefs["preferred_language"] == "Nepali"
        assert prefs["preferred_era"] == "2010-20"
        assert prefs["target_acousticness"] == 0.40

    def test_to_user_prefs_clamps_acousticness_bool(self):
        prof = get_profile("personal", "chill_unwind")
        prefs = to_user_prefs(prof)
        assert isinstance(prefs["likes_acoustic"], bool)
        assert prefs["likes_acoustic"] is True  # acousticness 0.55 > 0.5


class TestAllSectionMoodPairs:
    """Test all_section_mood_pairs() utility."""

    def test_all_section_mood_pairs_count(self):
        pairs = all_section_mood_pairs()
        assert len(pairs) == 17  # 5 + 6 + 6

    def test_all_section_mood_pairs_valid_keys(self):
        pairs = all_section_mood_pairs()
        for section, mood in pairs:
            assert section in SECTIONS
            assert mood in SECTIONS[section]


class TestClassify:
    """Test the keyword classifier."""

    def test_classify_exam_cram_phrases(self):
        section, mood, conf, scores = classify("cramming for calc final tomorrow")
        assert section == "student"
        assert mood == "exam_cram"
        assert conf > 0.15

        section, mood, conf, scores = classify("midterm exam preparation")
        assert section == "student"
        assert mood == "exam_cram"

    def test_classify_deep_focus_coding(self):
        section, mood, conf, scores = classify("deep dive into coding")
        assert section == "work"
        assert mood == "deep_focus_coding"

    def test_classify_workout_gym(self):
        section, mood, conf, scores = classify("gym workout session")
        assert section == "personal"
        assert mood == "workout_gym"

    def test_classify_empty_text_falls_back(self):
        section, mood, conf, scores = classify("")
        assert section == "work"
        assert mood == "email_triage"
        assert conf == 0.0

    def test_classify_low_confidence_falls_back(self):
        # Single word that doesn't match any keyword strongly
        section, mood, conf, scores = classify("xyz qwerty")
        if conf < 0.15:
            assert section == "work"
            assert mood == "email_triage"

    def test_classify_confidence_clamped_to_one(self):
        section, mood, conf, scores = classify("exam final test cram")
        assert 0 <= conf <= 1.0

    def test_classify_sleep_winddown(self):
        section, mood, conf, scores = classify("bedtime sleep wind down")
        assert section == "personal"
        assert mood == "sleep_winddown"

    def test_classify_meeting_prep(self):
        section, mood, conf, scores = classify("preparing for presentation interview")
        assert section == "work"
        assert mood == "meeting_prep"
