var enitity_name = "Employée";
var data = [];
var division_table = 7;
var search_link = 'get-employes?page=1&limit=' + division_table; // Default search link
var page = 1; // Current page number
let debounceTimer;
let controller = null;

const searchInput = document.querySelector("#search_by_name");
if (searchInput) {
    searchInput.addEventListener("input", function () {
        prepare_search_link(1); // Reset to page 1 on new search
    });
}


function initPage() {
    const table = document.getElementById('dataTable');
    if (!table) return; // Not on list page
    enter_loading_mode();
    load_page(search_link);
}

function prepare_search_link(p = 1) {
    let search_by_name = document.querySelector('#search_by_name').value;
    search_link = 'get-employes?page=' + p + '&limit=' + division_table;
    if (search_by_name && search_by_name.trim() !== '') {
        search_link += '&search_by_name=' + encodeURIComponent(search_by_name.trim());
    }
    page = p; // Update the current page number
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
        // Cancel previous request if ongoing
        if (controller) {
            controller.abort();
        }
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
                    try {
                        quit_loading_mode();
                    } catch (e) {
                    }
                } else {
                    if (response.status === 'failed') {
                        notifs.warn('Aucune employe trouvée.');
                        load_table_data([]);
                        load_backend_pagination(1, page, 0, 0);
                    } else {
                        notifs.error('Erreur');
                    }
                    quit_div_loading_mode('dataTable');
                }

            })
            .catch(err => {
                if (err.name !== "AbortError") {
                    console.error("Search error:", err);
                }
                try { quit_loading_mode() }
                catch (e) { };
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
                    <th>Poste</th>
                    <th>Statut Flotte</th>
                    <th class="text-end pe-4">Actions</th>
                </tr>
            </thead>
            <tbody>
                <tr><td colspan="5" class="text-center py-5 text-muted"><i class="fas fa-user-slash fa-2x mb-2 d-block opacity-25"></i>Aucun collaborateur trouvé</td></tr>
            </tbody>`;
        return;
    }

    const header = `
        <thead class="table-light">
            <tr class="text-xs text-uppercase text-muted">
                <th class="ps-4">Collaborateur</th>
                <th>Coordonnées</th>
                <th>Poste / Département</th>
                <th>Statut de Flotte</th>
                <th class="text-end pe-4">Actions</th>
            </tr>
        </thead>`;

    const footer = ""; // Removing legacy footer for cleaner look
    const body = data.map(employe => {
        const initials = `${(employe.prenom || 'E')[0]}${(employe.nom || 'P')[0]}`.toUpperCase();
        return `
            <tr>
                <td class="ps-4">
                    <div class="d-flex align-items-center">
                        <div class="bg-light p-2 rounded-circle me-3 text-center" style="width: 40px; height: 40px; line-height: 24px;">
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
                        <div class="text-dark"><i class="far fa-envelope me-2 text-muted"></i>${escapeHtml(employe.email)}</div>
                        <div class="text-muted extra-small"><i class="fas fa-phone-alt me-2"></i>${escapeHtml(employe.telephone || 'Non renseigné')}</div>
                    </div>
                </td>
                <td>
                    <div class="fw-bold text-sm text-dark">${escapeHtml(employe.poste || 'Employé')}</div>
                    <div class="text-xs text-primary fw-bold text-uppercase">Siège Social</div>
                </td>
                <td>
                    <button class="btn btn-sm btn-light border-primary text-primary rounded-pill px-3 shadow-none" onclick='window.location.href="/dashboard/ajout-voiture/${employe.id}"' style="font-size: 0.7rem; border-width:1px">
                        <i class="fas fa-car-side me-1"></i>Affectation
                    </button>
                </td>
                <td class="text-end pe-4">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary border-0 rounded-circle me-1" title="Modifier"><i class="fas fa-user-edit"></i></button>
                        <button class="btn btn-outline-danger border-0 rounded-circle" title="Supprimer"><i class="fas fa-trash-alt"></i></button>
                    </div>
                </td>
            </tr>`;
    });

    prepare_table(header, footer, body, division_table);
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function prepare_table(header, footer, body, division_table) {
    get_data_ready_load_table("dataTable", header, footer, body, division_table)
    // get_data_ready_pagination("data-pagination", data.length, division_table, "dataTable_info_marque", enitity_name)
}

function add_request_verification() {
    let name = document.getElementById('name').value;
    let description = document.getElementById('description').value;
    if (name === '' || description === '') {
        notifs.warn('Veuillez remplir tous les champs.');
        return;
    }
    add_request(name, description);
}

function add_request(name, description) {
    let btn = document.getElementById('action-btn');
    btn.disabled = true;
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/skill-category/add-skill-category', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.status === 'success') {
                notifs.success('Catégorie ajoutée avec succès.');
                openPageDashboardSkillCategory();
            } else {
                btn.disabled = false;
                notifs.error('Erreur : ' + response.message);
            }
        }
    };
    var data = JSON.stringify({ name: name, description: description });
    xhr.send(data);
}

function openUpdatePage(id) {
    openPageUpdateSkillCategory(id);
}

function update_request_verification(id) {
    let name = document.getElementById('name').value;
    let description = document.getElementById('description').value;
    if (name === '' || description === '') {
        notifs.warn('Veuillez remplir tous les champs.');
        return;
    }
    update_request(id, name, description);
}

function update_request(id, name, description) {
    let btn = document.getElementById('action-btn');
    btn.disabled = true;
    var xhr = new XMLHttpRequest();
    xhr.open('PUT', '/skill-category/update-skill-category/' + id, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.status === 'success') {
                notifs.success('Catégorie mise à jour avec succès.');
                openPageDashboardSkillCategory();
            } else {
                btn.disabled = false;
                notifs.error('Erreur : ' + response.message);
            }
        }
    };
    var data = JSON.stringify({ name: name, description: description });
    xhr.send(data);
}

function delete_request(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette catégorie ?')) {
        var xhr = new XMLHttpRequest();
        xhr.open('DELETE', '/skill-category/delete-skill-category/' + id, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                if (response.status === 'success') {
                    notifs.success('Catégorie supprimée avec succès.');
                    prepare_search_link(1); // Reload the first page after deletion
                } else {
                    notifs.error('Erreur : ' + response.message);
                }
            }
        };
        xhr.send();
    }
}



































////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////






async function enregistrerEmploye() {
    console.log("enregistrerEmploye called");
    const getV = (id) => {
        const el = document.getElementById(id);
        return el ? el.value.trim() : "";
    };

    // Get form data
    const data = {
        nom: getV("nom"),
        prenom: getV("prenom"),
        email: getV("email"),
        telephone: getV("telephone"), // Using the ID from HTML
        poste: getV("poste"),
        departement: getV("departement"),
        created_at: getV("created_at")
    };

    try {
        const response = await fetch("/employe/ajout-employe", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.status === "success") {
            Swal.fire({
                icon: "success",
                title: "Employé ajouté",
                text: result.message,
                showConfirmButton: false,
                timer: 1800   // SweetAlert closes after 1.8 seconds
            }).then(() => {
                window.location.href = "/dashboard/liste-employes";
            });



        } else {
            Swal.fire({
                icon: "warning",
                title: "Attention",
                text: result.message,
                confirmButtonColor: "#f0ad4e"
            });
        }

    } catch (error) {
        console.error("Erreur lors de l'envoi :", error);

        Swal.fire({
            icon: "error",
            title: "Erreur",
            text: "Une erreur s'est produite lors de l'enregistrement.",
            confirmButtonColor: "#d33"
        });
    }
}
