////////////////////////////////////////////////////////////////////////////////////////////////
// STATE

const carId     = new URLSearchParams(window.location.search).get('car_id');
let currentStep = 2;

// tracks which steps were saved vs skipped
const docStatus = {
    assurance: null,  // 'saved' | 'skipped'
    vignette:  null,
    visite:    null
};

////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

document.addEventListener("DOMContentLoaded", async () => {

    if (!carId) {
        Swal.fire({ icon: "error", title: "Erreur", text: "Aucun véhicule spécifié." });
        return;
    }

    await loadCarInfo();
    goToStep(2);
});

////////////////////////////////////////////////////////////////////////////////////////////////
// LOAD CAR INFO

async function loadCarInfo() {
    try {
        const res  = await fetch(`/car/get-voiture/${carId}`);
        const data = await res.json();
        if (data.status !== "success") return;

        const car = data.data;
        document.getElementById("car_subtitle").innerText =
            `${car.model || ''} — ${car.plate_number || ''}`;

        document.getElementById("cg_summary").innerHTML = `
            <div class="col-md-3 mb-3">
                <div class="text-xs text-muted fw-bold mb-1">MODÈLE</div>
                <div class="fw-bold">${escapeHtml(car.model || '-')}</div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="text-xs text-muted fw-bold mb-1">IMMATRICULATION</div>
                <div class="fw-bold text-primary font-monospace">${escapeHtml(car.plate_number || '-')}</div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="text-xs text-muted fw-bold mb-1">CHÂSSIS (VIN)</div>
                <div class="fw-bold">${escapeHtml(car.chassis_number || '-')}</div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="text-xs text-muted fw-bold mb-1">ANNÉE</div>
                <div class="fw-bold">${escapeHtml(car.year || '-')}</div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="text-xs text-muted fw-bold mb-1">PROPRIÉTAIRE</div>
                <div>${escapeHtml(car.owner_name || '-')}</div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="text-xs text-muted fw-bold mb-1">CARBURANT</div>
                <div>${escapeHtml(car.carburant || '-')}</div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="text-xs text-muted fw-bold mb-1">PUISSANCE FISCALE</div>
                <div>${escapeHtml(car.puissance_fiscale || '-')} CV</div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="text-xs text-muted fw-bold mb-1">EXPIRATION CG</div>
                <div class="text-danger">${escapeHtml(car.expiration_date || '-')}</div>
            </div>
        `;

        // also set the summary title for step 5
        const titleEl = document.getElementById("summary_car_title");
        if (titleEl) titleEl.innerText = `${car.model || ''} — ${car.plate_number || ''}`;

    } catch (e) {
        console.error("loadCarInfo error:", e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// STEP NAVIGATION

function goToStep(step) {
    currentStep = step;

    document.querySelectorAll(".step-panel").forEach(p => p.classList.remove("active"));
    document.getElementById(`panel-${step}`).classList.add("active");

    for (let i = 1; i <= 5; i++) {
        const ind    = document.getElementById(`step-ind-${i}`);
        const circle = ind.querySelector(".step-circle");
        ind.classList.remove("active", "done");

        if (i < step) {
            ind.classList.add("done");
            circle.innerHTML = '<i class="fas fa-check"></i>';
        } else if (i === step) {
            ind.classList.add("active");
            circle.innerHTML = i === 1 ? '<i class="fas fa-check"></i>' : i;
        } else {
            circle.innerHTML = i;
        }
    }

    // when reaching step 5, build the summary
    if (step === 5) buildSummary();

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

////////////////////////////////////////////////////////////////////////////////////////////////
// SKIP STEP — mark as skipped, move on

function skipStep(docType, nextStep) {
    docStatus[docType] = 'skipped';
    goToStep(nextStep);
}

////////////////////////////////////////////////////////////////////////////////////////////////
// FILE SELECTED

function onFileSelected(docType) {
    const fileInput = document.getElementById(`${docType}_file`);
    const zone      = document.getElementById(`${docType}_zone`);
    const scanBtn   = document.getElementById(`${docType}_scan_btn`);
    const nameDiv   = document.getElementById(`${docType}_file_name`);

    if (fileInput.files.length > 0) {
        zone.classList.add("has-file");
        scanBtn.disabled = false;
        nameDiv.style.display = "block";
        nameDiv.querySelector("span").innerText = fileInput.files[0].name;
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// SCAN DOCUMENT — mock OCR

async function scanDocument(docType) {
    const fileInput = document.getElementById(`${docType}_file`);
    const loader    = document.getElementById(`${docType}_loader`);
    const scanBtn   = document.getElementById(`${docType}_scan_btn`);

    if (!fileInput.files.length) return;

    loader.style.display = "block";
    scanBtn.disabled = true;

    const formData = new FormData();
    formData.append("file",     fileInput.files[0]);
    formData.append("doc_type", docType);

    try {
        const res  = await fetch(`/car/scan-document/${carId}`, { method: "POST", body: formData });
        const data = await res.json();

        if (data.status !== "success") {
            Swal.fire({ icon: "error", title: "Erreur", text: data.message });
            return;
        }

        prefillDocFields(docType, data.extracted_data);
        notifs.success("Extraction terminée", "Les champs ont été pré-remplis.");

    } catch (e) {
        Swal.fire({ icon: "error", title: "Erreur serveur", text: "Impossible de scanner le document." });
    } finally {
        loader.style.display = "none";
        scanBtn.disabled = false;
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// PREFILL FIELDS

function prefillDocFields(docType, data) {
    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el && val !== undefined && val !== null) el.value = val;
    };

    if (docType === "assurance") {
        setVal("assurance_insurer",       data.insurer);
        setVal("assurance_policy_number", data.policy_number);
        setVal("assurance_start_date",    data.start_date);
        setVal("assurance_end_date",      data.end_date);
    } else if (docType === "vignette") {
        setVal("vignette_year",            data.year);
        setVal("vignette_montant",         data.montant);
        setVal("vignette_expiration_date", data.expiration_date);
    } else if (docType === "visite") {
        setVal("visite_montant",         data.montant);
        setVal("visite_expiration_date", data.expiration_date);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// SAVE DOCUMENT

async function saveDocument(docType, nextStep) {

    const fileInput = document.getElementById(`${docType}_file`);
    const formData  = new FormData();

    if (fileInput.files.length > 0) {
        formData.append("file", fileInput.files[0]);
    }

    if (docType === "assurance") {
        const start_date = document.getElementById("assurance_start_date").value;
        const end_date   = document.getElementById("assurance_end_date").value;
        if (!start_date || !end_date) {
            Swal.fire({ icon: "warning", title: "Champs manquants", text: "Les dates de début et fin sont obligatoires." });
            return;
        }
        formData.append("insurer",       document.getElementById("assurance_insurer").value.trim());
        formData.append("policy_number", document.getElementById("assurance_policy_number").value.trim());
        formData.append("start_date",    start_date);
        formData.append("end_date",      end_date);

    } else if (docType === "vignette") {
        const expiration_date = document.getElementById("vignette_expiration_date").value;
        if (!expiration_date) {
            Swal.fire({ icon: "warning", title: "Champs manquants", text: "La date d'expiration est obligatoire." });
            return;
        }
        formData.append("year",            document.getElementById("vignette_year").value);
        formData.append("montant",         document.getElementById("vignette_montant").value);
        formData.append("expiration_date", expiration_date);

    } else if (docType === "visite") {
        const expiration_date = document.getElementById("visite_expiration_date").value;
        if (!expiration_date) {
            Swal.fire({ icon: "warning", title: "Champs manquants", text: "La date d'expiration est obligatoire." });
            return;
        }
        formData.append("montant",         document.getElementById("visite_montant").value);
        formData.append("expiration_date", expiration_date);
    }

    try {
        const res  = await fetch(`/car/save-document/${carId}/${docType}`, { method: "POST", body: formData });
        const data = await res.json();

        if (data.status === "success") {
            docStatus[docType] = 'saved';
            notifs.success("Enregistré", `Document enregistré avec succès.`);
            goToStep(nextStep);
        } else {
            Swal.fire({ icon: "error", title: "Erreur", text: data.message });
        }
    } catch (e) {
        Swal.fire({ icon: "error", title: "Erreur serveur", text: "Impossible d'enregistrer le document." });
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// BUILD SUMMARY for step 5

function buildSummary() {
    const docs = [
        { key: 'assurance', label: 'Assurance',       icon: 'fas fa-shield-alt' },
        { key: 'vignette',  label: 'Vignette',         icon: 'fas fa-receipt'    },
        { key: 'visite',    label: 'Visite Technique', icon: 'fas fa-tools'      },
    ];

    const summaryList = document.getElementById("summary_list");
    summaryList.innerHTML = `
        <div class="summary-item done mb-2">
            <i class="fas fa-id-card text-success me-3 fa-lg"></i>
            <div>
                <div class="fw-bold small">Carte Grise</div>
                <div class="text-muted text-xs">Enregistrée lors de la création du véhicule</div>
            </div>
            <span class="badge bg-success ms-auto">Enregistré</span>
        </div>
    ` + docs.map(doc => {
        const status  = docStatus[doc.key];
        const isDone  = status === 'saved';
        const cls     = isDone ? 'done' : 'skipped';
        const badge   = isDone
            ? '<span class="badge bg-success ms-auto">Enregistré</span>'
            : '<span class="badge bg-secondary ms-auto">Ignoré</span>';
        const subtext = isDone
            ? 'Document scanné et enregistré'
            : 'Non fourni — peut être ajouté depuis le dossier plus tard';

        return `
        <div class="summary-item ${cls} mb-2">
            <i class="${doc.icon} ${isDone ? 'text-success' : 'text-muted'} me-3 fa-lg"></i>
            <div>
                <div class="fw-bold small">${doc.label}</div>
                <div class="text-muted text-xs">${subtext}</div>
            </div>
            ${badge}
        </div>`;
    }).join("");
}

////////////////////////////////////////////////////////////////////////////////////////////////
// HELPERS

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}