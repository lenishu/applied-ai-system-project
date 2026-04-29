/**
 * StudyVibe Frontend
 * Modern UI with gradient album art, score bars, and pipeline timeline.
 */

let currentSection = "student";
let selectedMood = null;

// Mood emoji map (visual hint per mood key)
const MOOD_EMOJI = {
    exam_cram: "📖", deep_study: "🧠", light_reading: "📔",
    group_brainstorm: "👥", pre_exam_pump: "⚡",
    deep_focus_coding: "💻", email_triage: "📧", creative_brainstorm: "💡",
    meeting_prep: "📊", energizing_break: "⚡", commute: "🚇",
    workout_gym: "💪", chill_unwind: "🌿", happy_celebrate: "🎉",
    sad_reflective: "🌧", romantic: "❤️", sleep_winddown: "🌙",
};

// Album art gradient palette — varied gradients per rank for visual interest
const ART_GRADIENTS = [
    "linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)",
    "linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%)",
    "linear-gradient(135deg, #f59e0b 0%, #ec4899 100%)",
    "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)",
    "linear-gradient(135deg, #f43f5e 0%, #8b5cf6 100%)",
];

document.addEventListener("DOMContentLoaded", function () {
    initializeTabs();
    initializeEventListeners();
    renderMoodButtons();
});

// ============================================================================
// Tabs
// ============================================================================

function initializeTabs() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    tabButtons[0].classList.add("active");

    tabButtons.forEach((btn) => {
        btn.addEventListener("click", function () {
            tabButtons.forEach((b) => b.classList.remove("active"));
            this.classList.add("active");
            currentSection = this.dataset.section;
            selectedMood = null;
            renderMoodButtons();
        });
    });
}

function renderMoodButtons() {
    const container = document.getElementById("mood-buttons-container");
    container.innerHTML = "";

    const moods = window.SECTIONS_DATA[currentSection];
    Object.entries(moods).forEach(([moodKey, moodData]) => {
        const btn = document.createElement("button");
        btn.className = "mood-button";
        btn.dataset.mood = moodKey;
        btn.title = moodData.description || "";

        const emoji = MOOD_EMOJI[moodKey] || "🎵";
        btn.innerHTML = `
            <span class="mood-emoji">${emoji}</span>
            <span class="relative">${escapeHtml(moodData.display_name)}</span>
        `;

        btn.addEventListener("click", function () {
            const wasSelected = this.classList.contains("selected");
            document.querySelectorAll(".mood-button").forEach((b) => b.classList.remove("selected"));
            if (!wasSelected) {
                this.classList.add("selected");
                selectedMood = moodKey;
                // Clear free text when explicit mood is picked
                document.getElementById("free-text").value = "";
            } else {
                selectedMood = null;
            }
        });

        container.appendChild(btn);
    });
}

// ============================================================================
// Event listeners
// ============================================================================

function initializeEventListeners() {
    document.getElementById("recommend-btn").addEventListener("click", getRecommendations);
    document.getElementById("pipeline-toggle").addEventListener("click", togglePipelineDetails);

    document.getElementById("free-text").addEventListener("input", function () {
        if (this.value.trim()) {
            selectedMood = null;
            document.querySelectorAll(".mood-button").forEach((b) => b.classList.remove("selected"));
        }
    });

    // Allow Enter (with Cmd/Ctrl) to submit from textarea
    document.getElementById("free-text").addEventListener("keydown", function (e) {
        if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
            e.preventDefault();
            getRecommendations();
        }
    });

    // Click on example chips to fill free-text
    document.querySelectorAll(".example-chip").forEach((chip) => {
        chip.style.cursor = "pointer";
        chip.addEventListener("click", function () {
            document.getElementById("free-text").value = this.textContent.trim();
            selectedMood = null;
            document.querySelectorAll(".mood-button").forEach((b) => b.classList.remove("selected"));
        });
    });
}

// ============================================================================
// API
// ============================================================================

