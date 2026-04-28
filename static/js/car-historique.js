////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

const carId    = window.location.pathname.split('/').pop();
const urlParams = new URLSearchParams(window.location.search);
const defaultTab = urlParams.get('tab') || 'maintenance';

let allMaintenance = [];
let allSinistres   = [];
let filteredMaintenance = [];
let filteredSinistres   = [];

const rowsPerPage = 10;
let maintenancePage = 1;
let sinistresPage   = 1;

document.addEventListener("DOMContentLoaded", async () => {
    // set back link
    document.getElementById('back_to_detail').href = `/car/detail/${carId}`;

    // load car info for title
    try {
        const res  = await fetch(`/car/detail-data/${carId}`);
        const data = await res.json();
        if (data.status === 'success') {
            const car = data.data.car;
            document.getElementById('history_title').innerText =
                `Historique — ${car.model || ''} ${car.brand || ''}`;
            document.getElementById('history_subtitle').innerText = car.plate_number || '';
        }
    } catch (e) { console.error(e); }

    await loadAllMaintenance();
    await loadAllSinistres();

    switchTab(defaultTab);
});

////////////////////////////////////////////////////////////////////////////////////////////////
// TABS

function switchTab(tab) {
    document.getElementById('panel-maintenance').style.display = tab === 'maintenance' ? 'block' : 'none';
    document.getElementById('panel-sinistres').style.display   = tab === 'sinistres'   ? 'block' : 'none';
    document.getElementById('tab-maintenance').classList.toggle('active', tab === 'maintenance');
    document.getElementById('tab-sinistres').classList.toggle('active',   tab === 'sinistres');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// MAINTENANCE

async function loadAllMaintenance() {
    try {
        const res  = await fetch(`/maintenance/records/${carId}`);
        const data = await res.json();
        allMaintenance      = data.status === 'success' ? data.data : [];
        filteredMaintenance = [...allMaintenance];
        document.getElementById('maintenance_count').innerText = allMaintenance.length;
        renderMaintenanceTable();
    } catch (e) { console.error('loadAllMaintenance error:', e); }
}

function applyMaintenanceFilters() {
    const from    = document.getElementById('m_filter_from').value;
    const to      = document.getElementById('m_filter_to').value;
    const status  = document.getElementById('m_filter_status').value;
    const facture = document.getElementById('m_filter_facture').value;

    filteredMaintenance = allMaintenance.filter(r => {
        if (from && r.done_at < from) return false;
        if (to   && r.done_at > to)   return false;
        if (status && r.status !== status) return false;
        if (facture === 'sans' && r.facture_id)  return false;
        if (facture === 'avec' && !r.facture_id) return false;
        return true;
    });
    maintenancePage = 1;
    renderMaintenanceTable();
}

function resetMaintenanceFilters() {
    document.getElementById('m_filter_from').value   = '';
    document.getElementById('m_filter_to').value     = '';
    document.getElementById('m_filter_status').value = '';
    document.getElementById('m_filter_facture').value = '';
    filteredMaintenance = [...allMaintenance];
    maintenancePage = 1;
    renderMaintenanceTable();
}

function renderMaintenanceTable() {
    const tbody = document.getElementById('maintenance_tbody');
    const start = (maintenancePage - 1) * rowsPerPage;
    const page  = filteredMaintenance.slice(start, start + rowsPerPage);

    if (page.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Aucun entretien trouvé</td></tr>`;
        renderPagination('maintenance_pagination', filteredMaintenance.length, maintenancePage, 'changeMPage');
        updateInfo('maintenance_info', start, page.length, filteredMaintenance.length);
        return;
    }

    tbody.innerHTML = page.map(r => `
        <tr>
            <td class="ps-3">
                <strong>${escapeHtml(r.part_name)}</strong><br>
                <span class="text-muted" style="font-size:11px;">${escapeHtml(r.category || '')}</span>
            </td>
            <td>${escapeHtml(r.garage_name || '—')}</td>
            <td>${formatDate(r.done_at)}</td>
            <td>${r.km_at_service ? r.km_at_service.toLocaleString() + ' km' : '—'}</td>
            <td>
                ${r.next_due_date ? '<span class="text-muted small">' + formatDate(r.next_due_date) + '</span>' : ''}
                ${r.next_due_km   ? '<br><span class="text-muted small">' + r.next_due_km + ' km</span>' : ''}
                ${!r.next_due_date && !r.next_due_km ? '—' : ''}
            </td>
            <td>
                ${r.status === 'done'
                    ? '<span class="badge bg-success">Fait</span>'
                    : '<span class="badge bg-warning text-dark">En attente</span>'}
            </td>
            <td class="text-end pe-3">
                ${r.facture_id
                    ? `<a href="/${r.facture_file}" target="_blank" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-file-invoice me-1"></i>${r.montant_ttc ? r.montant_ttc + ' DT' : 'Voir'}
                       </a>`
                    : `<button class="btn btn-outline-secondary btn-sm"
                        onclick="ouvrirFactureMaintenanceModal(${r.id})">
                        <i class="fas fa-paperclip me-1"></i>Attacher
                       </button>`
                }
            </td>
        </tr>`).join('');

    renderPagination('maintenance_pagination', filteredMaintenance.length, maintenancePage, 'changeMPage');
    updateInfo('maintenance_info', start, page.length, filteredMaintenance.length);
}

function changeMPage(page) { maintenancePage = page; renderMaintenanceTable(); }

////////////////////////////////////////////////////////////////////////////////////////////////
// SINISTRES

async function loadAllSinistres() {
    try {
        const res  = await fetch(`/sinistre/by-car/${carId}`);
        const data = await res.json();
        allSinistres      = data.status === 'success' ? data.data : [];
        filteredSinistres = [...allSinistres];
        const open = allSinistres.filter(s => s.status !== 'cloture').length;
        document.getElementById('sinistres_count').innerText = open > 0 ? open : allSinistres.length;
        renderSinistresTable();
    } catch (e) { console.error('loadAllSinistres error:', e); }
}

function applySinistresFilters() {
    const from    = document.getElementById('s_filter_from').value;
    const to      = document.getElementById('s_filter_to').value;
    const type    = document.getElementById('s_filter_type').value;
    const status  = document.getElementById('s_filter_status').value;
    const facture = document.getElementById('s_filter_facture').value;

    filteredSinistres = allSinistres.filter(s => {
        if (from && s.date_sinistre < from) return false;
        if (to   && s.date_sinistre > to)   return false;
        if (type && s.type !== type) return false;
        if (status === 'non_cloture' && s.status === 'cloture') return false;
        else if (status && status !== 'non_cloture' && s.status !== status) return false;
        if (facture === 'sans' && s.facture_id)  return false;
        if (facture === 'avec' && !s.facture_id) return false;
        return true;
    });
    sinistresPage = 1;
    renderSinistresTable();
}

function resetSinistresFilters() {
    document.getElementById('s_filter_from').value   = '';
    document.getElementById('s_filter_to').value     = '';
    document.getElementById('s_filter_type').value   = '';
    document.getElementById('s_filter_status').value = '';
    document.getElementById('s_filter_facture').value = '';
    filteredSinistres = [...allSinistres];
    sinistresPage = 1;
    renderSinistresTable();
}

function renderSinistresTable() {
    const tbody = document.getElementById('sinistres_tbody');
    const start = (sinistresPage - 1) * rowsPerPage;
    const page  = filteredSinistres.slice(start, start + rowsPerPage);

    if (page.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">Aucun sinistre trouvé</td></tr>`;
        renderPagination('sinistres_pagination', filteredSinistres.length, sinistresPage, 'changeSPage');
        updateInfo('sinistres_info', start, page.length, filteredSinistres.length);
        return;
    }

    tbody.innerHTML = page.map(s => {
        const statusBadge =
            s.status === 'ouvert'   ? '<span class="badge bg-danger">Ouvert</span>'  :
            s.status === 'en_cours' ? '<span class="badge bg-warning text-dark">En cours</span>' :
            '<span class="badge bg-success">Clôturé</span>';

        return `
        <tr>
            <td class="ps-3">${formatDate(s.date_sinistre)}</td>
            <td><span class="badge bg-light text-dark border">${escapeHtml(s.type)}</span></td>
            <td>${s.nom ? escapeHtml(s.prenom + ' ' + s.nom) : '—'}</td>
            <td class="text-muted" style="max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                ${escapeHtml(s.description || '—')}
            </td>
            <td>${statusBadge}</td>
            <td>${s.montant_reparation ? s.montant_reparation + ' DT' : '—'}</td>
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
            <td class="text-end pe-3">
                ${s.status !== 'cloture'
                    ? `<button class="btn btn-outline-success btn-sm"
                        onclick="ouvrirClotureSinistre(${s.id}, ${s.employee_id || 'null'}, ${s.replacement_car_id || 'null'})">
                        <i class="fas fa-check me-1"></i>Clôturer
                       </button>`
                    : '<span class="text-muted small">—</span>'
                }
            </td>
        </tr>`;
    }).join('');

    renderPagination('sinistres_pagination', filteredSinistres.length, sinistresPage, 'changeSPage');
    updateInfo('sinistres_info', start, page.length, filteredSinistres.length);
}

function changeSPage(page) { sinistresPage = page; renderSinistresTable(); }

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
    document.getElementById('cloture_retour_section').style.display = replacementCarId ? 'block' : 'none';
    new bootstrap.Modal(document.getElementById('clotureSinistreModal')).show();
}

