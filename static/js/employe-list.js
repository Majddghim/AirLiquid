////////////////////////////////////////////////////////////////////////////////////////////////
// EMPLOYEE LIST — filter + table + pagination

let employees    = [];
let allEmployees = [];
let currentPage  = 1;
const rowsPerPage = 10;

async function loadEmployees() {
    try {
        const response = await fetch("/employe/get-all-employes");
        const result   = await response.json();
        if (result.status === "success") {
            allEmployees = result.data;
            employees    = [...allEmployees];

            // populate department filter
            const depts  = [...new Set(allEmployees.map(e => e.departement).filter(Boolean))].sort();
            const select = document.getElementById('filter_dept');
            depts.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d;
                opt.text  = d;
                select.appendChild(opt);
            });

            renderTable();
            renderPagination();
        }
    } catch (error) {
        console.error("Error loading employees:", error);
    }
}

function filterEmployees() {
    const search = document.getElementById('search_by_name').value.toLowerCase();
    const status = document.getElementById('filter_status').value;
    const dept   = document.getElementById('filter_dept').value;

    employees = allEmployees.filter(e => {
        const matchSearch = !search ||
            (e.prenom || '').toLowerCase().includes(search) ||
            (e.nom    || '').toLowerCase().includes(search) ||
            (e.email  || '').toLowerCase().includes(search) ||
            `${e.prenom} ${e.nom}`.toLowerCase().includes(search) ||
            `${e.nom} ${e.prenom}`.toLowerCase().includes(search);
        const matchStatus = !status || e.status === status;
        const matchDept   = !dept   || e.departement === dept;
        return matchSearch && matchStatus && matchDept;
    });

    currentPage = 1;
    renderTable();
    renderPagination();
}

function renderTable() {
    const tbody = document.getElementById("employeesTableBody");
    tbody.innerHTML = "";

    const start     = (currentPage - 1) * rowsPerPage;
    const end       = start + rowsPerPage;
    const pageItems = employees.slice(start, end);

    if (!pageItems.length) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">
            <i class="fas fa-search me-1"></i>Aucun employé trouvé.</td></tr>`;
        document.getElementById("tableInfo").innerText = '0 résultats';
        return;
    }

    pageItems.forEach(p => {
        const initials    = (p.prenom ? p.prenom[0].toUpperCase() : 'E') +
                            (p.nom    ? p.nom[0].toUpperCase()    : 'P');
        const statusBadge = p.status === 'active'
            ? '<span class="badge bg-success-subtle text-success ms-1">Actif</span>'
            : '<span class="badge bg-secondary-subtle text-secondary ms-1">Inactif</span>';

        tbody.innerHTML += `
        <tr style="cursor:pointer;" onclick="window.location.href='/employe/profil/${p.id}'">
            <td class="ps-4">
                <div class="d-flex align-items-center">
                    <div class="p-2 rounded-circle me-3 text-center fw-bold text-primary"
                        style="width:40px;height:40px;background:#eef4ff;line-height:24px;">
                        ${initials}
                    </div>
                    <div>
                        <div class="fw-bold text-dark">
                            ${p.prenom || ''} ${p.nom || ''}
                            ${statusBadge}
                        </div>
                        <div class="text-xs text-muted">ID: #${p.id}</div>
                    </div>
                </div>
            </td>
            <td>
                <div class="text-sm">
                    <div><i class="far fa-envelope me-1 text-muted"></i>${p.email || ''}</div>
                    <div class="text-muted small">
                        <i class="fas fa-phone-alt me-1"></i>${p.telephone || ''}
                    </div>
                </div>
            </td>
            <td>
                <div class="fw-bold text-sm">${p.poste || ''}</div>
                <div class="badge bg-light text-primary border-0">${p.departement || 'Général'}</div>
            </td>
            <td class="text-end pe-4" onclick="event.stopPropagation()">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary border-0 rounded-circle me-1"
                        title="Modifier"
                        onclick="ouvrirModalEditEmploye(event, ${p.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-warning border-0 rounded-circle me-1"
                        title="Réinitialiser le mot de passe"
                        onclick="resetPassword(event, ${p.id}, '${p.prenom} ${p.nom}', '${p.email}')">
                        <i class="fas fa-key"></i>
                    </button>
                    <button class="btn btn-outline-danger border-0 rounded-circle"
                        title="Supprimer"
                        onclick="supprimerEmploye(event, ${p.id}, '${p.prenom} ${p.nom}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>`;
    });

    const info      = document.getElementById("tableInfo");
    const startItem = start + 1;
    const endItem   = Math.min(end, employees.length);
    info.innerText  = `Affichage ${startItem} à ${endItem} sur ${employees.length} employés`;
}

function renderPagination() {
    const totalPages = Math.ceil(employees.length / rowsPerPage);
    const pagination = document.getElementById("pagination");
    pagination.innerHTML = "";
    for (let i = 1; i <= totalPages; i++) {
        pagination.innerHTML += `
        <li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#"
                onclick="changePage(${i}); return false;">${i}</a>
        </li>`;
    }
}

function changePage(page) {
    currentPage = page;
    renderTable();
    renderPagination();
}

async function resetPassword(event, id, name, email) {
    event.stopPropagation();
    const result = await Swal.fire({
        title: 'Réinitialiser le mot de passe ?',
        html: `Un nouveau mot de passe temporaire sera généré et envoyé à<br><strong>${email}</strong>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ffc107',
        confirmButtonText: 'Oui, réinitialiser',
        cancelButtonText: 'Annuler'
    });
    if (!result.isConfirmed) return;

    try {
        const res  = await fetch(`/employe/reset-password/${id}`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
            Swal.fire('Envoyé !', `Nouveau mot de passe envoyé à ${email}`, 'success');
        } else {
            Swal.fire('Erreur', data.message || 'Échec de la réinitialisation', 'error');
        }
    } catch (e) {
        Swal.fire('Erreur', 'Problème réseau', 'error');
    }
}

document.addEventListener("DOMContentLoaded", loadEmployees);