/**
 * StudyVibe Frontend JavaScript
 * Handles UI interactions, API calls, and result rendering
 */

let currentSection = "student";
let selectedMood = null;

document.addEventListener("DOMContentLoaded", function () {
    initializeTabs();
    initializeEventListeners();
    renderMoodButtons();
});

// ============================================================================
// Tab Management
// ============================================================================

function initializeTabs() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    tabButtons[0].classList.add("active"); // Student is default

    tabButtons.forEach((btn) => {
        btn.addEventListener("click", function () {
            // Remove active class from all buttons
            tabButtons.forEach((b) => b.classList.remove("active"));

            // Add active class to clicked button
            this.classList.add("active");

            // Update current section and re-render mood buttons
            currentSection = this.dataset.section;
            selectedMood = null; // Reset mood when switching sections
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
        btn.textContent = moodData.display_name;
        btn.title = moodData.description;

        btn.addEventListener("click", function () {
            // Toggle selection
            const wasSelected = this.classList.contains("selected");
            document.querySelectorAll(".mood-button").forEach((b) => b.classList.remove("selected"));

            if (!wasSelected) {
                this.classList.add("selected");
                selectedMood = moodKey;
            } else {
                selectedMood = null;
            }
        });

        container.appendChild(btn);
    });
}

// ============================================================================
// Event Listeners
// ============================================================================

function initializeEventListeners() {
    const recommendBtn = document.getElementById("recommend-btn");
    recommendBtn.addEventListener("click", getRecommendations);

    const pipelineToggle = document.getElementById("pipeline-toggle");
    pipelineToggle.addEventListener("click", togglePipelineDetails);

    const freeTextInput = document.getElementById("free-text");
    freeTextInput.addEventListener("input", function () {
        // Clear mood selection when user types
        if (this.value.trim()) {
            selectedMood = null;
            document.querySelectorAll(".mood-button").forEach((b) => b.classList.remove("selected"));
        }
    });
}

// ============================================================================
// API Call
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

    // Show loading
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
// Render Results
// ============================================================================

function renderResults(data) {
    const container = document.getElementById("results-container");
    const recsList = document.getElementById("recommendations-list");
    const pipelineDetails = document.getElementById("pipeline-details");
    const errorMsg = document.getElementById("error-message");

    // Clear previous results
    recsList.innerHTML = "";
    pipelineDetails.innerHTML = "";
    errorMsg.classList.add("hidden");

    // Show error if present
    if (data.error) {
        errorMsg.textContent = data.error;
        errorMsg.classList.remove("hidden");
        container.classList.remove("hidden");
        return;
    }

    // Render recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        data.recommendations.forEach((rec, idx) => {
            const card = createRecommendationCard(rec, idx + 1);
            recsList.appendChild(card);
        });
    } else {
        const emptyMsg = document.createElement("div");
        emptyMsg.className = "text-center py-8 text-gray-500";
        emptyMsg.textContent = "No recommendations found for this activity.";
        recsList.appendChild(emptyMsg);
    }

    // Render pipeline steps
    if (data.pipeline_steps) {
        data.pipeline_steps.forEach((step) => {
            const stepDiv = createPipelineStep(step);
            pipelineDetails.appendChild(stepDiv);
        });
    }

    // Show results
    container.classList.remove("hidden");
}

function createRecommendationCard(rec, rank) {
    const card = document.createElement("div");
    card.className = "recommendation-card";

    const scorePercent = rec.score_pct || Math.round((rec.score / 17.5) * 100);
    const sourceLabel = rec.source === "lastfm" ? "🌐 Last.fm" : "💾 Local";

    card.innerHTML = `
        <div class="flex items-start justify-between">
            <div class="flex-1">
                <div class="text-sm text-gray-500">#{rank}</div>
                <div class="song-title">${escapeHtml(rec.title)}</div>
                <div class="song-artist">${escapeHtml(rec.artist)}</div>
                <div class="text-xs text-gray-500 mt-2">
                    ${rec.genre ? rec.genre : ""}
                    ${rec.language ? `· ${rec.language}` : ""}
                    ${rec.era ? `· ${rec.era}` : ""}
                </div>
                <div class="score-badge">
                    Score: ${rec.score.toFixed(1)}/17.5 (${scorePercent.toFixed(0)}%)
                </div>
                <div class="explanation">${escapeHtml(rec.explanation_one_line)}</div>
                <div class="text-xs text-gray-400 mt-2">${sourceLabel}</div>
            </div>
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

    const inputJson = JSON.stringify(step.input, null, 2);
    const outputJson = JSON.stringify(step.output, null, 2);

    div.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="step-name">${stepLabel}</div>
            <div class="step-latency">${step.latency_ms.toFixed(1)}ms</div>
        </div>
        ${step.note ? `<div class="text-xs text-gray-500 mt-2">ℹ️ ${step.note}</div>` : ""}
        <div class="mt-3">
            <details class="text-xs">
                <summary class="cursor-pointer text-blue-600 hover:text-blue-800">View I/O</summary>
                <div class="step-input-output mt-2">
                    <div><strong>Input:</strong></div>
                    <pre>${escapeHtml(inputJson)}</pre>
                    <div style="margin-top: 0.5rem;"><strong>Output:</strong></div>
                    <pre>${escapeHtml(outputJson)}</pre>
                </div>
            </details>
        </div>
    `;

    return div;
}

function togglePipelineDetails() {
    const details = document.getElementById("pipeline-details");
    const chevron = document.getElementById("pipeline-chevron");

    if (details.classList.contains("hidden")) {
        details.classList.remove("hidden");
        chevron.textContent = "▲";
    } else {
        details.classList.add("hidden");
        chevron.textContent = "▼";
    }
}

// ============================================================================
// Error Handling
// ============================================================================

function showError(message) {
    document.getElementById("loading").classList.add("hidden");
    const errorMsg = document.getElementById("error-message");
    errorMsg.textContent = message;
    errorMsg.classList.remove("hidden");
    document.getElementById("results-container").classList.remove("hidden");
    document.getElementById("empty-state").classList.add("hidden");
}

// ============================================================================
// Utilities
// ============================================================================

function escapeHtml(text) {
    if (!text) return "";
    const map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
}
