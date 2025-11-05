import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from data_structure.GrapeVine import GrapeVine
from paintclouds.PointCloudInterpreter import PointCloudInterpreter
from BestCutAlgorithm.BranchPruner import BranchPruner


def _clean_feedback(feedback: dict, use_weights: bool) -> dict:
    """
    Converte il feedback della GUI in un formato numerico
    e traduce le chiavi dall'italiano all'inglese.
    """
    translation_map_weights = {
        "lunghezza": "length",
        "diametro": "diameter",
        "età": "age",
        "curvatura": "curvature",
        "gemme": "num_buds",
        "soglia taglio": "cut_threshold",
    }
    translation_map_parameters = {
        "numero minimo punti outlier": "nb_points",
        "risoluzione griglia": "voxel_size",
        "lunghezza": "length_factor",
        "diametro": "diameter_scale",
        "età": "age_factor",
        "curvatura":"curvature_threshold",
        "gemme per lunghezza": "bud_length_factor",
        "gemme su curvatura": "bud_curvature_factor"
    }

    translation_map = translation_map_weights if use_weights else translation_map_parameters

    cleaned = {}
    for key, value in feedback.items():
        eng_key = translation_map.get(key)
        if not eng_key:
            continue  # ignora chiavi sconosciute

        if value == "troppo alto":
            cleaned[eng_key] = -1
        elif value == "troppo basso":
            cleaned[eng_key] = 1
        else:
            cleaned[eng_key] = 0

    return cleaned


