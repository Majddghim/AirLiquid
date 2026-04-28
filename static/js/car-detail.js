////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

const carId = window.location.pathname.split('/').pop();

document.addEventListener("DOMContentLoaded", async () => {
    if (!carId) return;
    await loadCarDetail();
    await loadMaintenance();
    await loadKmSection();
    await loadSinistres();
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
        renderAffectation(d.affectation, d.car.status);

        // fix voir tout links
        document.getElementById('voir_tout_maintenance').href = `/car/historique/${carId}?tab=maintenance`;
        document.getElementById('voir_tout_sinistres').href   = `/car/historique/${carId}?tab=sinistres`;

        document.getElementById("detail-loading").style.display = "none";
        document.getElementById("detail-content").style.display = "block";

    } catch (e) {
        console.error("loadCarDetail error:", e);
        Swal.fire({ icon: "error", title: "Erreur serveur", text: "Impossible de charger le dossier." });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// LOAD MAINTENANCE

async function loadMaintenance() {
    await loadMaintenanceAlerts();
    await loadMaintenanceRecords();
}

async function loadMaintenanceAlerts() {
    try {
        const res   = await fetch(`/maintenance/alerts/${carId}`);
        const data  = await res.json();
        const el    = document.getElementById('maintenance_alerts_content');
        const badge = document.getElementById('maintenance_alerts_badge');

        if (data.status !== 'success' || data.data.length === 0) {
            el.innerHTML = `
                <div class="text-center py-3 text-muted small">
                    <i class="fas fa-check-circle text-success me-1"></i>
                    Aucune maintenance planifiée
                </div>`;
            return;
        }

        badge.style.display = 'inline';
        badge.innerText = data.data.length;

        el.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0 small">
                    <thead class="table-light">
                        <tr class="text-xs text-uppercase text-muted">
                            <th>Pièce</th>
                            <th>Type</th>
                            <th>Échéance Date</th>
                            <th>Échéance KM</th>
                            <th class="text-end">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.data.map(a => {
                            const isOverdue = a.due_date && new Date(a.due_date) < new Date();
                            return `
                            <tr class="${isOverdue ? 'table-danger' : ''}">
                                <td><strong>${escapeHtml(a.part_name)}</strong><br>
                                    <span class="text-muted" style="font-size:11px;">${escapeHtml(a.category || '')}</span>
                                </td>
                                <td>
                                    ${a.alert_type === 'km' ? '<span class="badge bg-info text-dark">KM</span>' :
                                      a.alert_type === 'date' ? '<span class="badge bg-warning text-dark">Date</span>' :
                                      '<span class="badge bg-secondary">KM + Date</span>'}
                                </td>
                                <td>${a.due_date ? formatDate(a.due_date) : '—'}</td>
                                <td>${a.due_km ? a.due_km + ' km' : '—'}</td>
                                <td class="text-end">
                                    <button class="btn btn-success btn-sm"
                                        onclick="ouvrirLogMaintenance(${a.id}, ${a.part_id})">
                                        <i class="fas fa-check me-1"></i>Logger
                                    </button>
                                </td>
                            </tr>`;
                        }).join('')}
                    </tbody>
                </table>
            </div>`;
    } catch (e) {
        console.error('loadMaintenanceAlerts error:', e);
    }
}

async function loadMaintenanceRecords() {
    try {
        const res  = await fetch(`/maintenance/records/${carId}`);
        const data = await res.json();
        const el   = document.getElementById('maintenance_records_content');

        if (data.status !== 'success' || data.data.length === 0) {
            el.innerHTML = `
                <div class="text-center py-3 text-muted small">
                    <i class="fas fa-history me-1"></i>
                    Aucun entretien enregistré
                </div>`;
            return;
        }

        el.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0 small">
                    <thead class="table-light">
                        <tr class="text-xs text-uppercase text-muted">
                            <th>Pièce</th>
                            <th>Garage</th>
                            <th>Date</th>
                            <th>KM</th>
                            <th>Prochain</th>
                            <th>Statut</th>
                            <th class="text-end">Facture</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.data.map(r => `
                        <tr>
                            <td><strong>${escapeHtml(r.part_name)}</strong><br>
                                <span class="text-muted" style="font-size:11px;">${escapeHtml(r.category || '')}</span>
                            </td>
                            <td>${escapeHtml(r.garage_name || '—')}</td>
                            <td>${formatDate(r.done_at)}</td>
                            <td>${r.km_at_service ? r.km_at_service + ' km' : '—'}</td>
                            <td>
                                ${r.next_due_date ? '<span class="text-muted">' + formatDate(r.next_due_date) + '</span>' : ''}
                                ${r.next_due_km ? '<br><span class="text-muted">' + r.next_due_km + ' km</span>' : ''}
                                ${!r.next_due_date && !r.next_due_km ? '—' : ''}
                            </td>
                            <td>
                                ${r.status === 'done'
                                    ? '<span class="badge bg-success">Fait</span>'
                                    : '<span class="badge bg-warning text-dark">En attente</span>'}
                            </td>
                            <td class="text-end">
                                ${r.facture_id
                                    ? `<a href="/${r.facture_file}" target="_blank"
                                        class="btn btn-outline-primary btn-sm">
                                        <i class="fas fa-file-invoice me-1"></i>${r.montant_ttc ? r.montant_ttc + ' DT' : 'Voir'}
                                       </a>`
                                    : `<button class="btn btn-outline-secondary btn-sm"
                                        onclick="ouvrirFactureModal(${r.id})">
                                        <i class="fas fa-paperclip me-1"></i>Attacher
                                       </button>`
                                }
                            </td>
                        </tr>`).join('')}
                    </tbody>
                </table>
            </div>`;
    } catch (e) {
        console.error('loadMaintenanceRecords error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// KM SECTION

async function loadKmSection() {
    try {
        const res  = await fetch(`/maintenance/current-km/${carId}`);
        const data = await res.json();
        const currentEl = document.getElementById('km_current');

        if (data.status === 'success' && data.data) {
            const km = data.data;
            currentEl.innerHTML = `
                <div class="d-flex align-items-center gap-3 p-3 bg-light rounded">
                    <div class="bg-secondary bg-opacity-10 p-2 rounded">
                        <i class="fas fa-tachometer-alt text-secondary fa-lg"></i>
                    </div>
                    <div>
                        <div class="fw-bold text-dark" style="font-size:18px;">${km.km.toLocaleString()} km</div>
                        <div class="text-muted small">Relevé le ${formatDate(km.recorded_at)}</div>
                    </div>
                </div>`;
        } else {
            currentEl.innerHTML = `
                <div class="text-muted small p-2">
                    <i class="fas fa-info-circle me-1"></i>Aucun relevé KM enregistré
                </div>`;
        }

        await loadKmHistory();
    } catch (e) {
        console.error('loadKmSection error:', e);
    }
}

async function loadKmHistory() {
    try {
        const res  = await fetch(`/maintenance/km-history/${carId}`);
        const data = await res.json();
        const el   = document.getElementById('km_history_content');

        if (data.status !== 'success' || data.data.length === 0) {
            el.innerHTML = '';
            return;
        }

        // show last 5 entries
        const entries = data.data.slice(0, 5);
        el.innerHTML = `
            <table class="table table-sm align-middle mb-0 small mt-2">
                <thead class="table-light">
                    <tr class="text-xs text-uppercase text-muted">
                        <th>KM</th>
                        <th>Date</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    ${entries.map(k => `
                    <tr>
                        <td class="fw-bold">${k.km.toLocaleString()} km</td>
                        <td>${formatDate(k.recorded_at)}</td>
                        <td class="text-muted">${escapeHtml(k.notes || '—')}</td>
                    </tr>`).join('')}
                </tbody>
            </table>`;
    } catch (e) {
        console.error('loadKmHistory error:', e);
    }
}

function ouvrirLogKm() {
    document.getElementById('km_value').value = '';
    document.getElementById('km_date').value  = new Date().toISOString().split('T')[0];
    document.getElementById('km_notes').value = '';
    new bootstrap.Modal(document.getElementById('logKmModal')).show();
}

async function confirmerLogKm() {
    const km   = document.getElementById('km_value').value;
    const date = document.getElementById('km_date').value;

    if (!km) {
        Swal.fire({ icon: 'warning', title: 'Champ manquant', text: 'Veuillez saisir le kilométrage.' });
        return;
    }

    try {
        const res    = await fetch(`/maintenance/log-km/${carId}`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                km:          parseInt(km),
                recorded_at: date,
                notes:       document.getElementById('km_notes').value.trim() || null
            })
        });
        const result = await res.json();

        if (result.status === 'success') {
            bootstrap.Modal.getInstance(document.getElementById('logKmModal')).hide();
            Swal.fire({ icon: 'success', title: 'KM enregistré !', showConfirmButton: false, timer: 1500 });
            setTimeout(() => loadKmSection(), 1500);
        } else {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
        }
    } catch (e) {
        console.error('confirmerLogKm error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// BON DE COMMANDE

let bonData      = null;
let bonExtraItems = [];

async function ouvrirBonCommande() {
    try {
        const res  = await fetch(`/maintenance/bon-data/${carId}`);
        const data = await res.json();
        if (data.status !== 'success') {
            Swal.fire({ icon: 'error', title: 'Erreur', text: data.message });
            return;
        }
        bonData      = data.data;
        bonExtraItems = [];

        const garageSelect = document.getElementById('bon_garage_id');
        garageSelect.innerHTML = '<option value="">-- Sélectionner un garage --</option>';
        bonData.garages.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.text  = `${g.name} (${g.type === 'dealership' ? 'Concessionnaire' : 'Indépendant'})`;
            opt.dataset.garage = JSON.stringify(g);
            garageSelect.appendChild(opt);
        });

        const alertsList = document.getElementById('bon_alerts_list');
        if (bonData.alerts.length === 0) {
            alertsList.innerHTML = '<div class="text-muted small text-center py-2">Aucune alerte ouverte</div>';
        } else {
            alertsList.innerHTML = bonData.alerts.map(a => `
                <div class="form-check py-1 border-bottom">
                    <input class="form-check-input" type="checkbox"
                        value="${a.id}" id="alert_${a.id}"
                        data-part-id="${a.part_id}"
                        data-part-name="${escapeHtml(a.part_name)}"
                        data-category="${escapeHtml(a.category || '')}"
                        ${a.urgent ? 'checked' : ''}>
                    <label class="form-check-label small" for="alert_${a.id}">
                        <strong>${escapeHtml(a.part_name)}</strong>
                        ${a.category ? `<span class="text-muted"> — ${escapeHtml(a.category)}</span>` : ''}
                        ${a.urgent
                            ? '<span class="badge bg-danger ms-2">Urgent</span>'
                            : '<span class="badge bg-secondary ms-2">Optionnel</span>'}
                        ${a.due_date ? `<span class="text-danger ms-2"><i class="fas fa-calendar me-1"></i>${formatDate(a.due_date)}</span>` : ''}
                        ${a.due_km ? `<span class="text-info ms-2"><i class="fas fa-tachometer-alt me-1"></i>${a.due_km} km</span>` : ''}
                    </label>
                </div>`).join('');
        }

        document.getElementById('bon_extra_items').innerHTML = '';
        new bootstrap.Modal(document.getElementById('bonCommandeModal')).show();
    } catch (e) {
        console.error('ouvrirBonCommande error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de charger les données.' });
    }
}

function ajouterLigneBon() {
    const container = document.getElementById('bon_extra_items');
    const idx = Date.now();
    const partOptions = bonData.parts.map(p =>
        `<option value="${p.id}" data-name="${escapeHtml(p.name)}" data-category="${escapeHtml(p.category || '')}">${escapeHtml(p.name)}${p.category ? ' — ' + escapeHtml(p.category) : ''}</option>`
    ).join('');

    const div = document.createElement('div');
    div.className = 'd-flex gap-2 mb-2 align-items-center';
    div.id = `extra_${idx}`;
    div.innerHTML = `
        <select class="form-select form-select-sm bg-light border-0" id="extra_part_${idx}">
            <option value="">-- Sélectionner une pièce --</option>
            ${partOptions}
        </select>
        <input type="text" class="form-control form-control-sm bg-light border-0"
            id="extra_notes_${idx}" placeholder="Remarques...">
        <button class="btn btn-outline-danger btn-sm rounded-circle"
            onclick="document.getElementById('extra_${idx}').remove()">
            <i class="fas fa-times"></i>
        </button>`;
    container.appendChild(div);
}

async function genererBon() {
    const garageSelect = document.getElementById('bon_garage_id');
    const garageOpt    = garageSelect.options[garageSelect.selectedIndex];

    if (!garageSelect.value) {
        Swal.fire({ icon: 'warning', title: 'Garage manquant', text: 'Veuillez sélectionner un garage.' });
        return;
    }

    const garage = JSON.parse(garageOpt.dataset.garage);
    const items  = [];

    document.querySelectorAll('#bon_alerts_list input[type=checkbox]:checked').forEach(cb => {
        items.push({ part_name: cb.dataset.partName, category: cb.dataset.category, notes: '' });
    });

    document.querySelectorAll('#bon_extra_items > div').forEach(row => {
        const select = row.querySelector('select');
        const notes  = row.querySelector('input[type=text]');
        if (select && select.value) {
            const opt = select.options[select.selectedIndex];
            items.push({ part_name: opt.dataset.name, category: opt.dataset.category, notes: notes ? notes.value.trim() : '' });
        }
    });

    if (items.length === 0) {
        Swal.fire({ icon: 'warning', title: 'Aucun travail', text: 'Veuillez sélectionner au moins un travail.' });
        return;
    }

    const payload = { car: bonData.car, garage, items, date: new Date().toLocaleDateString('fr-TN') };

    try {
        const res  = await fetch('/maintenance/bon/generate', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
        });
        const html = await res.text();
        const tab  = window.open('', '_blank');
        tab.document.write(html);
        tab.document.close();
        bootstrap.Modal.getInstance(document.getElementById('bonCommandeModal')).hide();
    } catch (e) {
        console.error('genererBon error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur', text: 'Impossible de générer le bon.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// LOG MAINTENANCE

let logPartsCache   = [];
let logGaragesCache = [];
let currentPartIntervals = null;

async function ouvrirLogMaintenance(alertId = null, partId = null) {
    try {
        if (logPartsCache.length === 0) {
            const res  = await fetch('/maintenance/bon-data/' + carId);
            const data = await res.json();
            if (data.status === 'success') {
                logPartsCache   = data.data.parts;
                logGaragesCache = data.data.garages;
            }
        }

        // reset form
        document.getElementById('log_alert_id').value              = alertId || '';
        document.getElementById('log_done_at').value               = new Date().toISOString().split('T')[0];
        document.getElementById('log_km').value                    = '';
        document.getElementById('log_next_date').value             = '';
        document.getElementById('log_next_km').value               = '';
        document.getElementById('log_notes').value                 = '';
        document.getElementById('log_next_date_hint').innerText    = '';
        document.getElementById('log_next_km_hint').innerText      = '';
        document.getElementById('log_facture_num').value           = '';
        document.getElementById('log_facture_num_reglement').value = '';
        document.getElementById('log_facture_date').value          = '';
        document.getElementById('log_facture_date_reglement').value= '';
        document.getElementById('log_facture_montant_ht').value    = '';
        document.getElementById('log_facture_tva').value           = '';
        document.getElementById('log_facture_montant_ttc').value   = '';
        currentPartIntervals = null;

        // fill parts
        const partSelect = document.getElementById('log_part_id');
        partSelect.innerHTML = '<option value="">-- Sélectionner --</option>';
        logPartsCache.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.text  = p.name + (p.category ? ' — ' + p.category : '');
            partSelect.appendChild(opt);
        });
        if (partId) {
            partSelect.value = partId;
            await onLogPartChange();
        }

        // fill garages
        const garageSelect = document.getElementById('log_garage_id');
        garageSelect.innerHTML = '<option value="">-- Sélectionner --</option>';
        logGaragesCache.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.text  = g.name;
            garageSelect.appendChild(opt);
        });

        // prefill current KM
        const kmRes  = await fetch(`/maintenance/current-km/${carId}`);
        const kmData = await kmRes.json();
        if (kmData.status === 'success' && kmData.data) {
            document.getElementById('log_km').value = kmData.data.km;
            onLogDateOrKmChange();
        }

        new bootstrap.Modal(document.getElementById('logMaintenanceModal')).show();
    } catch (e) {
        console.error('ouvrirLogMaintenance error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de charger les données.' });
    }
}

