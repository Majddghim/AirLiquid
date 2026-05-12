////////////////////////////////////////////////////////////////////////////////////////////////
// INIT

document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboard();
});

////////////////////////////////////////////////////////////////////////////////////////////////
// LOAD DATA

async function loadDashboard() {
    try {
        const res  = await fetch('/employe/dashboard-data');
        const data = await res.json();

        if (data.status !== 'success') {
            window.location.href = '/employe/login';
            return;
        }

        const d = data.data;
        renderHeader(d.employe);
        renderCar(d.cars);
        renderSinistres(d.sinistres);
        renderProfil(d.employe);

    } catch (e) {
        console.error('loadDashboard error:', e);
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER HEADER

function renderHeader(emp) {
    const initials = `${(emp.prenom||'E')[0]}${(emp.nom||'P')[0]}`.toUpperCase();
    document.getElementById('header_avatar').innerText = initials;
    document.getElementById('header_name').innerText   = `${emp.prenom} ${emp.nom}`;
    document.getElementById('header_post').innerText   = `${emp.poste || ''} — ${emp.departement || ''}`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER CAR

function renderCar(cars) {
    const el = document.getElementById('car_content');

    if (!cars || cars.length === 0) {
        el.innerHTML = `
            <div class="dash-card mt-3">
                <div class="dash-card-body empty-state">
                    <i class="fas fa-car-slash d-block"></i>
                    <p>Aucun véhicule affecté</p>
                    <small>Contactez votre responsable RH</small>
                </div>
            </div>`;
        return;
    }

    el.innerHTML = cars.map(c => {
        const isReplacement = c.notes && c.notes.includes('Remplacement');
        const statusColor   = c.car_status === 'active'      ? '#198754' :
                              c.car_status === 'maintenance'  ? '#ffc107' : '#6c757d';
        const statusLabel   = c.car_status === 'active'      ? 'Opérationnel' :
                              c.car_status === 'maintenance'  ? 'En maintenance' : 'Inactif';

        return `
        <div class="dash-card mt-3">
            <div class="dash-card-header">
                <div class="d-flex align-items-center">
                    <div class="card-icon" style="background:#ebf4ff;">
                        <i class="fas fa-car text-primary"></i>
                    </div>
                    <div>
                        <div class="fw-bold text-dark" style="font-size:14px;">
                            ${escapeHtml(c.brand || '')} ${escapeHtml(c.model || '')}
                        </div>
                        <div class="font-monospace text-muted" style="font-size:12px;">
                            ${escapeHtml(c.plate_number || '')}
                        </div>
                    </div>
                </div>
                <span class="status-pill"
                    style="background:${statusColor}20;color:${statusColor};">
                    ${statusLabel}
                </span>
            </div>
            <div class="dash-card-body">
    ${isReplacement ? `
    <div class="replacement-badge mb-3">
        <i class="fas fa-exchange-alt"></i>
        Véhicule de remplacement temporaire
    </div>` : ''}
    <div class="info-row">
        <span class="info-label">Modèle</span>
        <span class="info-value">${escapeHtml(c.model || '—')} (${c.year || '—'})</span>
    </div>
    <div class="info-row">
        <span class="info-label">Marque</span>
        <span class="info-value">${escapeHtml(c.brand || '—')}</span>
    </div>
    <div class="info-row">
        <span class="info-label">Affecté depuis</span>
        <span class="info-value">${formatDate(c.start_date)}</span>
    </div>
    ${c.current_km ? `
    <div class="km-box">
        <div class="info-label">Kilométrage actuel</div>
        <div class="km-number">${Number(c.current_km).toLocaleString()}</div>
        <div class="km-label">km — relevé le ${formatDate(c.km_date)}</div>
    </div>` : ''}
    <div class="d-flex gap-2 mt-3">
        <button class="auth-btn" style="flex:1;padding:10px;font-size:13px;"
            onclick="ouvrirOdometer(${c.car_id})">
            <i class="fas fa-tachometer-alt me-1"></i>MAJ KM
        </button>
        <button class="auth-btn" style="flex:1;padding:10px;font-size:13px;background:linear-gradient(135deg,#dc3545,#c82333);"
            onclick="ouvrirSignalement(${c.car_id})">
            <i class="fas fa-exclamation-triangle me-1"></i>Problème
        </button>
    </div>
</div>
        </div>`;
    }).join('');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER SINISTRES

function renderSinistres(sinistres) {
    const el = document.getElementById('sinistres_content');

    if (!sinistres || sinistres.length === 0) {
        el.innerHTML = `
            <div class="dash-card mt-3">
                <div class="dash-card-body empty-state">
                    <i class="fas fa-shield-check d-block" style="color:#198754;opacity:0.4;"></i>
                    <p>Aucun sinistre enregistré</p>
                    <small>Votre historique est vide</small>
                </div>
            </div>`;
        return;
    }

    el.innerHTML = `<div class="mt-3">` + sinistres.map(s => {
        const statusLabel = s.status === 'ouvert'   ? 'Ouvert'   :
                            s.status === 'en_cours' ? 'En cours' : 'Clôturé';
        const statusClass = s.status === 'ouvert'   ? 'bg-danger'              :
                            s.status === 'en_cours' ? 'bg-warning text-dark'   : 'bg-success';
        return `
        <div class="sinistre-card ${s.status}">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                    <div class="fw-bold" style="font-size:13px;">
                        ${escapeHtml(s.plate_number || '')} — ${escapeHtml(s.model || '')}
                    </div>
                    <div class="text-muted" style="font-size:11px;">
                        ${formatDate(s.date_sinistre)} · ${escapeHtml(s.type)}
                    </div>
                </div>
                <span class="badge ${statusClass}" style="font-size:10px;">${statusLabel}</span>
            </div>
            ${s.description ? `
            <div class="text-muted" style="font-size:12px;line-height:1.4;">
                ${escapeHtml(s.description)}
            </div>` : ''}
            ${s.montant_reparation ? `
            <div class="mt-2 fw-bold" style="font-size:13px;color:#0d6efd;">
                ${Number(s.montant_reparation).toLocaleString()} DT
            </div>` : ''}
        </div>`;
    }).join('') + `</div>`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// RENDER PROFIL

function renderProfil(emp) {
    document.getElementById('profil_content').innerHTML = `
        <div class="dash-card mt-3">
            <div class="dash-card-body">
                <div class="text-center mb-4 pt-2">
                    <div class="avatar-circle">
                        ${(emp.prenom||'E')[0]}${(emp.nom||'P')[0]}
                    </div>
                    <div class="fw-bold text-dark" style="font-size:16px;">
                        ${escapeHtml(emp.prenom)} ${escapeHtml(emp.nom)}
                    </div>
                    <div class="text-muted" style="font-size:12px;">
                        ${escapeHtml(emp.poste || '')}
                    </div>
                </div>
                <div class="info-row">
                    <span class="info-label">Email</span>
                    <span class="info-value" style="font-size:12px;">${escapeHtml(emp.email || '—')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Téléphone</span>
                    <span class="info-value">${escapeHtml(emp.telephone || '—')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Département</span>
                    <span class="info-value">${escapeHtml(emp.departement || '—')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Poste</span>
                    <span class="info-value">${escapeHtml(emp.poste || '—')}</span>
                </div>
            </div>
        </div>`;
}

////////////////////////////////////////////////////////////////////////////////////////////////
// NAVIGATION

function switchSection(section) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`section_${section}`).classList.add('active');
    document.getElementById(`nav_${section}`).classList.add('active');
}

////////////////////////////////////////////////////////////////////////////////////////////////
// HELPERS

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return d.toLocaleDateString('fr-TN', { day:'2-digit', month:'2-digit', year:'numeric' });
}
////////////////////////////////////////////////////////////////////////////////////////////////
// ODOMETER SCAN

function ouvrirOdometer(carId) {
    document.getElementById('odometer_car_id').value  = carId;
    document.getElementById('odometer_km').value      = '';
    document.getElementById('odometer_file').value    = '';
    document.getElementById('odometer_scan_status').style.display = 'none';
    document.getElementById('odometer_scan_btn').disabled  = false;
    document.getElementById('odometer_scan_btn').innerHTML = '<i class="fas fa-search me-1"></i>Lire le KM';
    new bootstrap.Modal(document.getElementById('odometerModal')).show();
}

async function scanOdometer() {
    const fileInput = document.getElementById('odometer_file');
    const statusEl  = document.getElementById('odometer_scan_status');
    const scanBtn   = document.getElementById('odometer_scan_btn');
    const carId     = document.getElementById('odometer_car_id').value;

    if (!fileInput.files.length) {
        alert('Veuillez sélectionner une photo du compteur.');
        return;
    }

    scanBtn.disabled  = true;
    scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Analyse (~30s)...';
    statusEl.style.display = 'block';
    statusEl.innerHTML = '<div class="text-muted small"><i class="fas fa-spinner fa-spin me-1"></i>Claude analyse l\'image... cela peut prendre 30 secondes.</div>';

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const res    = await fetch(`/employe/scan-odometer/${carId}`, { method: 'POST', body: formData });
        const result = await res.json();

        if (result.status === 'success' && result.km) {
            document.getElementById('odometer_km').value = result.km;
            statusEl.innerHTML = `<div class="text-success small"><i class="fas fa-check me-1"></i>KM détecté: <strong>${Number(result.km).toLocaleString()} km</strong> — vérifiez avant d'enregistrer.</div>`;
        } else {
            statusEl.innerHTML = `<div class="text-warning small"><i class="fas fa-exclamation me-1"></i>Impossible de lire automatiquement. Saisissez le KM manuellement.</div>`;
        }
    } catch (e) {
        statusEl.innerHTML = '<div class="text-danger small">Erreur réseau.</div>';
    }

    scanBtn.disabled  = false;
    scanBtn.innerHTML = '<i class="fas fa-search me-1"></i>Lire le KM';
}

async function confirmerUpdateKm() {
    const carId  = document.getElementById('odometer_car_id').value;
    const km     = document.getElementById('odometer_km').value;
    const saveBtn = document.getElementById('odometer_save_btn');

    if (!km || parseInt(km) <= 0) {
        alert('Veuillez saisir un kilométrage valide.');
        return;
    }

    saveBtn.disabled  = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enregistrement...';

    try {
        const res    = await fetch(`/employe/update-km/${carId}`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ km: parseInt(km) })
        });
        const result = await res.json();

        if (result.status === 'success') {
    bootstrap.Modal.getInstance(document.getElementById('odometerModal')).hide();
    alert('✅ Kilométrage mis à jour avec succès !');
    setTimeout(() => window.location.reload(), 500);
        } else {
            alert('Erreur: ' + result.message);
            saveBtn.disabled  = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Enregistrer';
        }
    } catch (e) {
        alert('Erreur réseau.');
        saveBtn.disabled  = false;
        saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Enregistrer';
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////
// PROBLEM REPORTING

function ouvrirSignalement(carId) {
    document.getElementById('problem_car_id').value      = carId;
    document.getElementById('problem_file_path').value   = '';
    document.getElementById('problem_file').value        = '';
    document.getElementById('problem_description').value = '';
    document.getElementById('problem_analysis').style.display = 'none';
    document.getElementById('problem_save_btn').disabled  = false;
    document.getElementById('problem_save_btn').innerHTML = '<i class="fas fa-paper-plane me-2"></i>Envoyer le signalement';
    new bootstrap.Modal(document.getElementById('problemModal')).show();
}

async function analyzeProblem() {
    const fileInput  = document.getElementById('problem_file');
    const analysisEl = document.getElementById('problem_analysis');
    const carId      = document.getElementById('problem_car_id').value;

    if (!fileInput.files.length) return;

    analysisEl.style.display = 'block';
    analysisEl.innerHTML = '<div class="text-muted small"><i class="fas fa-spinner fa-spin me-1"></i>Analyse de l\'image...</div>';

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const res    = await fetch('/employe/analyze-problem', { method: 'POST', body: formData });
        const result = await res.json();

        if (result.status === 'success') {
            document.getElementById('problem_file_path').value = result.file_path || '';

            const severityColor = result.severity === 'grave'  ? '#dc3545' :
                                  result.severity === 'modéré' ? '#ffc107' : '#198754';

            analysisEl.innerHTML = `
                <div class="border rounded p-2 mt-2" style="background:#f8f9fc;">
                    <div class="fw-bold small mb-1" style="color:${severityColor};">
                        <i class="fas fa-robot me-1"></i>Analyse IA — Gravité: ${result.severity}
                    </div>
                    <div class="text-muted small">${escapeHtml(result.analysis)}</div>
                </div>`;

            if (result.analysis && !document.getElementById('problem_description').value) {
                document.getElementById('problem_description').value = result.analysis;
            }
        } else {
            analysisEl.innerHTML = '<div class="text-muted small">Analyse non disponible — décrivez le problème manuellement.</div>';
        }
    } catch (e) {
        analysisEl.innerHTML = '<div class="text-muted small">Erreur d\'analyse.</div>';
    }
}

