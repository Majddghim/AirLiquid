////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

let allAlerts      = [];
let filteredAlerts = [];
const rowsPerPage  = 15;
let currentPage    = 1;

document.addEventListener("DOMContentLoaded", async () => {
    await loadAlerts();
});

////////////////////////////////////////////////////////////////////////////////////////////////
// LOAD

async function loadAlerts() {
    try {
        const res  = await fetch('/maintenance/all-alerts');
        const data = await res.json();

        allAlerts      = data.status === 'success' ? data.data : [];
        filteredAlerts = [...allAlerts];

        updateSummaryCards();
        renderTable();
    } catch (e) {
        console.error('loadAlerts error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// SUMMARY CARDS

function updateSummaryCards() {
    const today    = new Date();
    today.setHours(0,0,0,0);

    let overdue = 0, soon = 0, kmBased = 0;
    const carIds = new Set();

    allAlerts.forEach(a => {
        carIds.add(a.car_id);

        if (a.due_date) {
            const due = new Date(a.due_date);
            if (due < today) overdue++;
            else soon++;
        }
        if (a.alert_type === 'km' || a.alert_type === 'both') kmBased++;
    });

    document.getElementById('count_overdue').innerText = overdue;
    document.getElementById('count_soon').innerText    = soon;
    document.getElementById('count_km').innerText      = kmBased;
    document.getElementById('count_cars').innerText    = carIds.size;
    document.getElementById('total_alerts_badge').innerText = `${allAlerts.length} alerte${allAlerts.length > 1 ? 's' : ''}`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// FILTERS

function applyFilters() {
    const search  = document.getElementById('filter_search').value.toLowerCase().trim();
    const type    = document.getElementById('filter_type').value;
    const urgency = document.getElementById('filter_urgency').value;
    const today   = new Date();
    today.setHours(0,0,0,0);

    filteredAlerts = allAlerts.filter(a => {
        if (search) {
            const plate = (a.plate_number || '').toLowerCase();
            const model = (a.model || '').toLowerCase();
            const brand = (a.brand || '').toLowerCase();
            if (!plate.includes(search) && !model.includes(search) && !brand.includes(search)) return false;
        }
        if (type && a.alert_type !== type) return false;
        if (urgency === 'overdue') {
            if (!a.due_date || new Date(a.due_date) >= today) return false;
        }
        if (urgency === 'soon') {
            if (!a.due_date) return false;
            const due = new Date(a.due_date);
            if (due < today || due > new Date(today.getTime() + 15 * 86400000)) return false;
        }
        return true;
    });

    currentPage = 1;
    renderTable();
}

function resetFilters() {
    document.getElementById('filter_search').value  = '';
    document.getElementById('filter_type').value    = '';
    document.getElementById('filter_urgency').value = '';
    filteredAlerts = [...allAlerts];
    currentPage = 1;
    renderTable();
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER TABLE

function renderTable() {
    const tbody = document.getElementById('alerts_tbody');
    const start = (currentPage - 1) * rowsPerPage;
    const page  = filteredAlerts.slice(start, start + rowsPerPage);

    if (page.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">
            <i class="fas fa-check-circle text-success me-2"></i>Aucune alerte
        </td></tr>`;
        renderPagination();
        updateInfo(start, 0);
        return;
    }

    const today = new Date();
    today.setHours(0,0,0,0);

    tbody.innerHTML = page.map(a => {
        // urgency
        let urgencyBadge = '';
        let rowClass     = '';

        if (a.due_date) {
            const due      = new Date(a.due_date);
            const daysLeft = a.days_left;
            if (due < today) {
                urgencyBadge = `<span class="badge bg-danger">En retard (${Math.abs(daysLeft)}j)</span>`;
                rowClass     = 'table-danger';
            } else {
                urgencyBadge = `<span class="badge bg-warning text-dark">Dans ${daysLeft}j</span>`;
                rowClass     = 'table-warning';
            }
        } else if (a.due_km && a.current_km) {
            const diff = a.due_km - a.current_km;
            urgencyBadge = diff <= 0
                ? `<span class="badge bg-danger">Dépassé (${Math.abs(diff)} km)</span>`
                : `<span class="badge bg-info text-dark">Dans ${diff} km</span>`;
            rowClass = diff <= 0 ? 'table-danger' : '';
        }

        return `
        <tr class="${rowClass}" style="cursor:pointer;"
            onclick="window.location.href='/car/detail/${a.car_id}'">
            <td class="ps-3">
                <div class="fw-bold">${escapeHtml(a.plate_number || '—')}</div>
                <div class="text-muted" style="font-size:11px;">${escapeHtml(a.model || '')} ${escapeHtml(a.brand || '')}</div>
            </td>
            <td>
                ${a.nom
                    ? `${escapeHtml(a.prenom)} ${escapeHtml(a.nom)}`
                    : '<span class="text-muted">—</span>'
                }
            </td>
            <td>
                <strong>${escapeHtml(a.part_name)}</strong><br>
                <span class="text-muted" style="font-size:11px;">${escapeHtml(a.category || '')}</span>
            </td>
            <td>
                ${a.alert_type === 'km'   ? '<span class="badge bg-info text-dark">KM</span>'         :
                  a.alert_type === 'date' ? '<span class="badge bg-warning text-dark">Date</span>'    :
                  '<span class="badge bg-secondary">KM + Date</span>'}
            </td>
            <td>${a.due_date ? formatDate(a.due_date) : '—'}</td>
            <td>${a.due_km  ? a.due_km.toLocaleString() + ' km' : '—'}</td>
            <td>${a.current_km ? a.current_km.toLocaleString() + ' km' : '—'}</td>
            <td>${urgencyBadge}</td>
            <td class="text-end pe-3">
                <a href="/car/detail/${a.car_id}"
                    class="btn btn-outline-primary btn-sm"
                    onclick="event.stopPropagation()">
                    <i class="fas fa-tools me-1"></i>Voir
                </a>
            </td>
        </tr>`;
    }).join('');

    renderPagination();
    updateInfo(start, page.length);
}

////////////////////////////////////////////////////////////////////////////////////////////////
// PAGINATION

function renderPagination() {
    const pagination = document.getElementById('alerts_pagination');
    pagination.innerHTML = '';
    const totalPages = Math.ceil(filteredAlerts.length / rowsPerPage);
    if (totalPages <= 1) return;
    for (let i = 1; i <= totalPages; i++) {
        pagination.innerHTML += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>`;
    }
}

function changePage(page) { currentPage = page; renderTable(); }

function updateInfo(start, len) {
    const el = document.getElementById('alerts_info');
    if (!el) return;
    if (filteredAlerts.length === 0) { el.innerText = 'Aucun résultat'; return; }
    el.innerText = `Affichage de ${start + 1} à ${start + len} sur ${filteredAlerts.length}`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// HELPERS

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return d.toLocaleDateString('fr-TN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}