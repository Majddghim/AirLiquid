////////////////////////////////////////////////////////////////////////////////////////////////
// STATE

let monthlyChart = null;
let donutChart   = null;
let currentFrom  = null;
let currentTo    = null;

////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

document.addEventListener('DOMContentLoaded', () => {
    // set default dates BEFORE any API calls
    const y = new Date().getFullYear();
    currentFrom = `${y - 1}-01-01`;
    currentTo   = `${y - 1}-12-31`;
    document.getElementById('period_preset').value = 'last_year';

    loadFleetKpis();
    loadExpenseKpis();
    loadMonthlyChart();
    loadTopCars();
    loadAlerts();
});

////////////////////////////////////////////////////////////////////////////////////////////////
// PERIOD PRESET

function onPeriodPreset(val) {
    const today = new Date();
    const y     = today.getFullYear();
    const m     = String(today.getMonth() + 1).padStart(2, '0');
    const d     = String(today.getDate()).padStart(2, '0');

    const customDiv = document.getElementById('custom_dates');

    if (val === 'this_month') {
        currentFrom = `${y}-${m}-01`;
        currentTo   = `${y}-${m}-${d}`;
        customDiv.classList.add('d-none');
    } else if (val === 'this_year') {
        currentFrom = `${y}-01-01`;
        currentTo   = `${y}-${m}-${d}`;
        customDiv.classList.add('d-none');
    } else if (val === 'last_year') {
        currentFrom = `${y - 1}-01-01`;
        currentTo   = `${y - 1}-12-31`;
        customDiv.classList.add('d-none');
    } else if (val === 'custom') {
        customDiv.classList.remove('d-none');
        document.getElementById('date_from').value = `${y}-01-01`;
        document.getElementById('date_to').value   = `${y}-${m}-${d}`;
        return;
    }

    reloadExpenses();
}

function reloadExpenses() {
    const preset = document.getElementById('period_preset').value;
    if (preset === 'custom') {
        currentFrom = document.getElementById('date_from').value;
        currentTo   = document.getElementById('date_to').value;
        if (!currentFrom || !currentTo) return;
    }
    loadExpenseKpis();
    loadMonthlyChart();
    loadTopCars();
}

////////////////////////////////////////////////////////////////////////////////////////////////
// FLEET KPIs (not period-dependent)

