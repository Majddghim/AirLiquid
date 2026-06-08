let currentFrom = null;
let currentTo   = null;

document.addEventListener('DOMContentLoaded', () => {
    const y = new Date().getFullYear();
    currentFrom = `${y}-01-01`;
    currentTo   = new Date().toISOString().split('T')[0];
    loadData();
});

function onPeriodChange(val) {
    const today = new Date();
    const y = today.getFullYear();
    const m = String(today.getMonth() + 1).padStart(2, '0');
    const d = String(today.getDate()).padStart(2, '0');
    const customDiv = document.getElementById('custom_dates');

    if (val === 'this_year') {
        currentFrom = `${y}-01-01`;
        currentTo   = `${y}-${m}-${d}`;
        customDiv.classList.add('d-none');
        loadData();
    } else if (val === 'last_year') {
        currentFrom = `${y-1}-01-01`;
        currentTo   = `${y-1}-12-31`;
        customDiv.classList.add('d-none');
        loadData();
    } else if (val === 'this_month') {
        currentFrom = `${y}-${m}-01`;
        currentTo   = `${y}-${m}-${d}`;
        customDiv.classList.add('d-none');
        loadData();
    } else if (val === 'custom') {
        customDiv.classList.remove('d-none');
        document.getElementById('date_from').value = `${y}-01-01`;
        document.getElementById('date_to').value   = `${y}-${m}-${d}`;
    }
}

async function loadData() {
    if (document.getElementById('period_preset').value === 'custom') {
        currentFrom = document.getElementById('date_from').value;
        currentTo   = document.getElementById('date_to').value;
        if (!currentFrom || !currentTo) return;
    }

    const tbody = document.getElementById('cars_tbody');
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-5 text-muted">
        <div class="spinner-border text-primary mb-2"></div><p>Chargement...</p></td></tr>`;

    try {
        const res  = await fetch(`/dashboard/api/all-cars-expenses?from=${currentFrom}&to=${currentTo}`);
        const data = await res.json();
        if (data.status !== 'success') return;

        const cars = data.data;
        document.getElementById('cars_count').innerText = cars.length;

        if (!cars.length) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center py-5 text-muted">
                Aucune dépense pour cette période.</td></tr>`;
            return;
        }

        const medals = ['🥇','🥈','🥉'];
        tbody.innerHTML = cars.map((car, i) => {
            const rank        = medals[i] || `${i+1}.`;
            const statusColor = car.status === 'active'     ? 'success'   :
                                car.status === 'maintenance' ? 'warning'   :
                                car.status === 'inactive'    ? 'secondary' : 'dark';
            const statusLabel = car.status === 'active'     ? 'Actif'       :
                                car.status === 'maintenance' ? 'Maintenance' :
                                car.status === 'inactive'    ? 'Inactif'     : 'Retiré';
            return `
            <tr style="cursor:pointer;" onclick="window.location.href='/car/detail/${car.id}'">
                <td class="ps-3 fw-bold text-muted">${rank}</td>
                <td>
                    <div class="fw-bold small">${escapeHtml(car.model || car.brand || '—')}</div>
                    <span class="badge bg-${statusColor}-subtle text-${statusColor}"
                        style="font-size:10px;">${statusLabel}</span>
                </td>
                <td>
                    <span class="badge bg-white text-dark border font-monospace small">
                        ${escapeHtml(car.plate_number || '—')}
                    </span>
                </td>
                <td class="small text-muted">${escapeHtml(car.assigned_to || '—')}</td>
                <td class="small">${car.current_km ? Number(car.current_km).toLocaleString() + ' km' : '—'}</td>
                <td class="text-end small">${formatDT(car.total_maintenance)}</td>
                <td class="text-end small">${formatDT(car.total_sinistres)}</td>
                <td class="text-end small">${formatDT(car.total_carburant)}</td>
                <td class="text-end pe-3 fw-bold text-primary">${formatDT(car.grand_total)}</td>
            </tr>`;
        }).join('');

    } catch (e) {
        console.error('loadData error:', e);
    }
}

function formatDT(val) {
    if (!val && val !== 0) return '—';
    return Number(val).toLocaleString('fr-TN', {
        minimumFractionDigits: 2, maximumFractionDigits: 2
    }) + ' DT';
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}