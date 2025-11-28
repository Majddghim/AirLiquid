var enitity_name = "Employée";
var data = [];
var division_table = 7;
var search_link = 'get-employes?page=1&limit=' + division_table; // Default search link
var page = 1; // Current page number
let debounceTimer;
let controller = null;

document.querySelector("#search_by_name").addEventListener("input", function () {
    prepare_search_link(1); // Reset to page 1 on new search
});


function initPage() {
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

        fetch('/employe/' + search_link, {signal: controller.signal})
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
                try{quit_loading_mode()}
                catch (e){};
            });
    }, 300);
}


function load_table_data(data) {
    if (data.length === 0) {
        // notifs.warn('Aucune catégorie trouvée.');
        let division_table = document.getElementById('dataTable');
        division_table.innerHTML = "<tr><td colspan='4'>Aucun élement trouvée.</td></tr>";
        return;
    }
    header = "<thead><tr><th>Name</th><th>Position</th><th>Phone</th><th>Start Date</th><th>Voiture</th><th>Action</th></tr></thead>";
    footer = "<tfoot><tr><th>Name</th><th>Position</th><th>Phone</th><th>Start Date</th>Action<th></tr></tfoot>";
    body = [];

    data.forEach(employe => {
        body.push(
            `<tr >
                <td>${employe.first_name} ${employe.last_name}</td>
                <td>${employe.position}</td>
                <td>${employe.phone}</td>
                <td>${employe.created_at}</td>
                <td><button class="btn btn-success btn-sm" onclick='window.location.href="/dashboard/ajout-voiture/${employe.id}"'=>Assigner voiture</button></td>
                <td><button class='btn btn-outline-secondary' onclick=''>Modifier</button>
                <button class='btn btn-outline-danger' onclick=''>Supprimer</button></td>
            </tr>`
        );
    });

    prepare_table(header, footer, body, division_table);
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
    var data = JSON.stringify({name: name, description: description});
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
    var data = JSON.stringify({name: name, description: description});
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
    // Get form data
    const data = {
        nom: document.getElementById("nom").value.trim(),
        prenom: document.getElementById("prenom").value.trim(),
        email: document.getElementById("email").value.trim(),
        telephone: document.getElementById("phone").value.trim(),
        poste: document.getElementById("poste").value.trim(),
        departement: document.getElementById("departement").value.trim(),
        created_at: document.getElementById("created_at").value
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
