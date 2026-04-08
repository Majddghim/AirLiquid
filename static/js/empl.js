var enitity_name = "Employée";
var data = [];
var division_table = 7;
var search_link = 'get-employes?page=1&limit=' + division_table;
var page = 1;
let debounceTimer;
let controller = null;

const searchInput = document.querySelector("#search_by_name");
if (searchInput) {
    searchInput.addEventListener("input", function () {
        prepare_search_link(1);
    });
}

function initPage() {
    const table = document.getElementById('dataTable');
    if (!table) return;
    enter_loading_mode();
    load_page(search_link);
}

function prepare_search_link(p = 1) {
    let search_by_name = document.querySelector('#search_by_name').value;
    search_link = 'get-employes?page=' + p + '&limit=' + division_table;
    if (search_by_name && search_by_name.trim() !== '') {
        search_link += '&search_by_name=' + encodeURIComponent(search_by_name.trim());
    }
    page = p;
    load_page(search_link);
}

function quit_div_loading_mode(s) {
    let div = document.querySelector("#" + s);
    div.hidden = false;
    let loading = document.getElementById("inner-loading");
    loading.hidden = true;
}

function enter_div_loading_mode(s) {
    let div = document.querySelector("#" + s);
    div.hidden = true;
    let loading = document.querySelector("#inner-loading");
    loading.hidden = false;
}

function load_page(search_link) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        if (controller) controller.abort();
        controller = new AbortController();
        enter_div_loading_mode('dataTable');

        fetch('/employe/' + search_link, { signal: controller.signal })
            .then(res => {
                if (!res.ok) throw new Error("Network response failed");
                return res.json();
            })
            .then(response => {
                if (response.status === 'success') {
                    quit_div_loading_mode('dataTable');
                    data = response.data;
                    load_table_data(data);
                    let pages_count = Math.ceil(response.count / division_table);
                    load_backend_pagination(pages_count, page, response.count, response.data.length);
                    try { quit_loading_mode(); } catch (e) {}
                } else {
                    if (response.status === 'failed') {
                        notifs.warn('Aucune employé trouvé.');
                        load_table_data([]);
                        load_backend_pagination(1, page, 0, 0);
                    } else {
                        notifs.error('Erreur');
                    }
                    quit_div_loading_mode('dataTable');
                }
            })
            .catch(err => {
                if (err.name !== "AbortError") console.error("Search error:", err);
                try { quit_loading_mode(); } catch (e) {}
            });
    }, 300);
}

