async function changePassword() {
    const newPwd  = document.getElementById('new_password').value;
    const confirm = document.getElementById('confirm_password').value;
    const btn     = document.getElementById('save_btn');
    const err     = document.getElementById('error_msg');

    err.style.display = 'none';

    if (!newPwd || !confirm) {
        err.innerText = 'Veuillez remplir tous les champs.';
        err.style.display = 'block'; return;
    }
    if (newPwd.length < 6) {
        err.innerText = 'Mot de passe trop court (6 caractères minimum).';
        err.style.display = 'block'; return;
    }
    if (newPwd !== confirm) {
        err.innerText = 'Les mots de passe ne correspondent pas.';
        err.style.display = 'block'; return;
    }

    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enregistrement...';
    btn.disabled  = true;

    try {
        const res    = await fetch('/employe/change-password', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ new_password: newPwd, confirm_password: confirm })
        });
        const result = await res.json();

        if (result.status === 'success') {
            window.location.href = result.redirect;
        } else {
            err.innerText     = result.message;
            err.style.display = 'block';
            btn.innerHTML = '<i class="fas fa-save me-2"></i>Enregistrer';
            btn.disabled  = false;
        }
    } catch (e) {
        err.innerText     = 'Erreur réseau.';
        err.style.display = 'block';
        btn.innerHTML = '<i class="fas fa-save me-2"></i>Enregistrer';
        btn.disabled  = false;
    }
}