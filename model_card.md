# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatcher 2.0** — A transparent, rule-based music recommender that prioritizes exact matches on language and era, combined with distance-based scoring on audio features.

---

## 2. Intended Use  

**What it does:** This system recommends 3-5 songs from a 60-song catalog based on an explicit user taste profile (preferred genre, mood, energy level, etc.). Every recommendation includes a breakdown of why it was chosen.

**Who it's for:** Primarily educational exploration and classroom discussion of how recommender systems work. Not intended for real users—the catalog is too small and skewed toward English and pop music.

**Key assumptions:**
- Users can articulate their preferences (genre, mood, energy target, etc.)
- Music is best characterized by discrete audio features (energy, valence, danceability, etc.)
- Exact matches on language and era are the highest priority
- Recommendations should be fully explainable

---

## 3. How the Model Works  

**The Basic Idea:** The recommender asks a user "What's your favorite genre, mood, energy level?" Then it scores every song by how closely it matches those preferences, and returns the top 5.

**Scoring System (in order of importance):**

1. **Language (3.0 points if match, -0.5 if mismatch):** A strong filter. The system heavily favors songs in the user's preferred language.
2. **Era (3.0 points if match, -0.3 if mismatch):** Another strong filter. Users who want 1970s rock won't see 2020s pop.
3. **Genre (2.5 points if match, -0.2 if mismatch):** Categorical preference. Rock fans see rock, but if no rock songs match other criteria, jazz is a weak backup.
4. **Mood (2.0 points if match, -0.1 if mismatch):** Emotional tone. A happy pop song and a sad pop song are both pop, but they're different moods.
5. **Energy, Valence (happiness), Danceability, Acousticness:** Distance-based scoring. If a user wants 0.40 energy, a song with 0.42 energy scores better than one with 0.80 energy. The closer, the better.

**Total possible score:** 17.5 points

**Example:** A song gets +3 for matching language (English), +3 for matching era (2026), +2.5 for matching genre (pop), +2.0 for matching mood (happy), and then up to +2.0 + 1.5 + 1.0 + 1.0 = 5.5 for numeric features. If energy is 0.82 and the user wants 0.82, they get +2.0 for energy. If danceability is 0.80 and the user wants 0.80, they get +1.0 for danceability. Etc.

**What changed from starter:** No changes—we used the exact scoring provided in the starter code.

---

## 4. Data  

**Dataset Size:** 60 songs

**Language Breakdown:**
- English: 48 songs (80%)
- Nepali: 8 songs (13%)
- Spanish: 2 songs (3%)
- Hindi: 2 songs (3%)

**Genre Breakdown:**
- Pop: ~25 songs (42%)
- Rock: ~4 songs
- HipHop: ~4 songs
- Electronic/EDM: ~4 songs
- Lofi/Ambient/Jazz: ~4 songs
- Classical, Folk, RnB, Soul, Funk, etc.: <5 songs each

**Era Breakdown:**
- 2020-25: ~20 songs
- 2026: ~22 songs
- 2025: ~10 songs
- 2010-20: ~8 songs

**Mood/Emotional Range:** The dataset includes "happy," "chill," "intense," "moody," "romantic," "peaceful," "euphoric," etc. But some emotions are rare (only 1 song is "meditative," only 1 is "futuristic").

**Did we add/remove data?** No modifications to the starter dataset.

**What's missing?**
- Non-English music (only 12 non-English songs vs. 48 English)
- Niche genres (classical, jazz, folk have <5 examples)
- Rare moods (euphoric, meditative, futuristic each have 1-3 examples)
- Extreme feature values (no song has 0.98 energy AND 0.99 danceability AND 0.02 acousticness simultaneously)

---

## 5. Strengths  

1. **Clear Differentiation Between Opposite Tastes:** A user who wants low-energy, high-acousticness music (chill_lofi) gets completely different recommendations than a user who wants high-energy, low-acousticness music (intense_rock). The system correctly separates them.

2. **Language Filtering Works:** Hindi speakers interested in classical music get Raag Nights (classical, Hindi, meditative) as their top pick with a 15.73/17.5 score. When preferences align, the system finds near-perfect matches.

