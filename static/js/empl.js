async function enregistrerEmploye() {
    // Get form data
    const data = {
        nom: document.getElementById("nom").value.trim(),
        prenom: document.getElementById("prenom").value.trim(),
        email: document.getElementById("email").value.trim(),
        telephone: document.getElementById("telephone").value.trim(),
        poste: document.getElementById("poste").value.trim(),
        departement: document.getElementById("departement").value.trim(),
        created_at: document.getElementById("created_at").value
    };

    try {
        // Send data to Flask backend
        const response = await fetch("/ajout-employe", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        // Parse response
        const result = await response.json();

        // Display message
        if (result.status === "success") {
            alert("✅ " + result.message);
            document.getElementById("employeForm").reset();
        } else {
            alert("⚠️ " + result.message);
        }

    } catch (error) {
        console.error("Erreur lors de l'envoi :", error);
        alert("❌ Une erreur s'est produite lors de l'enregistrement.");
    }
}
