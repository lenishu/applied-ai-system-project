"""
Catalog retrieval. Pulls candidate tracks from Last.fm by activity tags,
falls back to the local CSV seed when offline or on API failure.

Last.fm has no audio features, so we synthesize energy/valence/danceability/
acousticness from the activity profile + tag hints. This is disclosed as a
limitation in model_card.md.
"""

import hashlib
import json
import logging
import os
import random
from pathlib import Path
from typing import Dict, List, Optional

import requests

try:
    from .activities import AudioFeatureTarget
    from .recommender import load_songs
except ImportError:
    from activities import AudioFeatureTarget
    from recommender import load_songs


logger = logging.getLogger(__name__)

LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"
LASTFM_TIMEOUT_SEC = 6.0
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache" / "lastfm"
CSV_PATH = Path(__file__).parent.parent / "data" / "songs.csv"


def _cache_path(tag: str, limit: int) -> Path:
    safe = hashlib.md5(f"{tag}:{limit}".encode()).hexdigest()[:12]
    return CACHE_DIR / f"{tag.replace(' ', '_')}_{safe}.json"


class LastFmClient:
    """Thin Last.fm client. Caches responses to disk."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LASTFM_API_KEY", "").strip()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_top_tracks_by_tag(self, tag: str, limit: int = 20) -> List[Dict]:
        """Fetch top tracks for a Last.fm tag. Returns list of raw track dicts."""
        cache_file = _cache_path(tag, limit)

        if cache_file.exists():
            try:
                with cache_file.open("r", encoding="utf-8") as f:
                    cached = json.load(f)
                logger.info("lastfm cache hit tag=%s n=%d", tag, len(cached))
                return cached
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("cache read failed tag=%s err=%s", tag, e)

        if not self.is_configured:
            logger.info("lastfm not configured, returning [] for tag=%s", tag)
            return []

        params = {
            "method": "tag.getTopTracks",
            "tag": tag,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit,
        }
        try:
            resp = requests.get(LASTFM_BASE_URL, params=params, timeout=LASTFM_TIMEOUT_SEC)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("lastfm fetch failed tag=%s err=%s", tag, e)
            return []

        tracks = (data.get("tracks") or {}).get("track") or []
        if isinstance(tracks, dict):
            tracks = [tracks]

        try:
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(tracks, f, indent=2)
        except OSError as e:
            logger.warning("cache write failed tag=%s err=%s", tag, e)

        logger.info("lastfm fetched tag=%s n=%d", tag, len(tracks))
        return tracks


def _synthesize_features(profile: AudioFeatureTarget, tag: str, seed: int) -> Dict[str, float]:
    """
    Last.fm doesn't give audio features. Derive plausible values from the
    activity profile (target_*) plus a small jitter so songs aren't identical.
    Tag-based heuristics nudge in the direction of what the tag implies.
    """
    rng = random.Random(seed)
    jitter = lambda center: max(0.0, min(1.0, center + rng.uniform(-0.10, 0.10)))

    energy = jitter(profile.target_energy)
    valence = jitter(profile.target_valence)
    danceability = jitter(profile.target_danceability)
    acousticness = jitter(profile.target_acousticness)
    instrumentalness = jitter(max(profile.instrumentalness_min, 0.3))

    tag_l = tag.lower()
    if "acoustic" in tag_l or "piano" in tag_l or "classical" in tag_l:
        acousticness = max(acousticness, 0.75)
        instrumentalness = max(instrumentalness, 0.6)
    if "workout" in tag_l or "edm" in tag_l or "dance" in tag_l:
        energy = max(energy, 0.80)
        danceability = max(danceability, 0.75)
    if "sleep" in tag_l or "ambient" in tag_l:
        energy = min(energy, 0.30)
        acousticness = max(acousticness, 0.70)
    if "sad" in tag_l:
        valence = min(valence, 0.30)

    return {
        "energy": round(energy, 3),
        "valence": round(valence, 3),
        "danceability": round(danceability, 3),
        "acousticness": round(acousticness, 3),
        "instrumentalness": round(instrumentalness, 3),
    }


def _lastfm_to_song_dict(track: Dict, profile: AudioFeatureTarget, tag: str, idx: int) -> Dict:
    """Convert a Last.fm raw track + an activity profile into our Song dict shape."""
    title = track.get("name", "Unknown Title")
    artist_obj = track.get("artist") or {}
    artist = artist_obj.get("name") if isinstance(artist_obj, dict) else str(artist_obj)
    artist = artist or "Unknown Artist"
    url = track.get("url", "")

    seed_str = f"{title}|{artist}|{tag}".lower()
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    feats = _synthesize_features(profile, tag, seed)

    track_id = -(abs(seed) % 1_000_000) - 1

    return {
        "id": track_id,
        "title": title,
        "artist": artist,
        "genre": profile.favorite_genre,
        "mood": profile.favorite_mood,
        "energy": feats["energy"],
        "tempo_bpm": 100.0 + (seed % 60),
        "valence": feats["valence"],
        "danceability": feats["danceability"],
        "acousticness": feats["acousticness"],
        "instrumentalness": feats["instrumentalness"],
        "language": "English",
        "era": "2026",
        "_source": "lastfm",
        "_lastfm_url": url,
        "_lastfm_tag": tag,
    }


def load_csv_seed() -> List[Dict]:
    """Load the local CSV catalog. Returns [] if the file is missing."""
    if not CSV_PATH.exists():
        logger.warning("CSV seed missing path=%s", CSV_PATH)
        return []
    songs = load_songs(str(CSV_PATH))
    for s in songs:
        s["_source"] = "csv"
    return songs


def fetch_candidates(
    profile: AudioFeatureTarget,
    use_lastfm: bool = True,
    per_tag_limit: int = 15,
    client: Optional[LastFmClient] = None,
) -> tuple[List[Dict], Dict[str, int]]:
    """
    Build the candidate pool for a given activity profile.

    Returns (candidates, source_counts). source_counts is e.g.
    {"lastfm": 30, "csv": 60} for the pipeline trace.
    """
    candidates: List[Dict] = []
    seen: set[tuple[str, str]] = set()
    source_counts: Dict[str, int] = {"lastfm": 0, "csv": 0}

    if use_lastfm:
        client = client or LastFmClient()
        if client.is_configured or any(_cache_path(t, per_tag_limit).exists() for t in profile.lastfm_tags):
            for tag in profile.lastfm_tags:
                tracks = client.get_top_tracks_by_tag(tag, limit=per_tag_limit)
                for idx, raw in enumerate(tracks):
                    song = _lastfm_to_song_dict(raw, profile, tag, idx)
                    key = (song["title"].lower(), song["artist"].lower())
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append(song)
                    source_counts["lastfm"] += 1

    csv_songs = load_csv_seed()
    for song in csv_songs:
        key = (song["title"].lower(), song["artist"].lower())
        if key in seen:
            continue
        seen.add(key)
        candidates.append(song)
        source_counts["csv"] += 1

    return candidates, source_counts
