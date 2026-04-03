////////////////////////////////////////////////////////////////////////////////////////////////
// BRANDS & MODELS — cascading dropdowns
// allBrands is cached after first load so we can match OCR text against it

let allBrands = [];

async function loadBrands() {
    try {
        const res  = await fetch('/car/get-brands');
        const data = await res.json();
        if (data.status !== 'success') return;

        allBrands = data.data; // cache for OCR matching

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

        // auto-select if a model name was provided from OCR
        if (preselect) {
            const lower = preselect.toLowerCase();
            const match = Array.from(modelSelect.options).find(
                o => o.value.toLowerCase() === lower
            );
            if (match) {
                modelSelect.value = match.value;
            } else {
                // model not in list → add it as custom option and select it
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

// called by the brand dropdown onchange
async function onBrandChange() {
    const brandId = document.getElementById('modal_brand_id').value;
    await loadModels(brandId);
}

// called after OCR scan — matches brand name and pre-selects brand + model
async function setBrandAndModelFromOcr(ocrModelString) {
    if (!ocrModelString) return;

    // OCR returns e.g. "Peugeot Partner" → split on first space
    const parts     = ocrModelString.trim().split(' ');
    const brandName = parts[0];                    // "Peugeot"
    const modelName = parts.slice(1).join(' ');    // "Partner"

    // find matching brand in cached list (case-insensitive)
    const brand = allBrands.find(
        b => b.name.toLowerCase() === brandName.toLowerCase()
    );

    const brandSelect = document.getElementById('modal_brand_id');

    if (brand) {
        brandSelect.value = brand.id;
        await loadModels(brand.id, modelName);
    } else {
        // brand not in DB — add as custom option
        const opt    = document.createElement('option');
        opt.value    = '';
        opt.text     = brandName;
        opt.selected = true;
        brandSelect.appendChild(opt);

        // still try to load a custom model name
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

        // load brands first (needed for OCR matching)
        await loadBrands();

        // fill simple fields
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

        // auto-select brand + model from OCR string e.g. "Peugeot Partner"
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

    // get brand name from selected option text
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
                        onclick="event.stopPropagation()">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-danger border-0 rounded-circle"
                        title="Supprimer"
                        onclick="event.stopPropagation()">
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