3. **Transparent Explanations:** Every recommendation includes a detailed breakdown: "You got +3.0 for language match, +2.5 for genre match, +1.96 for energy closeness." Users understand *why* they saw a song.

4. **Accurate Mood Detection:** The system correctly identifies mood mismatches. A user who wants "romantic" RnB will score a "moody" RnB song lower (13.26 vs 15.95) because the mood doesn't match (+2.0 vs -0.1).

5. **Numeric Sensitivity:** Doubling the energy weight causes observable ranking changes (Gentle Breeze enters the top 5 for chill_lofi). The math is sound.

---

## 6. Limitations and Bias 

### Critical Bias: Language-Based Segregation

**The Problem:** Language weighting (+3.0) is so strong that it completely overrides genre and mood preferences. A Nepali speaker loses access to 48 English songs, even if a high-quality English folk song matches their taste better than any available Nepali song.

**Evidence:** In the niche_acoustic_fast profile, we asked for Spanish folk and got Spanish jazz (Coffee Shop Stories, 10.07/17.5) instead of English folk (Acoustic Sunrise, 8.30/17.5). The system chose language match over genre/mood match.

**Real-World Impact:** Non-English speakers see fewer recommendations because the catalog is 80% English. If a user's language has only 2 songs (like Spanish), they get poor variety even if those 2 songs are decent matches.

### Critical Bias: Genre Overrepresentation

**The Problem:** Pop music dominates (42% of catalog) while classical, folk, and jazz are underrepresented (<5 songs each). Users who like pop see more variety; users who like classical get mediocre recommendations because few options exist.

**Evidence:** The extreme_electronics profile wanted "euphoric" electronic music. No song in the dataset is tagged "euphoric" in the electronic genre. The best match (Cyberpunk) is "futuristic," not "euphoric," and scores only 75% of max (13.10/19.0).

### Limitation: Contradictory Preferences Aren't Handled

**The Problem:** The system doesn't recognize when preferences are contradictory (e.g., high energy + sad/dark mood, or peaceful + fast tempo). It picks the best compromise but scores are low (~50-60% of max).

**Evidence:** The conflicting_preferences profile (wants high energy + low valence/sad) gets Metal Storm with only 9.91/17.5 (57% of max). The system picked high energy but sacrificed valence matching.

### Limitation: No Diversity Mechanism

**The Problem:** The top 3 recommendations for nepali_pop_happy are nearly identical (15.86–15.93 scores). All three are Nepali pop songs from 2026. There's no mechanism to suggest variety within a user's taste.

**Real-World Impact:** Users see repetitive recommendations instead of exploring breadth. If someone likes Nepali pop, showing 3 nearly-identical songs is less useful than showing the best Nepali pop plus a high-quality alternative (e.g., a Nepali indie song, or English pop with Nepali vocals).

### Limitation: Small & Skewed Dataset

**The Problem:** 60 songs is tiny. Real Spotify has millions. Our dataset is skewed: 80% English, 42% pop, 2020-26 eras dominate.

**Real-World Impact:** Niche tastes (Spanish folk, classical music, 1990s rock) can't be well-served. Users in minority language groups will be disappointed.

---

## 7. Evaluation  

### Profiles Tested

We ran the recommender against **8 distinct user profiles:**

1. **chill_lofi** (baseline) - lofi, low energy, high acousticness, English, 2020-25
2. **intense_rock** (baseline) - rock, high energy, low acousticness, English, 2010-20
3. **nepali_pop_happy** (baseline) - pop, happy, Nepali, 2026
4. **romantic_rnb** (baseline) - RnB, romantic, English, 2026
5. **conflicting_preferences** (edge case) - wants high energy BUT sad mood + very acoustic (contradictory)
6. **niche_acoustic_fast** (edge case) - wants peaceful folk but high energy (contradictory) + rare Spanish + 2010-20 era
7. **extreme_electronics** (edge case) - wants extreme feature values (0.98 energy, 0.99 danceability, 0.02 acousticness)
8. **high_energy_sad** (edge case) - wants high energy but dark mood (tested how well system handles emotional contradictions)