async function confirmerClotureSinistre() {
    const sinistreId    = document.getElementById('cloture_sinistre_id').value;
    const employeeId    = document.getElementById('cloture_employee_id').value;
    const replacementId = document.getElementById('cloture_replacement_car_id').value;
    const retourner     = document.getElementById('cloture_retourner_vehicule').checked;

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
            formData.append('car_id',      carId);
            formData.append('num_facture', factureNum);
            formData.append('date_facture',document.getElementById('cloture_facture_date').value);
            formData.append('montant_ht',  document.getElementById('cloture_facture_ht').value);
            formData.append('tva',         document.getElementById('cloture_facture_tva').value);
            formData.append('montant_ttc', factureTtc);
            formData.append('prise_en_charge', 'societe');
            if (factureFile) formData.append('file', factureFile);
            await fetch(`/sinistre/facture/attach/${sinistreId}`, { method: 'POST', body: formData });
        }

        bootstrap.Modal.getInstance(document.getElementById('clotureSinistreModal')).hide();
        Swal.fire({ icon: 'success', title: 'Sinistre clôturé !', showConfirmButton: false, timer: 2000 });
        setTimeout(() => loadAllSinistres(), 2000);

    } catch (e) {
        console.error('confirmerClotureSinistre error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// FACTURE SINISTRE

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
            setTimeout(() => loadAllSinistres(), 2000);
        } else {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
        }
    } catch (e) {
        console.error(e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// FACTURE MAINTENANCE

function ouvrirFactureMaintenanceModal(recordId) {
    document.getElementById('maint_facture_record_id').value      = recordId;
    document.getElementById('maint_facture_num').value            = '';
    document.getElementById('maint_facture_num_reglement').value  = '';
    document.getElementById('maint_facture_date').value           = '';
    document.getElementById('maint_facture_date_reglement').value = '';
    document.getElementById('maint_facture_montant_ht').value     = '';
    document.getElementById('maint_facture_tva').value            = '';
    document.getElementById('maint_facture_montant_ttc').value    = '';
    new bootstrap.Modal(document.getElementById('factureMaintenanceModal')).show();
}

async function confirmerAttacherFactureMaintenance() {
    const recordId = document.getElementById('maint_facture_record_id').value;
    const formData = new FormData();
    formData.append('car_id',          carId);
    formData.append('num_facture',      document.getElementById('maint_facture_num').value.trim());
    formData.append('num_reglement',    document.getElementById('maint_facture_num_reglement').value.trim());
    formData.append('date_facture',     document.getElementById('maint_facture_date').value);
    formData.append('date_reglement',   document.getElementById('maint_facture_date_reglement').value);
    formData.append('montant_ht',       document.getElementById('maint_facture_montant_ht').value);
    formData.append('tva',              document.getElementById('maint_facture_tva').value);
    formData.append('montant_ttc',      document.getElementById('maint_facture_montant_ttc').value);
    const fileInput = document.getElementById('maint_facture_file');
    if (fileInput.files.length > 0) formData.append('file', fileInput.files[0]);

    try {
        const res    = await fetch(`/maintenance/facture/attach/${recordId}`, { method: 'POST', body: formData });
        const result = await res.json();
        if (result.status === 'success') {
            bootstrap.Modal.getInstance(document.getElementById('factureMaintenanceModal')).hide();
            Swal.fire({ icon: 'success', title: 'Facture attachée !', showConfirmButton: false, timer: 2000 });
            setTimeout(() => loadAllMaintenance(), 2000);
        } else {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
        }
    } catch (e) {
        console.error(e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// PAGINATION

function renderPagination(elId, total, currentPage, changeFn) {
    const pagination = document.getElementById(elId);
    pagination.innerHTML = '';
    const totalPages = Math.ceil(total / rowsPerPage);
    if (totalPages <= 1) return;
    for (let i = 1; i <= totalPages; i++) {
        const active = i === currentPage ? 'active' : '';
        pagination.innerHTML += `
            <li class="page-item ${active}">
                <a class="page-link" href="#" onclick="${changeFn}(${i})">${i}</a>
            </li>`;
    }
}

function updateInfo(elId, start, len, total) {
    const el = document.getElementById(elId);
    if (!el) return;
    if (total === 0) { el.innerText = 'Aucun résultat'; return; }
    el.innerText = `Affichage de ${start + 1} à ${start + len} sur ${total}`;
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