// Reports dashboard charts and summary binding.
document.addEventListener('DOMContentLoaded', () => {
    const summaryHost = document.querySelector('[data-admin-summary-endpoint]');
    const summaryEndpoint = summaryHost?.dataset.adminSummaryEndpoint;
    const charts = {};

    function setTextContent(id, value, fallback = '—') {
        const element = document.getElementById(id);
        if (!element) {
            return;
        }
        const text = value === undefined || value === null || value === '' ? fallback : value;
        element.textContent = text;
    }

    function togglePlaceholder(id, hasData) {
        const element = document.getElementById(id);
        if (!element) {
            return;
        }
        if (hasData) {
            element.setAttribute('hidden', 'hidden');
        } else {
            element.removeAttribute('hidden');
        }
    }

    function destroyChart(key) {
        if (charts[key]) {
            charts[key].destroy();
            charts[key] = null;
        }
    }

    function createOrUpdateChart(key, ctx, config) {
        if (typeof Chart === 'undefined' || !ctx) {
            return false;
        }
        if (charts[key]) {
            charts[key].data = config.data;
            charts[key].options = config.options;
            charts[key].update();
            return true;
        }
        charts[key] = new Chart(ctx, config);
        return true;
    }

    function buildLineChartConfig(labels, dataPoints) {
        return {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Usage',
                        data: dataPoints,
                        fill: false,
                        borderColor: '#1f3b70',
                        tension: 0.2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } },
            },
        };
    }

    function buildBarChartConfig(labels, dataPoints) {
        return {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Count',
                        data: dataPoints,
                        backgroundColor: '#e0b341',
                        borderColor: '#c89a2f',
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } },
            },
        };
    }

    function updateCharts(data) {
        const trafficCtx = document.getElementById('trafficChart');
        const regionalCtx = document.getElementById('regionalChart');
        const systemHealthCtx = document.getElementById('systemHealthChart');

        const trafficLabels = data?.traffic?.map((item) => item.label) || [];
        const trafficData = data?.traffic?.map((item) => item.value) || [];
        const regionalLabels = data?.regional?.map((item) => item.label) || [];
        const regionalData = data?.regional?.map((item) => item.value) || [];
        const systemHealthLabels = data?.system_health?.map((item) => item.label) || [];
        const systemHealthData = data?.system_health?.map((item) => item.value) || [];

        const hasTraffic = trafficLabels.length && trafficData.length;
        const hasRegional = regionalLabels.length && regionalData.length;
        const hasSystemHealth = systemHealthLabels.length && systemHealthData.length;

        togglePlaceholder('trafficPlaceholder', hasTraffic);
        togglePlaceholder('regionalPlaceholder', hasRegional);
        togglePlaceholder('systemHealthPlaceholder', hasSystemHealth);

        const trafficConfig = buildLineChartConfig(trafficLabels, trafficData);
        const regionalConfig = buildBarChartConfig(regionalLabels, regionalData);
        const systemHealthConfig = buildBarChartConfig(systemHealthLabels, systemHealthData);

        createOrUpdateChart('traffic', trafficCtx, trafficConfig);
        createOrUpdateChart('regional', regionalCtx, regionalConfig);
        createOrUpdateChart('systemHealth', systemHealthCtx, systemHealthConfig);
    }

    function updateSummary(data) {
        setTextContent('companiesCount', data?.companies);
        setTextContent('membersCount', data?.members);
        setTextContent('offersCount', data?.offers);
        setTextContent('redemptionsCount', data?.redemptions);
        setTextContent('activeCampaigns', data?.active_campaigns);
        setTextContent('pendingApprovals', data?.pending_approvals);
        setTextContent('supportTickets', data?.support_tickets);
    }

    async function loadReports() {
        if (!summaryEndpoint) {
            return;
        }
        try {
            const response = await fetch(summaryEndpoint);
            const payload = await response.json();
            updateSummary(payload.summary || {});
            updateCharts(payload.charts || {});
        } catch (error) {
            console.error('Failed to load admin reports', error);
        }
    }

    loadReports();
});