async function getRecommendations() {
    const freeText = document.getElementById("free-text").value;
    const language = document.getElementById("language").value;
    const era = document.getElementById("era").value;
    const useLastfm = document.getElementById("use-lastfm").checked;

    const payload = {
        free_text: freeText,
        section: selectedMood ? currentSection : null,
        mood: selectedMood,
        language,
        era,
        use_lastfm: useLastfm,
        k: 5,
    };

    document.getElementById("empty-state").classList.add("hidden");
    document.getElementById("results-container").classList.add("hidden");
    document.getElementById("loading").classList.remove("hidden");

    try {
        const response = await fetch("/api/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            showError(data.error || "Request failed");
            return;
        }

        renderResults(data);
    } catch (err) {
        showError(`Error: ${err.message}`);
    } finally {
        document.getElementById("loading").classList.add("hidden");
    }
}

// ============================================================================
// Render results
// ============================================================================

function renderResults(data) {
    const container       = document.getElementById("results-container");
    const recsList        = document.getElementById("recommendations-list");
    const pipelineDetails = document.getElementById("pipeline-details");
    const errorMsg        = document.getElementById("error-message");
    const intentBanner    = document.getElementById("intent-banner");

    recsList.innerHTML = "";
    pipelineDetails.innerHTML = "";
    errorMsg.classList.add("hidden");
    intentBanner.classList.add("hidden");
    intentBanner.innerHTML = "";

    if (data.error) {
        errorMsg.textContent = data.error;
        errorMsg.classList.remove("hidden");
        container.classList.remove("hidden");
        return;
    }

    // Intent banner
    if (data.intent) {
        intentBanner.className = "intent-banner";
        const moodEmoji = MOOD_EMOJI[data.intent.mood] || "🎵";
        const conf = (data.intent.confidence * 100).toFixed(0);
        const confClass = data.intent.confidence >= 0.5 ? "" : "low";
        const fallback = data.intent.fallback_used
            ? `<span class="text-yellow-300 text-xs ml-1">(fallback)</span>`
            : "";
        intentBanner.innerHTML = `
            <div class="intent-icon">${moodEmoji}</div>
            <div>
                <div class="text-xs text-white/60 uppercase tracking-wider">Detected activity</div>
                <div class="font-semibold text-white">
                    ${escapeHtml(data.intent.section)} · ${escapeHtml(data.intent.mood)}
                    ${fallback}
                </div>
            </div>
            <div class="confidence-pill ${confClass}">${conf}% conf</div>
        `;
        intentBanner.classList.remove("hidden");
    }

    // Recommendation cards
    if (data.recommendations && data.recommendations.length > 0) {
        data.recommendations.forEach((rec, idx) => {
            const card = createRecommendationCard(rec, idx + 1);
            card.style.animationDelay = `${idx * 0.06}s`;
            recsList.appendChild(card);
        });
    } else {
        const emptyMsg = document.createElement("div");
        emptyMsg.className = "glass-card p-10 text-center text-white/60";
        emptyMsg.innerHTML = `
            <div class="text-4xl mb-3 opacity-60">🤷</div>
            <div class="font-semibold text-white mb-1">No recommendations found</div>
            <div class="text-sm">Try a different activity or check the online database toggle.</div>
        `;
        recsList.appendChild(emptyMsg);
    }

    // Pipeline steps
    if (data.pipeline_steps) {
        data.pipeline_steps.forEach((step) => {
            pipelineDetails.appendChild(createPipelineStep(step));
        });
    }

    container.classList.remove("hidden");
}

