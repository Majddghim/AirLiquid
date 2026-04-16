////////////////////////////////////////////////////////////////////////////////////////////////
// STATE

let selectedBrandId = null;
let selectedDeptId  = null;

////////////////////////////////////////////////////////////////////////////////////////////////
// TABS

function switchTab(tab) {
    ['brands', 'depts', 'parts', 'garages'].forEach(t => {
        document.getElementById(`panel-${t}`).style.display = t === tab ? 'block' : 'none';
        document.getElementById(`tab-${t}`).classList.toggle('active', t === tab);
    });
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
    const res    = await fetch('/settings/add-brand', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name }) });
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
    const res    = await fetch(`/settings/update-brand/${id}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name }) });
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
        showCancelButton: true, confirmButtonText: 'Oui, supprimer', cancelButtonText: 'Annuler',
        confirmButtonColor: '#e74a3b', cancelButtonColor: '#858796'
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
    const res    = await fetch('/settings/add-model', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name, brand_id: selectedBrandId }) });
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
    const res    = await fetch(`/settings/update-model/${id}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name }) });
    const result = await res.json();
    if (result.status === 'success') {
        bootstrap.Modal.getInstance(document.getElementById('editModelModal')).hide();
        loadModels(selectedBrandId);
    } else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

async function deleteModel(event, id, name) {
    event.stopPropagation();
    const confirm = await Swal.fire({
        icon: 'warning', title: 'Supprimer ce modèle ?', text: name,
        showCancelButton: true, confirmButtonText: 'Oui, supprimer', cancelButtonText: 'Annuler',
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
    const res    = await fetch('/settings/add-dept', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name }) });
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
    const res    = await fetch(`/settings/update-dept/${id}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name }) });
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
        showCancelButton: true, confirmButtonText: 'Oui, supprimer', cancelButtonText: 'Annuler',
        confirmButtonColor: '#e74a3b', cancelButtonColor: '#858796'
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
    const res    = await fetch('/settings/add-poste', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name, departement_id: selectedDeptId }) });
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
    const res    = await fetch(`/settings/update-poste/${id}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name }) });
    const result = await res.json();
    if (result.status === 'success') {
        bootstrap.Modal.getInstance(document.getElementById('editPosteModal')).hide();
        loadPostes(selectedDeptId);
    } else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

