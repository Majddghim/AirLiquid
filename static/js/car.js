async function enregistrerVoiture() {

    const formData = new FormData();

    const getVal = (id) => {
        const el = document.getElementById(id);
        return el ? el.value.trim() : "";
    };

    formData.append("model", getVal("model"));
    formData.append("year", getVal("year"));
    formData.append("plate_number", getVal("plate_number"));
    formData.append("owner_name", getVal("owner_name"));
    formData.append("chassis_number", getVal("chassis_number"));
    formData.append("status", getVal("status"));
    formData.append("registration_date", getVal("registration_date"));
    formData.append("acquisition_date", getVal("acquisition_date"));
    formData.append("expiration_date", getVal("expiration_date"));
    formData.append("notes", getVal("notes"));

    const carteGriseFile = document.getElementById("carte_grise").files[0];
    if (carteGriseFile) {
        formData.append("carte_grise", carteGriseFile);
    }

    try {

        const response = await fetch("/car/ajout-voiture", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        // ❌ Erreur
        if (result.status !== "success") {
            Swal.fire({
                icon: "error",
                title: "Erreur",
                text: result.message,
                confirmButtonColor: "#d33"
            });
            return;
        }

        // ✅ Succès + redirection
        Swal.fire({
            icon: "success",
            title: "Voiture ajoutée !",
            text: "Le véhicule a été enregistré avec succès.",
            showConfirmButton: false,
            timer: 2000
        });

        setTimeout(() => {
            window.location.href = "/dashboard/cars";
        }, 2000);

    } catch (error) {

        console.error("Erreur réseau :", error);

        Swal.fire({
            icon: "error",
            title: "Erreur interne",
            text: "Une erreur s'est produite lors de l'envoi.",
            confirmButtonColor: "#d33"
        });
    }
}


async function scannerCarteGrise() {
    const fileInput = document.getElementById("carte_grise_scan");
    const loader = document.getElementById("scan-loader");
    const scanBtn = document.getElementById("scanBtn");

    if (!fileInput.files || fileInput.files.length === 0) {
        Swal.fire({
            icon: "warning",
            title: "Document manquant",
            text: "Veuillez sélectionner une image de carte grise.",
        });
        return;
    }

    loader.style.display = "block";
    scanBtn.disabled = true;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch("/car/extract-data", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (result.status === "success") {
            const data = result.extracted_data;

            // Map JSON keys to form IDs
            const fieldsMap = {
                "model": "model",
                "year": "year",
                "plate_number": "plate_number",
                "owner_name": "owner_name",
                "chassis_number": "chassis_number",
                "registration_date": "registration_date",
                "expiration_date": "expiration_date"
            };

            for (const [jsonKey, elementId] of Object.entries(fieldsMap)) {
                if (data[jsonKey]) {
                    document.getElementById(elementId).value = data[jsonKey];
                }
            }

            notifs.success("Extraction terminée", "Le formulaire a été pré-rempli.");
        } else {
            notifs.error("Erreur d'extraction", result.message || "Format non reconnu");
        }
    } catch (error) {
        console.error("Scan error:", error);
        notifs.error("Serveur indisponible", "Impossible de contacter le service d'extraction.");
    } finally {
        loader.style.display = "none";
        scanBtn.disabled = false;
    }
}


////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// javascript
function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

async function loadCars(page = 1, limit = 10) {
    const tbody = document.querySelector("#dataTable tbody");
    if (!tbody) {
        // Not on the cars list page
        return;
    }
    try {
        const url = `/car/get-voitures?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(limit)}`;
        const response = await fetch(url);

        if (!response.ok) {
            console.error("HTTP error while loading cars:", response.status, response.statusText);
            return;
        }

        const result = await response.json();

        if (result.status !== "success") {
            console.error("Error loading cars:", result.message);
            return;
        }

        const cars = Array.isArray(result.data) ? result.data : [];

        const tbody = document.querySelector("#dataTable tbody");
        if (!tbody) {
            console.error("Element '#dataTable tbody' introuvable.");
            return;
        }

        const rowsHtml = cars.map(car => {
            let statusBadge = '';
            const status = (car.status || '').toLowerCase();
            if (status === 'disponible' || status === 'active' || status === 'opérationnel') {
                statusBadge = '<span class="badge bg-success shadow-sm">Opérationnel</span>';
            } else if (status === 'maintenance') {
                statusBadge = '<span class="badge bg-warning text-dark shadow-sm">Maintenance</span>';
            } else {
                statusBadge = `<span class="badge bg-secondary shadow-sm">${escapeHtml(car.status || 'N/A')}</span>`;
            }

            return `
                <tr>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="bg-light p-2 rounded me-3 text-center" style="width: 40px;">
                                <i class="fas fa-car text-primary"></i>
                            </div>
                            <div>
                                <div class="fw-bold text-dark">${escapeHtml(car.model || 'Inconnu')}</div>
                                <div class="text-xs text-muted">Année: ${escapeHtml(car.year || '-')}</div>
                            </div>
                        </div>
                    </td>
                    <td><span class="badge bg-white text-dark border p-2 font-monospace small">${escapeHtml(car.plate_number || 'N/A')}</span></td>
                    <td><div class="text-sm font-weight-bold">${escapeHtml(car.owner_name || "N/A")}</div></td>
                    <td>
                        <div class="text-xs">
                             <div class="text-muted"><span class="fw-bold text-uppercase">VIN:</span> ${escapeHtml(car.chassis_number || 'N/A')}</div>
                        </div>
                    </td>
                    <td class="text-center">${statusBadge}</td>
                    <td>
                        <div class="text-xs">
                            <div class="text-muted mb-1"><i class="far fa-calendar-alt me-1 text-primary"></i>Reg: ${escapeHtml(car.registration_date || '-')}</div>
                            <div class="text-danger"><i class="far fa-clock me-1"></i>Exp: ${escapeHtml(car.expiration_date || '-')}</div>
                        </div>
                    </td>
                    <td class="text-end">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary border-0 rounded-circle me-1" title="Modifier"><i class="fas fa-edit"></i></button>
                            <button class="btn btn-outline-danger border-0 rounded-circle" title="Supprimer"><i class="fas fa-trash"></i></button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        tbody.innerHTML = rowsHtml;

        // Update total columns if empty
        if (cars.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">Aucun véhicule trouvé</td></tr>';
        }

    } catch (error) {
        console.error("Erreur interne :", error);
    }
}

function initPage() {
    loadCars();
}

document.addEventListener("DOMContentLoaded", initPage);

