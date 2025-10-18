const API_ENDPOINT = "/admin/api/summary";
const EXPORT_ENDPOINT = "/admin/reports/export";
const REFRESH_INTERVAL = 60_000;

const palette = {
    primary: "#0b3d91",
    accent: "#c9a227",
    neutral: "#f0f2f5",
    slate: "#4a4f63"
};

const { Chart } = window;

const chartInstances = {
    membership: null,
    activity: null,
    offers: null
};

async function fetchSummary() {
    const response = await fetch(API_ENDPOINT, {
        headers: {
            Accept: "application/json"
        },
        credentials: "include"
    });

    if (!response.ok) {
        throw new Error(`Failed to load analytics (${response.status})`);
    }

    return response.json();
}

function updateStatCards(summary) {
    const userStats = summary.users ?? {};
    const companyStats = summary.companies ?? {};
    const offerStats = summary.offers ?? {};

    document.getElementById("totalUsers").textContent = userStats.total_users ?? 0;
    document.getElementById("newUsers").textContent = `New last 7 days: ${userStats.new_last_7_days ?? 0}`;
    document.getElementById("totalCompanies").textContent = companyStats.total_companies ?? 0;
    document.getElementById("newCompanies").textContent = `New last 30 days: ${companyStats.new_last_30_days ?? 0}`;
    document.getElementById("activeOffers").textContent = offerStats.active_offers ?? 0;
    document.getElementById("avgDiscount").textContent = `Average discount: ${(offerStats.average_discount ?? 0).toFixed(2)}%`;
}

function ensureChart(ctx, configKey, chartConfig) {
    if (chartInstances[configKey]) {
        chartInstances[configKey].data.labels = chartConfig.data.labels;
        chartInstances[configKey].data.datasets = chartConfig.data.datasets;
        chartInstances[configKey].options = chartConfig.options;
        chartInstances[configKey].update();
        return chartInstances[configKey];
    }

    chartInstances[configKey] = new Chart(ctx, chartConfig);
    return chartInstances[configKey];
}

function renderCharts(summary) {
    const membership = summary.membership_distribution ?? { labels: [], values: [] };
    const membershipCtx = document.getElementById("membershipChart");
    if (membershipCtx) {
        ensureChart(membershipCtx, "membership", {
            type: "pie",
            data: {
                labels: membership.labels,
                datasets: [
                    {
                        data: membership.values,
                        backgroundColor: [
                            palette.primary,
                            palette.accent,
                            "#1f6feb",
                            "#ffc857"
                        ],
                        borderWidth: 0
                    }
                ]
            },
            options: {
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        });
    }

    const activity = summary.recent_activity?.timeline ?? [];
    const activityCtx = document.getElementById("activityChart");
    if (activityCtx) {
        ensureChart(activityCtx, "activity", {
            type: "bar",
            data: {
                labels: activity.map((entry) => entry.date),
                datasets: [
                    {
                        label: "Registrations",
                        data: activity.map((entry) => entry.registrations),
                        backgroundColor: palette.primary,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                scales: {
                    x: {
                        ticks: {
                            color: palette.slate
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: palette.slate
                        }
                    }
                }
            }
        });
    }

    const offerTrend = summary.offers?.trend ?? [];
    const offersCtx = document.getElementById("offersChart");
    if (offersCtx) {
        ensureChart(offersCtx, "offers", {
            type: "line",
            data: {
                labels: offerTrend.map((entry) => entry.period_start),
                datasets: [
                    {
                        label: "Offers",
                        data: offerTrend.map((entry) => entry.count),
                        borderColor: palette.accent,
                        backgroundColor: "rgba(201, 162, 39, 0.2)",
                        fill: true,
                        tension: 0.3,
                        pointRadius: 4,
                        pointBackgroundColor: palette.accent
                    }
                ]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

function updateRecentOffers(summary) {
    const tableBody = document.getElementById("recentOffersBody");
    if (!tableBody) {
        return;
    }

    const rows = (summary.recent_offers ?? []).map((offer) => {
        const tr = document.createElement("tr");
        const created = offer.created_at ? new Date(offer.created_at).toLocaleString() : "-";
        const validUntil = offer.valid_until ? new Date(offer.valid_until).toLocaleDateString() : "-";
        tr.innerHTML = `
            <td>${offer.title ?? ""}</td>
            <td>${offer.company ?? "-"}</td>
            <td>${Number.parseFloat(offer.base_discount ?? 0).toFixed(2)}%</td>
            <td>${created}</td>
            <td>${validUntil}</td>
        `;
        return tr;
    });

    tableBody.replaceChildren(...(rows.length ? rows : [createEmptyRow()]));
}

function createEmptyRow() {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="5" class="text-center text-muted">No offers found.</td>';
    return tr;
}

async function refreshDashboard() {
    try {
        const summary = await fetchSummary();
        updateStatCards(summary);
        renderCharts(summary);
        updateRecentOffers(summary);
    } catch (error) {
        console.error(error);
    }
}

function scheduleRefresh() {
    setInterval(refreshDashboard, REFRESH_INTERVAL);
}

function setupExportButton() {
    const button = document.getElementById("exportPdfButton");
    if (!button) {
        return;
    }
    button.addEventListener("click", () => {
        window.location.href = EXPORT_ENDPOINT;
    });
}

function init() {
    setupExportButton();
    refreshDashboard();
    scheduleRefresh();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}