async function confirmerSignalement() {
    const carId       = document.getElementById('problem_car_id').value;
    const description = document.getElementById('problem_description').value.trim();
    const fileInput   = document.getElementById('problem_file');
    const saveBtn     = document.getElementById('problem_save_btn');

    if (!description) {
        alert('Veuillez décrire le problème.');
        return;
    }

    saveBtn.disabled  = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Envoi...';

    const formData = new FormData();
    formData.append('description', description);
    formData.append('ai_analysis', document.getElementById('problem_analysis').innerText || '');
    if (fileInput.files.length) {
        formData.append('file', fileInput.files[0]);
    }

    try {
        const res    = await fetch(`/employe/report-problem/${carId}`, { method: 'POST', body: formData });
        const result = await res.json();

        if (result.status === 'success') {
            bootstrap.Modal.getInstance(document.getElementById('problemModal')).hide();
            alert('✅ Problème signalé ! Le service RH a été notifié.');
        } else {
            alert('Erreur: ' + result.message);
            saveBtn.disabled  = false;
            saveBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Envoyer le signalement';
        }
    } catch (e) {
        alert('Erreur réseau.');
        saveBtn.disabled  = false;
        saveBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Envoyer le signalement';
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////
// MOBILE MESSAGING

let mobilePolling = null;

async function loadMobileMessages() {
    try {
        const res  = await fetch('/messages/employee-messages');
        const data = await res.json();
        if (data.status !== 'success') return;

        const el       = document.getElementById('messages_content');
        const messages = data.data;
        const badge    = document.getElementById('mobile_unread_badge');

        // count unread from admin
        const unread = messages.filter(m =>
            m.sender_type === 'admin' && !m.is_read
        ).length;

        if (unread > 0) {
            badge.style.display = 'inline';
            badge.innerText     = unread;
        } else {
            badge.style.display = 'none';
        }

        if (messages.length === 0) {
            el.innerHTML = `
                <div class="text-center text-muted small py-4">
                    <i class="fas fa-comments fa-2x mb-2 opacity-25 d-block"></i>
                    Aucun message de votre RH
                </div>`;
            return;
        }

        el.innerHTML = messages.map(m => {
            const isEmployee = m.sender_type === 'employee';
            const time = new Date(m.created_at).toLocaleTimeString('fr-TN', {
                hour: '2-digit', minute: '2-digit'
            });
            const date = new Date(m.created_at).toLocaleDateString('fr-TN', {
                day: '2-digit', month: '2-digit'
            });

            return isEmployee ? `
                <div class="d-flex justify-content-end mb-3">
                    <div style="max-width:75%;">
                        <div style="background:#0d6efd;color:white;
                            border-radius:18px 18px 4px 18px;
                            padding:10px 14px;font-size:13px;line-height:1.4;">
                            ${escapeHtml(m.content)}
                        </div>
                        <div class="text-muted text-end mt-1" style="font-size:10px;">
                            ${date} ${time}
                        </div>
                    </div>
                </div>` : `
                <div class="d-flex justify-content-start mb-3">
                    <div style="max-width:75%;">
                        <div style="background:white;border:1px solid #dee2e6;
                            border-radius:18px 18px 18px 4px;
                            padding:10px 14px;font-size:13px;line-height:1.4;">
                            ${escapeHtml(m.content)}
                        </div>
                        <div class="text-muted mt-1" style="font-size:10px;">
                            RH · ${date} ${time}
                        </div>
                    </div>
                </div>`;
        }).join('');

        el.scrollTop = el.scrollHeight;

    } catch (e) {
        console.error('loadMobileMessages error:', e);
    }
}

async function envoyerMessageMobile() {
    const input   = document.getElementById('mobile_chat_input');
    const content = input.value.trim();
    if (!content) return;

    input.value = '';

    try {
        await fetch('/messages/send', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                sender_type: 'employee',
                content:     content
            })
        });
        await loadMobileMessages();
    } catch (e) {
        console.error('envoyerMessageMobile error:', e);
    }
}

// start polling for messages
document.addEventListener('DOMContentLoaded', () => {
    mobilePolling = setInterval(loadMobileMessages, 5000);
    loadMobileMessages();
});