"""
Activity taxonomy for StudyVibe.

Three top-level sections (student / work / personal); each has a list of moods.
Each mood maps to an AudioFeatureTarget that plugs straight into the existing
score_song() function in recommender.py.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class AudioFeatureTarget:
    """Audio-feature targets for a single mood. Maps directly to score_song's user_prefs."""
    target_energy: float
    target_valence: float
    target_danceability: float
    target_acousticness: float
    instrumentalness_min: float
    lastfm_tags: Tuple[str, ...]
    favorite_genre: str
    favorite_mood: str
    display_name: str
    description: str


# SECTIONS[section][mood] -> AudioFeatureTarget
SECTIONS: Dict[str, Dict[str, AudioFeatureTarget]] = {
    "student": {
        "exam_cram": AudioFeatureTarget(
            target_energy=0.30, target_valence=0.50, target_danceability=0.25,
            target_acousticness=0.70, instrumentalness_min=0.7,
            lastfm_tags=("study", "classical", "instrumental"),
            favorite_genre="classical", favorite_mood="focused",
            display_name="Exam Cramming",
            description="Late-night studying before a big exam. Low distraction, high focus.",
        ),
        "deep_study": AudioFeatureTarget(
            target_energy=0.25, target_valence=0.55, target_danceability=0.30,
            target_acousticness=0.75, instrumentalness_min=0.7,
            lastfm_tags=("study", "ambient", "piano"),
            favorite_genre="ambient", favorite_mood="meditative",
            display_name="Deep Study",
            description="Long study session. Peaceful, instrumental, helps concentration.",
        ),
        "light_reading": AudioFeatureTarget(
            target_energy=0.40, target_valence=0.60, target_danceability=0.35,
            target_acousticness=0.65, instrumentalness_min=0.4,
            lastfm_tags=("chill", "lofi", "jazz"),
            favorite_genre="lofi", favorite_mood="chill",
            display_name="Light Reading",
            description="Casual reading or note review. Mellow with light beats.",
        ),
        "group_brainstorm": AudioFeatureTarget(
            target_energy=0.60, target_valence=0.70, target_danceability=0.55,
            target_acousticness=0.40, instrumentalness_min=0.0,
            lastfm_tags=("indie", "upbeat", "creativity"),
            favorite_genre="indie", favorite_mood="happy",
            display_name="Group Brainstorm",
            description="Collaborative work or group study. Upbeat but not distracting.",
        ),
        "pre_exam_pump": AudioFeatureTarget(
            target_energy=0.80, target_valence=0.75, target_danceability=0.70,
            target_acousticness=0.20, instrumentalness_min=0.0,
            lastfm_tags=("hype", "motivation", "edm"),
            favorite_genre="electronic", favorite_mood="intense",
            display_name="Pre-Exam Pump",
            description="Walking into the exam room. Confidence boost, high energy.",
        ),
    },
    "work": {
        "deep_focus_coding": AudioFeatureTarget(
            target_energy=0.35, target_valence=0.50, target_danceability=0.35,
            target_acousticness=0.55, instrumentalness_min=0.6,
            lastfm_tags=("focus", "post-rock", "ambient"),
            favorite_genre="ambient", favorite_mood="focused",
            display_name="Deep Focus Coding",
            description="In the zone. Long coding or writing session. No vocals.",
        ),
        "email_triage": AudioFeatureTarget(
            target_energy=0.55, target_valence=0.65, target_danceability=0.50,
            target_acousticness=0.40, instrumentalness_min=0.0,
            lastfm_tags=("chill", "indie", "lofi"),
            favorite_genre="lofi", favorite_mood="chill",
            display_name="Email & Admin",
            description="Shallow work, slack, emails, organizing. Lyrics okay.",
        ),
        "creative_brainstorm": AudioFeatureTarget(
            target_energy=0.65, target_valence=0.75, target_danceability=0.60,
            target_acousticness=0.35, instrumentalness_min=0.0,
            lastfm_tags=("indie", "electronic", "creative"),
            favorite_genre="indie", favorite_mood="happy",
            display_name="Creative Brainstorm",
            description="Design, writing, ideation. Energy without overwhelming focus.",
        ),
        "meeting_prep": AudioFeatureTarget(
            target_energy=0.45, target_valence=0.60, target_danceability=0.40,
            target_acousticness=0.50, instrumentalness_min=0.3,
            lastfm_tags=("calm", "instrumental", "focus"),
            favorite_genre="classical", favorite_mood="peaceful",
            display_name="Meeting Prep",
            description="Calm prep before a presentation or interview.",
        ),
        "energizing_break": AudioFeatureTarget(
            target_energy=0.85, target_valence=0.80, target_danceability=0.85,
            target_acousticness=0.15, instrumentalness_min=0.0,
            lastfm_tags=("workout", "dance", "pop"),
            favorite_genre="pop", favorite_mood="happy",
            display_name="Energizing Break",
            description="Quick break between meetings. Reset and re-energize.",
        ),
        "commute": AudioFeatureTarget(
            target_energy=0.55, target_valence=0.65, target_danceability=0.55,
            target_acousticness=0.40, instrumentalness_min=0.0,
            lastfm_tags=("pop", "indie", "podcast-friendly"),
            favorite_genre="pop", favorite_mood="chill",
            display_name="Commute",
            description="Driving, walking, or transit. Familiar and energizing.",
        ),
    },
    "personal": {
        "workout_gym": AudioFeatureTarget(
            target_energy=0.90, target_valence=0.80, target_danceability=0.85,
            target_acousticness=0.10, instrumentalness_min=0.0,
            lastfm_tags=("workout", "hiphop", "edm"),
            favorite_genre="hiphop", favorite_mood="intense",
            display_name="Workout / Gym",
            description="Cardio, lifting, running. Maximum energy.",
        ),
        "chill_unwind": AudioFeatureTarget(
            target_energy=0.40, target_valence=0.60, target_danceability=0.45,
            target_acousticness=0.55, instrumentalness_min=0.0,
            lastfm_tags=("chill", "lofi", "indie"),
            favorite_genre="lofi", favorite_mood="chill",
            display_name="Chill & Unwind",
            description="End of day relaxation. Mellow but engaged.",
        ),
        "happy_celebrate": AudioFeatureTarget(
            target_energy=0.85, target_valence=0.95, target_danceability=0.85,
            target_acousticness=0.20, instrumentalness_min=0.0,
            lastfm_tags=("feel-good", "pop", "dance"),
            favorite_genre="pop", favorite_mood="happy",
            display_name="Happy / Celebrate",
            description="Friday night, celebration, party mode.",
        ),
        "sad_reflective": AudioFeatureTarget(
            target_energy=0.30, target_valence=0.20, target_danceability=0.30,
            target_acousticness=0.60, instrumentalness_min=0.0,
            lastfm_tags=("sad", "indie", "acoustic"),
            favorite_genre="indie", favorite_mood="sad",
            display_name="Sad / Reflective",
            description="Processing emotions. Slow, honest, emotional.",
        ),
        "romantic": AudioFeatureTarget(
            target_energy=0.55, target_valence=0.75, target_danceability=0.55,
            target_acousticness=0.45, instrumentalness_min=0.0,
            lastfm_tags=("love", "rnb", "soul"),
            favorite_genre="rnb", favorite_mood="romantic",
            display_name="Romantic",
            description="Date night, dinner, intimate moments.",
        ),
        "sleep_winddown": AudioFeatureTarget(
            target_energy=0.15, target_valence=0.45, target_danceability=0.20,
            target_acousticness=0.90, instrumentalness_min=0.5,
            lastfm_tags=("sleep", "ambient", "calm"),
            favorite_genre="ambient", favorite_mood="peaceful",
            display_name="Sleep / Wind Down",
            description="Bedtime. Soft, ambient, sleep-inducing.",
        ),
    },
}


