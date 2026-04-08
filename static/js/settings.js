////////////////////////////////////////////////////////////////////////////////////////////////
// STATE

let selectedBrandId = null;
let selectedDeptId  = null;

////////////////////////////////////////////////////////////////////////////////////////////////
// TABS

function switchTab(tab) {
    document.getElementById('panel-brands').style.display = tab === 'brands' ? 'block' : 'none';
    document.getElementById('panel-depts').style.display  = tab === 'depts'  ? 'block' : 'none';
    document.getElementById('tab-brands').classList.toggle('active', tab === 'brands');
    document.getElementById('tab-depts').classList.toggle('active',  tab === 'depts');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// HELPERS

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

////////////////////////////////////////////////////////////////////////////////////////////////
// BRANDS

async function loadBrands() {
    const res  = await fetch('/car/get-brands');
    const data = await res.json();
    const list = document.getElementById('brandsList');
    list.innerHTML = '';
    if (data.status !== 'success' || data.data.length === 0) {
        list.innerHTML = `<li class="list-group-item text-muted text-center py-4">Aucune marque</li>`;
        return;
    }
    data.data.forEach(b => {
        const li = document.createElement('li');
        li.className = `list-group-item d-flex justify-content-between align-items-center py-2 px-3 ${selectedBrandId === b.id ? 'active' : ''}`;
        li.style.cursor = 'pointer';
        li.innerHTML = `
            <span onclick="selectBrand(${b.id}, '${escapeHtml(b.name)}')" style="flex:1;">
                <i class="fas fa-car me-2 text-primary"></i>${escapeHtml(b.name)}
            </span>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary border-0 rounded-circle me-1"
                    onclick="ouvrirEditBrand(event, ${b.id}, '${escapeHtml(b.name)}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-outline-danger border-0 rounded-circle"
                    onclick="deleteBrand(event, ${b.id}, '${escapeHtml(b.name)}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>`;
        list.appendChild(li);
    });
}

function selectBrand(brandId, brandName) {
    selectedBrandId = brandId;
    document.getElementById('selectedBrandName').innerText = brandName;
    document.getElementById('addModelBtn').style.display = 'inline-block';
    loadModels(brandId);
    loadBrands();
}

async function loadModels(brandId) {
    const res  = await fetch(`/car/get-models/${brandId}`);
    const data = await res.json();
    const list = document.getElementById('modelsList');
    const placeholder = document.getElementById('modelsPlaceholder');
    list.innerHTML = '';
    list.style.display = 'block';
    placeholder.style.display = 'none';
    if (data.status !== 'success' || data.data.length === 0) {
        list.innerHTML = `<li class="list-group-item text-muted text-center py-4">Aucun modèle</li>`;
        return;
    }
    data.data.forEach(m => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center py-2 px-3';
        li.innerHTML = `
            <span><i class="fas fa-car-side me-2 text-muted"></i>${escapeHtml(m.name)}</span>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary border-0 rounded-circle me-1"
                    onclick="ouvrirEditModel(event, ${m.id}, '${escapeHtml(m.name)}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-outline-danger border-0 rounded-circle"
                    onclick="deleteModel(event, ${m.id}, '${escapeHtml(m.name)}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>`;
        list.appendChild(li);
    });
}

function showAddBrand() { document.getElementById('addBrandForm').style.display = 'block'; document.getElementById('newBrandName').focus(); }
function hideAddBrand() { document.getElementById('addBrandForm').style.display = 'none';  document.getElementById('newBrandName').value = ''; }

async function addBrand() {
    const name = document.getElementById('newBrandName').value.trim();
    if (!name) return;
    const res    = await fetch('/settings/add-brand', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name })
    });
    const result = await res.json();
    if (result.status === 'success') { hideAddBrand(); loadBrands(); }
    else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

function ouvrirEditBrand(event, id, name) {
    event.stopPropagation();
    document.getElementById('editBrandId').value   = id;
    document.getElementById('editBrandName').value = name;
    new bootstrap.Modal(document.getElementById('editBrandModal')).show();
}

async function confirmerEditBrand() {
    const id   = document.getElementById('editBrandId').value;
    const name = document.getElementById('editBrandName').value.trim();
    if (!name) return;
    const res    = await fetch(`/settings/update-brand/${id}`, {
        method: 'PUT', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name })
    });
    const result = await res.json();
    if (result.status === 'success') {
        bootstrap.Modal.getInstance(document.getElementById('editBrandModal')).hide();
        if (selectedBrandId === parseInt(id)) document.getElementById('selectedBrandName').innerText = name;
        loadBrands();
    } else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