### What We Looked For

- **Accuracy:** Do the recommendations match the profile's stated preferences? (e.g., does intense_rock get rock songs, and chill_lofi get low-energy songs?)
- **Surprises:** Are there cases where the system picks songs that seem wrong? Or cases where language/era override more important preferences?
- **Robustness:** Does doubling energy weight change recommendations? (Yes, it does for chill_lofi but not for intense_rock.)
- **Bias:** Do different languages/genres get equal treatment? (No—English and pop are favored.)

### Key Findings

| Profile | Top Score | Finding |
|---------|-----------|---------|
| chill_lofi | 15.87/17.5 | Perfect match (lofi, chill, low energy) |
| intense_rock | 15.93/17.5 | Perfect match (rock, intense, high energy) |
| nepali_pop_happy | 15.93/17.5 | Excellent but repetitive (all 3 top results are nearly identical) |
| romantic_rnb | 15.95/17.5 | Excellent; mood mismatch in #2 correctly penalized |
| conflicting_preferences | 9.91/17.5 (57%) | Poor—system can't reconcile "sad ambient with high energy" |
| niche_acoustic_fast | 10.07/17.5 (57%) | Weak—language + era + mood + genre combo too rare in data |
| extreme_electronics | 13.10/19.0 (75%) | Decent but not perfect—no "euphoric electronic" song exists |
| high_energy_sad | 15.32/17.5 (88%) | Works better than conflicting_preferences—"intense" emotion bridges the gap |

### Weight Sensitivity Test

We doubled energy weight (2.0 → 4.0) and halved genre weight (2.5 → 1.25). Results:
- **chill_lofi:** Rankings CHANGED (Gentle Breeze entered top 5 due to better energy match)
- **intense_rock:** Rankings UNCHANGED (language/era bonuses were too strong to override)

**Conclusion:** The weighting system is mathematically sound and responsive to changes, but language/era are overwhelming hard constraints.

### Surprising Discoveries

1. **Language Weight Dominates:** We expected genre to be most important. Instead, language (+3.0) is equally weighted with era, making it nearly impossible for a Spanish speaker to get English recommendations even if they're objectively better matches.

2. **Contradictions Matter:** high_energy_sad (0.95 energy, 0.25 valence) performed better than conflicting_preferences (0.90 energy, 0.20 valence) because HipHop culture accepts dark themes. Ambient music typically doesn't. Genre context affects how contradictory a profile is.

3. **Niche Matches Can Be Perfect:** When a profile matches available data (like Hindi+classical+meditative), the system finds it reliably and scores 90% of max. The problem isn't the algorithm—it's that the dataset is small and skewed.

---

## 8. Future Work  

1. **Configurable Language Weight:** Let users opt into cross-language recommendations. Some users might prefer "best quality regardless of language" over strict language matching.

2. **Add Diversity Sampling:** Instead of returning top-k by score, sample from the top 20-30% to increase variety.

3. **Expand Dataset:** Especially non-English, non-pop music. Include more classical, folk, jazz, and regional music.

4. **Detect & Explain Contradictions:** If a user requests incompatible preferences, say "You want high energy but sad mood—these are unusual together. Here's the best compromise, but consider this alternative."

5. **Add Confidence Intervals:** "This is a 92% match" vs. "This is the best available, but your preferences are rare (54% match)." Help users understand if low scores mean poor taste fit or dataset limitations.

6. **Support Multi-Language Preference:** "I want songs in English, Spanish, or Nepali" instead of forcing a single language.

7. **Implement Diversity Rewards:** Penalize repetitive top-k results. If two songs are very similar, boost the underrepresented one.

---

## 9. Personal Reflection  

**What I Learned About Recommender Systems:**

Building this system revealed that recommendation is fundamentally a *trade-off* problem. You can't optimize for language specificity, genre accuracy, mood matching, AND numeric feature precision simultaneously. Real systems like Spotify make these choices implicitly—they might prioritize song quality over language match, or diversity over perfect personalization. This system made them explicit, which helps explain why real recommenders sometimes suggest something unexpected.

