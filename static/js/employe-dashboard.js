////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboard();
});

////////////////////////////////////////////////////////////////////////////////////////////////
// LOAD DATA

async function loadDashboard() {
    try {
        const res  = await fetch('/employe/dashboard-data');
        const data = await res.json();

        if (data.status !== 'success') {
            window.location.href = '/employe/login';
            return;
        }

        const d = data.data;
        renderHeader(d.employe);
        renderCar(d.cars);
        renderSinistres(d.sinistres);
        renderProfil(d.employe);

    } catch (e) {
        console.error('loadDashboard error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER HEADER

function renderHeader(emp) {
    const initials = `${(emp.prenom||'E')[0]}${(emp.nom||'P')[0]}`.toUpperCase();
    document.getElementById('header_avatar').innerText = initials;
    document.getElementById('header_name').innerText   = `${emp.prenom} ${emp.nom}`;
    document.getElementById('header_post').innerText   = `${emp.poste || ''} — ${emp.departement || ''}`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER CAR

function renderCar(cars) {
    const el = document.getElementById('car_content');

    if (!cars || cars.length === 0) {
        el.innerHTML = `
            <div class="dash-card mt-3">
                <div class="dash-card-body empty-state">
                    <i class="fas fa-car-slash d-block"></i>
                    <p>Aucun véhicule affecté</p>
                    <small>Contactez votre responsable RH</small>
                </div>
            </div>`;
        return;
    }

    el.innerHTML = cars.map(c => {
        const isReplacement = c.notes && c.notes.includes('Remplacement');
        const statusColor   = c.car_status === 'active'      ? '#198754' :
                              c.car_status === 'maintenance'  ? '#ffc107' : '#6c757d';
        const statusLabel   = c.car_status === 'active'      ? 'Opérationnel' :
                              c.car_status === 'maintenance'  ? 'En maintenance' : 'Inactif';

        return `
        <div class="dash-card mt-3">
            <div class="dash-card-header">
                <div class="d-flex align-items-center">
                    <div class="card-icon" style="background:#ebf4ff;">
                        <i class="fas fa-car text-primary"></i>
                    </div>
                    <div>
                        <div class="fw-bold text-dark" style="font-size:14px;">
                            ${escapeHtml(c.brand || '')} ${escapeHtml(c.model || '')}
                        </div>
                        <div class="font-monospace text-muted" style="font-size:12px;">
                            ${escapeHtml(c.plate_number || '')}
                        </div>
                    </div>
                </div>
                <span class="status-pill"
                    style="background:${statusColor}20;color:${statusColor};">
                    ${statusLabel}
                </span>
            </div>
            <div class="dash-card-body">
                ${isReplacement ? `
                <div class="replacement-badge mb-3">
                    <i class="fas fa-exchange-alt"></i>
                    Véhicule de remplacement temporaire
                </div>` : ''}
                <div class="info-row">
                    <span class="info-label">Modèle</span>
                    <span class="info-value">${escapeHtml(c.model || '—')} (${c.year || '—'})</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Marque</span>
                    <span class="info-value">${escapeHtml(c.brand || '—')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Affecté depuis</span>
                    <span class="info-value">${formatDate(c.start_date)}</span>
                </div>
                ${c.current_km ? `
                <div class="km-box">
                    <div class="info-label">Kilométrage actuel</div>
                    <div class="km-number">${Number(c.current_km).toLocaleString()}</div>
                    <div class="km-label">km — relevé le ${formatDate(c.km_date)}</div>
                </div>` : ''}
            </div>
        </div>`;
    }).join('');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER SINISTRES

function renderSinistres(sinistres) {
    const el = document.getElementById('sinistres_content');

    if (!sinistres || sinistres.length === 0) {
        el.innerHTML = `
            <div class="dash-card mt-3">
                <div class="dash-card-body empty-state">
                    <i class="fas fa-shield-check d-block" style="color:#198754;opacity:0.4;"></i>
                    <p>Aucun sinistre enregistré</p>
                    <small>Votre historique est vide</small>
                </div>
            </div>`;
        return;
    }

    el.innerHTML = `<div class="mt-3">` + sinistres.map(s => {
        const statusLabel = s.status === 'ouvert'   ? 'Ouvert'   :
                            s.status === 'en_cours' ? 'En cours' : 'Clôturé';
        const statusClass = s.status === 'ouvert'   ? 'bg-danger'              :
                            s.status === 'en_cours' ? 'bg-warning text-dark'   : 'bg-success';
        return `
        <div class="sinistre-card ${s.status}">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                    <div class="fw-bold" style="font-size:13px;">
                        ${escapeHtml(s.plate_number || '')} — ${escapeHtml(s.model || '')}
                    </div>
                    <div class="text-muted" style="font-size:11px;">
                        ${formatDate(s.date_sinistre)} · ${escapeHtml(s.type)}
                    </div>
                </div>
                <span class="badge ${statusClass}" style="font-size:10px;">${statusLabel}</span>
            </div>
            ${s.description ? `
            <div class="text-muted" style="font-size:12px;line-height:1.4;">
                ${escapeHtml(s.description)}
            </div>` : ''}
            ${s.montant_reparation ? `
            <div class="mt-2 fw-bold" style="font-size:13px;color:#0d6efd;">
                ${Number(s.montant_reparation).toLocaleString()} DT
            </div>` : ''}
        </div>`;
    }).join('') + `</div>`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER PROFIL

function renderProfil(emp) {
    document.getElementById('profil_content').innerHTML = `
        <div class="dash-card mt-3">
            <div class="dash-card-body">
                <div class="text-center mb-4 pt-2">
                    <div class="avatar-circle">
                        ${(emp.prenom||'E')[0]}${(emp.nom||'P')[0]}
                    </div>
                    <div class="fw-bold text-dark" style="font-size:16px;">
                        ${escapeHtml(emp.prenom)} ${escapeHtml(emp.nom)}
                    </div>
                    <div class="text-muted" style="font-size:12px;">
                        ${escapeHtml(emp.poste || '')}
                    </div>
                </div>
                <div class="info-row">
                    <span class="info-label">Email</span>
                    <span class="info-value" style="font-size:12px;">${escapeHtml(emp.email || '—')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Téléphone</span>
                    <span class="info-value">${escapeHtml(emp.telephone || '—')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Département</span>
                    <span class="info-value">${escapeHtml(emp.departement || '—')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Poste</span>
                    <span class="info-value">${escapeHtml(emp.poste || '—')}</span>
                </div>
            </div>
        </div>`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// NAVIGATION

function switchSection(section) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`section_${section}`).classList.add('active');
    document.getElementById(`nav_${section}`).classList.add('active');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// HELPERS

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return d.toLocaleDateString('fr-TN', { day:'2-digit', month:'2-digit', year:'numeric' });
}