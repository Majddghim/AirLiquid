////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

const carId = window.location.pathname.split('/').pop();

document.addEventListener("DOMContentLoaded", async () => {
    if (!carId) return;
    await loadCarDetail();
});

////////////////////////////////////////////////////////////////////////////////////////////////
// LOAD CAR DETAIL

async function loadCarDetail() {
    try {
        const res  = await fetch(`/car/detail-data/${carId}`);
        const data = await res.json();

        if (data.status !== "success") {
            Swal.fire({ icon: "error", title: "Erreur", text: data.message });
            return;
        }

        const d = data.data;

        renderHeader(d.car);
        renderCarteGrise(d.car);
        renderDocuments(d.documents);
        renderAffectation(d.affectation);

        document.getElementById("detail-loading").style.display = "none";
        document.getElementById("detail-content").style.display = "block";

    } catch (e) {
        console.error("loadCarDetail error:", e);
        Swal.fire({ icon: "error", title: "Erreur serveur", text: "Impossible de charger le dossier." });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER HEADER

function renderHeader(car) {
    document.getElementById("detail_title").innerText =
        `${car.model || 'Véhicule inconnu'} — ${car.brand || ''}`;

    document.getElementById("detail_plate").innerText = car.plate_number || 'N/A';

    const statusBadge = document.getElementById("detail_status_badge");
    const status = (car.status || '').toLowerCase();
    if      (status === 'active')      { statusBadge.className = 'badge bg-success'; statusBadge.innerText = 'Opérationnel'; }
    else if (status === 'maintenance') { statusBadge.className = 'badge bg-warning text-dark'; statusBadge.innerText = 'Maintenance'; }
    else if (status === 'inactive')    { statusBadge.className = 'badge bg-secondary'; statusBadge.innerText = 'Hors Service'; }
    else if (status === 'retired')     { statusBadge.className = 'badge bg-dark'; statusBadge.innerText = 'Retiré'; }
    else                               { statusBadge.className = 'badge bg-secondary'; statusBadge.innerText = car.status || 'N/A'; }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER CARTE GRISE

function renderCarteGrise(car) {
    const fields = [
        { label: 'Modèle',            value: car.model },
        { label: 'Marque',            value: car.brand },
        { label: 'Année',             value: car.year },
        { label: 'Immatriculation',   value: car.plate_number, mono: true, primary: true },
        { label: 'Propriétaire',      value: car.owner_name },
        { label: 'Châssis (VIN)',     value: car.chassis_number, mono: true },
        { label: 'Puissance fiscale', value: car.puissance_fiscale ? `${car.puissance_fiscale} CV` : null },
        { label: 'Carburant',         value: car.carburant },
        { label: 'Date 1ère circ.',   value: formatDate(car.registration_date) },
        { label: 'Expiration CG',     value: formatDate(car.expiration_date), danger: isExpired(car.expiration_date) },
        { label: 'Date acquisition',  value: formatDate(car.acquisition_date) },
        { label: 'Notes',             value: car.notes },
    ];

    document.getElementById("cg_detail").innerHTML = fields.map(f => `
        <div class="col-md-3 col-sm-6 mb-4">
            <div class="info-label">${f.label}</div>
            <div class="info-value ${f.mono ? 'font-monospace' : ''} ${f.primary ? 'text-primary' : ''} ${f.danger ? 'text-danger' : ''}">
                ${escapeHtml(f.value || '—')}
            </div>
        </div>
    `).join('');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER DOCUMENTS

function renderDocuments(docs) {
    let missingCount = 0;

    const assurance = docs.assurance;
    const vignette  = docs.vignette;
    const visite    = docs.visite;

    if (!assurance) missingCount++;
    if (!vignette)  missingCount++;
    if (!visite)    missingCount++;

    if (missingCount > 0) {
        const badge = document.getElementById("docs_missing_badge");
        badge.style.display = "inline";
        badge.innerText = `${missingCount} manquant${missingCount > 1 ? 's' : ''}`;
    }

    document.getElementById("docs_detail").innerHTML = `

        <!-- Assurance -->
        <div class="col-md-4 mb-3">
            <div class="card border-0 bg-light h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div class="d-flex align-items-center">
                            <div class="bg-primary bg-opacity-10 p-2 rounded me-2">
                                <i class="fas fa-shield-alt text-primary" style="font-size:13px;"></i>
                            </div>
                            <span class="fw-bold small">Assurance</span>
                        </div>
                        ${docStatusBadge(assurance, 'end_date')}
                    </div>
                    ${assurance ? `
                        <div class="info-label">Assureur</div>
                        <div class="info-value mb-2">${escapeHtml(assurance.insurer || '—')}</div>
                        <div class="info-label">N° Police</div>
                        <div class="info-value mb-2 font-monospace small">${escapeHtml(assurance.policy_number || '—')}</div>
                        <div class="row">
                            <div class="col-6">
                                <div class="info-label">Début</div>
                                <div class="info-value small">${formatDate(assurance.start_date)}</div>
                            </div>
                            <div class="col-6">
                                <div class="info-label">Fin</div>
                                <div class="info-value small ${isExpired(assurance.end_date) ? 'text-danger fw-bold' : ''}">${formatDate(assurance.end_date)}</div>
                            </div>
                        </div>
                        ${assurance.file_path ? `<a href="/${assurance.file_path}" target="_blank" class="btn btn-outline-primary btn-sm w-100 mt-3"><i class="fas fa-file-alt me-1"></i> Voir le document</a>` : ''}
                    ` : `
                        <div class="text-center py-3 text-muted">
                            <i class="fas fa-exclamation-circle text-warning mb-2"></i>
                            <p class="small mb-0">Non enregistrée</p>
                        </div>
                    `}
                </div>
            </div>
        </div>

        <!-- Vignette -->
        <div class="col-md-4 mb-3">
            <div class="card border-0 bg-light h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div class="d-flex align-items-center">
                            <div class="bg-success bg-opacity-10 p-2 rounded me-2">
                                <i class="fas fa-receipt text-success" style="font-size:13px;"></i>
                            </div>
                            <span class="fw-bold small">Vignette</span>
                        </div>
                        ${docStatusBadge(vignette, 'expiration_date')}
                    </div>
                    ${vignette ? `
                        <div class="info-label">Année</div>
                        <div class="info-value mb-2">${escapeHtml(vignette.year || '—')}</div>
                        <div class="info-label">Montant</div>
                        <div class="info-value mb-2">${vignette.montant ? vignette.montant + ' DT' : '—'}</div>
                        <div class="info-label">Expiration</div>
                        <div class="info-value ${isExpired(vignette.expiration_date) ? 'text-danger fw-bold' : ''}">${formatDate(vignette.expiration_date)}</div>
                        ${vignette.file_path ? `<a href="/${vignette.file_path}" target="_blank" class="btn btn-outline-success btn-sm w-100 mt-3"><i class="fas fa-file-alt me-1"></i> Voir le document</a>` : ''}
                    ` : `
                        <div class="text-center py-3 text-muted">
                            <i class="fas fa-exclamation-circle text-warning mb-2"></i>
                            <p class="small mb-0">Non enregistrée</p>
                        </div>
                    `}
                </div>
            </div>
        </div>

        <!-- Visite Technique -->
        <div class="col-md-4 mb-3">
            <div class="card border-0 bg-light h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div class="d-flex align-items-center">
                            <div class="bg-info bg-opacity-10 p-2 rounded me-2">
                                <i class="fas fa-tools text-info" style="font-size:13px;"></i>
                            </div>
                            <span class="fw-bold small">Visite Technique</span>
                        </div>
                        ${docStatusBadge(visite, 'expiration_date')}
                    </div>
                    ${visite ? `
                        <div class="info-label">Montant</div>
                        <div class="info-value mb-2">${visite.montant ? visite.montant + ' DT' : '—'}</div>
                        <div class="info-label">Expiration</div>
                        <div class="info-value ${isExpired(visite.expiration_date) ? 'text-danger fw-bold' : ''}">${formatDate(visite.expiration_date)}</div>
                        ${visite.file_path ? `<a href="/${visite.file_path}" target="_blank" class="btn btn-outline-info btn-sm w-100 mt-3"><i class="fas fa-file-alt me-1"></i> Voir le document</a>` : ''}
                    ` : `
                        <div class="text-center py-3 text-muted">
                            <i class="fas fa-exclamation-circle text-warning mb-2"></i>
                            <p class="small mb-0">Non enregistrée</p>
                        </div>
                    `}
                </div>
            </div>
        </div>
    `;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER AFFECTATION BANNER

function renderAffectation(affectation) {
    const el = document.getElementById("affectation_content");

    if (!affectation) {
        el.innerHTML = `
            <div class="text-muted d-flex align-items-center">
                <i class="fas fa-user-slash me-3 fa-lg opacity-50"></i>
                <div>
                    <div class="fw-bold small">Aucun employé affecté</div>
                    <div class="text-xs">Vous pouvez affecter un employé depuis la liste des véhicules.</div>
                </div>
            </div>`;
        // grey out the border when not assigned
        document.getElementById("affectation_banner").style.borderLeftColor = "#dee2e6";
        return;
    }

    el.innerHTML = `
        <div class="bg-success bg-opacity-10 p-2 rounded me-3">
            <i class="fas fa-user-tag text-success fa-lg"></i>
        </div>
        <div class="flex-grow-1">
            <div class="fw-bold text-dark">
                ${escapeHtml(affectation.prenom)} ${escapeHtml(affectation.nom)}
            </div>
            <div class="text-muted small">
                ${escapeHtml(affectation.poste || '')}
                ${affectation.departement ? ' — ' + escapeHtml(affectation.departement) : ''}
            </div>
        </div>
        <div class="text-end">
            <div class="info-label">Affecté depuis</div>
            <div class="fw-bold small text-success">${formatDate(affectation.start_date)}</div>
        </div>`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// HELPERS

function docStatusBadge(doc, dateField) {
    if (!doc) return '<span class="badge bg-warning text-dark doc-badge">Manquant</span>';
    if (isExpired(doc[dateField])) return '<span class="badge bg-danger doc-badge">Expiré</span>';
    return '<span class="badge bg-success doc-badge">Valide</span>';
}

function isExpired(dateStr) {
    if (!dateStr) return false;
    return new Date(dateStr) < new Date();
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return d.toLocaleDateString('fr-TN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}