# Flat lookup: "section.mood" -> AudioFeatureTarget.
# Convenient for places that don't want to do nested dict access (eval harness,
# UI rendering, debug dumps).
ACTIVITY_LOOKUP: Dict[str, AudioFeatureTarget] = {
    f"{section}.{mood}": target
    for section, moods in SECTIONS.items()
    for mood, target in moods.items()
}


def get_profile(section: str, mood: str) -> AudioFeatureTarget:
    """Look up a mood profile. Raises KeyError if not found."""
    return SECTIONS[section][mood]


def to_user_prefs(profile: AudioFeatureTarget, language: str = "English", era: str = "2026") -> Dict:
    """Convert an AudioFeatureTarget into the user_prefs dict that score_song expects."""
    return {
        "favorite_genre": profile.favorite_genre,
        "favorite_mood": profile.favorite_mood,
        "target_energy": profile.target_energy,
        "target_valence": profile.target_valence,
        "target_danceability": profile.target_danceability,
        "target_acousticness": profile.target_acousticness,
        "preferred_language": language,
        "preferred_era": era,
        # Boolean derived from acousticness, kept for compatibility with
        # the UserProfile dataclass in recommender.py.
        "likes_acoustic": profile.target_acousticness > 0.5,
    }


def all_section_mood_pairs() -> List[Tuple[str, str]]:
    """List every (section, mood) pair. Useful for eval and UI rendering."""
    return [(s, m) for s, moods in SECTIONS.items() for m in moods]