async function onLogPartChange() {
    const partId = document.getElementById('log_part_id').value;
    if (!partId) {
        currentPartIntervals = null;
        document.getElementById('log_next_date_hint').innerText = '';
        document.getElementById('log_next_km_hint').innerText   = '';
        return;
    }
    try {
        const res  = await fetch(`/maintenance/part-intervals/${partId}`);
        const data = await res.json();
        if (data.status === 'success' && data.data) {
            currentPartIntervals = data.data;
            const kmInterval    = data.data.alert_km_interval;
            const monthInterval = data.data.alert_month_interval;
            document.getElementById('log_next_km_hint').innerText   = kmInterval    ? `(intervalle: ${kmInterval} km)` : '';
            document.getElementById('log_next_date_hint').innerText = monthInterval ? `(intervalle: ${monthInterval} mois)` : '';
            onLogDateOrKmChange();
        }
    } catch (e) {
        console.error('onLogPartChange error:', e);
    }
}

function onLogDateOrKmChange() {
    if (!currentPartIntervals) return;

    const km        = parseInt(document.getElementById('log_km').value);
    const doneAt    = document.getElementById('log_done_at').value;
    const kmInt     = currentPartIntervals.alert_km_interval;
    const monthInt  = currentPartIntervals.alert_month_interval;

    if (km && kmInt) {
        document.getElementById('log_next_km').value = km + kmInt;
    }

    if (doneAt && monthInt) {
        const d = new Date(doneAt);
        d.setMonth(d.getMonth() + monthInt);
        document.getElementById('log_next_date').value = d.toISOString().split('T')[0];
    }
}

