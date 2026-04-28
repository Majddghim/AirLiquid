////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

const employeId = window.location.pathname.split('/').pop();

document.addEventListener("DOMContentLoaded", async () => {
    if (!employeId) return;
    await loadProfil();
});

////////////////////////////////////////////////////////////////////////////////////////////////
// LOAD PROFIL

async function loadProfil() {
    try {
        const res  = await fetch(`/employe/profil-data/${employeId}`);
        const data = await res.json();

        if (data.status !== 'success') {
            Swal.fire({ icon: 'error', title: 'Erreur', text: data.message });
            return;
        }

        const d = data.data;
        renderHeader(d.employe);
        renderInfo(d.employe);
        renderCurrentCar(d.assignments);
        renderAssignments(d.assignments);
        renderSinistres(d.sinistres);

        document.getElementById('profil-loading').style.display = 'none';
        document.getElementById('profil-content').style.display = 'block';

    } catch (e) {
        console.error('loadProfil error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur serveur', text: 'Impossible de charger le profil.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER HEADER

function renderHeader(emp) {
    const initials = `${(emp.prenom || 'E')[0]}${(emp.nom || 'P')[0]}`.toUpperCase();
    document.getElementById('profil_avatar').innerText = initials;
    document.getElementById('profil_name').innerText   = `${emp.prenom} ${emp.nom}`;
    document.getElementById('profil_post').innerText   = `${emp.poste || ''} — ${emp.departement || ''}`;

    const badge = document.getElementById('profil_status_badge');
    if (emp.status === 'active') {
        badge.className   = 'badge bg-success mt-1';
        badge.innerText   = 'Actif';
    } else {
        badge.className   = 'badge bg-secondary mt-1';
        badge.innerText   = 'Inactif';
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER INFO

function renderInfo(emp) {
    document.getElementById('profil_info').innerHTML = `
        <div class="mb-3">
            <div class="info-label">Email</div>
            <div class="info-value">${escapeHtml(emp.email || '—')}</div>
        </div>
        <div class="mb-3">
            <div class="info-label">Téléphone</div>
            <div class="info-value">${escapeHtml(emp.telephone || '—')}</div>
        </div>
        <div class="mb-3">
            <div class="info-label">Département</div>
            <div class="info-value">${escapeHtml(emp.departement || '—')}</div>
        </div>
        <div class="mb-3">
            <div class="info-label">Poste</div>
            <div class="info-value">${escapeHtml(emp.poste || '—')}</div>
        </div>
        <div class="mb-3">
            <div class="info-label">Date de recrutement</div>
            <div class="info-value">${formatDate(emp.created_at)}</div>
        </div>`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER CURRENT CAR

function renderCurrentCar(assignments) {
    const el      = document.getElementById('profil_current_car');
    const current = assignments.filter(a => !a.end_date);

    if (current.length === 0) {
        el.innerHTML = `
            <div class="text-center py-3 text-muted small">
                <i class="fas fa-car-slash mb-2 d-block fa-2x opacity-25"></i>
                Aucun véhicule affecté actuellement
            </div>`;
        return;
    }

    el.innerHTML = current.map(a => {
        const isReplacement = a.notes && a.notes.includes('Remplacement sinistre');
        return `
        <div class="d-flex align-items-center gap-3 p-2 ${isReplacement ? 'bg-warning bg-opacity-10 rounded' : ''}">
            <div class="bg-success bg-opacity-10 p-2 rounded">
                <i class="fas fa-car text-success fa-lg"></i>
            </div>
            <div>
                <div class="fw-bold text-dark">${escapeHtml(a.model || '')} ${escapeHtml(a.brand || '')}</div>
                <div class="text-muted small font-monospace">${escapeHtml(a.plate_number || '')}</div>
                ${isReplacement ? '<span class="badge bg-warning text-dark mt-1">Véhicule de remplacement</span>' : ''}
                <div class="text-muted small mt-1">Depuis le ${formatDate(a.start_date)}</div>
            </div>
        </div>`;
    }).join('<hr class="my-2">');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER ASSIGNMENTS

function renderAssignments(assignments) {
    const tbody = document.getElementById('assignments_tbody');
    document.getElementById('assignments_count').innerText = assignments.length;

    if (assignments.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Aucune affectation</td></tr>`;
        return;
    }

    tbody.innerHTML = assignments.map(a => {
        const isActive      = !a.end_date;
        const isReplacement = a.notes && a.notes.includes('Remplacement sinistre');

        const typeBadge = isReplacement
            ? '<span class="badge bg-warning text-dark">Remplacement</span>'
            : '<span class="badge bg-light text-dark border">Normal</span>';

        const statusBadge = isActive
            ? '<span class="badge bg-success">En cours</span>'
            : '<span class="badge bg-secondary">Terminé</span>';

        const duree = a.duree_jours
            ? a.duree_jours + ' j'
            : '—';

        return `
        <tr class="${isActive ? 'table-success bg-opacity-25' : ''}">
            <td class="ps-3">
                <div class="fw-bold">${escapeHtml(a.plate_number || '—')}</div>
                <div class="text-muted" style="font-size:11px;">${escapeHtml(a.model || '')} ${escapeHtml(a.brand || '')}</div>
            </td>
            <td>${typeBadge}</td>
            <td>${formatDate(a.start_date)}</td>
            <td>${a.end_date ? formatDate(a.end_date) : '<span class="text-success fw-bold">En cours</span>'}</td>
            <td>${duree}</td>
            <td>${statusBadge}</td>
        </tr>`;
    }).join('');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER SINISTRES

function renderSinistres(sinistres) {
    const tbody = document.getElementById('sinistres_tbody');
    document.getElementById('sinistres_count').innerText = sinistres.length;

    if (sinistres.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">Aucun sinistre</td></tr>`;
        return;
    }

    tbody.innerHTML = sinistres.map(s => {
        const statusBadge =
            s.status === 'ouvert'   ? '<span class="badge bg-danger">Ouvert</span>'  :
            s.status === 'en_cours' ? '<span class="badge bg-warning text-dark">En cours</span>' :
            '<span class="badge bg-success">Clôturé</span>';

        return `
        <tr onclick="window.location.href='/car/detail/${s.car_id}'" style="cursor:pointer;">
            <td class="ps-3">${formatDate(s.date_sinistre)}</td>
            <td>
                <div class="fw-bold small">${escapeHtml(s.plate_number || '—')}</div>
                <div class="text-muted" style="font-size:11px;">${escapeHtml(s.model || '')}</div>
            </td>
            <td><span class="badge bg-light text-dark border">${escapeHtml(s.type)}</span></td>
            <td>${statusBadge}</td>
            <td>${s.montant_reparation ? s.montant_reparation + ' DT' : '—'}</td>
        </tr>`;
    }).join('');
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