# ─── Keyword classifier ──────────────────────────────────────────────────────
# Maps phrases (lowercase) to (section, mood). The classifier scores each
# (section, mood) by counting matched keywords in the user's free text.

KEYWORDS: Dict[Tuple[str, str], Tuple[str, ...]] = {
    ("student", "exam_cram"):       ("exam", "final", "midterm", "test", "cram", "cramming", "tomorrow morning"),
    ("student", "deep_study"):      ("study", "studying", "library", "revision", "review", "homework"),
    ("student", "light_reading"):   ("reading", "notes", "skim", "casual study", "light"),
    ("student", "group_brainstorm"):("group", "brainstorm", "team study", "collaborate"),
    ("student", "pre_exam_pump"):   ("pre-exam", "before exam", "pump up", "psyching", "pre exam"),

    ("work", "deep_focus_coding"):  ("coding", "code", "programming", "deep work", "focus", "locked in", "deep dive", "sprint"),
    ("work", "email_triage"):       ("email", "emails", "slack", "admin", "inbox", "triage"),
    ("work", "creative_brainstorm"):("design", "creative", "brainstorm", "ideation", "writing", "draft"),
    ("work", "meeting_prep"):       ("meeting", "presentation", "interview", "prep", "calls", "standup"),
    ("work", "energizing_break"):   ("break", "between meetings", "energize", "reset", "coffee"),
    ("work", "commute"):            ("commute", "driving", "drive", "train", "bus", "walking to"),

    ("personal", "workout_gym"):    ("gym", "workout", "lifting", "cardio", "running", "run", "exercise"),
    ("personal", "chill_unwind"):   ("chill", "unwind", "relax", "evening", "after work"),
    ("personal", "happy_celebrate"):("celebrate", "celebration", "party", "friday", "weekend", "happy"),
    ("personal", "sad_reflective"): ("sad", "down", "blue", "breakup", "lonely", "reflective", "crying"),
    ("personal", "romantic"):       ("romantic", "date", "dinner", "love", "anniversary"),
    ("personal", "sleep_winddown"): ("sleep", "bedtime", "wind down", "tired", "winding down", "before bed"),
}


def classify(free_text: str) -> Tuple[str, str, float, Dict[Tuple[str, str], int]]:
    """
    Rule-based intent classifier.

    Returns (section, mood, confidence, score_breakdown).
    Confidence is matched_keywords / total_words, clamped to [0,1].
    Below 0.15 threshold, falls back to ('work', 'email_triage').
    """
    text = (free_text or "").lower().strip()
    words = [w for w in text.split() if w]
    total_words = max(len(words), 1)

    scores: Dict[Tuple[str, str], int] = {}
    for (section, mood), keywords in KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > 0:
            scores[(section, mood)] = hits

    if not scores:
        return ("work", "email_triage", 0.0, {})

    best_pair = max(scores.items(), key=lambda kv: kv[1])
    (section, mood), hits = best_pair
    confidence = min(1.0, hits / total_words)

    if confidence < 0.15:
        return ("work", "email_triage", confidence, scores)

    return (section, mood, confidence, scores)
