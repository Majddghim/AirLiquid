////////////////////////////////////////////////////////////////////////////////////////////////
// BRANDS & MODELS — cascading dropdowns
// allBrands is cached after first load so we can match OCR text against it

let allBrands = [];

async function loadBrands() {
    try {
        const res  = await fetch('/car/get-brands');
        const data = await res.json();
        if (data.status !== 'success') return;

        allBrands = data.data;

        const select = document.getElementById('modal_brand_id');
        select.innerHTML = '<option value="">-- Sélectionner --</option>';
        allBrands.forEach(b => {
            const opt    = document.createElement('option');
            opt.value    = b.id;
            opt.text     = b.name;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('loadBrands error:', e);
    }
}

async function loadModels(brandId, preselect = null) {
    const modelSelect = document.getElementById('modal_model');

    if (!brandId) {
        modelSelect.innerHTML = '<option value="">-- Sélectionner la marque --</option>';
        return;
    }

    modelSelect.innerHTML = '<option value="">Chargement...</option>';

    try {
        const res  = await fetch(`/car/get-models/${brandId}`);
        const data = await res.json();

        modelSelect.innerHTML = '<option value="">-- Sélectionner le modèle --</option>';

        if (data.status === 'success') {
            data.data.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.name;
                opt.text  = m.name;
                modelSelect.appendChild(opt);
            });
        }

        if (preselect) {
            const lower = preselect.toLowerCase();
            const match = Array.from(modelSelect.options).find(
                o => o.value.toLowerCase() === lower
            );
            if (match) {
                modelSelect.value = match.value;
            } else {
                const opt    = document.createElement('option');
                opt.value    = preselect;
                opt.text     = preselect;
                opt.selected = true;
                modelSelect.appendChild(opt);
            }
        }

    } catch (e) {
        console.error('loadModels error:', e);
        modelSelect.innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

async function onBrandChange() {
    const brandId = document.getElementById('modal_brand_id').value;
    await loadModels(brandId);
}

async function setBrandAndModelFromOcr(ocrModelString) {
    if (!ocrModelString) return;

    const parts     = ocrModelString.trim().split(' ');
    const brandName = parts[0];
    const modelName = parts.slice(1).join(' ');

    const brand = allBrands.find(
        b => b.name.toLowerCase() === brandName.toLowerCase()
    );

    const brandSelect = document.getElementById('modal_brand_id');

    if (brand) {
        brandSelect.value = brand.id;
        await loadModels(brand.id, modelName);
    } else {
        const opt    = document.createElement('option');
        opt.value    = '';
        opt.text     = brandName;
        opt.selected = true;
        brandSelect.appendChild(opt);

        const modelSelect = document.getElementById('modal_model');
        modelSelect.innerHTML = `<option value="${modelName}" selected>${modelName}</option>`;
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// SCAN CARTE GRISE

async function scannerCarteGrise() {

    const fileInput = document.getElementById("carte_grise_scan");
    const loader    = document.getElementById("scan-loader");
    const scanBtn   = document.getElementById("scanBtn");

    if (!fileInput?.files || fileInput.files.length === 0) {
        Swal.fire({
            icon: "warning",
            title: "Document manquant",
            text: "Veuillez sélectionner une image ou un PDF de carte grise."
        });
        return;
    }

    loader.style.display = "block";
    scanBtn.disabled = true;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch("/car/upload-cg", { method: "POST", body: formData });
        const result   = await response.json();

        if (result.status !== "success") {
            Swal.fire({ icon: "error", title: "Erreur d'extraction", text: result.message || "Format non reconnu" });
            return;
        }

        const data = result.extracted_data;
        const cgId = result.cg_id;

        document.getElementById("modal_cg_id").value             = cgId;
        document.getElementById("modal_cg_id_display").innerText  = cgId;

        await loadBrands();

        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el && val !== undefined && val !== null) el.value = val;
        };

        setVal("modal_plate_number",      data.plate_number);
        setVal("modal_year",              data.year);
        setVal("modal_owner_name",        data.owner_name);
        setVal("modal_chassis_number",    data.chassis_number);
        setVal("modal_puissance_fiscale", data.puissance_fiscale);
        setVal("modal_registration_date", data.registration_date);
        setVal("modal_expiration_date",   data.expiration_date);

        const carburantEl = document.getElementById("modal_carburant");
        if (carburantEl && data.carburant) carburantEl.value = data.carburant;

        if (data.model) {
            await setBrandAndModelFromOcr(data.model);
        }

        if (result.file_path) {
            const preview = document.getElementById("modal_doc_preview");
            const link    = document.getElementById("modal_doc_link");
            if (preview) preview.style.display = "block";
            if (link)    link.href = "/" + result.file_path;
        }

        const modal = new bootstrap.Modal(document.getElementById("reviewModal"));
        modal.show();

    } catch (error) {
        console.error("Scan error:", error);
        Swal.fire({ icon: "error", title: "Serveur indisponible", text: "Impossible de contacter le service d'extraction." });
    } finally {
        loader.style.display = "none";
        scanBtn.disabled = false;
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// CONFIRM CAR CREATION

async function confirmerVoiture() {

    const cgId = document.getElementById("modal_cg_id")?.value;
    if (!cgId) return;

    const getVal = (id) => {
        const el = document.getElementById(id);
        return el ? el.value.trim() : "";
    };

    const brandSelect  = document.getElementById('modal_brand_id');
    const brandName    = brandSelect.options[brandSelect.selectedIndex]?.text || '';
    const modelName    = getVal('modal_model');

    if (!brandName || brandName === '-- Sélectionner --') {
        Swal.fire({ icon: "warning", title: "Marque manquante", text: "Veuillez sélectionner une marque." });
        return;
    }
    if (!modelName) {
        Swal.fire({ icon: "warning", title: "Modèle manquant", text: "Veuillez sélectionner un modèle." });
        return;
    }

    const formData = new FormData();
    formData.append("brand",             brandName);
    formData.append("model",             modelName);
    formData.append("year",              getVal("modal_year"));
    formData.append("plate_number",      getVal("modal_plate_number"));
    formData.append("owner_name",        getVal("modal_owner_name"));
    formData.append("chassis_number",    getVal("modal_chassis_number"));
    formData.append("puissance_fiscale", getVal("modal_puissance_fiscale"));
    formData.append("carburant",         getVal("modal_carburant"));
    formData.append("status",            getVal("modal_status"));
    formData.append("acquisition_date",  getVal("modal_acquisition_date"));
    formData.append("registration_date", getVal("modal_registration_date"));
    formData.append("expiration_date",   getVal("modal_expiration_date"));
    formData.append("notes",             getVal("modal_notes"));

    try {
        const response = await fetch(`/car/confirm/${cgId}`, { method: "POST", body: formData });
        const result   = await response.json();

        if (result.status === "success") {
            bootstrap.Modal.getInstance(document.getElementById("reviewModal")).hide();
            Swal.fire({
                icon: "success",
                title: "Véhicule créé !",
                text: "Complétez maintenant le dossier du véhicule.",
                showConfirmButton: false,
                timer: 2000
            });
            setTimeout(() => {
                window.location.href = result.redirect || `/car/dossier?car_id=${result.car_id}`;
            }, 2000);
        } else {
            Swal.fire({ icon: "error", title: "Erreur", text: result.message, confirmButtonColor: "#d33" });
        }

    } catch (error) {
        console.error("Erreur réseau :", error);
        Swal.fire({ icon: "error", title: "Erreur interne", text: "Une erreur s'est produite lors de l'envoi." });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// OPEN AFFECTATION MODAL

async function ouvrirModalAffectation(event, carId, carLabel) {

    event.stopPropagation();

    document.getElementById("affectation_car_id").value       = carId;
    document.getElementById("affectation_car_label").innerText = carLabel;
    document.getElementById("affectation_employee_id").value  = "";
    document.getElementById("affectation_notes").value        = "";
    document.getElementById("affectation_start_date").value   = new Date().toISOString().split("T")[0];
    document.getElementById("affectation_warning").style.display = "none";

    try {
        const empRes  = await fetch("/car/get-employes-list");
        const empData = await empRes.json();
        const select  = document.getElementById("affectation_employee_id");
        select.innerHTML = '<option value="">-- Sélectionner un employé --</option>';
        if (empData.status === "success") {
            empData.data.forEach(e => {
                const opt       = document.createElement("option");
                opt.value       = e.id;
                opt.textContent = `${e.prenom} ${e.nom} — ${e.poste} (${e.departement})`;
                select.appendChild(opt);
            });
        }

        const affRes  = await fetch(`/car/get-affectation/${carId}`);
        const affData = await affRes.json();
        if (affData.status === "success" && affData.assigned) {
            const a = affData.data;
            document.getElementById("affectation_warning").style.display = "flex";
            document.getElementById("affectation_warning_text").innerText =
                `Ce véhicule est actuellement affecté à ${a.prenom} ${a.nom}. Une nouvelle affectation mettra fin à l'actuelle.`;
            select.value = a.employee_id;
        }
    } catch (error) {
        console.error("Erreur chargement modal affectation:", error);
    }

    new bootstrap.Modal(document.getElementById("affectationModal")).show();
}

////////////////////////////////////////////////////////////////////////////////////////////////
// CONFIRM AFFECTATION

async function affecterVoiture() {

    const carId      = document.getElementById("affectation_car_id").value;
    const employeeId = document.getElementById("affectation_employee_id").value;
    const startDate  = document.getElementById("affectation_start_date").value;
    const notes      = document.getElementById("affectation_notes").value.trim();

    if (!employeeId) {
        Swal.fire({ icon: "warning", title: "Employé manquant", text: "Veuillez sélectionner un employé." });
        return;
    }
    if (!startDate) {
        Swal.fire({ icon: "warning", title: "Date manquante", text: "Veuillez sélectionner une date de début." });
        return;
    }

    const formData = new FormData();
    formData.append("employee_id", employeeId);
    formData.append("start_date",  startDate);
    formData.append("notes",       notes);

    try {
        const response = await fetch(`/car/affecter/${carId}`, { method: "POST", body: formData });
        const result   = await response.json();

        if (result.status === "success") {
            bootstrap.Modal.getInstance(document.getElementById("affectationModal")).hide();
            Swal.fire({ icon: "success", title: "Affecté !", text: result.message, showConfirmButton: false, timer: 2000 });
            setTimeout(() => { loadCars(); }, 2000);
        } else {
            Swal.fire({ icon: "error", title: "Erreur", text: result.message, confirmButtonColor: "#d33" });
        }
    } catch (error) {
        console.error("Erreur réseau :", error);
        Swal.fire({ icon: "error", title: "Erreur interne", text: "Une erreur s'est produite." });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// OPEN EDIT MODAL

async function ouvrirModalEdit(event, carId) {
    event.stopPropagation();
    try {
        const res  = await fetch(`/car/get-voiture/${carId}`);
        const data = await res.json();
        if (data.status !== 'success') {
            Swal.fire({ icon: 'error', title: 'Erreur', text: 'Impossible de charger les données.' });
            return;
        }
        const car = data.data;

        document.getElementById('edit_car_id').value            = car.id;
        document.getElementById('edit_car_subtitle').innerText  = `${car.model || ''} — ${car.plate_number || ''}`;
        document.getElementById('edit_brand').value             = car.brand || '';
        document.getElementById('edit_model').value             = car.model || '';
        document.getElementById('edit_plate_number').value      = car.plate_number || '';
        document.getElementById('edit_year').value              = car.year || '';
        document.getElementById('edit_owner_name').value        = car.owner_name || '';
        document.getElementById('edit_chassis_number').value    = car.chassis_number || '';
        document.getElementById('edit_puissance_fiscale').value = car.puissance_fiscale || '';
        document.getElementById('edit_carburant').value         = (car.carburant || '').toLowerCase();
        document.getElementById('edit_status').value            = car.status || 'active';
        document.getElementById('edit_registration_date').value = car.registration_date
            ? car.registration_date.split('T')[0] : '';
        document.getElementById('edit_expiration_date').value   = car.expiration_date
            ? car.expiration_date.split('T')[0] : '';
        document.getElementById('edit_acquisition_date').value  = car.acquisition_date
            ? car.acquisition_date.split('T')[0] : '';
        document.getElementById('edit_notes').value             = car.notes || '';

        new bootstrap.Modal(document.getElementById('editCarModal')).show();
    } catch (e) {
        console.error('ouvrirModalEdit error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// CONFIRM EDIT

async function confirmerModification() {
    const carId = document.getElementById('edit_car_id').value;
    const payload = {
        brand:             document.getElementById('edit_brand').value.trim(),
        model:             document.getElementById('edit_model').value.trim(),
        plate_number:      document.getElementById('edit_plate_number').value.trim(),
        year:              document.getElementById('edit_year').value,
        owner_name:        document.getElementById('edit_owner_name').value.trim(),
        chassis_number:    document.getElementById('edit_chassis_number').value.trim(),
        puissance_fiscale: document.getElementById('edit_puissance_fiscale').value,
        carburant:         document.getElementById('edit_carburant').value,
        status:            document.getElementById('edit_status').value,
        registration_date: document.getElementById('edit_registration_date').value || null,
        expiration_date:   document.getElementById('edit_expiration_date').value || null,
        acquisition_date:  document.getElementById('edit_acquisition_date').value || null,
        notes:             document.getElementById('edit_notes').value.trim()
    };

    if (!payload.brand || !payload.model || !payload.plate_number) {
        Swal.fire({ icon: 'warning', title: 'Champs manquants', text: 'Marque, modèle et immatriculation sont obligatoires.' });
        return;
    }

    try {
        const res    = await fetch(`/car/update/${carId}`, {
            method:  'PUT',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload)
        });
        const result = await res.json();

        if (result.status === 'success') {
            bootstrap.Modal.getInstance(document.getElementById('editCarModal')).hide();
            Swal.fire({ icon: 'success', title: 'Modifié !', text: result.message, showConfirmButton: false, timer: 2000 });
            setTimeout(() => loadCars(), 2000);
        } else {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
        }
    } catch (e) {
        console.error('confirmerModification error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// DELETE CAR (soft delete → status = retired)

async function supprimerVoiture(event, carId, carLabel) {
    event.stopPropagation();

    // check if car has an active assignment first
    let warningHtml = `
        <span class="text-muted">${carLabel}</span><br>
        <small class="text-muted">Le véhicule sera marqué comme <strong>Retiré</strong>.</small>
    `;

    try {
        const affRes  = await fetch(`/car/get-affectation/${carId}`);
        const affData = await affRes.json();

        if (affData.status === 'success' && affData.assigned) {
            const a = affData.data;
            warningHtml = `
                <span class="text-muted">${carLabel}</span><br><br>
                <div class="alert alert-warning py-2 text-start small">
                    <i class="fas fa-user me-1"></i>
                    Ce véhicule est actuellement affecté à 
                    <strong>${a.prenom} ${a.nom}</strong> (${a.poste}).<br>
                    L'affectation sera clôturée mais <strong>l'historique sera conservé</strong>.
                </div>
            `;
        }
    } catch (e) {
        console.error('Erreur vérification affectation:', e);
    }

    const confirm = await Swal.fire({
        icon:              'warning',
        title:             'Retirer ce véhicule ?',
        html:              warningHtml,
        showCancelButton:  true,
        confirmButtonText: 'Oui, retirer',
        cancelButtonText:  'Annuler',
        confirmButtonColor:'#e74a3b',
        cancelButtonColor: '#858796'
    });

    if (!confirm.isConfirmed) return;

    try {
        const res    = await fetch(`/car/delete/${carId}`, { method: 'DELETE' });
        const result = await res.json();

        if (result.status === 'success') {
            Swal.fire({ icon: 'success', title: 'Retiré !', text: result.message, showConfirmButton: false, timer: 2000 });
            setTimeout(() => loadCars(), 2000);
        } else {
            Swal.fire({ icon: 'error', title: 'Erreur', text: result.message, confirmButtonColor: '#d33' });
        }
    } catch (e) {
        console.error('supprimerVoiture error:', e);
        Swal.fire({ icon: 'error', title: 'Erreur réseau', text: 'Impossible de contacter le serveur.' });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// HELPERS

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

////////////////////////////////////////////////////////////////////////////////////////////////
// TABLE STATE

let cars = [];
let currentPage = 1;
const rowsPerPage = 5;

////////////////////////////////////////////////////////////////////////////////////////////////
// LOAD CARS

async function loadCars() {
    const tbody = document.querySelector("#dataTable tbody");
    if (!tbody) return;
    try {
        const response = await fetch("/car/get-all-voitures");
        const result   = await response.json();
        if (result.status !== "success") { console.error("Error loading cars:", result.message); return; }
        cars = Array.isArray(result.data) ? result.data : [];
        renderTable();
    } catch (error) {
        console.error("Erreur interne :", error);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER TABLE

function renderTable() {
    const tbody = document.querySelector("#dataTable tbody");
    if (!tbody) return;

    const start    = (currentPage - 1) * rowsPerPage;
    const pageCars = cars.slice(start, start + rowsPerPage);

    if (pageCars.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Aucun véhicule trouvé</td></tr>`;
        return;
    }

    tbody.innerHTML = pageCars.map(car => {

        let statusBadge = '';
        const status = (car.status || '').toLowerCase();
        if      (status === 'active')      statusBadge = '<span class="badge bg-success shadow-sm">Opérationnel</span>';
        else if (status === 'maintenance') statusBadge = '<span class="badge bg-warning text-dark shadow-sm">Maintenance</span>';
        else if (status === 'inactive')    statusBadge = '<span class="badge bg-secondary shadow-sm">Hors Service</span>';
        else if (status === 'retired')     statusBadge = '<span class="badge bg-dark shadow-sm">Retiré</span>';
        else                               statusBadge = `<span class="badge bg-secondary shadow-sm">${escapeHtml(car.status || 'N/A')}</span>`;

        const carLabel   = `${escapeHtml(car.model || 'Véhicule')} — ${escapeHtml(car.plate_number || '')}`;
        const dossierBtn = car.dossier_complet ? '' : `
            <a href="/car/dossier?car_id=${car.id}"
                onclick="event.stopPropagation()"
                class="btn btn-outline-warning border-0 rounded-circle me-1"
                title="Compléter le dossier">
                <i class="fas fa-folder-open"></i>
            </a>`;

        return `
        <tr style="cursor:pointer;" onclick="window.location.href='/car/detail/${car.id}'">
            <td>
                <div class="d-flex align-items-center">
                    <div class="bg-light p-2 rounded me-3 text-center" style="width:40px">
                        <i class="fas fa-car text-primary"></i>
                    </div>
                    <div>
                        <div class="fw-bold text-dark">${escapeHtml(car.model || 'Inconnu')}</div>
                        <div class="text-xs text-muted">Année: ${escapeHtml(car.year || '-')}</div>
                    </div>
                </div>
            </td>
            <td>
                <span class="badge bg-white text-dark border p-2 font-monospace small">
                    ${escapeHtml(car.plate_number || 'N/A')}
                </span>
            </td>
            <td>
                <div class="text-sm fw-bold">${escapeHtml(car.owner_name || "N/A")}</div>
                <div class="text-xs text-muted">${escapeHtml(car.brand || '')}</div>
            </td>
            <td>
                <div class="text-xs text-muted">
                    <span class="fw-bold text-uppercase">VIN:</span>
                    ${escapeHtml(car.chassis_number || 'N/A')}
                </div>
            </td>
            <td class="text-center">${statusBadge}</td>
            <td>
                <div class="text-xs">
                    <div class="text-muted mb-1">
                        <i class="far fa-calendar-alt me-1 text-primary"></i>
                        Reg: ${escapeHtml(car.registration_date || '-')}
                    </div>
                    <div class="text-danger">
                        <i class="far fa-clock me-1"></i>
                        Exp: ${escapeHtml(car.expiration_date || '-')}
                    </div>
                </div>
            </td>
            <td class="text-end">
                <div class="btn-group btn-group-sm">
                    ${dossierBtn}
                    <button class="btn btn-outline-success border-0 rounded-circle me-1"
                        title="Affecter un employé"
                        onclick="ouvrirModalAffectation(event, ${car.id}, '${carLabel}')">
                        <i class="fas fa-user-tag"></i>
                    </button>
                    <button class="btn btn-outline-primary border-0 rounded-circle me-1"
                        title="Modifier"
                        onclick="ouvrirModalEdit(event, ${car.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-danger border-0 rounded-circle"
                        title="Supprimer"
                        onclick="supprimerVoiture(event, ${car.id}, '${carLabel}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>`;

    }).join("");

    renderPagination();
    updateTableInfo();
}

////////////////////////////////////////////////////////////////////////////////////////////////
// PAGINATION

function renderPagination() {
    const pagination = document.getElementById("data-pagination");
    if (!pagination) return;
    pagination.innerHTML = "";
    const totalPages = Math.ceil(cars.length / rowsPerPage);
    for (let i = 1; i <= totalPages; i++) {
        const active = i === currentPage ? "active" : "";
        pagination.innerHTML += `
            <li class="page-item ${active}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>`;
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// TABLE INFO

function updateTableInfo() {
    const info = document.getElementById("dataTable_info");
    if (!info) return;
    const start = (currentPage - 1) * rowsPerPage + 1;
    const end   = Math.min(currentPage * rowsPerPage, cars.length);
    info.innerText = `Showing ${start} to ${end} of ${cars.length} voitures`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// CHANGE PAGE

function changePage(page) { currentPage = page; renderTable(); }

////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

document.addEventListener("DOMContentLoaded", () => { loadCars(); });