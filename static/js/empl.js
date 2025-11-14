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
        window.location.href = "/dashboard/employe";
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
