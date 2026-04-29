from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    instrumentalness: float = 0.0
    language: str = "English"
    era: str = "2026"

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: float = 0.5  # 0=sad/dark, 1=happy/bright
    target_danceability: float = 0.5  # 0=not danceable, 1=highly danceable
    target_acousticness: float = 0.5  # 0=electric, 1=acoustic
    preferred_language: str = "English"
    preferred_era: str = "2026"

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """
        Recommends top k songs for a user based on preference matching.
        """
        # Convert Song objects to dicts for scoring
        user_dict = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "target_valence": user.target_valence,
            "target_danceability": user.target_danceability,
            "target_acousticness": user.target_acousticness,
            "preferred_language": user.preferred_language,
            "preferred_era": user.preferred_era,
        }

        songs_dicts = [
            {
                "id": s.id,
                "title": s.title,
                "artist": s.artist,
                "genre": s.genre,
                "mood": s.mood,
                "energy": s.energy,
                "tempo_bpm": s.tempo_bpm,
                "valence": s.valence,
                "danceability": s.danceability,
                "acousticness": s.acousticness,
                "instrumentalness": s.instrumentalness,
                "language": s.language,
                "era": s.era,
            }
            for s in self.songs
        ]

        # Use the functional scorer
        recommendations = recommend_songs(user_dict, songs_dicts, k)

        # Convert ranked dicts back to Song objects for the test contract.
        return [
            Song(
                id=s["id"],
                title=s["title"],
                artist=s["artist"],
                genre=s["genre"],
                mood=s["mood"],
                energy=s["energy"],
                tempo_bpm=s["tempo_bpm"],
                valence=s["valence"],
                danceability=s["danceability"],
                acousticness=s["acousticness"],
                instrumentalness=s.get("instrumentalness", 0.0),
                language=s.get("language", "English"),
                era=s.get("era", "2026"),
            )
            for s, _, _ in recommendations
        ]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """
        Explains why a song was recommended to a user.
        """
        user_dict = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "target_valence": user.target_valence,
            "target_danceability": user.target_danceability,
            "target_acousticness": user.target_acousticness,
            "preferred_language": user.preferred_language,
            "preferred_era": user.preferred_era,
        }

        song_dict = {
            "id": song.id,
            "title": song.title,
            "artist": song.artist,
            "genre": song.genre,
            "mood": song.mood,
            "energy": song.energy,
            "valence": song.valence,
            "danceability": song.danceability,
            "acousticness": song.acousticness,
            "instrumentalness": song.instrumentalness,
            "language": song.language,
            "era": song.era,
        }

        score, reasons = score_song(user_dict, song_dict)
        explanation = f"'{song.title}' by {song.artist}\nScore: {score:.2f}\n\n" + "\n".join(reasons)
        return explanation

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file and returns list of song dicts.
    CSV columns: id, title, artist, genre, mood, energy, tempo_bpm, valence,
                 danceability, acousticness, instrumentalness, language, era
    """
    songs = []
    print(f"Loading songs from {csv_path}...")

    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert numeric strings to floats
                song = {
                    "id": int(row["id"]),
                    "title": row["title"],
                    "artist": row["artist"],
                    "genre": row["genre"],
                    "mood": row["mood"],
                    "energy": float(row["energy"]),
                    "tempo_bpm": float(row["tempo_bpm"]),
                    "valence": float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                    "instrumentalness": float(row["instrumentalness"]),
                    "language": row["language"],
                    "era": row["era"],
                }
                songs.append(song)

        print(f"[OK] Loaded {len(songs)} songs")
        return songs

    except FileNotFoundError:
        print(f"[ERROR] Could not find file {csv_path}")
        return []
    except Exception as e:
        print(f"[ERROR] {e}")
        return []

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.

    Strategy:
    - EXACT MATCHES (Era, Language): weight=3.0 (highest priority - hard requirements)
    - Genre & Mood: weight=2.5, 2.0 (categorical preferences)
    - Numerical Features: distance-based (closer to target = higher score)

    Returns: (total_score, list_of_reasons)
    """
    score = 0.0
    reasons = []

    # EXACT MATCHES - Hardest constraints (highest weight)

    # Language match (exact)
    if song["language"].lower() == user_prefs["preferred_language"].lower():
        score += 3.0
        reasons.append(f"[MATCH] Language ({song['language']})")
    else:
        score -= 0.5  # Small penalty for language mismatch
        reasons.append(f"[MISMATCH] Language (song: {song['language']}, prefer: {user_prefs['preferred_language']})")

    # Era match (exact)
    if song["era"] == user_prefs["preferred_era"]:
        score += 3.0
        reasons.append(f"[MATCH] Era ({song['era']})")
    else:
        score -= 0.3  # Small penalty for era mismatch
        reasons.append(f"[MISMATCH] Era (song: {song['era']}, prefer: {user_prefs['preferred_era']})")

    # CATEGORICAL PREFERENCES - Medium weight

    # Genre match (skip if either side is None / unset)
    pref_genre = user_prefs.get("favorite_genre")
    song_genre = song.get("genre")
    if pref_genre and song_genre and song_genre.lower() == pref_genre.lower():
        score += 2.5
        reasons.append(f"[MATCH] Genre ({song_genre})")
    elif pref_genre is None:
        reasons.append("[SKIP] Genre (no preference)")
    else:
        score -= 0.2
        reasons.append("[MISMATCH] Genre")

    # Mood match (skip if either side is None / unset)
    pref_mood = user_prefs.get("favorite_mood")
    song_mood = song.get("mood")
    if pref_mood and song_mood and song_mood.lower() == pref_mood.lower():
        score += 2.0
        reasons.append(f"[MATCH] Mood ({song_mood})")
    elif pref_mood is None:
        reasons.append("[SKIP] Mood (no preference)")
    else:
        score -= 0.1
        reasons.append("[MISMATCH] Mood")

    # NUMERICAL FEATURES - Distance-based scoring (closer to target = higher score)
    # Scoring formula: 1 - |feature_value - target_value| = reward for proximity

    # Energy (higher penalty for distance)
    energy_distance = abs(song["energy"] - user_prefs["target_energy"])
    energy_score = max(0, 2.0 * (1 - energy_distance))  # max 2.0 points
    score += energy_score
    reasons.append(f"Energy: {song['energy']:.2f} (target: {user_prefs['target_energy']:.2f}) => +{energy_score:.2f}")

    # Valence (emotional tone)
    valence_distance = abs(song["valence"] - user_prefs["target_valence"])
    valence_score = max(0, 1.5 * (1 - valence_distance))  # max 1.5 points
    score += valence_score
    reasons.append(f"Valence: {song['valence']:.2f} (target: {user_prefs['target_valence']:.2f}) => +{valence_score:.2f}")

    # Danceability (optional vibe)
    danceability_distance = abs(song["danceability"] - user_prefs["target_danceability"])
    danceability_score = max(0, 1.0 * (1 - danceability_distance))  # max 1.0 points
    score += danceability_score
    reasons.append(f"Danceability: {song['danceability']:.2f} (target: {user_prefs['target_danceability']:.2f}) => +{danceability_score:.2f}")

    # Acousticness (texture preference)
    acousticness_distance = abs(song["acousticness"] - user_prefs["target_acousticness"])
    acousticness_score = max(0, 1.0 * (1 - acousticness_distance))  # max 1.0 points
    score += acousticness_score
    reasons.append(f"Acousticness: {song['acousticness']:.2f} (target: {user_prefs['target_acousticness']:.2f}) => +{acousticness_score:.2f}")

    return (score, reasons)

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.

    Process:
    1. Score each song against user preferences
    2. Sort by score (highest first)
    3. Return top k songs with explanations

    Returns: [(song_dict, score, explanation), ...]
    """
    scored_songs = []

    # Score all songs
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "\n".join(reasons)
        scored_songs.append((song, score, explanation))

    # Sort by score (descending)
    scored_songs.sort(key=lambda x: x[1], reverse=True)

    # Return top k
    return scored_songs[:k]
