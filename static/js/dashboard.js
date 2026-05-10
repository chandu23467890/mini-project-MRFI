let stabilityGauge = null;
let trendChart = null;
let metabolicMonitor = null;
let currentUser = null;

class StabilityGauge {
    constructor(canvasId, score) {
        this.canvas = document.getElementById(canvasId);
        this.score = score;
        this.render();
    }

    render() {
        const ctx = this.canvas.getContext("2d");
        const width = this.canvas.width;
        const height = this.canvas.height;
        const radius = Math.min(width, height) / 2 - 18;
        const cx = width / 2;
        const cy = height / 2;
        const start = -Math.PI / 2;
        const angle = start + (Math.max(0, Math.min(100, this.score)) / 100) * (2 * Math.PI);
        const color = this.score >= 80 ? "#1f7a4f" : this.score >= 50 ? "#c97316" : this.score >= 30 ? "#d97706" : "#c23a2b";

        ctx.clearRect(0, 0, width, height);
        ctx.lineWidth = 18;
        ctx.beginPath();
        ctx.strokeStyle = "#e8ddcf";
        ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
        ctx.stroke();

        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.arc(cx, cy, radius, start, angle);
        ctx.stroke();

        ctx.fillStyle = "#16202a";
        ctx.font = "700 40px Georgia";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(Math.round(this.score), cx, cy - 8);
        ctx.fillStyle = "#5b6772";
        ctx.font = "16px Georgia";
        ctx.fillText("Stability Score", cx, cy + 28);
    }

    update(newScore) {
        this.score = newScore;
        this.render();
    }
}

class MetabolicMonitor {
    constructor(userId, options = {}) {
        this.userId = userId;
        this.onStabilityUpdate = options.onStabilityUpdate || (() => {});
        this.onAnomalyDetected = options.onAnomalyDetected || (() => {});
        this.connect();
    }

    connect() {
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        const host = window.location.hostname;
        const port = document.querySelector('meta[name="ws-port"]')?.content || "8765";
        this.ws = new WebSocket(`${protocol}://${host}:${port}/ws/monitor/${this.userId}`);
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "stability_update") this.onStabilityUpdate(data);
            if (data.type === "anomaly") this.onAnomalyDetected(data);
        };
        this.ws.onclose = () => {
            window.setTimeout(() => this.connect(), 5000);
        };
    }
}

const API = {
    get token() {
        return localStorage.getItem("token");
    },

    async request(endpoint, options = {}) {
        const headers = {
            ...(options.headers || {}),
            Authorization: `Bearer ${this.token}`,
        };
        const hasFormData = options.body instanceof FormData;
        if (!hasFormData) headers["Content-Type"] = "application/json";

        const response = await fetch(`/api${endpoint}`, { ...options, headers });
        const payload = await response.json();
        if (response.status === 401) {
            logout();
            throw new Error("Unauthorized");
        }
        if (!response.ok) throw new Error(payload.error || payload.message || "Request failed");
        return payload;
    },

    getProfile() { return this.request("/auth/me"); },
    getStability() { return this.request("/measurements/stability"); },
    getHistory() { return this.request("/measurements/stability/history"); },
    getMeasurements() { return this.request("/measurements?days=30"); },
    getRecommendations() { return this.request("/recommendations"); },
    addMeasurement(data) { return this.request("/measurements", { method: "POST", body: JSON.stringify(data) }); },
    acceptRecommendation(id) { return this.request(`/recommendations/${id}/accept`, { method: "POST" }); },
    logMeal(formData) { return this.request("/measurements/food-log", { method: "POST", body: formData }); },
};

function updateComponentScore(component, score, maxScore) {
    const scoreElement = document.getElementById(`${component}-score`);
    const barElement = document.getElementById(`${component}-bar`);
    if (scoreElement) scoreElement.textContent = Math.round(score);
    if (barElement) barElement.style.width = `${Math.max(0, Math.min(100, (score / maxScore) * 100))}%`;
}

function renderGauge(score) {
    if (stabilityGauge) stabilityGauge.update(score);
    else stabilityGauge = new StabilityGauge("stability-gauge", score);
}