async function deleteBrand(event, id, name) {
    event.stopPropagation();
    const confirm = await Swal.fire({
        icon: 'warning', title: 'Supprimer cette marque ?',
        html: `<span class="text-muted">${name}</span><br><small class="text-muted">Tous les modèles associés seront également supprimés.</small>`,
        showCancelButton: true, confirmButtonText: 'Oui, supprimer',
        cancelButtonText: 'Annuler', confirmButtonColor: '#e74a3b', cancelButtonColor: '#858796'
    });
    if (!confirm.isConfirmed) return;
    const res    = await fetch(`/settings/delete-brand/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'success') {
        if (selectedBrandId === id) {
            selectedBrandId = null;
            document.getElementById('selectedBrandName').innerText = 'sélectionner une marque';
            document.getElementById('modelsList').style.display = 'none';
            document.getElementById('modelsPlaceholder').style.display = 'block';
            document.getElementById('addModelBtn').style.display = 'none';
        }
        loadBrands();
    } else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

function showAddModel() { document.getElementById('addModelForm').style.display = 'block'; document.getElementById('newModelName').focus(); }
function hideAddModel() { document.getElementById('addModelForm').style.display = 'none';  document.getElementById('newModelName').value = ''; }

async function addModel() {
    const name = document.getElementById('newModelName').value.trim();
    if (!name || !selectedBrandId) return;
    const res    = await fetch('/settings/add-model', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name, brand_id: selectedBrandId })
    });
    const result = await res.json();
    if (result.status === 'success') { hideAddModel(); loadModels(selectedBrandId); }
    else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

function ouvrirEditModel(event, id, name) {
    event.stopPropagation();
    document.getElementById('editModelId').value   = id;
    document.getElementById('editModelName').value = name;
    new bootstrap.Modal(document.getElementById('editModelModal')).show();
}

async function confirmerEditModel() {
    const id   = document.getElementById('editModelId').value;
    const name = document.getElementById('editModelName').value.trim();
    if (!name) return;
    const res    = await fetch(`/settings/update-model/${id}`, {
        method: 'PUT', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name })
    });
    const result = await res.json();
    if (result.status === 'success') {
        bootstrap.Modal.getInstance(document.getElementById('editModelModal')).hide();
        loadModels(selectedBrandId);
    } else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

async function deleteModel(event, id, name) {
    event.stopPropagation();
    const confirm = await Swal.fire({
        icon: 'warning', title: 'Supprimer ce modèle ?',
        text: name, showCancelButton: true,
        confirmButtonText: 'Oui, supprimer', cancelButtonText: 'Annuler',
        confirmButtonColor: '#e74a3b', cancelButtonColor: '#858796'
    });
    if (!confirm.isConfirmed) return;
    const res    = await fetch(`/settings/delete-model/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'success') loadModels(selectedBrandId);
    else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

////////////////////////////////////////////////////////////////////////////////////////////////
// DÉPARTEMENTS

async function loadDepts() {
    const res  = await fetch('/employe/get-departements');
    const data = await res.json();
    const list = document.getElementById('deptsList');
    list.innerHTML = '';
    if (data.status !== 'success' || data.data.length === 0) {
        list.innerHTML = `<li class="list-group-item text-muted text-center py-4">Aucun département</li>`;
        return;
    }
    data.data.forEach(d => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center py-2 px-3';
        li.style.cursor = 'pointer';
        li.innerHTML = `
            <span onclick="selectDept(${d.id}, '${escapeHtml(d.name)}')" style="flex:1;">
                <i class="fas fa-building me-2 text-primary"></i>${escapeHtml(d.name)}
            </span>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary border-0 rounded-circle me-1"
                    onclick="ouvrirEditDept(event, ${d.id}, '${escapeHtml(d.name)}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-outline-danger border-0 rounded-circle"
                    onclick="deleteDept(event, ${d.id}, '${escapeHtml(d.name)}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>`;
        list.appendChild(li);
    });
}

function selectDept(deptId, deptName) {
    selectedDeptId = deptId;
    document.getElementById('selectedDeptName').innerText = deptName;
    document.getElementById('addPosteBtn').style.display = 'inline-block';
    loadPostes(deptId);
}

async function loadPostes(deptId) {
    const res  = await fetch(`/employe/get-postes/${deptId}`);
    const data = await res.json();
    const list = document.getElementById('postesList');
    const placeholder = document.getElementById('postesPlaceholder');
    list.innerHTML = '';
    list.style.display = 'block';
    placeholder.style.display = 'none';
    if (data.status !== 'success' || data.data.length === 0) {
        list.innerHTML = `<li class="list-group-item text-muted text-center py-4">Aucun poste</li>`;
        return;
    }
    data.data.forEach(p => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center py-2 px-3';
        li.innerHTML = `
            <span><i class="fas fa-user-tie me-2 text-muted"></i>${escapeHtml(p.name)}</span>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary border-0 rounded-circle me-1"
                    onclick="ouvrirEditPoste(event, ${p.id}, '${escapeHtml(p.name)}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-outline-danger border-0 rounded-circle"
                    onclick="deletePoste(event, ${p.id}, '${escapeHtml(p.name)}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>`;
        list.appendChild(li);
    });
}

