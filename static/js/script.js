var id_table = ''
var current_page = 1;
var data = []
var id_pagination = ''
var header = ''
var footer = ''
// var division_table = 1
var show_div_id = ''
var entite = ''
var notifs = new Notifications()


function enter_loading_mode() {
    big_div = document.getElementsByClassName('container-fluid')[0];
    loading_div = document.createElement('div');
    loading_div.id = 'loading';
    loading_div.style = "    position: fixed;\n" +
        "    top: 0;\n" +
        "    left: 0;\n" +
        "    width: 100%;\n" +
        "    height: 100%;\n" +
        "    background-color: rgba(0, 0, 0, 0.5);\n" +
        "    backdrop-filter: blur(4px);\n" +
        "    z-index: 3;" +
        "display: flex;" +
        "align-items: center;" +
        "justify-content: center;"
    loading_div.innerHTML = `<div class="spinner-border text-primary" role="status">
    <span class="sr-only">Loading...</span>
    </div>`;
    big_div.appendChild(loading_div);
}

function quit_loading_mode() {
    loading_div = document.getElementById('loading');
    loading_div.remove();
}


function get_data_ready_load_table(table_id, table_header, table_footer, table_data, table_division_table) {
    id_table = table_id;
    header = table_header;
    footer = table_footer;
    data = table_data;
    console.log(data)
    division_table = table_division_table;

    load_table();
}

function load_table() {

    var table = document.getElementById(id_table);
    table.innerHTML = header;
    var start = (current_page - 1) * division_table;
    var end = current_page * division_table;
    var data_page = data.slice(start, end);
    table.innerHTML += data_page.join("");
    table.innerHTML += footer;
}


function get_page_backend(p) {
    prepare_search_link(p)
}

function previous_page_backend(p) {
    prepare_search_link(p)
}

function next_page_backend(p) {
    prepare_search_link(p)
}

function load_backend_pagination(pages, current_page, nombre_totale, len) {
    var pagination = document.getElementById("data-pagination");
    pagination.innerHTML = ""
    if (nombre_totale === 0) {
        load_pagination_backend_status(20, nombre_totale, current_page, len)
        return;
    }
    disable_prev = ''
    if (current_page === 1) {
        disable_prev = 'disabled'
    }
    pagination.innerHTML += `<li class="page-item"><button class="page-link ${disable_prev}" onclick="previous_page_backend(${current_page - 1})" aria-label="Previous" ><span aria-hidden="true">«</span></button></li>`
    for (var i = 1; i <= pages; i++) {
        active = ''
        if (i === current_page) {
            active = 'active'
        }
        pagination.innerHTML += `<li id="button-pagination-${i}" class="page-item ${active}"><button onclick="get_page_backend(${i})" class="page-link">${i}</button></li>`
    }
    disable_next = ''
    if (current_page === pages) {
        disable_next = 'disabled'
    }
    pagination.innerHTML += `<li class="page-item"><button class="page-link ${disable_next}" onclick="next_page_backend(${current_page + 1})" aria-label="Next" ><span aria-hidden="true">»</span></button></li>`
    load_pagination_backend_status(20, nombre_totale, current_page, len)
}

function load_pagination_backend_status(dt, nombre_totale, current_page, len) {
    console.log("Loading pagination status", nombre_totale);
    var pagination = document.getElementById("dataTable_info");
    pagination.innerHTML = ""
    if (nombre_totale === 0) {
        return;
    }
    pagination.innerHTML += `Affichage de ${dt * (current_page - 1) + 1} à ${(dt * current_page) - (20 - len)} sur ${nombre_totale} `
}

function open_details_window(name) {
    body = document.querySelector("body");

    hidden_big_div = document.createElement('div');
    hidden_big_div.id = 'hidden_big_div';
    hidden_big_div.style = "    position: fixed;\n" +
        "    top: 0;\n" +
        "    left: 0;\n" +
        "    width: 100%;\n" +
        "    height: 100%;\n" +
        "    background-color: rgba(0, 0, 0, 0.5);\n" +
        "    backdrop-filter: blur(4px);\n" +
        "    z-index: 3;" +
        "display: flex;" +
        "align-items: center;" +
        "justify-content: center;"

    div = document.createElement("div");
    div.id = "request-details";
    div.className = "max-w-4xl mx-auto bg-white shadow-lg rounded-xl p-6 border-t-8";
    div.style.borderColor = '#3a3b45'
    div.style.width = '100%';
    div.style.height = '100%';
    div.style.overflowY = 'auto';
    div.style.borderRadius = '1rem';
    div.setAttribute("data-aos", "fade-up");
    div.setAttribute("data-aos-once", "true");
    div.innerHTML += `
        <div style="display: flex; justify-content: space-between">
            <h2 class="text-2xl font-bold mb-4 text-gray-800">${name}</h2>
            <button type="button" class="px-6 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition" style="max-height: 40px;" onclick="remove_post_div()">Fermer</button>
        </div>
    `
    hidden_big_div.appendChild(div);
    body.appendChild(hidden_big_div);
}

function remove_post_div() {
    // Get the div by ID
    const div = document.querySelector('#hidden_big_div');

    if (div) {
        // Add a fade-out transition
        div.style.transition = 'opacity 0.5s ease';
        div.style.opacity = '0';

        // Wait for the transition to finish before removing the element
        setTimeout(() => {
            if (div.parentNode) {
                div.parentNode.removeChild(div);
            }
        }, 500); // Duration matches the transition time
    }
}

