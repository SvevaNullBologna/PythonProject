import tkinter as tk
from paintclouds.PointCloudInterpreter import PointCloudInterpreter
from BestCutAlgorithm.BranchPruner import BranchPruner
from GUI.tkinterModel import tkinterModel

# Crea le istanze dei tuoi oggetti
pointcloudinterpreter = PointCloudInterpreter()
pruner = BranchPruner()

# Crea la finestra principale
root = tk.Tk()
root.title("Parametri Branch Estimator & Pruner")
root.geometry("400x600")

# Crea e aggiungi il frame
gui = tkinterModel(root, pointcloudinterpreter, pruner)
gui.pack(fill="both", expand=True, padx=10, pady=10)

# Avvia il loop principale di Tkinter
root.mainloop()
