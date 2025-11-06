document.addEventListener("DOMContentLoaded", async () => {
    const translate = {
        outlier_radius: "Raggio outlier",
        nb_points: "Numero punti",
        voxel_size: "Voxel size",
        curvature_threshold: "Soglia curvatura",
        diameter_scale: "Scala diametro",
        age_factor: "età",
        length_factor: "lunghezza",
        bud_length_factor: "gemme per lunghezza",
        bud_curvature_factor: "gemme secondo la curvatura",
        length: "lunghezza",
        diameter: "diametro",
        age: "età",
        num_buds: "gemme",
        curvature: "curvatura",
        cut_threshold: "Soglia di taglio"
    };

    // --- Mostra parametri e pesi ---
    function displayTable(containerSelector, data) {
        const container = document.querySelector(containerSelector);
        if (!container) return;
        container.innerHTML = "";
        const table = document.createElement("table");
        table.classList.add("data-table");
        const tbody = document.createElement("tbody");
        Object.entries(data).forEach(([key, value]) => {
            const tr = document.createElement("tr");
            const tdKey = document.createElement("td");
            tdKey.classList.add("key");
            tdKey.textContent = translate[key] || key;
            const tdValue = document.createElement("td");
            tdValue.classList.add("value");
            tdValue.textContent = value ?? "—";
            tr.appendChild(tdKey);
            tr.appendChild(tdValue);
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        container.appendChild(table);
    }

    // --- Recupera parametri e pesi all'avvio ---
    try {
        const res = await fetch("/get_params_weights");
        const data = await res.json();
        if (!data.error) {
            displayTable("#params-container", data.parameters);
            displayTable("#weights-container", data.weights);
        } else {
            console.error("Errore dal backend:", data.error);
        }
    } catch (err) {
        console.error("Errore di connessione:", err);
    }

    const setFolderBtn = document.getElementById("set-basefolder");
    const loadDatasetBtn = document.getElementById("load-dataset");
    const basePathInput = document.getElementById("basefolder-path");

    setFolderBtn.addEventListener("click", async () => {
        const folderPath = basePathInput.value.trim();
        if (!folderPath) {
            alert("Inserisci prima un path valido!");
            return;
        }

        try {
            const res = await fetch("/set_dataset_folder", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ folder: folderPath })
            });
            const data = await res.json();
            if (data.status === "ok") {
                alert("Cartella base impostata correttamente!");
            } else {
                alert("Errore: " + (data.error || "Unknown"));
            }
        } catch (err) {
            console.error(err);
            alert("Errore di connessione al backend");
        }
    });

    loadDatasetBtn.addEventListener("click", async () => {
        try {
            const res = await fetch("/load_dataset", { method: "POST" });
            const data = await res.json();
            if (data.status === "ok") {
                alert(`Dataset caricato! File trovati: ${data.num_files}`);
            } else {
                alert("Errore caricamento dataset: " + (data.error || data["error message"]));
            }
        } catch (err) {
            console.error(err);
            alert("Errore di connessione al backend");
        }
    });

    const computeBtn = document.getElementById("compute-cut");
    const saveBtn = document.getElementById("save-cut");
    const outputArea = document.getElementById("branches-output");

    computeBtn.addEventListener("click", async () => {
        try {
            const res = await fetch("/show_dataset");  // ← cambiato qui
            const data = await res.json();
            if (data.status === "error") {
                outputArea.value = "Errore: " + data.message;
            } else {
                outputArea.value = data.branches.join("\n");
            }
        } catch (err) {
            console.error("Errore di connessione:", err);
            outputArea.value = "Errore di connessione al server.";
        }
    });


    // --- Salvataggio risultati ---
    saveBtn.addEventListener("click", () => {
        if (!outputArea.value) {
            alert("Nessun risultato da salvare!");
            return;
        }

        const blob = new Blob([outputArea.value], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "cut_branches.txt";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

});
