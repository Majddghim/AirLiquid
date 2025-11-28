async function enregistrerVoiture() {

    const formData = new FormData();

    formData.append("model", document.getElementById("model").value.trim());
    formData.append("year", document.getElementById("year").value.trim());
    formData.append("plate_number", document.getElementById("plate_number").value.trim());
    formData.append("owner_name", document.getElementById("owner_name").value.trim());
    formData.append("chassis_number", document.getElementById("chassis_number").value.trim());
    formData.append("status", document.getElementById("status").value);
    formData.append("registration_date", document.getElementById("registration_date").value);
    // formData.append("registration_date", document.getElementById("registration_date").value);
    formData.append("expiration_date", document.getElementById("expiration_date").value);
    formData.append("notes", document.getElementById("notes").value.trim());

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
    try {
        const url = `/get-cars?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(limit)}`;
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

        if (cars.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8">Aucune voiture</td></tr>';
            return;
        }

        const rowsHtml = cars.map(car => `
            <tr>
                <td>${escapeHtml(car.model)}</td>
                <td>${escapeHtml(car.year)}</td>
                <td>${escapeHtml(car.plate_number)}</td>
                <td>${escapeHtml(car.owner_name)}</td>
                <td>${escapeHtml(car.chassis_number)}</td>
                <td>${escapeHtml(car.status)}</td>
                <td>${escapeHtml(car.registration_date)}</td>
                <td>${escapeHtml(car.expiration_date)}</td>
            </tr>
        `).join("");

        tbody.innerHTML = rowsHtml;

    } catch (error) {
        console.error("Erreur interne :", error);
    }
}

function initPage() {
    loadCars();
}

document.addEventListener("DOMContentLoaded", initPage);