async function loadFleetKpis() {
    try {
        const res  = await fetch('/dashboard/api/fleet-kpis');
        const data = await res.json();
        if (data.status !== 'success') return;

        const d = data.data;
        document.getElementById('kpi_total').innerText      = d.total;
        document.getElementById('kpi_active').innerText     = d.active;
        document.getElementById('kpi_maintenance').innerText = d.maintenance;
        document.getElementById('kpi_incomplete').innerText  = d.incomplete;
    } catch (e) {
        console.error('loadFleetKpis error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// EXPENSE KPIs

async function loadExpenseKpis() {
    try {
        const res  = await fetch(`/dashboard/api/expense-kpis?from=${currentFrom}&to=${currentTo}`);
        const data = await res.json();
        if (data.status !== 'success') return;

        const d = data.data;
        document.getElementById('exp_maintenance').innerText = formatDT(d.maintenance);
        document.getElementById('exp_sinistres').innerText   = formatDT(d.sinistres);
        document.getElementById('exp_carburant').innerText   = formatDT(d.carburant);
        document.getElementById('exp_admin').innerText       = formatDT(d.vignettes + d.visites);
        document.getElementById('exp_total').innerText       = formatDT(d.total);
    } catch (e) {
        console.error('loadExpenseKpis error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// MONTHLY CHART

async function loadMonthlyChart() {
    try {
        const res  = await fetch(`/dashboard/api/monthly-expenses?from=${currentFrom}&to=${currentTo}`);
        const data = await res.json();
        if (data.status !== 'success') return;

        const d = data.data;

        if (monthlyChart) monthlyChart.destroy();

        // show message if no data
        if (!d.labels || d.labels.length === 0) {
            document.getElementById('monthlyChart').style.display = 'none';
            const parent = document.getElementById('monthlyChart').parentElement;
            if (!document.getElementById('chart_no_data')) {
                parent.innerHTML += `<div id="chart_no_data" class="text-center py-5 text-muted">
                    <i class="fas fa-chart-bar fa-2x mb-3 opacity-25"></i>
                    <p class="small mb-0">Aucune dépense enregistrée pour cette période.</p>
                </div>`;
            }
            return;
}

// clear no data message if switching back
        const noData = document.getElementById('chart_no_data');
        if (noData) noData.remove();
        document.getElementById('monthlyChart').style.display = 'block';


        const ctx = document.getElementById('monthlyChart').getContext('2d');
        monthlyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: d.labels.map(l => {
                    const [y, m] = l.split('-');
                    return new Date(y, m - 1).toLocaleDateString('fr-TN', { month: 'short', year: '2-digit' });
                }),
                datasets: [
                    {
                        label:           'Maintenance',
                        data:            d.maintenance,
                        backgroundColor: 'rgba(78, 115, 223, 0.8)',
                        borderRadius:    4,
                    },
                    {
                        label:           'Sinistres',
                        data:            d.sinistres,
                        backgroundColor: 'rgba(231, 74, 59, 0.8)',
                        borderRadius:    4,
                    },
                    {
                        label:           'Carburant',
                        data:            d.carburant,
                        backgroundColor: 'rgba(246, 194, 62, 0.8)',
                        borderRadius:    4,
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, stacked: false },
                    y: {
                        grid: { color: 'rgba(0,0,0,0.05)' },
                        ticks: { callback: v => v + ' DT' }
                    }
                }
            }
        });

        // update donut too
        loadDonutChart(d);

    } catch (e) {
        console.error('loadMonthlyChart error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// DONUT CHART

function loadDonutChart(d) {
    const totals = [
        d.maintenance.reduce((a, b) => a + b, 0),
        d.sinistres.reduce((a, b) => a + b, 0),
        d.carburant.reduce((a, b) => a + b, 0),
    ];
    const labels = ['Maintenance', 'Sinistres', 'Carburant'];
    const colors = ['#4e73df', '#e74a3b', '#f6c23e'];

    if (donutChart) donutChart.destroy();

    const ctx = document.getElementById('donutChart').getContext('2d');
    donutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{ data: totals, backgroundColor: colors, borderWidth: 2 }]
        },
        options: {
            responsive: true,
            cutout: '70%',
            plugins: { legend: { display: false } }
        }
    });

    const total = totals.reduce((a, b) => a + b, 0);
    document.getElementById('donut_legend').innerHTML = labels.map((l, i) => {
        const pct = total > 0 ? Math.round(totals[i] / total * 100) : 0;
        return `<span class="me-3">
            <i class="fas fa-circle me-1" style="color:${colors[i]}"></i>
            ${l} <strong>${pct}%</strong>
        </span>`;
    }).join('');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// TOP 5 CARS

async function loadTopCars() {
    try {
        const res  = await fetch(`/dashboard/api/top-cars?from=${currentFrom}&to=${currentTo}`);
        const data = await res.json();
        if (data.status !== 'success') return;

        const tbody = document.getElementById('top_cars_body');

        if (!data.data.length) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Aucune dépense enregistrée pour cette période.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.data.map((car, i) => {
            const medals = ['🥇','🥈','🥉','4.','5.'];
            return `
            <tr style="cursor:pointer;" onclick="window.location.href='/car/detail/${car.id}'">
                <td class="ps-3 fw-bold text-muted">${medals[i] || (i + 1) + '.'}</td>
                <td>
                    <div class="fw-bold small">${escapeHtml(car.model || 'Inconnu')}</div>
                </td>
                <td>
                    <span class="badge bg-white text-dark border font-monospace small">
                        ${escapeHtml(car.plate_number || '—')}
                    </span>
                </td>
                <td class="text-end small">${formatDT(car.total_factures)}</td>
                <td class="text-end small">${formatDT(car.total_carburant)}</td>
                <td class="text-end pe-3 fw-bold text-primary">${formatDT(car.grand_total)}</td>
            </tr>`;
        }).join('');

    } catch (e) {
        console.error('loadTopCars error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// ALERTS LIST

async function loadAlerts() {
    try {
        const res  = await fetch('/dashboard/api/alerts?days=30');
        const data = await res.json();
        if (data.status !== 'success') return;

        const alerts = data.data;
        document.getElementById('alerts_count').innerText = alerts.length;

        const list = document.getElementById('alerts_list');

        if (!alerts.length) {
            list.innerHTML = `
                <div class="text-center py-4 text-muted">
                    <i class="fas fa-check-circle text-success fa-2x mb-2"></i>
                    <p class="small mb-0">Aucune alerte active — tout est en ordre.</p>
                </div>`;
            return;
        }

        list.innerHTML = alerts.map(a => {
            const bgClass   = a.level === 'danger' ? 'bg-danger' : 'bg-warning';
            const textClass = a.level === 'danger' ? 'text-danger' : 'text-warning';
            const icon      = a.type === 'incomplete' ? 'fa-folder-open'
                            : a.type === 'expired'    ? 'fa-times-circle'
                            : 'fa-exclamation-triangle';
            const sub       = a.type === 'expired'    ? `<span class="text-danger fw-bold">Expiré le ${a.expiry}</span>`
                            : a.type === 'expiry'     ? `Expire le <strong>${a.expiry}</strong> (dans ${a.days} jour${a.days > 1 ? 's' : ''})`
                            : `Documents manquants : <strong>${a.doc}</strong>`;

            return `
            <a href="/car/detail/${a.car_id}"
                class="d-flex align-items-center px-4 py-3 border-bottom text-decoration-none text-dark hover-bg-light">
                <div class="${bgClass} bg-opacity-10 p-2 rounded me-3" style="min-width:36px; text-align:center;">
                    <i class="fas ${icon} ${textClass}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="fw-bold small">${escapeHtml(a.doc)} — ${escapeHtml(a.car)}</div>
                    <div class="text-muted text-xs">${sub}</div>
                </div>
                <i class="fas fa-chevron-right text-muted small"></i>
            </a>`;
        }).join('');

    } catch (e) {
        console.error('loadAlerts error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// HELPERS

function formatDT(val) {
    if (val === null || val === undefined) return '— DT';
    return Number(val).toLocaleString('fr-TN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }) + ' DT';
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}