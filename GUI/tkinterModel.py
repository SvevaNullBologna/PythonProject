import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from paintclouds.PointCloudInterpreter import PointCloudInterpreter
from BestCutAlgorithm.BranchPruner import BranchPruner

class tkinterModel(tk.Frame):
    def __init__(self, master, pointcloudinterpreter: PointCloudInterpreter, pruner: BranchPruner):
        super().__init__(master)
        self.pointcloudinterpreter = pointcloudinterpreter
        self.pruner = pruner
        self.selected_basefolder = None
        self.output_path = None
        self.entries = {}

        # ------------------------------
        # SEZIONE 1: Parametri e Pesi affiancati
        # ------------------------------
        params_weights_frame = ttk.Frame(self)
        params_weights_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        params_weights_frame.columnconfigure(0, weight=1)
        params_weights_frame.columnconfigure(1, weight=1)

        # Parametri
        params_frame = ttk.LabelFrame(params_weights_frame, text="⚙️ Parametri di misurazione", padding=10)
        params_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Pesi
        weights_frame = ttk.LabelFrame(params_weights_frame, text="⚖️ Pesi per decisione taglio", padding=10)
        weights_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Lista dei file JSON di output
        self.json_files = []
        self.current_json_index = 0

        # Recupera valori
        self.params, self.weights = self.update_values()
        self._populate_frame(params_frame, self.params)
        self._populate_frame(weights_frame, self.weights)

        # ------------------------------
        # SEZIONE 2: Selezione cartella dataset
        # ------------------------------
        folder_frame = ttk.LabelFrame(self, text="📂 Seleziona cartella dataset", padding=10)
        folder_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        folder_frame.columnconfigure(0, weight=1)

        self.folder_label = ttk.Label(folder_frame, text="Nessuna cartella selezionata", foreground="gray")
        self.folder_label.grid(row=0, column=0, sticky="w")

        browse_btn = ttk.Button(folder_frame, text="Sfoglia...", command=self.browse_folder)
        browse_btn.grid(row=0, column=1, padx=5)

        self.load_btn = ttk.Button(folder_frame, text="Carica dati", command=self.load_data, state="disabled")
        self.load_btn.grid(row=0, column=2, padx=5)

        # ------------------------------
        # SEZIONE 3: Pulsante per ottenere i rami da tagliare
        # ------------------------------
        cut_frame = ttk.LabelFrame(self, text="✂️ Calcolo rami da tagliare", padding=10)
        cut_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        self.calculate_btn = ttk.Button(
            cut_frame,
            text="Calcola rami da tagliare",
            command=lambda: self.show_dataset(self.current_json_index)
        )
        self.calculate_btn.grid(row=0, column=0, padx=5, pady=5)

        # ------------------------------
        # SEZIONE 4: Tabella che mostra i rami che secondo il calcolo vanno tagliati
        # ------------------------------
        table_frame = ttk.LabelFrame(self, text="📋 Rami selezionati per il taglio", padding=10)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

        self.tree = ttk.Treeview(table_frame, columns=("class", "length", "diameter", "score"), show="headings")
        self.tree.heading("class", text="Classe")
        self.tree.heading("length", text="Lunghezza")
        self.tree.heading("diameter", text="Diametro")
        self.tree.heading("score", text="Punteggio")
        self.tree.pack(fill="both", expand=True)

        # ------------------------------
        # SEZIONE 5: Pulsante Salva modifiche
        # ------------------------------
        button_frame = ttk.Frame(self, padding=10)
        button_frame.grid(row=4, column=0, sticky="ew")
        ttk.Button(button_frame, text="Salva modifiche", command=self.save_parameters).pack(side="right", padx=5)

        # ------------------------------
        # SEZIONE 6: Pulsanti per scorrere i dataset
        # ------------------------------
        nav_frame = ttk.Frame(self)
        nav_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        self.prev_btn = ttk.Button(nav_frame, text="⬅ Precedente", command=self.show_prev_dataset)
        self.prev_btn.pack(side="left", padx=5)
        self.next_btn = ttk.Button(nav_frame, text="Successivo ➡", command=self.show_next_dataset)
        self.next_btn.pack(side="right", padx=5)

        # Espandi la riga della tabella per usare lo spazio disponibile
        self.grid_rowconfigure(3, weight=1)

    # ------------------------------
    # Metodi di supporto
    # ------------------------------
    def _populate_frame(self, frame, values_dict):
        for i, (key, value) in enumerate(values_dict.items()):
            ttk.Label(frame, text=key).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(frame, width=12)
            entry.insert(0, str(value))
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.entries[key] = entry

    def update_values(self):
        params = {
            "outlier_radius": self.pointcloudinterpreter.estimator.outlier_radius,
            "nb_points": self.pointcloudinterpreter.estimator.nb_points,
            "voxel_size": self.pointcloudinterpreter.estimator.voxel_size,
            "min_number_points": self.pointcloudinterpreter.estimator.min_number_points,
            "min_points_branch": self.pointcloudinterpreter.estimator.min_points_branch,
            "curvature_threshold": self.pointcloudinterpreter.estimator.curvature_threshold,
            "diameter_scale": self.pointcloudinterpreter.estimator.diameter_scale,
            "age_factor": self.pointcloudinterpreter.estimator.age_factor,
            "length_factor": self.pointcloudinterpreter.estimator.length_factor,
            "bud_length_factor": self.pointcloudinterpreter.estimator.bud_length_factor,
            "bud_curvature_factor": self.pointcloudinterpreter.estimator.bud_curvature_factor
        }

        weights = {
            "length": self.pruner.weights["length"],
            "diameter": self.pruner.weights["diameter"],
            "age": self.pruner.weights["age"],
            "num_buds": self.pruner.weights["num_buds"],
            "curvature": self.pruner.weights["curvature"],
            "cut_threshold": self.pruner.cut_threshold
        }
        return params, weights

    def get_parameters(self):
        updated = {}
        for key, entry in self.entries.items():
            try:
                updated[key] = float(entry.get())
            except ValueError:
                updated[key] = entry.get()
        return updated

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Seleziona la cartella del dataset")
        if folder:
            self.selected_basefolder = Path(folder)
            self.folder_label.config(text=str(self.selected_basefolder), foreground="black")
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
                self.show_dataset(self.current_json_index)
            messagebox.showinfo(
                "Caricamento completato",
                f"Dati caricati correttamente da:\n{self.selected_basefolder} in 'output'"
            )
        except Exception as e:
            messagebox.showerror("Errore critico", f"Si è verificato un errore:\n{e}")

    def show_dataset(self, index):
        if not self.json_files:
            return

        filepath = self.json_files[index]
        branches_to_cut = self.pruner.calculate_best_cut_from_file(filepath)

        # Aggiorna la Treeview
        self.tree.delete(*self.tree.get_children())
        for branch in branches_to_cut:
            self.tree.insert("", "end", values=(branch.classTitle, branch.length, branch.diameter, branch.score))

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

