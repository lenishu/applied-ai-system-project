"""
StudyVibe pipeline orchestrator.

Five deterministic, observable steps:
  1. Parse Intent  - keyword classifier with confidence
  2. Resolve       - look up activity profile, build user_prefs
  3. Retrieve      - fetch candidates from Last.fm + CSV
  4. Rerank        - existing recommend_songs (UNCHANGED)
  5. Explain       - templated explanation grounded in score reasons

Each step is recorded as a PipelineStep so the UI can show its input,
output, and latency. Logged to logs/studyvibe.log.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import activities
    from . import guardrails
    from . import catalog
    from .recommender import recommend_songs, score_song
except ImportError:
    import activities
    import guardrails
    import catalog
    from recommender import recommend_songs, score_song


# ─── Logging setup ───────────────────────────────────────────────────────────

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_PATH = LOG_DIR / "studyvibe.log"

_logger_configured = False


def _configure_logger() -> logging.Logger:
    global _logger_configured
    logger = logging.getLogger("studyvibe")
    if _logger_configured:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    fh = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=512_000, backupCount=2, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh.setLevel(logging.WARNING)
    logger.addHandler(sh)

    _logger_configured = True
    return logger


logger = _configure_logger()


# ─── Pipeline data structures ────────────────────────────────────────────────

@dataclass
class PipelineStep:
    name: str
    input: Any
    output: Any
    latency_ms: float
    note: Optional[str] = None


@dataclass
class PipelineResult:
    steps: List[PipelineStep] = field(default_factory=list)
    recommendations: List[Dict] = field(default_factory=list)
    intent: Optional[Dict] = None
    user_prefs: Optional[Dict] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "steps": [
                {
                    "name": s.name,
                    "input": s.input,
                    "output": s.output,
                    "latency_ms": round(s.latency_ms, 2),
                    "note": s.note,
                }
                for s in self.steps
            ],
            "recommendations": self.recommendations,
            "intent": self.intent,
            "user_prefs": self.user_prefs,
            "error": self.error,
        }


# ─── Step 1: Parse Intent ────────────────────────────────────────────────────

def parse_intent(
    free_text: str,
    explicit_section: Optional[str] = None,
    explicit_mood: Optional[str] = None,
) -> Tuple[Dict, PipelineStep]:
    """
    If the user picked a (section, mood) explicitly, use it (confidence=1.0).
    Otherwise classify the free text. Either way, returns a validated IntentSchema.
    """
    t0 = time.perf_counter()
    free_text = guardrails.validate_input_length(free_text)

    if explicit_section and explicit_mood:
        guardrails.validate_section_mood(explicit_section, explicit_mood)
        section, mood, confidence = explicit_section, explicit_mood, 1.0
        scores: Dict[Tuple[str, str], int] = {}
        fallback_used, fallback_reason = False, None
        note = "explicit selection from UI"
    else:
        section, mood, confidence, scores = activities.classify(free_text)
        section, mood, fallback_used, fallback_reason = guardrails.apply_low_confidence_fallback(
            section, mood, confidence
        )
        note = f"keyword classifier (confidence={confidence:.2f})"
        if fallback_used:
            note += " | fallback applied"

    intent = guardrails.IntentSchema(
        section=section,
        mood=mood,
        confidence=confidence,
        free_text=free_text,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
    )

    step = PipelineStep(
        name="1_parse_intent",
        input={"free_text": free_text, "explicit_section": explicit_section, "explicit_mood": explicit_mood},
        output={
            "section": intent.section,
            "mood": intent.mood,
            "confidence": round(intent.confidence, 3),
            "fallback_used": intent.fallback_used,
            "fallback_reason": intent.fallback_reason,
            "score_breakdown": {f"{s}.{m}": v for (s, m), v in scores.items()},
        },
        latency_ms=(time.perf_counter() - t0) * 1000,
        note=note,
    )
    return intent.model_dump(), step


# ─── Step 2: Resolve Activity ────────────────────────────────────────────────

def resolve_activity(intent: Dict, language: str, era: str) -> Tuple[Dict, PipelineStep]:
    t0 = time.perf_counter()
    profile = activities.get_profile(intent["section"], intent["mood"])
    user_prefs = activities.to_user_prefs(profile, language=language, era=era)
    user_prefs = guardrails.clamp_prefs(user_prefs)

    step = PipelineStep(
        name="2_resolve_activity",
        input={"section": intent["section"], "mood": intent["mood"], "language": language, "era": era},
        output={
            "user_prefs": user_prefs,
            "lastfm_tags": list(profile.lastfm_tags),
            "instrumentalness_min": profile.instrumentalness_min,
            "display_name": profile.display_name,
        },
        latency_ms=(time.perf_counter() - t0) * 1000,
    )
    return user_prefs, step


# ─── Step 3: Retrieve Catalog ────────────────────────────────────────────────

def retrieve_catalog(
    intent: Dict, use_lastfm: bool, lastfm_client: Optional[catalog.LastFmClient] = None
) -> Tuple[List[Dict], PipelineStep]:
    t0 = time.perf_counter()
    profile = activities.get_profile(intent["section"], intent["mood"])
    candidates, source_counts = catalog.fetch_candidates(
        profile, use_lastfm=use_lastfm, client=lastfm_client
    )

    note = None
    if source_counts.get("lastfm", 0) == 0 and use_lastfm:
        note = "Last.fm returned 0 results - using CSV seed only"

    step = PipelineStep(
        name="3_retrieve_catalog",
        input={
            "tags": list(profile.lastfm_tags),
            "use_lastfm": use_lastfm,
            "instrumentalness_min": profile.instrumentalness_min,
        },
        output={
            "total_candidates": len(candidates),
            "source_counts": source_counts,
        },
        latency_ms=(time.perf_counter() - t0) * 1000,
        note=note,
    )

    if profile.instrumentalness_min > 0:
        before = len(candidates)
        candidates = [s for s in candidates if s.get("instrumentalness", 0) >= profile.instrumentalness_min]
        step.output["after_instrumentalness_filter"] = len(candidates)
        step.output["filter_dropped"] = before - len(candidates)

    return candidates, step


# ─── Step 4: Rerank (uses existing recommend_songs unchanged) ────────────────

def rerank(user_prefs: Dict, candidates: List[Dict], k: int = 5) -> Tuple[List[Tuple[Dict, float, str]], PipelineStep]:
    t0 = time.perf_counter()

    if not candidates:
        step = PipelineStep(
            name="4_rerank",
            input={"k": k, "candidate_count": 0},
            output={"top_k": []},
            latency_ms=(time.perf_counter() - t0) * 1000,
            note="no candidates to rerank",
        )
        return [], step

    ranked = recommend_songs(user_prefs, candidates, k=k)

    step = PipelineStep(
        name="4_rerank",
        input={"k": k, "candidate_count": len(candidates)},
        output={
            "top_k": [
                {"title": s["title"], "artist": s["artist"], "score": round(score, 2)}
                for (s, score, _) in ranked
            ],
        },
        latency_ms=(time.perf_counter() - t0) * 1000,
        note="uses existing recommend_songs (unchanged)",
    )
    return ranked, step


# ─── Step 5: Explain (templated, no LLM) ─────────────────────────────────────

def explain(
    ranked: List[Tuple[Dict, float, str]], intent: Dict
) -> Tuple[List[Dict], PipelineStep]:
    t0 = time.perf_counter()
    profile = activities.get_profile(intent["section"], intent["mood"])

    out: List[Dict] = []
    for song, score, reason_text in ranked:
        # reason_text may arrive as a list of reasons (from score_song) or a
        # joined string (from recommend_songs). Normalize to string.
        if isinstance(reason_text, list):
            reason_text = "\n".join(reason_text)
        matched_signals = [line for line in reason_text.split("\n") if line.startswith("[MATCH]")]
        feature_lines = [line for line in reason_text.split("\n") if "=>" in line]
        positive_features = [
            line.split(":")[0].strip()
            for line in feature_lines
            if "+" in line.split("=>")[-1] and float(line.split("+")[-1].strip()) >= 0.7
        ]

        bits = [f"Fits **{profile.display_name}**"]
        if matched_signals:
            bits.append("matches " + ", ".join(s.replace("[MATCH] ", "").lower() for s in matched_signals[:2]))
        if positive_features:
            bits.append("close on " + " & ".join(positive_features[:2]).lower())
        explanation_one_line = "; ".join(bits) + "."

        out.append({
            "id": song.get("id"),
            "title": song["title"],
            "artist": song["artist"],
            "genre": song.get("genre", ""),
            "language": song.get("language", ""),
            "era": song.get("era", ""),
            "score": round(score, 2),
            "max_score": 17.5,
            "score_pct": round((score / 17.5) * 100, 1),
            "explanation_one_line": explanation_one_line,
            "explanation_full": reason_text,
            "source": song.get("_source", "csv"),
            "lastfm_url": song.get("_lastfm_url"),
            "audio_features": {
                "energy": song.get("energy"),
                "valence": song.get("valence"),
                "danceability": song.get("danceability"),
                "acousticness": song.get("acousticness"),
                "instrumentalness": song.get("instrumentalness"),
            },
        })

    step = PipelineStep(
        name="5_explain",
        input={"top_k_count": len(ranked)},
        output={"explanations_generated": len(out), "method": "templated (deterministic)"},
        latency_ms=(time.perf_counter() - t0) * 1000,
    )
    return out, step


# ─── Pipeline orchestrator ───────────────────────────────────────────────────

def run_pipeline(
    free_text: str = "",
    section: Optional[str] = None,
    mood: Optional[str] = None,
    language: str = "English",
    era: str = "2026",
    use_lastfm: bool = True,
    k: int = 5,
    lastfm_client: Optional[catalog.LastFmClient] = None,
) -> PipelineResult:
    """Top-level entry point. Returns PipelineResult with full trace."""
    result = PipelineResult()
    t0 = time.perf_counter()

    try:
        intent_dict, step1 = parse_intent(free_text, section, mood)
        result.steps.append(step1)
        result.intent = intent_dict

        user_prefs, step2 = resolve_activity(intent_dict, language, era)
        result.steps.append(step2)
        result.user_prefs = user_prefs

        candidates, step3 = retrieve_catalog(intent_dict, use_lastfm, lastfm_client)
        result.steps.append(step3)

        ranked, step4 = rerank(user_prefs, candidates, k=k)
        result.steps.append(step4)

        explanations, step5 = explain(ranked, intent_dict)
        result.steps.append(step5)
        result.recommendations = explanations

        total_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "pipeline ok section=%s mood=%s confidence=%.2f n=%d total_ms=%.1f",
            intent_dict["section"], intent_dict["mood"], intent_dict["confidence"],
            len(explanations), total_ms,
        )

    except guardrails.GuardrailError as e:
        result.error = f"GuardrailError: {e}"
        logger.warning("pipeline guardrail layer=%s msg=%s", e.layer, e.message)
    except Exception as e:
        result.error = f"{type(e).__name__}: {e}"
        logger.exception("pipeline failed")

    return result


if __name__ == "__main__":
    res = run_pipeline(
        free_text="cramming for my calc final tomorrow morning",
        use_lastfm=False,
        k=3,
    )
    print(json.dumps(res.to_dict(), indent=2, default=str))