async function confirmerLogMaintenance() {
    const partId = document.getElementById('log_part_id').value;
    const doneAt = document.getElementById('log_done_at').value;

    if (!partId) {
        Swal.fire({ icon: 'warning', title: 'Champ manquant', text: 'Veuillez sélectionner une pièce.' });
        return;
    }
    if (!doneAt) {
        Swal.fire({ icon: 'warning', title: 'Champ manquant', text: 'Veuillez saisir la date.' });
        return;
    }

    const payload = {
        part_id:       parseInt(partId),
        garage_id:     document.getElementById('log_garage_id').value || null,
        done_at:       doneAt,
        km_at_service: document.getElementById('log_km').value || null,
        next_due_date: document.getElementById('log_next_date').value || null,
        next_due_km:   document.getElementById('log_next_km').value || null,
        notes:         document.getElementById('log_notes').value.trim() || null,
        alert_id:      document.getElementById('log_alert_id').value || null
    };

    try {
        const res    = await fetch(`/maintenance/log/${carId}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
        });
        const result = await res.json();

        if (result.status !== 'success') {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
            return;
        }

        const recordId = result.record_id;

        // attach facture if any facture fields filled
        const factureNum = document.getElementById('log_facture_num').value.trim();
        const factureTtc = document.getElementById('log_facture_montant_ttc').value;
        const factureFile = document.getElementById('log_facture_file').files[0];

        if (factureNum || factureTtc || factureFile) {
            const formData = new FormData();
            formData.append('car_id',        carId);
            formData.append('num_facture',   factureNum);
            formData.append('num_reglement', document.getElementById('log_facture_num_reglement').value.trim());
            formData.append('date_facture',  document.getElementById('log_facture_date').value);
            formData.append('date_reglement',document.getElementById('log_facture_date_reglement').value);
            formData.append('montant_ht',    document.getElementById('log_facture_montant_ht').value);
            formData.append('tva',           document.getElementById('log_facture_tva').value);
            formData.append('montant_ttc',   factureTtc);
            if (factureFile) formData.append('file', factureFile);

            await fetch(`/maintenance/facture/attach/${recordId}`, { method: 'POST', body: formData });
        }

        bootstrap.Modal.getInstance(document.getElementById('logMaintenanceModal')).hide();
        await loadMaintenance();
        await loadKmSection();
        Swal.fire({ icon: 'success', title: 'Enregistré !', text: 'Entretien logué avec succès.', showConfirmButton: false, timer: 2000 });

    } catch (e) {
        console.error('confirmerLogMaintenance error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// FACTURE (standalone — for attaching later)

function ouvrirFactureModal(recordId) {
    document.getElementById('facture_record_id').value      = recordId;
    document.getElementById('facture_num').value            = '';
    document.getElementById('facture_num_reglement').value  = '';
    document.getElementById('facture_date').value           = '';
    document.getElementById('facture_date_reglement').value = '';
    document.getElementById('facture_montant_ht').value     = '';
    document.getElementById('facture_tva').value            = '';
    document.getElementById('facture_montant_ttc').value    = '';
    new bootstrap.Modal(document.getElementById('factureModal')).show();
}

async function confirmerAttacherFacture() {
    const recordId = document.getElementById('facture_record_id').value;
    const formData = new FormData();
    formData.append('car_id',          carId);
    formData.append('num_facture',      document.getElementById('facture_num').value.trim());
    formData.append('num_reglement',    document.getElementById('facture_num_reglement').value.trim());
    formData.append('date_facture',     document.getElementById('facture_date').value);
    formData.append('date_reglement',   document.getElementById('facture_date_reglement').value);
    formData.append('montant_ht',       document.getElementById('facture_montant_ht').value);
    formData.append('tva',              document.getElementById('facture_tva').value);
    formData.append('montant_ttc',      document.getElementById('facture_montant_ttc').value);
    const fileInput = document.getElementById('facture_file');
    if (fileInput.files.length > 0) formData.append('file', fileInput.files[0]);

    try {
        const res    = await fetch(`/maintenance/facture/attach/${recordId}`, { method: 'POST', body: formData });
        const result = await res.json();
        if (result.status === 'success') {
            bootstrap.Modal.getInstance(document.getElementById('factureModal')).hide();
            Swal.fire({ icon: 'success', title: 'Facture attachée !', showConfirmButton: false, timer: 2000 });
            setTimeout(() => loadMaintenanceRecords(), 2000);
        } else {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
        }
    } catch (e) {
        console.error('confirmerAttacherFacture error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
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
// RENDER AFFECTATION

function renderAffectation(affectation, carStatus) {
    const el = document.getElementById("affectation_content");
    if (!affectation) {
        if (carStatus === 'maintenance') {
            el.innerHTML = `
                <div class="text-warning d-flex align-items-center">
                    <i class="fas fa-tools me-3 fa-lg"></i>
                    <div>
                        <div class="fw-bold small">Véhicule en maintenance</div>
                        <div class="text-xs text-muted">L'employé est temporairement affecté à un véhicule de remplacement.</div>
                    </div>
                </div>`;
            document.getElementById("affectation_banner").style.borderLeftColor = "#ffc107";
        } else {
            el.innerHTML = `
                <div class="text-muted d-flex align-items-center">
                    <i class="fas fa-user-slash me-3 fa-lg opacity-50"></i>
                    <div>
                        <div class="fw-bold small">Aucun employé affecté</div>
                        <div class="text-xs">Vous pouvez affecter un employé depuis la liste des véhicules.</div>
                    </div>
                </div>`;
            document.getElementById("affectation_banner").style.borderLeftColor = "#dee2e6";
        }
        return;
    }
    el.innerHTML = `
        <div class="bg-success bg-opacity-10 p-2 rounded me-3">
            <i class="fas fa-user-tag text-success fa-lg"></i>
        </div>
        <div class="flex-grow-1">
            <div class="fw-bold text-dark">${escapeHtml(affectation.prenom)} ${escapeHtml(affectation.nom)}</div>
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
// SINISTRES

async function loadSinistres() {
    try {
        const res   = await fetch(`/sinistre/by-car/${carId}`);
        const data  = await res.json();
        const el    = document.getElementById('sinistres_content');
        const badge = document.getElementById('sinistres_badge');

        if (data.status !== 'success' || data.data.length === 0) {
            el.innerHTML = `
                <div class="text-center py-3 text-muted small">
                    <i class="fas fa-check-circle text-success me-1"></i>
                    Aucun sinistre enregistré
                </div>`;
            return;
        }

        const open = data.data.filter(s => s.status !== 'cloture');
        if (open.length > 0) {
            badge.style.display = 'inline';
            badge.innerText = open.length;
        }

        // show last 3 only — full list on history page
        const preview = data.data.slice(0, 3);

        el.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0 small">
                    <thead class="table-light">
                        <tr class="text-xs text-uppercase text-muted">
                            <th>Date</th>
                            <th>Type</th>
                            <th>Employé</th>
                            <th>Statut</th>
                            <th>Prise en charge</th>
                            <th class="text-end">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${preview.map(s => {
                            const statusBadge =
                                s.status === 'ouvert'   ? '<span class="badge bg-danger">Ouvert</span>' :
                                s.status === 'en_cours' ? '<span class="badge bg-warning text-dark">En cours</span>' :
                                '<span class="badge bg-success">Clôturé</span>';
                            return `
                            <tr>
                                <td>${formatDate(s.date_sinistre)}</td>
                                <td><span class="badge bg-light text-dark border">${escapeHtml(s.type)}</span></td>
                                <td>${s.nom ? escapeHtml(s.prenom + ' ' + s.nom) : '—'}</td>
                                <td>${statusBadge}</td>
                                <td>
                                    ${s.facture_id
                                        ? `<a href="/${s.facture_file}" target="_blank" class="btn btn-outline-primary btn-sm">
                                            <i class="fas fa-file-invoice me-1"></i>${s.montant_ttc ? s.montant_ttc + ' DT' : 'Voir'}
                                           </a>`
                                        : `<button class="btn btn-outline-secondary btn-sm"
                                            onclick="ouvrirFactureSinistreModal(${s.id})">
                                            <i class="fas fa-paperclip me-1"></i>Facture
                                           </button>`
                                    }
                                </td>
                                <td class="text-end">
                                    <div class="btn-group btn-group-sm">
                                        ${s.status !== 'cloture' ? `
                                        <button class="btn btn-outline-success border-0 rounded-circle"
                                            title="Clôturer"
                                            onclick="ouvrirClotureSinistre(${s.id}, ${s.employee_id || 'null'}, ${s.replacement_car_id || 'null'})">
                                            <i class="fas fa-check"></i>
                                        </button>` : ''}
                                    </div>
                                </td>
                            </tr>`;
                        }).join('')}
                    </tbody>
                </table>
            </div>`;
    } catch (e) {
        console.error('loadSinistres error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// DECLARER SINISTRE

let sinEmployeesCache = [];

async function ouvrirDeclarerSinistre() {
    // reset form
    document.getElementById('sin_date').value          = new Date().toISOString().split('T')[0];
    document.getElementById('sin_type').value          = '';
    document.getElementById('sin_n_constat').value     = '';
    document.getElementById('sin_date_constat').value  = '';
    document.getElementById('sin_description').value   = '';
    document.getElementById('sin_set_maintenance').checked              = false;
    document.getElementById('sin_assign_replacement').checked           = false;
    document.getElementById('sin_replacement_section').style.display   = 'none';
    document.getElementById('sin_replacement_car_section').style.display = 'none';
    document.getElementById('sin_pec_societe').checked = true;

    // load employees + pre-select current assignee
    try {
        const [empRes, affRes] = await Promise.all([
            fetch('/car/get-employes-list'),
            fetch(`/car/get-affectation/${carId}`)
        ]);
        const empData = await empRes.json();
        const affData = await affRes.json();

        const sel = document.getElementById('sin_employee_id');
        sel.innerHTML = '<option value="">-- Sélectionner --</option>';

        if (empData.status === 'success') {
            sinEmployeesCache = empData.data;
            empData.data.forEach(e => {
                const opt = document.createElement('option');
                opt.value = e.id;
                opt.text  = `${e.prenom} ${e.nom} — ${e.poste}`;
                sel.appendChild(opt);
            });
        }

        // pre-select current assignee if car is assigned
        if (affData.status === 'success' && affData.assigned) {
            sel.value = affData.data.employee_id;
        }

    } catch (e) {
        console.error('load employees error:', e);
    }

    new bootstrap.Modal(document.getElementById('declarerSinistreModal')).show();
}

function onSinSetMaintenanceChange() {
    const checked = document.getElementById('sin_set_maintenance').checked;
    document.getElementById('sin_replacement_section').style.display = checked ? 'block' : 'none';
    if (!checked) {
        document.getElementById('sin_assign_replacement').checked = false;
        document.getElementById('sin_replacement_car_section').style.display = 'none';
    }
}

async function onSinAssignReplacementChange() {
    const checked = document.getElementById('sin_assign_replacement').checked;
    const section = document.getElementById('sin_replacement_car_section');
    section.style.display = checked ? 'block' : 'none';

    if (checked) {
        try {
            const res  = await fetch('/sinistre/available-cars');
            const data = await res.json();
            const sel  = document.getElementById('sin_replacement_car_id');
            sel.innerHTML = '<option value="">-- Sélectionner --</option>';
            if (data.status === 'success') {
                data.data.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.text  = `${c.plate_number} — ${c.model || ''} ${c.brand || ''}`;
                    sel.appendChild(opt);
                });
            }
        } catch (e) {
            console.error('load available cars error:', e);
        }
    }
}

async function confirmerDeclarerSinistre() {
    const date = document.getElementById('sin_date').value;
    const type = document.getElementById('sin_type').value;

    if (!date) {
        Swal.fire({ icon: 'warning', title: 'Champ manquant', text: 'Veuillez saisir la date.' });
        return;
    }
    if (!type) {
        Swal.fire({ icon: 'warning', title: 'Champ manquant', text: 'Veuillez sélectionner le type.' });
        return;
    }

    const formData = new FormData();
    formData.append('date_sinistre',    date);
    formData.append('type_sinistre',    type);
    formData.append('employee_id',      document.getElementById('sin_employee_id').value || '');
    formData.append('n_constat',        document.getElementById('sin_n_constat').value.trim());
    formData.append('date_constat',     document.getElementById('sin_date_constat').value);
    formData.append('description',      document.getElementById('sin_description').value.trim());
    formData.append('set_maintenance',  document.getElementById('sin_set_maintenance').checked ? 'true' : 'false');
    formData.append('prise_en_charge',  document.querySelector('input[name="sin_prise_en_charge"]:checked').value);

    const replacementCar = document.getElementById('sin_replacement_car_id').value;
    if (replacementCar) formData.append('replacement_car_id', replacementCar);

    const constatFile = document.getElementById('sin_constat_file').files[0];
    if (constatFile) formData.append('constat_file', constatFile);

    try {
        const res    = await fetch(`/sinistre/declarer/${carId}`, { method: 'POST', body: formData });
        const result = await res.json();

        if (result.status === 'success') {
            bootstrap.Modal.getInstance(document.getElementById('declarerSinistreModal')).hide();

            // if car set to maintenance, refresh header badge
            if (document.getElementById('sin_set_maintenance').checked) {
                await loadCarDetail();
            }

            await loadSinistres();
            Swal.fire({ icon: 'success', title: 'Sinistre déclaré !', showConfirmButton: false, timer: 2000 });
        } else {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
        }
    } catch (e) {
        console.error('confirmerDeclarerSinistre error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// CLOTURE SINISTRE

function ouvrirClotureSinistre(sinistreId, employeeId, replacementCarId) {
    document.getElementById('cloture_sinistre_id').value        = sinistreId;
    document.getElementById('cloture_employee_id').value        = employeeId || '';
    document.getElementById('cloture_replacement_car_id').value = replacementCarId || '';
    document.getElementById('cloture_montant').value            = '';
    document.getElementById('cloture_mode_reglement').value     = '';
    document.getElementById('cloture_n_reglement').value        = '';
    document.getElementById('cloture_date_reglement').value     = '';
    document.getElementById('cloture_facture_num').value        = '';
    document.getElementById('cloture_facture_date').value       = '';
    document.getElementById('cloture_facture_ht').value         = '';
    document.getElementById('cloture_facture_tva').value        = '';
    document.getElementById('cloture_facture_ttc').value        = '';
    document.getElementById('cloture_retourner_vehicule').checked = true;

    // show/hide retour section based on whether there's a replacement
    document.getElementById('cloture_retour_section').style.display =
        replacementCarId ? 'block' : 'none';

    new bootstrap.Modal(document.getElementById('clotureSinistreModal')).show();
}

async function confirmerClotureSinistre() {
    const sinistreId     = document.getElementById('cloture_sinistre_id').value;
    const employeeId     = document.getElementById('cloture_employee_id').value;
    const replacementId  = document.getElementById('cloture_replacement_car_id').value;
    const retourner      = document.getElementById('cloture_retourner_vehicule').checked;

    const payload = {
        car_id:               carId,
        employee_id:          employeeId || null,
        montant_reparation:   document.getElementById('cloture_montant').value || null,
        mode_reglement:       document.getElementById('cloture_mode_reglement').value || null,
        n_cheque_or_virement: document.getElementById('cloture_n_reglement').value.trim() || null,
        date_reglement:       document.getElementById('cloture_date_reglement').value || null,
        retourner_vehicule:   retourner,
        replacement_car_id:   replacementId || null
    };

    try {
        const res    = await fetch(`/sinistre/cloturer/${sinistreId}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();

        if (result.status !== 'success') {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
            return;
        }

        // attach facture if filled
        const factureNum  = document.getElementById('cloture_facture_num').value.trim();
        const factureTtc  = document.getElementById('cloture_facture_ttc').value;
        const factureFile = document.getElementById('cloture_facture_file').files[0];

        if (factureNum || factureTtc || factureFile) {
            const formData = new FormData();
            formData.append('car_id',        carId);
            formData.append('num_facture',   factureNum);
            formData.append('date_facture',  document.getElementById('cloture_facture_date').value);
            formData.append('montant_ht',    document.getElementById('cloture_facture_ht').value);
            formData.append('tva',           document.getElementById('cloture_facture_tva').value);
            formData.append('montant_ttc',   factureTtc);
            formData.append('prise_en_charge', 'societe');
            if (factureFile) formData.append('file', factureFile);
            await fetch(`/sinistre/facture/attach/${sinistreId}`, { method: 'POST', body: formData });
        }

        bootstrap.Modal.getInstance(document.getElementById('clotureSinistreModal')).hide();
        await loadCarDetail();
        await loadSinistres();
        Swal.fire({ icon: 'success', title: 'Sinistre clôturé !', showConfirmButton: false, timer: 2000 });

    } catch (e) {
        console.error('confirmerClotureSinistre error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// FACTURE SINISTRE STANDALONE

function ouvrirFactureSinistreModal(sinistreId) {
    document.getElementById('sin_facture_sinistre_id').value    = sinistreId;
    document.getElementById('sin_facture_num').value            = '';
    document.getElementById('sin_facture_num_reglement').value  = '';
    document.getElementById('sin_facture_date').value           = '';
    document.getElementById('sin_facture_date_reglement').value = '';
    document.getElementById('sin_facture_montant_ht').value     = '';
    document.getElementById('sin_facture_tva').value            = '';
    document.getElementById('sin_facture_montant_ttc').value    = '';
    document.getElementById('sin_facture_pec').value            = 'societe';
    new bootstrap.Modal(document.getElementById('factureSinistreModal')).show();
}

async function confirmerAttacherFactureSinistre() {
    const sinistreId = document.getElementById('sin_facture_sinistre_id').value;
    const formData   = new FormData();
    formData.append('car_id',          carId);
    formData.append('num_facture',      document.getElementById('sin_facture_num').value.trim());
    formData.append('num_reglement',    document.getElementById('sin_facture_num_reglement').value.trim());
    formData.append('date_facture',     document.getElementById('sin_facture_date').value);
    formData.append('date_reglement',   document.getElementById('sin_facture_date_reglement').value);
    formData.append('montant_ht',       document.getElementById('sin_facture_montant_ht').value);
    formData.append('tva',              document.getElementById('sin_facture_tva').value);
    formData.append('montant_ttc',      document.getElementById('sin_facture_montant_ttc').value);
    formData.append('prise_en_charge',  document.getElementById('sin_facture_pec').value);
    const fileInput = document.getElementById('sin_facture_file');
    if (fileInput.files.length > 0) formData.append('file', fileInput.files[0]);

    try {
        const res    = await fetch(`/sinistre/facture/attach/${sinistreId}`, { method: 'POST', body: formData });
        const result = await res.json();
        if (result.status === 'success') {
            bootstrap.Modal.getInstance(document.getElementById('factureSinistreModal')).hide();
            Swal.fire({ icon: 'success', title: 'Facture attachée !', showConfirmButton: false, timer: 2000 });
            await loadSinistres();
        } else {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
        }
    } catch (e) {
        console.error('confirmerAttacherFactureSinistre error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
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