function renderTrajectory(prediction) {
    const trajectoryBadge = document.getElementById("trajectory-badge");
    const diabetesRisk = document.getElementById("diabetes-risk");
    const nextCheck = document.getElementById("next-check");
    
    if (trajectoryBadge) trajectoryBadge.textContent = prediction?.trajectory || "--";
    if (diabetesRisk) diabetesRisk.textContent = prediction?.diabetes_risk_90d || "--";
    if (nextCheck) nextCheck.textContent = prediction ? new Date(prediction.next_assessment_date).toLocaleDateString() : "--";
}

function renderStateBadge(state) {
    const badge = document.getElementById("state-badge");
    if (!badge || !state) return;
    badge.textContent = state.replaceAll("_", " ");
    badge.style.background = state === "STABLE" ? "#e4f6ea" : state === "PREDIABETIC_EARLY" ? "#fff2dd" : state === "PREDIABETIC_LATE" ? "#ffe7cb" : "#fde7e3";
    badge.style.color = state === "STABLE" ? "#1f7a4f" : state === "PREDIABETIC_EARLY" ? "#a35f12" : state === "PREDIABETIC_LATE" ? "#a84f15" : "#a13023";
}

function renderInsights(stability, prediction) {
    const panel = document.getElementById("insights-panel");
    if (!panel) return;
    
    const insights = [];
    
    if (stability && stability.evidence?.drift_detected) {
        insights.push(stability.evidence.drift_reason);
    }
    if (stability && stability.components) {
        if (stability.components.glucose_control < 20) {
            insights.push("Glucose control is the weakest component and should be prioritized.");
        }
        if (stability.components.insulin_sensitivity < 12) {
            insights.push("Reduced insulin sensitivity is contributing materially to overall instability.");
        }
    }
    if (prediction?.trajectory === "WORSENING") {
        insights.push("Trajectory model predicts a worsening path over the next 30 days.");
    }
    if (!insights.length) {
        if (stability) {
            insights.push("Measurements indicate relatively stable metabolism at the moment.");
        } else {
            insights.push("Start logging measurements to get personalized insights.");
        }
    }

    panel.innerHTML = `<div class="panel-head"><h2>Key Insights</h2></div><ul>${insights.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

function renderRecommendations(recommendations) {
    const panel = document.getElementById("recommendations-panel");
    if (!recommendations?.length) {
        panel.innerHTML = `<div class="panel-head"><h2>Personalized Recommendations</h2></div><p class="muted">No recommendations available yet.</p>`;
        return;
    }
    panel.innerHTML = `<div class="panel-head"><h2>Personalized Recommendations</h2></div>${recommendations.map((rec) => `
        <article class="recommendation-card">
            <h3>${rec.title}</h3>
            <p>${rec.description || ""}</p>
            <ul>${rec.actions.map((action) => `<li>${action}</li>`).join("")}</ul>
            <p><strong>Expected improvement:</strong> ${rec.expected_improvement || "Monitor over 2-3 weeks"}</p>
            <button class="btn btn-primary" type="button" onclick="acceptRecommendation(${rec.id})">Accept Plan</button>
        </article>
    `).join("")}`;
}

function renderMeasurements(measurements) {
    console.log("Rendering measurements:", measurements);
    const root = document.getElementById("measurements-table");
    if (!measurements.length) {
        console.log("No measurements to display");
        root.innerHTML = `<p class="muted">No measurements logged yet.</p>`;
        return;
    }
    root.innerHTML = `<table><thead><tr><th>Date</th><th>Type</th><th>Value</th><th>Status</th></tr></thead><tbody>${
        measurements.slice(0, 10).map((m) => `
            <tr>
                <td>${new Date(m.timestamp).toLocaleString()}</td>
                <td>${m.type.replaceAll("_", " ")}</td>
                <td>${m.value} ${m.unit}</td>
                <td><span class="pill ${m.status}">${m.status.toUpperCase()}</span></td>
            </tr>
        `).join("")
    }</tbody></table>`;
}

function renderTrendChart(history, prediction) {
    const ctx = document.getElementById("trend-chart").getContext("2d");
    if (trendChart) trendChart.destroy();
    const labels = history.map((item) => new Date(item.calculated_at).toLocaleDateString());
    const scores = history.map((item) => item.stability_score);
    const futureLabels = prediction?.predictions?.map((item) => `Week ${item.week}`) || [];
    const futureScores = prediction?.predictions?.map((item) => item.predicted_score) || [];
    trendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [...labels, ...futureLabels],
            datasets: [
                {
                    label: "Historical Stability",
                    data: [...scores, ...Array(futureScores.length).fill(null)],
                    borderColor: "#4caf50",
                    backgroundColor: "rgba(76, 175, 80, 0.1)",
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: "Predicted Trajectory",
                    data: [...Array(scores.length).fill(null), ...futureScores],
                    borderColor: "#66bb6a",
                    backgroundColor: "rgba(102, 187, 106, 0.1)",
                    borderDash: [6, 5],
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: { y: { min: 0, max: 100 } }
        }
    });
}

async function updateDashboard() {
    try {
        console.log("Fetching dashboard data...");
        const [profileData, stabilityData, historyData, measurementsData] = await Promise.all([
            API.getProfile(),
            API.getStability(),
            API.getHistory(),
            API.getMeasurements()
        ]);
        
        console.log("Dashboard data received:", { profileData, stabilityData, historyData, measurementsData });
        
        currentUser = profileData.user;
        document.getElementById("user-name").textContent = currentUser.name;
        document.getElementById("data-quality-grade").textContent = stabilityData.data_quality.grade;

    if (stabilityData.insufficient_data) {
        // Handle insufficient data case
        const gaugeElement = document.getElementById("stability-gauge");
        if (gaugeElement) gaugeElement.style.display = "none";
        
        // Remove existing warning if present
        const existingWarning = document.querySelector(".insufficient-data-warning");
        if (existingWarning) existingWarning.remove();
        
        // Create a warning message in the score panel
        const scorePanel = document.querySelector(".score-panel");
        if (scorePanel) {
            const warningDiv = document.createElement("div");
            warningDiv.className = "insufficient-data-warning";
            warningDiv.innerHTML = `<h3>Insufficient Data</h3><p>${stabilityData.message}</p>`;
            warningDiv.style.cssText = "padding: 20px; text-align: center; background: #fef3c7; border-radius: 8px; margin: 20px 0;";
            scorePanel.appendChild(warningDiv);
        }
        
        const stateBadge = document.getElementById("state-badge");
        if (stateBadge) stateBadge.textContent = "INSUFFICIENT DATA";
        
        const confidenceLevel = document.getElementById("confidence-level");
        if (confidenceLevel) confidenceLevel.textContent = "N/A";
        
        updateComponentScore("glucose", 0, 40);
        updateComponentScore("trend", 0, 25);
        updateComponentScore("insulin", 0, 20);
        updateComponentScore("lifestyle", 0, 15);
        renderTrajectory(null);
        renderInsights(null, null);
        renderTrendChart([], null);
        renderMeasurements(measurementsData);
    } else {
        // Remove existing warning if present when we have sufficient data
        const existingWarning = document.querySelector(".insufficient-data-warning");
        if (existingWarning) existingWarning.remove();
        
        const gaugeElement = document.getElementById("stability-gauge");
        if (gaugeElement) gaugeElement.style.display = "block";
        const stability = stabilityData.stability;
        renderGauge(stability.stability_score);
        renderStateBadge(stability.metabolic_state);
        document.getElementById("confidence-level").textContent = stability.confidence;
        updateComponentScore("glucose", stability.components.glucose_control, 40);
        updateComponentScore("trend", stability.components.trend_stability, 25);
        updateComponentScore("insulin", stability.components.insulin_sensitivity, 20);
        updateComponentScore("lifestyle", stability.components.lifestyle, 15);
        renderTrajectory(stabilityData.prediction);
        renderInsights(stability, stabilityData.prediction);
        renderTrendChart(historyData, stabilityData.prediction);
        renderMeasurements(measurementsData);
    }

    if (!metabolicMonitor) {
        metabolicMonitor = new MetabolicMonitor(currentUser.id, {
            onStabilityUpdate: async () => {
                await updateDashboard();
            }
        });
    }
    } catch (error) {
        console.error('Error updating dashboard:', error);
        console.error('Error details:', error.message, error.stack);
        
        // Show more specific error message
        let errorMessage = "Failed to update dashboard";
        if (error.message.includes('fetch')) {
            errorMessage = "Network error - please check connection";
        } else if (error.message.includes('JSON')) {
            errorMessage = "Data format error - please try again";
        } else if (error.message.includes('stability')) {
            errorMessage = "Stability calculation error - data may be insufficient";
        } else {
            errorMessage = `Dashboard update failed: ${error.message}`;
        }
        
        Swal.fire("Error", errorMessage, "error");
    }
}

async function loadRecommendations(showToast = false) {
    const response = await API.getRecommendations();
    renderRecommendations(response.recommendations);
    if (showToast) Swal.fire("Updated", "Recommendations refreshed successfully.", "success");
}

async function acceptRecommendation(id) {
    await API.acceptRecommendation(id);
    Swal.fire("Accepted", "Recommendation accepted successfully.", "success");
    
    // Hide the accepted recommendation from the UI
    const recommendationCards = document.querySelectorAll('.recommendation-card');
    recommendationCards.forEach(card => {
        const acceptButton = card.querySelector(`button[onclick="acceptRecommendation(${id})"]`);
        if (acceptButton) {
            card.style.opacity = '0.5';
            card.style.pointerEvents = 'none';
            acceptButton.textContent = 'Accepted';
            acceptButton.disabled = true;
            acceptButton.classList.remove('btn-primary');
            acceptButton.classList.add('btn-secondary');
        }
    });
}

function refreshDashboard() {
    console.log("Manual dashboard refresh triggered");
    updateDashboard();
    loadRecommendations();
}

function openMeasurementModal() {
    const modal = document.getElementById("measurement-modal");
    modal.classList.remove("hidden");
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById("measurement-timestamp").value = now.toISOString().slice(0, 16);
}

function openMealModal() {
    document.getElementById("meal-modal").classList.remove("hidden");
}

function closeModal(id) {
    document.getElementById(id).classList.add("hidden");
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}

document.getElementById("measurement-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const measurementData = {
            measurement_type: document.getElementById("measurement-type").value,
            value: parseFloat(document.getElementById("measurement-value").value),
            timestamp: new Date(document.getElementById("measurement-timestamp").value).toISOString(),
            meal_context: document.getElementById("measurement-context").value || null
        };
        
        console.log("Adding measurement:", measurementData);
        
        const result = await API.addMeasurement(measurementData);
        console.log("Measurement added successfully:", result);
        
        closeModal("measurement-modal");
        
        // Show success message immediately
        Swal.fire("Saved", "Measurement logged successfully.", "success");
        
        // Add a delay to ensure server processes data
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        console.log("Updating dashboard...");
        
        // Force dashboard update
        await updateDashboard();
        
        console.log("Dashboard updated successfully");
        
        // Refresh recommendations as well
        await loadRecommendations();
        
    } catch (error) {
        console.error("Error adding measurement:", error);
        Swal.fire("Error", error.message, "error");
    }
});

document.getElementById("meal-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const formData = new FormData();
        const photo = document.getElementById("meal-photo").files[0];
        if (photo) formData.append("image", photo);
        formData.append("meal_type", document.getElementById("meal-type").value);
        formData.append("carbs_grams", document.getElementById("meal-carbs").value || "");
        formData.append("timestamp", new Date().toISOString());
        await API.logMeal(formData);
        closeModal("meal-modal");
        Swal.fire("Logged", "Meal captured successfully.", "success");
    } catch (error) {
        Swal.fire("Error", error.message, "error");
    }
});

document.getElementById("meal-photo")?.addEventListener("change", (event) => {
    const file = event.target.files[0];
    const preview = document.getElementById("meal-preview");
    if (!file) {
        preview.classList.add("hidden");
        return;
    }
    const reader = new FileReader();
    reader.onload = (loadEvent) => {
        preview.src = loadEvent.target.result;
        preview.classList.remove("hidden");
    };
    reader.readAsDataURL(file);
});

document.addEventListener("DOMContentLoaded", async () => {
    if (!localStorage.getItem("token")) {
        window.location.href = "/";
        return;
    }
    try {
        await updateDashboard();
        await loadRecommendations();
    } catch (error) {
        Swal.fire("Dashboard error", error.message, "error");
    }
});
