const OBSERVABILITY = (() => {
    const OBS_MODULE = "admin-reports";
    const originalFetch = window.fetch.bind(window);

    const send = (endpoint, payload) => {
        const body = {
            module: OBS_MODULE,
            page_url: window.location.href,
            timestamp: new Date().toISOString(),
            ...payload,
        };
        return originalFetch(`/log/${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
            credentials: "include",
        }).catch(() => undefined);
    };

    const logUIEvent = (event, details = {}) => send("ui-event", { event, ...details });

    const trackedFetch = async (url, options = {}) => {
        const started = performance.now();
        const method = options.method || "GET";
        const targetUrl = typeof url === "string" ? url : url?.url || "";
        try {
            const response = await originalFetch(url, options);
            send("api-trace", {
                event: "request_end",
                url: targetUrl,
                method,
                status: response.status,
                duration_ms: Math.round(performance.now() - started),
            });
            return response;
        } catch (error) {
            send("api-trace", {
                event: "request_error",
                url: targetUrl,
                method,
                status: "network_error",
                duration_ms: Math.round(performance.now() - started),
                message: error?.message,
            });
            throw error;
        }
    };

    window.addEventListener("error", (event) => {
        send("frontend-error", {
            message: event.message,
            module: OBS_MODULE,
            filename: event.filename,
            line: event.lineno,
            column: event.colno,
            stack: event.error?.stack,
            browser: navigator.userAgent,
        });
    });

    window.addEventListener("unhandledrejection", (event) => {
        send("frontend-error", {
            message: event.reason?.message || "Unhandled promise rejection",
            module: OBS_MODULE,
            stack: event.reason?.stack,
            browser: navigator.userAgent,
        });
    });

    logUIEvent("page_open", { path: window.location.pathname });
    document.addEventListener("click", (event) => {
        const target = event.target?.closest("button, a");
        if (target) {
            logUIEvent("button_click", {
                label: target.innerText?.trim() || target.getAttribute("aria-label") || target.id || target.className,
            });
        }
    });

    document.addEventListener("submit", (event) => {
        logUIEvent("form_submit", { action: event.target?.action || window.location.pathname });
    });

    window.fetch = trackedFetch;
    return { fetch: trackedFetch, logUIEvent };
})();

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

function setTextContent(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

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

    setTextContent("totalUsers", userStats.total_users ?? 0);
    setTextContent(
        "newUsers",
        `انضم خلال ٧ أيام: ${userStats.new_last_7_days ?? 0}`
    );
    setTextContent("totalCompanies", companyStats.total_companies ?? 0);
    setTextContent(
        "newCompanies",
        `انضمت خلال ٣٠ يوم: ${companyStats.new_last_30_days ?? 0}`
    );
    setTextContent("activeOffers", offerStats.active_offers ?? 0);
    setTextContent(
        "avgDiscount",
        `متوسط الخصم: ${(offerStats.average_discount ?? 0).toFixed(2)}%`
    );
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
        const created = offer.created_at
            ? new Date(offer.created_at).toLocaleString("ar-EG")
            : "-";
        const validUntil = offer.valid_until
            ? new Date(offer.valid_until).toLocaleDateString("ar-EG")
            : "-";
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
    tr.innerHTML = '<td colspan="5" class="text-center text-muted">لا توجد عروض متاحة.</td>';
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