async function deletePoste(event, id, name) {
    event.stopPropagation();
    const confirm = await Swal.fire({
        icon: 'warning', title: 'Supprimer ce poste ?', text: name,
        showCancelButton: true, confirmButtonText: 'Oui, supprimer', cancelButtonText: 'Annuler',
        confirmButtonColor: '#e74a3b', cancelButtonColor: '#858796'
    });
    if (!confirm.isConfirmed) return;
    const res    = await fetch(`/settings/delete-poste/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'success') loadPostes(selectedDeptId);
    else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

////////////////////////////////////////////////////////////////////////////////////////////////
// CAR PARTS

async function loadParts() {
    const res  = await fetch('/settings/get-parts');
    const data = await res.json();
    const tbody = document.getElementById('partsTableBody');
    tbody.innerHTML = '';
    if (data.status !== 'success' || data.data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Aucune pièce</td></tr>`;
        return;
    }
    data.data.forEach(p => {
        tbody.innerHTML += `
            <tr>
                <td class="ps-4 fw-bold">${escapeHtml(p.name)}</td>
                <td><span class="badge bg-light text-dark border">${escapeHtml(p.category || '—')}</span></td>
                <td>${p.alert_km_interval ? p.alert_km_interval + ' km' : '—'}</td>
                <td>${p.alert_month_interval ? p.alert_month_interval + ' mois' : '—'}</td>
                <td class="text-muted small">${escapeHtml(p.notes || '—')}</td>
                <td class="text-end pe-4">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary border-0 rounded-circle me-1"
                            onclick="ouvrirEditPart(${p.id}, '${escapeHtml(p.name)}', '${escapeHtml(p.category || '')}', '${p.alert_km_interval || ''}', '${p.alert_month_interval || ''}', '${escapeHtml(p.notes || '')}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger border-0 rounded-circle"
                            onclick="deletePart(${p.id}, '${escapeHtml(p.name)}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    });
}

function ouvrirAddPart() {
    document.getElementById('partId').value          = '';
    document.getElementById('partModalTitle').innerText = 'Ajouter une Pièce';
    document.getElementById('partName').value        = '';
    document.getElementById('partCategory').value    = '';
    document.getElementById('partAlertKm').value     = '';
    document.getElementById('partAlertMonth').value  = '';
    document.getElementById('partNotes').value       = '';
    new bootstrap.Modal(document.getElementById('partModal')).show();
}

function ouvrirEditPart(id, name, category, alertKm, alertMonth, notes) {
    document.getElementById('partId').value          = id;
    document.getElementById('partModalTitle').innerText = 'Modifier la Pièce';
    document.getElementById('partName').value        = name;
    document.getElementById('partCategory').value    = category;
    document.getElementById('partAlertKm').value     = alertKm || '';
    document.getElementById('partAlertMonth').value  = alertMonth || '';
    document.getElementById('partNotes').value       = notes;
    document.getElementById('partAlertKm').value    = alertKm    !== 'null' ? alertKm    : '';
    document.getElementById('partAlertMonth').value = alertMonth !== 'null' ? alertMonth : '';
    new bootstrap.Modal(document.getElementById('partModal')).show();
}

async function confirmerSavePart() {
    const id   = document.getElementById('partId').value;
    const name = document.getElementById('partName').value.trim();
    if (!name) {
        Swal.fire({ icon: 'warning', title: 'Champ manquant', text: 'Le nom est obligatoire.' });
        return;
    }
    const payload = {
        name,
        category:             document.getElementById('partCategory').value.trim() || null,
        alert_km_interval:    document.getElementById('partAlertKm').value    || null,
        alert_month_interval: document.getElementById('partAlertMonth').value || null,
        notes:                document.getElementById('partNotes').value.trim() || null
    };
    const url    = id ? `/settings/update-part/${id}` : '/settings/add-part';
    const method = id ? 'PUT' : 'POST';
    const res    = await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
    const result = await res.json();
    if (result.status === 'success') {
        bootstrap.Modal.getInstance(document.getElementById('partModal')).hide();
        loadParts();
    } else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

async function deletePart(id, name) {
    const confirm = await Swal.fire({
        icon: 'warning', title: 'Supprimer cette pièce ?', text: name,
        showCancelButton: true, confirmButtonText: 'Oui, supprimer', cancelButtonText: 'Annuler',
        confirmButtonColor: '#e74a3b', cancelButtonColor: '#858796'
    });
    if (!confirm.isConfirmed) return;
    const res    = await fetch(`/settings/delete-part/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'success') loadParts();
    else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

////////////////////////////////////////////////////////////////////////////////////////////////
// GARAGES

async function loadGarages() {
    const res  = await fetch('/settings/get-garages');
    const data = await res.json();
    const tbody = document.getElementById('garagesTableBody');
    tbody.innerHTML = '';
    if (data.status !== 'success' || data.data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Aucun garage</td></tr>`;
        return;
    }
    data.data.forEach(g => {
        const typeBadge = g.type === 'dealership'
            ? '<span class="badge bg-primary">Concessionnaire</span>'
            : '<span class="badge bg-secondary">Indépendant</span>';
        const statusBadge = g.status === 'active'
            ? '<span class="badge bg-success">Actif</span>'
            : '<span class="badge bg-danger">Inactif</span>';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="ps-4 fw-bold">${escapeHtml(g.name)}</td>
            <td>${typeBadge}</td>
            <td>${escapeHtml(g.brand || '—')}</td>
            <td>${escapeHtml(g.phone || '—')}</td>
            <td>${escapeHtml(g.contact_person || '—')}</td>
            <td>${statusBadge}</td>
            <td class="text-end pe-4">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary border-0 rounded-circle me-1 btn-edit-garage"
                        title="Modifier">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-danger border-0 rounded-circle btn-delete-garage"
                        title="Supprimer">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>`;

        // store data safely on the buttons
        const editBtn   = tr.querySelector('.btn-edit-garage');
        const deleteBtn = tr.querySelector('.btn-delete-garage');

        editBtn.dataset.id             = g.id;
        editBtn.dataset.name           = g.name           || '';
        editBtn.dataset.type           = g.type           || 'independent';
        editBtn.dataset.brand          = g.brand          || '';
        editBtn.dataset.phone          = g.phone          || '';
        editBtn.dataset.contact        = g.contact_person || '';
        editBtn.dataset.address        = g.address        || '';
        editBtn.dataset.status         = g.status         || 'active';

        deleteBtn.dataset.id   = g.id;
        deleteBtn.dataset.name = g.name || '';

        editBtn.addEventListener('click', function () {
            ouvrirEditGarage(
                this.dataset.id,
                this.dataset.name,
                this.dataset.type,
                this.dataset.brand,
                this.dataset.phone,
                this.dataset.contact,
                this.dataset.address,
                this.dataset.status
            );
        });

        deleteBtn.addEventListener('click', function () {
            deleteGarage(this.dataset.id, this.dataset.name);
        });

        tbody.appendChild(tr);
    });
}

function ouvrirAddGarage() {
    document.getElementById('garageId').value            = '';
    document.getElementById('garageModalTitle').innerText = 'Ajouter un Garage';
    document.getElementById('garageName').value          = '';
    document.getElementById('garageType').value          = 'independent';
    document.getElementById('garageBrand').value         = '';
    document.getElementById('garagePhone').value         = '';
    document.getElementById('garageContact').value       = '';
    document.getElementById('garageAddress').value       = '';
    document.getElementById('garageStatus').value = 'active';
    new bootstrap.Modal(document.getElementById('garageModal')).show();
}

function ouvrirEditGarage(id, name, type, brand, phone, contact, address, status) {
    document.getElementById('garageId').value             = id;
    document.getElementById('garageModalTitle').innerText = 'Modifier le Garage';
    document.getElementById('garageName').value           = name;
    document.getElementById('garageType').value           = type;
    document.getElementById('garageBrand').value          = brand;
    document.getElementById('garagePhone').value          = phone;
    document.getElementById('garageContact').value        = contact;
    document.getElementById('garageAddress').value        = address;
    document.getElementById('garageStatus').value         = status || 'active';
    new bootstrap.Modal(document.getElementById('garageModal')).show();
}

async function confirmerSaveGarage() {
    const id   = document.getElementById('garageId').value;
    const name = document.getElementById('garageName').value.trim();
    if (!name) {
        Swal.fire({ icon: 'warning', title: 'Champ manquant', text: 'Le nom est obligatoire.' });
        return;
    }
    const payload = {
        name,
        type:           document.getElementById('garageType').value,
        brand:          document.getElementById('garageBrand').value.trim()   || null,
        phone:          document.getElementById('garagePhone').value.trim()   || null,
        contact_person: document.getElementById('garageContact').value.trim() || null,
        status: document.getElementById('garageStatus').value,
        address:        document.getElementById('garageAddress').value.trim() || null
    };
    const url    = id ? `/settings/update-garage/${id}` : '/settings/add-garage';
    const method = id ? 'PUT' : 'POST';
    const res    = await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
    const result = await res.json();
    if (result.status === 'success') {
        bootstrap.Modal.getInstance(document.getElementById('garageModal')).hide();
        loadGarages();
    } else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

async function deleteGarage(id, name) {
    const confirm = await Swal.fire({
        icon: 'warning', title: 'Désactiver ce garage ?',
        html: `<span class="text-muted">${name}</span><br><small class="text-muted">Le garage sera marqué comme inactif.</small>`,
        showCancelButton: true, confirmButtonText: 'Oui, désactiver', cancelButtonText: 'Annuler',
        confirmButtonColor: '#e74a3b', cancelButtonColor: '#858796'
    });
    if (!confirm.isConfirmed) return;
    const res    = await fetch(`/settings/delete-garage/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'success') loadGarages();
    else Swal.fire({ icon: 'error', title: 'Erreur', text: result.message });
}

////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

document.addEventListener("DOMContentLoaded", () => {
    loadBrands();
    loadDepts();
    loadParts();
    loadGarages();
});