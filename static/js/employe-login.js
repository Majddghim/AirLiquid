document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', e => {
        if (e.key === 'Enter') login();
    });
});

async function login() {
    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const btn      = document.getElementById('login_btn');
    const errorMsg = document.getElementById('error_msg');

    errorMsg.style.display = 'none';

    if (!email || !password) {
        errorMsg.innerText      = 'Veuillez remplir tous les champs.';
        errorMsg.style.display  = 'block';
        return;
    }

    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Connexion...';
    btn.disabled  = true;

    try {
        const res    = await fetch('/employe/login', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ email, password })
        });
        const result = await res.json();

        if (result.status === 'success') {
            window.location.href = result.redirect;
        } else {
            errorMsg.innerText     = result.message;
            errorMsg.style.display = 'block';
            btn.innerHTML = '<i class="fas fa-sign-in-alt me-2"></i>Se connecter';
            btn.disabled  = false;
        }
    } catch (e) {
        errorMsg.innerText     = 'Erreur réseau. Veuillez réessayer.';
        errorMsg.style.display = 'block';
        btn.innerHTML = '<i class="fas fa-sign-in-alt me-2"></i>Se connecter';
        btn.disabled  = false;
    }
}