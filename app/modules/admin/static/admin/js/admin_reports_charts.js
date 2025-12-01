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

    function buildLineChartConfig(labels, dataPoints, label = 'Usage', color = '#1f3b70') {
        return {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label,
                        data: dataPoints,
                        fill: false,
                        borderColor: color,
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

    function buildBarChartConfig(labels, dataPoints, label = 'Count') {
        return {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label,
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

    function buildDoughnutConfig(labels, dataPoints) {
        return {
            type: 'doughnut',
            data: {
                labels,
                datasets: [
                    {
                        data: dataPoints,
                        backgroundColor: ['#1f3b70', '#e0b341', '#6c757d', '#0d6efd', '#20c997'],
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
            },
        };
    }

    function updateCharts(data) {
        const offerMixCtx = document.getElementById('offerMixChart');
        const signupCtx = document.getElementById('signupChart');
        const regionalCtx = document.getElementById('regionalChart');
        const systemHealthCtx = document.getElementById('systemHealthChart');

        const membership = data?.membership_distribution || {};
        const offerMixLabels = membership.labels || [];
        const offerMixValues = membership.values || [];

        const activity = data?.recent_activity?.timeline || [];
        const signupLabels = activity.map((item) => item.date);
        const signupData = activity.map((item) => item.registrations);

        const companySummary = data?.companies || {};
        const regionalLabels = ['Total Companies', 'New (30d)'];
        const regionalData = [companySummary.total_companies || 0, companySummary.new_last_30_days || 0];

        const offers = data?.offers || {};
        const systemHealthLabels = ['Active Offers', 'Expired Offers'];
        const systemHealthData = [offers.active_offers || 0, offers.expired_offers || 0];

        const hasOfferMix = offerMixLabels.length && offerMixValues.length && offerMixValues.some((val) => val > 0);
        const hasSignups = signupLabels.length && signupData.length;
        const hasRegional = regionalData.some((val) => val > 0);
        const hasSystemHealth = systemHealthData.some((val) => val > 0);

        togglePlaceholder('offerMixPlaceholder', hasOfferMix);
        togglePlaceholder('signupPlaceholder', hasSignups);
        togglePlaceholder('regionalPlaceholder', hasRegional);
        togglePlaceholder('systemHealthPlaceholder', hasSystemHealth);

        const offerMixConfig = buildDoughnutConfig(offerMixLabels, offerMixValues);
        const signupConfig = buildLineChartConfig(signupLabels, signupData, 'Registrations', '#0d6efd');
        const regionalConfig = buildBarChartConfig(regionalLabels, regionalData, 'Companies');
        const systemHealthConfig = buildBarChartConfig(systemHealthLabels, systemHealthData, 'Offers');

        createOrUpdateChart('offerMix', offerMixCtx, offerMixConfig);
        createOrUpdateChart('signup', signupCtx, signupConfig);
        createOrUpdateChart('regional', regionalCtx, regionalConfig);
        createOrUpdateChart('systemHealth', systemHealthCtx, systemHealthConfig);
    }

    function formatGrowth(value) {
        if (value === undefined || value === null) {
            return 'Awaiting data';
        }
        const prefix = value >= 0 ? '+' : '';
        return `${prefix}${value} last 7 days`;
    }

    function updateSummary(data) {
        const users = data.users || {};
        const companies = data.companies || {};
        const offers = data.offers || {};

        setTextContent('totalUsersMetric', users.total_users);
        setTextContent('userGrowthMetric', formatGrowth(users.new_last_7_days));

        setTextContent('activeOffersMetric', offers.active_offers);
        setTextContent('offerDeltaMetric', `${offers.average_discount ?? '0'}% avg discount`);

        setTextContent('totalCompaniesMetric', companies.total_companies);
        setTextContent('newCompaniesMetric', `${companies.new_last_30_days ?? 0} new (30d)`);
    }

    async function loadReports() {
        if (!summaryEndpoint) {
            return;
        }
        const errorMessage = document.getElementById('reportsErrorMessage');
        try {
            const response = await fetch(summaryEndpoint);
            if (!response.ok) {
                throw new Error(`Request failed with status ${response.status}`);
            }
            const payload = await response.json();
            updateSummary(payload);
            updateCharts(payload);
            if (errorMessage) {
                errorMessage.setAttribute('hidden', 'hidden');
            }
        } catch (error) {
            console.error('Failed to load admin reports', error);
            if (errorMessage) {
                errorMessage.removeAttribute('hidden');
            }
        }
    }

    loadReports();
});
