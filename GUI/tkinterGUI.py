import tkinter as tk
from tkinter import filedialog, messagebox
import json
from BestCutAlgorithm.BranchEstimator import BranchEstimator
from BestCutAlgorithm.BranchPruner import  BranchPruner
from paintclouds.PointCloudInterpreter import PointCloudInterpreter


# --- Parametri dell'AI (copiati dal tuo input) ---
PARAMETRI = {
    "outlier_radius": None,
    "nb_points": 10,
    "voxel_size": 0.001,
    "min_number_points": 3,
    "min_points_branch": 3,
    "curvature_threshold": 0.1,
    "diameter_scale": 2,
    "age_factor": 25.0,
    "length_factor": 2.5,
    "bud_length_factor": 15.0,
    "bud_curvature_factor": 0.8
}

PESI = {
    "length": 1.0,
    "diameter": 0.5,
    "age": 0.2,
    "num_buds": 0.1,
    "curvature": 0.3,
    "cut_threshold": 1.0
}

# --- Motivi di Errore (per la scelta multipla) ---
MOTIVI_ERRORE = [
    "Età",
    "Lunghezza",
    "Curvatura",
    "Diametro",
    "Fattore Età (age_factor)",
    "Soglia Taglio (cut_threshold)"
]


class AIFeedbackApp:
    def __init__(self, master):
        self.master = master
        master.title("Pannello di Monitoraggio AI")

        # Variabili per memorizzare i percorsi e il feedback
        self.supervisely_folder = ""
        self.target_file = ""
        self.risultato_ai = tk.StringVar(value="Nessun risultato AI")
        self.rami_tagliati_errati = tk.IntVar(value=0)
        self.motivi_selezionati = {}  # Per le checkbox

        # --- Configurazione dei Frame (sezioni) ---
        self.setup_frames()
        self.setup_selettore_cartelle_e_file()
        self.setup_display_parametri()
        self.setup_feedback_form()

    def setup_frames(self):
        """Crea i contenitori principali per l'organizzazione."""
        # Frame per i selettori (Cartella e File)
        # Usiamo pack() per i frame principali
        self.frame_selettori = tk.Frame(self.master, padx=10, pady=10, relief=tk.GROOVE, borderwidth=2)
        self.frame_selettori.pack(fill='x', pady=5)

        # Frame per i parametri (diviso in due colonne)
        self.frame_parametri = tk.Frame(self.master, padx=10, pady=10, relief=tk.GROOVE, borderwidth=2)
        self.frame_parametri.pack(fill='x', pady=5)

        self.frame_set1 = tk.Frame(self.frame_parametri)
        self.frame_set1.pack(side=tk.LEFT, padx=10, fill='y')  # Usiamo pack per dividere i due set
        self.frame_set2 = tk.Frame(self.frame_parametri)
        self.frame_set2.pack(side=tk.LEFT, padx=10, fill='y')  # Usiamo pack per dividere i due set

        # Frame per il Feedback dell'Utente
        self.frame_feedback = tk.Frame(self.master, padx=10, pady=10, relief=tk.GROOVE, borderwidth=2)
        self.frame_feedback.pack(fill='x', pady=5)

    def setup_selettore_cartelle_e_file(self):
        """Gestisce la selezione della cartella principale e del file di test. Usa GRID."""

        # Selettore Cartella Supervisely
        tk.Label(self.frame_selettori, text="Folder Supervisely:").grid(row=0, column=0, sticky="w")
        self.supervisely_path_label = tk.Label(self.frame_selettori, text="Nessuna Cartella Selezionata", width=35,
                                               anchor="w")
        self.supervisely_path_label.grid(row=0, column=1, padx=5)
        tk.Button(self.frame_selettori, text="Scegli Folder", command=self.seleziona_folder_supervisely).grid(row=0,
                                                                                                              column=2,
                                                                                                              padx=5)

        # Selettore File (inizialmente disabilitato)
        tk.Label(self.frame_selettori, text="File da Valutare:").grid(row=1, column=0, sticky="w")
        self.target_file_label = tk.Label(self.frame_selettori, text="Selezionare prima il folder...", width=35,
                                          anchor="w")
        self.target_file_label.grid(row=1, column=1, padx=5)

        self.btn_seleziona_file = tk.Button(self.frame_selettori, text="Scegli File",
                                            command=self.seleziona_file_target, state=tk.DISABLED)
        self.btn_seleziona_file.grid(row=1, column=2, padx=5)

        # Pulsante per avviare la valutazione AI
        tk.Button(self.frame_selettori, text="Esegui Valutazione AI", command=self.esegui_valutazione_ai,
                  bg="lightblue").grid(row=2, column=1, pady=10)

        # Risultato AI
        tk.Label(self.frame_selettori, text="Risultato AI:").grid(row=3, column=0, sticky="w")
        tk.Label(self.frame_selettori, textvariable=self.risultato_ai, fg="blue", font=('Arial', 10, 'bold')).grid(
            row=3, column=1, sticky="w")

    def setup_display_parametri(self):
        """Visualizza i due set di parametri dell'AI. Usa GRID nei sub-frame."""

        # --- Set 1 ---
        # Usiamo GRID per allineare il titolo e i parametri, risolvendo il TclError
        tk.Label(self.frame_set1, text="PARAMETRI", font=('Arial', 10, 'bold')).grid(row=0, column=0,
                                                                                     columnspan=2, pady=5)
        self._display_params(self.frame_set1, PARAMETRI, start_row=1)

        # --- Set 2 ---
        # Usiamo GRID per allineare il titolo e i parametri, risolvendo il TclError
        tk.Label(self.frame_set2, text="PESI", font=('Arial', 10, 'bold')).grid(row=0, column=0,
                                                                                columnspan=2, pady=5)
        self._display_params(self.frame_set2, PESI, start_row=1)

    def _display_params(self, parent_frame, params, start_row=0):
        """
        Funzione helper per visualizzare i parametri in etichette.
        CORREZIONE: Accetta start_row come argomento per risolvere il TypeError.
        """
        row_num = start_row
        for key, value in params.items():
            tk.Label(parent_frame, text=f"{key}:", anchor="w").grid(row=row_num, column=0, sticky="w", padx=5)
            tk.Label(parent_frame, text=str(value), anchor="w", fg="gray").grid(row=row_num, column=1, sticky="w")
            row_num += 1

    def setup_feedback_form(self):
        """Crea il form per la raccolta del feedback. Usa PACK."""

        tk.Label(self.frame_feedback, text="RACCOLTA FEEDBACK UTENTE", font=('Arial', 10, 'bold')).pack(pady=5)

        # 1. Input Rami Tagliati Erroneamente
        tk.Label(self.frame_feedback, text="N° Rami Tagliati Erroneamente:").pack(anchor="w", pady=(5, 0))
        tk.Entry(self.frame_feedback, textvariable=self.rami_tagliati_errati, width=10).pack(anchor="w")

        # 2. Motivi di Errore (Checkbox)
        tk.Label(self.frame_feedback, text="Motivo Principale dell'Errore (Seleziona uno o più):").pack(anchor="w",
                                                                                                        pady=(10, 0))

        motivi_frame = tk.Frame(self.frame_feedback)
        motivi_frame.pack(anchor="w")

        # Usiamo GRID all'interno di 'motivi_frame' per una disposizione compatta
        col = 0
        row = 0
        for motivo in MOTIVI_ERRORE:
            var = tk.IntVar()
            cb = tk.Checkbutton(motivi_frame, text=motivo, variable=var)
            cb.grid(row=row, column=col, sticky="w", padx=5)
            self.motivi_selezionati[motivo] = var
            col += 1
            if col > 2:  # 3 colonne max
                col = 0
                row += 1

        # 3. Approvazione Configurazione
        tk.Label(self.frame_feedback, text="Approvazione Configurazione:").pack(anchor="w", pady=(10, 0))
        self.approvazione = tk.StringVar(value="Rifiuta")  # Default a Rifiuta
        tk.Radiobutton(self.frame_feedback, text="Approva", variable=self.approvazione, value="Approva").pack(
            side=tk.LEFT, padx=10)
        tk.Radiobutton(self.frame_feedback, text="Rifiuta", variable=self.approvazione, value="Rifiuta").pack(
            side=tk.LEFT)

        # 4. Pulsante di Invio Finale
        tk.Button(self.frame_feedback, text="INVIA FEEDBACK E SALVA", command=self.salva_feedback, bg="green",
                  fg="white").pack(pady=20)

    # --- LOGICA APPLICATIVA ---

    def seleziona_folder_supervisely(self):
        """Permette all'utente di selezionare la cartella principale."""
        folder_selezionato = filedialog.askdirectory(title="Seleziona la Cartella Principale Supervisely")
        if folder_selezionato:
            self.supervisely_folder = folder_selezionato
            self.supervisely_path_label.config(text=folder_selezionato)

            # Abilita il selettore file dopo aver scelto la cartella
            self.target_file_label.config(text="Pronto per scegliere il file...")
            self.btn_seleziona_file.config(state=tk.NORMAL)

    def seleziona_file_target(self):
        """Permette all'utente di selezionare un file da valutare."""
        if not self.supervisely_folder:
            messagebox.showwarning("Attenzione", "Devi prima selezionare la Cartella Supervisely.")
            return

        # Simula la restrizione del folder
        file_selezionato = filedialog.askopenfilename(
            initialdir=self.supervisely_folder,  # Inizia la ricerca in questo folder
            title="Seleziona il File da Valutare"
        )

        if file_selezionato:
            self.target_file = file_selezionato
            self.target_file_label.config(text=file_selezionato)

    def esegui_valutazione_ai(self):
        """Simula l'esecuzione dell'AI e visualizza un risultato."""
        if not self.target_file:
            messagebox.showwarning("Attenzione", "Seleziona prima un file da valutare.")
            return

        # *** QUI INSERIRAI LA TUA VERA LOGICA DI ESECUZIONE AI ***

        # Esempio di risultato simulato
        risultato_simulato = "Rami Tagliati: 15 / Precisione: 85%"

        self.risultato_ai.set(risultato_simulato)
        messagebox.showinfo("Valutazione Completata", "Risultato AI pronto per il feedback.")

    def salva_feedback(self):
        """Raccoglie tutti i dati di feedback e li gestisce (salvataggio su file/DB)."""

        # 1. Raccogli dati
        try:
            rami_errati = self.rami_tagliati_errati.get()
        except tk.TclError:
            messagebox.showerror("Errore Input", "Per favore, inserisci un numero valido per i rami erronei.")
            return

        stato_approvazione = self.approvazione.get()

        motivi = [motivo for motivo, var in self.motivi_selezionati.items() if var.get() == 1]

        # 2. Struttura del log
        log_feedback = {
            "timestamp": tk.CURRENT,
            "folder_supervisely": self.supervisely_folder,
            "file_valutato": self.target_file,
            "risultato_ai_visualizzato": self.risultato_ai.get(),
            "config_approvata": stato_approvazione,
            "rami_tagliati_errati": rami_errati,
            "motivi_errore_selezionati": motivi,
            "parametri_set_1_usati": PARAMETRI,
            "parametri_set_2_usati": PESI
        }

        # 3. Azione (es. Stampa in console e salva in un file JSON)
        print("\n--- DATI FEEDBACK SALVATI ---")
        print(json.dumps(log_feedback, indent=4))

        try:
            # Qui potresti voler salvare ogni record separatamente in un log file.
            # Per una gestione più robusta in un ambiente reale, considera SQLite o un DB.
            with open("feedback_log.json", "a") as f:
                json.dump(log_feedback, f, indent=4)
                f.write(",\n")
            messagebox.showinfo("Successo", "Feedback salvato con successo!")
        except Exception as e:
            messagebox.showerror("Errore di Salvataggio", f"Impossibile salvare il file: {e}")


# --- Esecuzione dell'Applicazione ---
if __name__ == '__main__':
    root = tk.Tk()
    app = AIFeedbackApp(root)
    root.mainloop()