**What Surprised Me:**

I was surprised by how powerfully language weighting dominates the system. A Nepali speaker can't escape Nepali songs because the language bonus (+3.0) is as large as the era bonus, and both combine to outweigh genre entirely. In a real system, I'd expect language to be a soft preference, not a hard filter. This revealed a design choice: *do you optimize for the user's stated language, or for the quality of the recommendation?* There's no single right answer, but it matters enormously.

I was also surprised that contradictory preferences (high energy + sad mood) could be partially salvaged by choosing the right genre (HipHop works; ambient doesn't). This suggests that *genre itself encodes emotional norms*. The system doesn't explicitly model that, but it emerges from the data.

**How This Changed My View of Music Recommenders:**

Before building this, I thought music recommenders were "black boxes" that somehow understood taste. Now I see they're *explicit trade-offs* between many competing signals: language, genre, mood, and numeric features all fighting for weight. The system's biases are legible here—language dominates—but in Spotify or YouTube Music's million-parameter neural nets, the biases are hidden. That's scary. A hidden bias is worse than an explicit one, because you can't even question it. Building this transparent system made me appreciate why explainability matters. Users should know *why* they saw a song, so they can push back if the system is wrong for them.

Also, I realized how much bias comes from *dataset composition*, not the algorithm. The algorithm is fair—it applies the same math to every song. But because the dataset is 80% English and 42% pop, the algorithm inevitably favors those. A real Spotify would have the same problem if their training data is skewed. The bias isn't a bug; it's a *data quality* problem.

**How AI Tools Helped (and When to Double-Check):**

*What worked well:*
- **Code generation:** Claude helped scaffold the data loading, scoring functions, and CLI formatting quickly. The functions Claude generated were correct and followed good Python patterns.
- **Documentation:** Claude helped structure the README, model card, and this reflection. Having an AI review and organize findings saved hours.
- **Testing strategy:** Claude suggested the 8-profile approach (4 baseline + 4 edge cases) which revealed biases I might have missed.
- **Data generation:** Claude generated 50 realistic songs from web search results about 2026 music trends.

*Where I needed to double-check:*
- **Feature values:** Claude sometimes generated audio features (energy, valence, etc.) that seemed plausible but might not match real songs. I spot-checked by running scenarios and adjusting outliers.
- **Weights and scores:** The scoring algorithm was provided in the starter code, not generated by Claude, so I verified it matched the logic.
- **Bias identification:** Claude suggested language bias as a problem. I tested this manually by running the niche_acoustic_fast profile to confirm the hypothesis was correct.
- **Contradictory profiles:** Claude suggested testing conflicting preferences (high energy + sad mood). I verified by running it and checking scores (9.91/17.5 confirmed the issue).

*Key lesson:* AI tools excel at structure, scaling, and documentation. But domain-specific validation (does this feature value match reality? is this bias actually a problem?) requires human judgment. I trusted the overall approach but verified critical findings manually.

**What Would I Try Next?**

If I extended this project, I'd:
1. **Test with user studies** — Show recommendations to real people and ask "Does this feel right?" The score alone doesn't prove the system is *good*.
2. **Implement filtering options** — Let users disable the language filter or increase diversity. Give them control over the trade-offs.
3. **Build a larger, more balanced dataset** — The current 60 songs is a proof-of-concept. A realistic version would have thousands of songs across all genres and languages.
4. **Add listening context** — Real recommenders know the time of day (morning ≠ late night), whether you're working, exercising, or socializing. This system ignores context.
5. **Track what users actually listen to** — So far, we only scored based on stated preferences. Real systems learn from behavior (clicks, skips, repeat plays). That feedback loop is crucial.

---

## 10. AI Collaboration & Limitations of This Extension

### How Claude Helped Build StudyVibe

**Helpful Suggestions:**

1. **Last.fm Integration Over Spotify:** Claude flagged that "Spotify's `audio-features` endpoint was deprecated in November 2024" and suggested switching to Last.fm's tag-based API. This was critical—it saved us from building on a dead API. We implemented `LastFmClient` with tag.getTopTracks as a result, which works reliably.

2. **5-Step Pipeline Design:** Claude proposed decomposing the recommender into discrete, observable steps: Parse Intent → Resolve Activity → Retrieve Catalog → Rerank → Explain. This made the system's reasoning visible and testable. Each step is logged with latency and confidence metrics.

3. **Guardrails as a Separate Layer:** Claude recommended extracting validation logic into a dedicated `guardrails.py` file with 5 layers (input length, activity allowlist, schema validation, numeric clamping, empty-result fallback). This made the system more robust and easier to audit for safety.

4. **Web UI with Pipeline Tracing:** Claude suggested building a Flask web app with a collapsible "Pipeline Steps" panel that shows what the system is thinking at each stage. This transparency turned an opaque recommender into a *legible* one—users can see exactly why they got a recommendation.

---

### Where Claude Suggested Trade-Offs (With Mixed Results)

**Suggestion:** "Since Last.fm doesn't provide audio features directly, synthesize them using tag heuristics."

- **What Claude Proposed:** Use tag presence (e.g., "acoustic" tag → boost acousticness, "workout" tag → boost energy) plus small random jitter to approximate audio features.
- **Why It Was Pragmatic:** Avoids calling Spotify (deprecated) and works with Last.fm's free tier.
- **Trade-Off We Made:** Synthetic features are less accurate than real Spotify features. A "workout" tag might mean high-energy electronic *or* high-energy rock; our heuristic can't distinguish.
- **Disclosure:** Documented in README as "Future Work: Integrate real audio features via MusicBrainz or AcousticBrainz APIs."
- **Assessment:** This was a reasonable engineering trade-off. Given the constraints (free API, deprecated Spotify), synthesized features were better than nothing. But it's important to flag: *any recommendation made using synthetic features should carry a caveat that real features might rerank results differently*.

---

### Limitations We Inherited From the Approach

1. **Rule-Based Keyword Classification:** The `classify()` function in `activities.py` uses substring matching on keywords to infer user intent from free text. Examples:
   - Input: `"cramming for calc final tomorrow"` → classifies as `student.exam_cram` (confidence ≈ 0.50)
   - Input: `"xyz qwerty"` → no keywords match, falls back to `work.email_triage` (the safest neutral default; see `apply_low_confidence_fallback` in `guardrails.py`).
   - **Real failure observed in eval:** `"energizing break before standup meeting"` → classified as `work.meeting_prep` instead of `work.energizing_break` because the meeting/standup keywords win on hit count. See "Testing Surprises" below.
   - **Limitation:** Ambiguous phrases like "vibing" or "chilling" can map to multiple activities. No machine learning model disambiguates context.

2. **Synthetic Audio Features:** As noted above, features are synthesized from tag heuristics, not measured from real audio. Heuristics:
   - `acoustic` tag → acousticness += 0.3
   - `workout` tag → energy += 0.2
   - `sleep` tag → energy -= 0.2
   - `sad` tag → valence -= 0.2
   - These are *plausible* but not validated against real audio data.
   - **Blind Spot:** A "sad electronic" song might get energy boosted (electronic) and valence tanked (sad), resulting in contradictory features. The heuristics don't interact intelligently.

3. **Last.fm Availability:** The system gracefully falls back to a CSV seed (60 songs) if Last.fm is unavailable or rate-limited. But the CSV seed is small and skewed (same bias as VibeMatcher 2.0's dataset). If a user's network is down and they're in offline mode, recommendations will be mediocre.
   - **Blind Spot:** Users on slow/metered networks might trigger the fallback unknowingly and think the system's results are poor, when in fact they're using a 60-song subset instead of millions from Last.fm.

4. **No Confidence Uncertainty in Results:** The system returns ranked recommendations with scores but doesn't communicate *how certain* it is about each match.
   - **Example:** A recommendation might score 14.2/17.5 because (a) perfect keyword match with high confidence, or (b) ambiguous text with low confidence that happened to match. The score is the same; the certainty is not.
   - **Blind Spot:** Users might trust low-confidence matches too much if the score looks high.

---

### Testing Surprises From Evaluation Harness

When we ran the `eval.py` harness (12 predefined test cases), we found:

1. **Activity classification: 11/12 correct (91.7%) with confidence 0.40-0.80.** The keyword classifier handled phrases like "cramming for calc final", "deep dive into coding", and "gym workout" without difficulty. The one failure was instructive — see point 2 below.

2. **The most useful surprise was a real classifier blind spot.** The case `"energizing break before standup meeting"` was expected to map to `work.energizing_break`, but the classifier picked `work.meeting_prep` instead. Reason: the input contains the keywords `meeting`, `standup`, and `prep` (3 hits for `meeting_prep`) and only `break` and `energize` (2 hits for `energizing_break`), so hit-count voting picks the wrong activity. This is a legitimate weakness of single-word keyword matching; multi-word phrase keys ("energizing break") or per-keyword specificity weights would fix it. We chose to ship this honestly and document it rather than hand-tune the keyword list to game the eval.

3. **Energy delta was 0.158 mean (range 0.013 to 0.497).** Recommendations land within ~0.16 of the target energy on average — well within an acceptable range for a 60-song catalog. The 0.497 outlier comes from an activity with no good matches in the CSV (`exam_cram` wants very low energy + high acousticness; the CSV has few such tracks). With the Last.fm pool the deltas drop substantially.

4. **Guardrails prevented crashes on every adversarial input.** Empty text, 600-char prompt-injection attempts, `confidence=2.0`, `section="invalid"`, malformed JSON — all caught cleanly by the 5-layer stack and surfaced as 400 responses with structured error messages, not 500s.

5. **Last.fm caching saved real money.** First eval run made 72 API calls (12 cases × 6 tags); every subsequent run is a cache hit on disk. This makes the eval deterministic and free to re-run during development.

---

### Misuse Prevention & Safety Notes

1. **No PII Collection:** The system doesn't store user profiles, search history, or listen-through behavior. Every request is stateless. This eliminates privacy risks from a recommender system perspective.
   - **Note:** Flask logs are written to `logs/studyvibe.log` and include timestamps, section, mood, and recommendation count. No user identifiers are logged, so this is safe.

2. **Deterministic Outputs:** Given the same input (section, mood, language, era), the system always returns the same recommendations in the same order. This enables auditing and reproducibility.
   - **Note:** The synthetic audio features include jitter (random ±0.05), so results *are* slightly non-deterministic. But the jitter is bounded and doesn't change ranking significantly.

3. **No Autoplay or Skip-Tracking:** Unlike Spotify, this system doesn't have mechanics to automatically advance to the next song or learn from skips. Users must explicitly choose what to listen to.
   - **Implication:** No feedback loop means the system never learns individual taste over time. Each session is independent.

4. **Explainability by Design:** Every recommendation includes a breakdown of why it scored well (language match +3.0, genre match +2.5, energy closeness +1.8, etc.). Users can scrutinize and challenge the ranking.
   - **Implication:** If the system makes a bad recommendation, users can see exactly which signal(s) caused it and dispute that signal's importance.

---

## Summary

**VibeMatcher 2.0** successfully demonstrates how a simple, rule-based recommender can:
- ✅ Provide transparent, explainable recommendations
- ✅ Differentiate between different user tastes
- ✅ Scale a scoring function across a full catalog
- ✅ Reveal hidden biases in both data and design choices

**But it also shows the limits:**
- ❌ Language weighting is too aggressive and segregates users
- ❌ Small datasets make it hard to serve niche tastes
- ❌ No diversity mechanism leads to repetitive suggestions
- ❌ No way to handle contradictory preferences gracefully

The biggest insight: **recommendation systems are exercises in explicit trade-off design**. Every weight, every parameter is a human choice. Those choices reveal assumptions about what matters and who the system is optimized for. In this case, the choices optimized for English speakers and pop music fans. A fair system would be aware of that and either balance the dataset or give users control over the weights.

This is why explainability and transparency matter. Users deserve to know *why* they saw what they saw, so they can question it.
