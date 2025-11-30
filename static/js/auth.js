var notifs = new Notifications();
var loginBtn = document.querySelector('#loginBtn')

function login_request(email, password) {
    loginBtn.disabled = true;
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/auth/login', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            console.log(response);
            if (response.status === 'success') {
                notifs.success("Authentification réussie", "Redirection en cours...");
                setTimeout(function () {
                    window.location.href = '/dashboard';
                }, 1500);

            } else {
                loginBtn.disabled = false;
                notifs.error("Erreur d'authentification", response.message);
            }
        }
        }

    xhr.send(JSON.stringify({email: email, password: password}));
}