function createRecommendationCard(rec, rank) {
    const card = document.createElement("div");
    card.className = "recommendation-card";

    const scorePct = rec.score_pct != null ? rec.score_pct : (rec.score / 17.5) * 100;
    const scoreClamped = Math.max(0, Math.min(100, scorePct));

    const sourceLabel = rec.source === "lastfm"
        ? `<span class="source-tag lastfm">● Last.fm</span>`
        : `<span class="source-tag csv">● Local catalog</span>`;

    const initials = (rec.title || "?")
        .split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase().slice(0, 2);

    const gradient = ART_GRADIENTS[(rank - 1) % ART_GRADIENTS.length];

    const linkHTML = rec.lastfm_url
        ? `<a href="${escapeHtml(rec.lastfm_url)}" target="_blank" rel="noopener" class="text-cyan-300 text-xs hover:underline ml-2">↗ open</a>`
        : "";

    const metaPills = [
        rec.genre,
        rec.language,
        rec.era,
    ].filter(Boolean).map(v => `<span class="meta-pill">${escapeHtml(v)}</span>`).join("");

    card.innerHTML = `
        <div class="relative" style="flex-shrink: 0;">
            <div class="rank-badge">#${rank}</div>
            <div class="album-art" style="background: ${gradient};">${escapeHtml(initials || "♪")}</div>
        </div>
        <div class="flex-1 min-w-0">
            <div class="flex items-start gap-2">
                <div class="flex-1 min-w-0">
                    <h3 class="song-title">${escapeHtml(rec.title)}</h3>
                    <div class="song-artist">${escapeHtml(rec.artist)}${linkHTML}</div>
                </div>
            </div>
            ${metaPills ? `<div class="song-meta">${metaPills}</div>` : ""}
            <div class="score-row">
                <span class="score-label">Match score</span>
                <span class="score-value">${rec.score.toFixed(1)} / 17.5 · ${scorePct.toFixed(0)}%</span>
            </div>
            <div class="score-bar"><div class="score-fill" style="width: ${scoreClamped}%"></div></div>
            <div class="explanation">${escapeHtml(rec.explanation_one_line || "")}</div>
            ${sourceLabel}
        </div>
    `;

    return card;
}

function createPipelineStep(step) {
    const div = document.createElement("div");
    div.className = "pipeline-step";

    const stepNum = step.name.split("_")[0];
    const stepLabel = {
        "1": "Parse Intent",
        "2": "Resolve Activity",
        "3": "Retrieve Catalog",
        "4": "Rerank (Score & Sort)",
        "5": "Explain",
    }[stepNum] || step.name;

    const inputJson  = JSON.stringify(step.input,  null, 2);
    const outputJson = JSON.stringify(step.output, null, 2);

    div.innerHTML = `
        <div class="step-header">
            <div class="step-num">${stepNum}</div>
            <div class="step-name">${escapeHtml(stepLabel)}</div>
            <div class="step-latency">${step.latency_ms.toFixed(1)} ms</div>
        </div>
        ${step.note ? `<div class="step-note">ℹ ${escapeHtml(step.note)}</div>` : ""}
        <details class="step-io-toggle">
            <summary>View input / output</summary>
            <div class="step-io-content">
                <div class="step-io-label">Input</div>
                <pre>${escapeHtml(inputJson)}</pre>
                <div class="step-io-label">Output</div>
                <pre>${escapeHtml(outputJson)}</pre>
            </div>
        </details>
    `;

    return div;
}

function togglePipelineDetails() {
    const details = document.getElementById("pipeline-details");
    const chevron = document.getElementById("pipeline-chevron");

    if (details.classList.contains("hidden")) {
        details.classList.remove("hidden");
        chevron.classList.add("rotated");
    } else {
        details.classList.add("hidden");
        chevron.classList.remove("rotated");
    }
}

// ============================================================================
// Utilities
// ============================================================================

function showError(message) {
    document.getElementById("loading").classList.add("hidden");
    const errorMsg = document.getElementById("error-message");
    errorMsg.textContent = message;
    errorMsg.classList.remove("hidden");
    document.getElementById("results-container").classList.remove("hidden");
    document.getElementById("empty-state").classList.add("hidden");
}

function escapeHtml(text) {
    if (text == null) return "";
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
    return String(text).replace(/[&<>"']/g, (m) => map[m]);
}