function showAddDept() { document.getElementById('addDeptForm').style.display = 'block'; document.getElementById('newDeptName').focus(); }
function hideAddDept() { document.getElementById('addDeptForm').style.display = 'none';  document.getElementById('newDeptName').value = ''; }

async function addDept() {
    const name = document.getElementById('newDeptName').value.trim();
    if (!name) return;
    const res    = await fetch('/settings/add-dept', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name })
    });
    const result = await res.json();
    if (result.status === 'success') { hideAddDept(); loadDepts(); }
    else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

function ouvrirEditDept(event, id, name) {
    event.stopPropagation();
    document.getElementById('editDeptId').value   = id;
    document.getElementById('editDeptName').value = name;
    new bootstrap.Modal(document.getElementById('editDeptModal')).show();
}

async function confirmerEditDept() {
    const id   = document.getElementById('editDeptId').value;
    const name = document.getElementById('editDeptName').value.trim();
    if (!name) return;
    const res    = await fetch(`/settings/update-dept/${id}`, {
        method: 'PUT', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name })
    });
    const result = await res.json();
    if (result.status === 'success') {
        bootstrap.Modal.getInstance(document.getElementById('editDeptModal')).hide();
        if (selectedDeptId === parseInt(id)) document.getElementById('selectedDeptName').innerText = name;
        loadDepts();
    } else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

async function deleteDept(event, id, name) {
    event.stopPropagation();
    const confirm = await Swal.fire({
        icon: 'warning', title: 'Supprimer ce département ?',
        html: `<span class="text-muted">${name}</span><br><small class="text-muted">Tous les postes associés seront également supprimés.</small>`,
        showCancelButton: true, confirmButtonText: 'Oui, supprimer',
        cancelButtonText: 'Annuler', confirmButtonColor: '#e74a3b', cancelButtonColor: '#858796'
    });
    if (!confirm.isConfirmed) return;
    const res    = await fetch(`/settings/delete-dept/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'success') {
        if (selectedDeptId === id) {
            selectedDeptId = null;
            document.getElementById('selectedDeptName').innerText = 'sélectionner un département';
            document.getElementById('postesList').style.display = 'none';
            document.getElementById('postesPlaceholder').style.display = 'block';
            document.getElementById('addPosteBtn').style.display = 'none';
        }
        loadDepts();
    } else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

function showAddPoste() { document.getElementById('addPosteForm').style.display = 'block'; document.getElementById('newPosteName').focus(); }
function hideAddPoste() { document.getElementById('addPosteForm').style.display = 'none';  document.getElementById('newPosteName').value = ''; }

async function addPoste() {
    const name = document.getElementById('newPosteName').value.trim();
    if (!name || !selectedDeptId) return;
    const res    = await fetch('/settings/add-poste', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name, departement_id: selectedDeptId })
    });
    const result = await res.json();
    if (result.status === 'success') { hideAddPoste(); loadPostes(selectedDeptId); }
    else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

function ouvrirEditPoste(event, id, name) {
    event.stopPropagation();
    document.getElementById('editPosteId').value   = id;
    document.getElementById('editPosteName').value = name;
    new bootstrap.Modal(document.getElementById('editPosteModal')).show();
}

async function confirmerEditPoste() {
    const id   = document.getElementById('editPosteId').value;
    const name = document.getElementById('editPosteName').value.trim();
    if (!name) return;
    const res    = await fetch(`/settings/update-poste/${id}`, {
        method: 'PUT', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name })
    });
    const result = await res.json();
    if (result.status === 'success') {
        bootstrap.Modal.getInstance(document.getElementById('editPosteModal')).hide();
        loadPostes(selectedDeptId);
    } else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

async function deletePoste(event, id, name) {
    event.stopPropagation();
    const confirm = await Swal.fire({
        icon: 'warning', title: 'Supprimer ce poste ?',
        text: name, showCancelButton: true,
        confirmButtonText: 'Oui, supprimer', cancelButtonText: 'Annuler',
        confirmButtonColor: '#e74a3b', cancelButtonColor: '#858796'
    });
    if (!confirm.isConfirmed) return;
    const res    = await fetch(`/settings/delete-poste/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'success') loadPostes(selectedDeptId);
    else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

document.addEventListener("DOMContentLoaded", () => {
    loadBrands();
    loadDepts();
});