class TkinterModel(tk.Frame):
    def __init__(self, master, pointcloudinterpreter: PointCloudInterpreter, pruner: BranchPruner):
        super().__init__(master)
        self.pointcloudinterpreter = pointcloudinterpreter
        self.pruner = pruner
        self.selected_basefolder = None
        self.output_path = None
        self.entries = {}
        self.json_files = []
        self.current_json_index = 0

        self.grid_columnconfigure(0, weight=1)  # Espandi colonna principale

        self.feedback_estimation_vars = {}
        self.feedback_weight_vars = {}

        # Parametri e Pesi
        self._create_params_weights_frame()

        # Selezione cartella dataset
        self._create_folder_selection_frame()

        # Pulsante calcolo rami
        self._create_calculate_frame()

        # Visualizzazione rami
        self._create_branches_frame()

        # Crea feedback section
        self._create_feedback_section()

        # Pulsante salva parametri
        self._create_save_frame()

    # ------------------------------
    # Creazione componenti GUI
    # ------------------------------
    def _create_params_weights_frame(self):
        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        params_frame = ttk.LabelFrame(frame, text="⚙️ Parametri di misurazione", padding=10)
        params_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        weights_frame = ttk.LabelFrame(frame, text="⚖️ Pesi per decisione taglio", padding=10)
        weights_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.params, self.weights = self.update_values()
        self._populate_frame(params_frame, self.params)
        self._populate_frame(weights_frame, self.weights)

    def _create_folder_selection_frame(self):
        frame = ttk.LabelFrame(self, text="📂 Seleziona cartella dataset", padding=10)
        frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        frame.columnconfigure(0, weight=1)

        self.folder_label = ttk.Label(frame, text="Nessuna cartella selezionata", foreground="gray")
        self.folder_label.grid(row=0, column=0, sticky="w")

        ttk.Button(frame, text="Sfoglia...", command=self.browse_folder).grid(row=0, column=1, padx=5)
        self.load_btn = ttk.Button(frame, text="Carica dati", command=self.load_data, state="disabled")
        self.load_btn.grid(row=0, column=2, padx=5)

    def _create_calculate_frame(self):
        frame = ttk.LabelFrame(self, text="✂️ Calcolo rami da tagliare", padding=10)
        frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ttk.Button(frame, text="Calcola rami da tagliare",
                   command=lambda: self.show_dataset(self.current_json_index)).grid(row=0, column=0, padx=5, pady=5)

    def _create_feedback_section(self):
        frame = ttk.LabelFrame(self, text="📝 Feedback per miglioramento algoritmo", padding=10)
        frame.grid(row=6, column=0, sticky="ew", padx=10, pady=10)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        attributes = ["numero minimo punti outlier", "risoluzione griglia","lunghezza", "diametro", "età", "curvatura", "gemme per lunghezza", "gemme su curvatura"]
        options = ["troppo basso", "ok", "troppo alto"]

        # Errori di stima
        est_frame = ttk.LabelFrame(frame, text="Errori di stima delle dimensioni dell'albero")
        est_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        for i, attr in enumerate(attributes):
            ttk.Label(est_frame, text=attr).grid(row=i, column=0, sticky="w")
            var = tk.StringVar(value="ok")
            self.feedback_estimation_vars[attr] = var
            for j, opt in enumerate(options):
                ttk.Radiobutton(est_frame, text=opt, variable=var, value=opt).grid(row=i, column=j + 1, sticky="w")

        # Errori nel calcolo del taglio
        weight_frame = ttk.LabelFrame(frame, text="Errori nel calcolo del taglio")
        weight_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 👇 Aggiungo anche il valore di soglia al feedback dei pesi
        weight_attributes = ["lunghezza", "diametro", "età", "curvatura", "gemme", "soglia taglio"]

        for i, attr in enumerate(weight_attributes):
            ttk.Label(weight_frame, text=attr).grid(row=i, column=0, sticky="w")
            var = tk.StringVar(value="ok")
            self.feedback_weight_vars[attr] = var
            for j, opt in enumerate(options):
                ttk.Radiobutton(weight_frame, text=opt, variable=var, value=opt).grid(row=i, column=j + 1, sticky="w")

        # Pulsanti accetta/rifiuta
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="salva algoritmo attuale", command=self.save_current_algorithm).pack(side="left", padx=5)
        ttk.Button(button_frame, text="migliora algoritmo", command=self.better_algorithm).pack(side="left", padx=5)


    def _create_save_frame(self):
        frame = ttk.Frame(self, padding=10)
        frame.grid(row=4, column=0, sticky="ew")
        ttk.Button(frame, text="Salva modifiche", command=self.save_parameters).pack(side="right", padx=5)

    # ------------------------------
    # Supporto e logica
    # ------------------------------
    def _populate_frame(self, frame, values_dict):
        for i, (key, value) in enumerate(values_dict.items()):
            ttk.Label(frame, text=key).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(frame, width=12)
            entry.insert(0, str(value))
            entry.configure(state="readonly")
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.entries[key] = entry

    def update_values(self):
        p = self.pointcloudinterpreter.estimator
        params = {
            "outlier_radius": p.outlier_radius,
            "nb_points": p.nb_points,
            "voxel_size": p.voxel_size,
            "min_number_points": p.min_number_points,
            "min_points_branch": p.min_points_branch,
            "curvature_threshold": p.curvature_threshold,
            "diameter_scale": p.diameter_scale,
            "age_factor": p.age_factor,
            "length_factor": p.length_factor,
            "bud_length_factor": p.bud_length_factor,
            "bud_curvature_factor": p.bud_curvature_factor
        }
        w = self.pruner
        weights = {
            "length": w.weights["length"],
            "diameter": w.weights["diameter"],
            "age": w.weights["age"],
            "num_buds": w.weights["num_buds"],
            "curvature": w.weights["curvature"],
            "cut_threshold": w.cut_threshold
        }
        return params, weights

    def refresh_entries(self):
        # aggiorna le Entry con i valori correnti dell'estimatore e del pruner
        params, weights = self.update_values()
        for key, value in params.items():
            if key in self.entries:
                self.entries[key].configure(state="normal")
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, str(value))
                self.entries[key].configure(state="readonly")

        for key, value in weights.items():
            if key in self.entries:
                self.entries[key].configure(state="normal")
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, str(value))
                self.entries[key].configure(state="readonly")

    def get_parameters(self):
        updated = {}
        for k, e in self.entries.items():
            try:
                updated[k] = float(e.get())
            except ValueError:
                updated[k] = e.get()
        return updated

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Seleziona la cartella del dataset")
        if folder:
            self.selected_basefolder = Path(folder)
            self.folder_label.config(text=str(folder), foreground="black")
            self.load_btn.config(state="normal")
        else:
            self.folder_label.config(text="Nessuna cartella selezionata", foreground="gray")
            self.load_btn.config(state="disabled")

    def load_data(self):
        if not self.selected_basefolder:
            messagebox.showwarning("Attenzione", "Seleziona prima una cartella valida.")
            return
        try:
            self.pointcloudinterpreter.interpreting_dataset(self.selected_basefolder)
            self.output_path = self.pointcloudinterpreter.output_folder
            self.json_files = sorted(self.output_path.glob("*_albero.json"))
            self.current_json_index = 0
            if self.json_files:
                messagebox.showinfo("Caricamento completato",
                                f"Dati caricati correttamente da:\n{self.selected_basefolder} in 'output'.\nClicca 'calcola rami da tagliare'.")
        except Exception as e:
            messagebox.showerror("Errore critico", f"Si è verificato un errore:\n{e}")

    def _create_branches_frame(self):
        frame = ttk.LabelFrame(self, text="📋 Rami selezionati per il taglio", padding=10)
        frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.grid_rowconfigure(3, weight=1)

        self.text_branches = tk.Text(frame, wrap="none", height=20)
        self.text_branches.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.text_branches.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_branches.configure(yscrollcommand=scrollbar.set)

    def show_dataset(self, index):
        if not self.json_files:
            messagebox.showwarning("Attenzione", "Seleziona prima un dataset valido e caricalo.")
            return

        if index < 0 or index >= len(self.json_files):
            messagebox.showwarning("Indice non valido", "Indice fuori dal range dei file JSON.")
            return

        filepath = self.json_files[index]
        print("File selezionato", filepath)
        try:
            gv = GrapeVine()
            gv.set_basefolder(self.output_path.parent)
            gv.load_grapevine_from_file(filepath.name)

            self.text_branches.delete("1.0", tk.END)

            branches = self.pruner.calculate_best_cut(gv)

            if not branches:
                self.text_branches.insert(tk.END, "Nessun ramo trovato. \n")
                return

            for branch in branches:
                self.text_branches.insert(tk.END, str(branch) + "\n" + "-" * 50 + "\n")

        except Exception as e:
            messagebox.showerror("errore mostra grapevine")


    def show_next_dataset(self):
        if self.current_json_index + 1 < len(self.json_files):
            self.current_json_index += 1
            self.show_dataset(self.current_json_index)

    def show_prev_dataset(self):
        if self.current_json_index > 0:
            self.current_json_index -= 1
            self.show_dataset(self.current_json_index)

    def save_parameters(self):
        updated = self.get_parameters()
        print("Parametri aggiornati:", updated)
        messagebox.showinfo("Salvato", "I nuovi parametri sono stati acquisiti correttamente.")

    def save_current_algorithm(self):
        print("si sta salvando il nuovo algoritmo")
        self.pointcloudinterpreter.estimator.promote_new_params()
        self.pruner.promote_new_weights()
        messagebox.showinfo("Feedback", "Algoritmo salvato")


    def better_algorithm(self):
        parameters_feedback = {k: v.get() for k, v in self.feedback_estimation_vars.items()}
        weight_feedback = {k: v.get() for k, v in self.feedback_weight_vars.items()}

        parameters_feedback = _clean_feedback(parameters_feedback, False)
        weight_feedback = _clean_feedback(weight_feedback, True)

        print("aggiorno i pesi dell'algoritmo secondo il feedback dato.")
        print("Errori stima:", parameters_feedback)
        print("Errori peso:", weight_feedback)

        # 👉 chiama il metodo del BranchPruner
        self.pointcloudinterpreter.estimator.calculate_new_parameters(parameters_feedback)
        self.pruner.calculate_new_weights_and_treshold(weight_feedback)

        #update visivo dei parametri e dei pesi
        self.refresh_entries()
        # reset visivo dei campi feedback
        for var in self.feedback_estimation_vars.values():
            var.set("ok")
        for var in self.feedback_weight_vars.values():
            var.set("ok")

        messagebox.showinfo("Feedback", "Algoritmo aggiornato in base al feedback.")