function load_table_data(data) {
    const table = document.getElementById('dataTable');
    if (data.length === 0) {
        table.innerHTML = `
            <thead class="table-light">
                <tr class="text-xs text-uppercase text-muted">
                    <th class="ps-4">Collaborateur</th>
                    <th>Coordonnées</th>
                    <th>Poste / Département</th>
                    <th class="text-end pe-4">Actions</th>
                </tr>
            </thead>
            <tbody>
                <tr><td colspan="4" class="text-center py-5 text-muted">
                    <i class="fas fa-user-slash fa-2x mb-2 d-block opacity-25"></i>
                    Aucun collaborateur trouvé
                </td></tr>
            </tbody>`;
        return;
    }

    const header = `
        <thead class="table-light">
            <tr class="text-xs text-uppercase text-muted">
                <th class="ps-4">Collaborateur</th>
                <th>Coordonnées</th>
                <th>Poste / Département</th>
                <th class="text-end pe-4">Actions</th>
            </tr>
        </thead>`;

    const body = data.map(employe => {
        const initials = `${(employe.prenom || 'E')[0]}${(employe.nom || 'P')[0]}`.toUpperCase();
        return `
            <tr style="cursor:pointer;"
                onclick="window.location.href='/employe/profil/${employe.id}'">
                <td class="ps-4">
                    <div class="d-flex align-items-center">
                        <div class="bg-light p-2 rounded-circle me-3 text-center"
                            style="width:40px; height:40px; line-height:24px;">
                            <span class="fw-bold text-primary small">${initials}</span>
                        </div>
                        <div>
                            <div class="fw-bold text-dark">${escapeHtml(employe.prenom)} ${escapeHtml(employe.nom)}</div>
                            <div class="text-xs text-muted">ID: #00${employe.id}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="text-sm">
                        <div class="text-dark">
                            <i class="far fa-envelope me-2 text-muted"></i>${escapeHtml(employe.email)}
                        </div>
                        <div class="text-muted extra-small">
                            <i class="fas fa-phone-alt me-2"></i>${escapeHtml(employe.telephone || 'Non renseigné')}
                        </div>
                    </div>
                </td>
                <td>
                    <div class="fw-bold text-sm text-dark">${escapeHtml(employe.poste || '—')}</div>
                    <div class="text-xs text-primary fw-bold text-uppercase">${escapeHtml(employe.departement || '—')}</div>
                </td>
                <td class="text-end pe-4" onclick="event.stopPropagation()">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary border-0 rounded-circle me-1"
                            title="Modifier"
                            onclick="ouvrirModalEditEmploye(event, ${employe.id})">
                            <i class="fas fa-user-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger border-0 rounded-circle"
                            title="Supprimer"
                            onclick="supprimerEmploye(event, ${employe.id}, '${escapeHtml(employe.prenom)} ${escapeHtml(employe.nom)}')">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    });

    prepare_table(header, "", body, division_table);
}

function escapeHtml(text) {
    if (!text) return "";
    return text.toString()
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function prepare_table(header, footer, body, division_table) {
    get_data_ready_load_table("dataTable", header, footer, body, division_table);
}

////////////////////////////////////////////////////////////////////////////////////////////////
// DÉPARTEMENTS & POSTES — cascading dropdowns

let allDepartements = [];

async function loadDepartements() {
    try {
        const res  = await fetch('/employe/get-departements');
        const data = await res.json();
        if (data.status !== 'success') return;

        allDepartements = data.data;

        const select = document.getElementById('departement_id');
        if (!select) return;

        select.innerHTML = '<option value="">-- Sélectionner --</option>';
        allDepartements.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.id;
            opt.text  = d.name;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('loadDepartements error:', e);
    }
}

async function onDepartementChange() {
    const departementId = document.getElementById('departement_id').value;
    const posteSelect   = document.getElementById('poste');

    if (!departementId) {
        posteSelect.innerHTML = '<option value="">-- Sélectionner le département --</option>';
        return;
    }

    posteSelect.innerHTML = '<option value="">Chargement...</option>';

    try {
        const res  = await fetch(`/employe/get-postes/${departementId}`);
        const data = await res.json();

        posteSelect.innerHTML = '<option value="">-- Sélectionner le poste --</option>';
        if (data.status === 'success') {
            data.data.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.name;
                opt.text  = p.name;
                posteSelect.appendChild(opt);
            });
        }
    } catch (e) {
        console.error('onDepartementChange error:', e);
        posteSelect.innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// DÉPARTEMENTS & POSTES — edit modal

async function loadDepartementsForEdit() {
    try {
        const res  = await fetch('/employe/get-departements');
        const data = await res.json();
        if (data.status !== 'success') return;

        allDepartements = data.data;

        const select = document.getElementById('edit_departement_id');
        if (!select) return;

        select.innerHTML = '<option value="">-- Sélectionner --</option>';
        allDepartements.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.id;
            opt.text  = d.name;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('loadDepartementsForEdit error:', e);
    }
}

async function onEditDepartementChange() {
    const deptId      = document.getElementById('edit_departement_id').value;
    const posteSelect = document.getElementById('edit_poste');

    if (!deptId) {
        posteSelect.innerHTML = '<option value="">-- Sélectionner le département --</option>';
        return;
    }

    posteSelect.innerHTML = '<option value="">Chargement...</option>';

    try {
        const res  = await fetch(`/employe/get-postes/${deptId}`);
        const data = await res.json();
        posteSelect.innerHTML = '<option value="">-- Sélectionner le poste --</option>';
        if (data.status === 'success') {
            data.data.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.name;
                opt.text  = p.name;
                posteSelect.appendChild(opt);
            });
        }
    } catch (e) {
        posteSelect.innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// OPEN EDIT MODAL

async function ouvrirModalEditEmploye(event, employeId) {
    event.stopPropagation();
    try {
        const res  = await fetch(`/employe/get-employe/${employeId}`);
        const data = await res.json();
        if (data.status !== 'success') {
            Swal.fire({ icon: 'error', title: 'Erreur', text: 'Impossible de charger les données.' });
            return;
        }
        const e = data.data;

        document.getElementById('edit_employe_id').value          = e.id;
        document.getElementById('edit_employe_subtitle').innerText = `${e.prenom} ${e.nom}`;
        document.getElementById('edit_nom').value                  = e.nom || '';
        document.getElementById('edit_prenom').value               = e.prenom || '';
        document.getElementById('edit_email').value                = e.email || '';
        document.getElementById('edit_telephone').value            = e.telephone || '';

        await loadDepartementsForEdit();

        const deptSelect = document.getElementById('edit_departement_id');
        const matchDept  = Array.from(deptSelect.options).find(o => o.text === e.departement);
        if (matchDept) {
            deptSelect.value = matchDept.value;
            await onEditDepartementChange();
            const posteSelect = document.getElementById('edit_poste');
            const matchPoste  = Array.from(posteSelect.options).find(o => o.value === e.poste);
            if (matchPoste) posteSelect.value = matchPoste.value;
        }

        new bootstrap.Modal(document.getElementById('editEmployeModal')).show();
    } catch (err) {
        console.error('ouvrirModalEditEmploye error:', err);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// CONFIRM EDIT

async function confirmerModificationEmploye() {
    const employeId  = document.getElementById('edit_employe_id').value;
    const deptSelect = document.getElementById('edit_departement_id');
    const deptName   = deptSelect.options[deptSelect.selectedIndex]?.text || '';

    const payload = {
        nom:         document.getElementById('edit_nom').value.trim(),
        prenom:      document.getElementById('edit_prenom').value.trim(),
        email:       document.getElementById('edit_email').value.trim(),
        telephone:   document.getElementById('edit_telephone').value.trim(),
        departement: deptName === '-- Sélectionner --' ? '' : deptName,
        poste:       document.getElementById('edit_poste').value
    };

    if (!payload.nom || !payload.prenom || !payload.email) {
        Swal.fire({ icon: 'warning', title: 'Champs manquants', text: 'Nom, prénom et email sont obligatoires.' });
        return;
    }

    try {
        const res    = await fetch(`/employe/update/${employeId}`, {
            method:  'PUT',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload)
        });
        const result = await res.json();

        if (result.status === 'success') {
            bootstrap.Modal.getInstance(document.getElementById('editEmployeModal')).hide();
            Swal.fire({ icon: 'success', title: 'Modifié !', text: result.message, showConfirmButton: false, timer: 2000 });
            setTimeout(() => { loadEmployees(); }, 2000);
        } else {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
        }
    } catch (e) {
        console.error('confirmerModificationEmploye error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// DELETE EMPLOYEE (soft delete → status = inactive)

async function supprimerEmploye(event, employeId, employeLabel) {
    event.stopPropagation();

    let warningHtml = `
        <span class="text-muted">${employeLabel}</span><br>
        <small class="text-muted">L'employé sera marqué comme <strong>Inactif</strong>.</small>
    `;

    try {
        const res  = await fetch(`/employe/get-affectation-active/${employeId}`);
        const data = await res.json();
        if (data.status === 'success' && data.assigned) {
            const v = data.data;
            warningHtml = `
                <span class="text-muted">${employeLabel}</span><br><br>
                <div class="alert alert-warning py-2 text-start small">
                    <i class="fas fa-car me-1"></i>
                    Cet employé est actuellement affecté au véhicule
                    <strong>${v.plate_number}</strong> (${v.model || ''}).<br>
                    L'affectation sera clôturée mais <strong>l'historique sera conservé</strong>.
                </div>
            `;
        }
    } catch (e) {
        console.error('Erreur vérification affectation:', e);
    }

    const confirm = await Swal.fire({
        icon:              'warning',
        title:             'Désactiver cet employé ?',
        html:              warningHtml,
        showCancelButton:  true,
        confirmButtonText: 'Oui, désactiver',
        cancelButtonText:  'Annuler',
        confirmButtonColor:'#e74a3b',
        cancelButtonColor: '#858796'
    });

    if (!confirm.isConfirmed) return;

    try {
        const res    = await fetch(`/employe/delete/${employeId}`, { method: 'DELETE' });
        const result = await res.json();
        if (result.status === 'success') {
            Swal.fire({ icon: 'success', title: 'Désactivé !', text: result.message, showConfirmButton: false, timer: 2000 });
            setTimeout(() => { loadEmployees(); }, 2000);
        } else {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
        }
    } catch (e) {
        console.error('supprimerEmploye error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RESET FORM

function resetForm() {
    document.getElementById('employeForm').reset();
    const posteSelect = document.getElementById('poste');
    if (posteSelect) {
        posteSelect.innerHTML = '<option value="">-- Sélectionner le département --</option>';
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// ENREGISTRER EMPLOYÉ

async function enregistrerEmploye() {
    const getV = (id) => {
        const el = document.getElementById(id);
        return el ? el.value.trim() : "";
    };

    const deptSelect = document.getElementById('departement_id');
    const deptName   = deptSelect
        ? deptSelect.options[deptSelect.selectedIndex]?.text || ''
        : '';

    const payload = {
        nom:         getV("nom"),
        prenom:      getV("prenom"),
        email:       getV("email"),
        telephone:   getV("telephone"),
        poste:       getV("poste"),
        departement: deptName,
        created_at:  getV("created_at")
    };

    if (!payload.nom)         { Swal.fire({ icon: "warning", title: "Champ manquant", text: "Veuillez saisir le nom." }); return; }
    if (!payload.prenom)      { Swal.fire({ icon: "warning", title: "Champ manquant", text: "Veuillez saisir le prénom." }); return; }
    if (!payload.email)       { Swal.fire({ icon: "warning", title: "Champ manquant", text: "Veuillez saisir l'email." }); return; }
    if (!payload.telephone)   { Swal.fire({ icon: "warning", title: "Champ manquant", text: "Veuillez saisir le téléphone." }); return; }
    if (!deptName || deptName === '-- Sélectionner --') {
        Swal.fire({ icon: "warning", title: "Champ manquant", text: "Veuillez sélectionner un département." });
        return;
    }
    if (!payload.poste || payload.poste === '-- Sélectionner le poste --') {
        Swal.fire({ icon: "warning", title: "Champ manquant", text: "Veuillez sélectionner un poste." });
        return;
    }
    if (!payload.created_at)  { Swal.fire({ icon: "warning", title: "Champ manquant", text: "Veuillez saisir la date de recrutement." }); return; }

    try {
        const response = await fetch("/employe/ajout-employe", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify(payload)
        });

        const result = await response.json();

        if (result.status === "success") {
            Swal.fire({
                icon: "success", title: "Employé ajouté",
                text: result.message, showConfirmButton: false, timer: 1800
            }).then(() => {
                window.location.href = "/dashboard/liste-employes";
            });
        } else {
            Swal.fire({ icon: "warning", title: "Attention", text: result.message, confirmButtonColor: "#f0ad4e" });
        }

    } catch (error) {
        console.error("Erreur lors de l'envoi :", error);
        Swal.fire({ icon: "error", title: "Erreur", text: "Une erreur s'est produite lors de l'enregistrement.", confirmButtonColor: "#d33" });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

document.addEventListener("DOMContentLoaded", () => {
    initPage();
    loadDepartements();
});