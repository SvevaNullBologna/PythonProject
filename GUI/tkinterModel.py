import tkinter as tk
from tkinter import ttk
from paintclouds.PointCloudInterpreter import PointCloudInterpreter
from BestCutAlgorithm.BranchPruner import BranchPruner

class tkinterModel(tk.Frame):
    def __init__(self, master, pointcloudinterpreter:PointCloudInterpreter, pruner: BranchPruner):
        super().__init__(master)
        self.pointcloudinterpreter = pointcloudinterpreter
        self.pruner = pruner
        self.update_values()

        # crea i dizionari una sola volta
        self.params, self.weights = self.update_values()
        # mostra i valori nella GUI
        self.show_values_on_GUI()

        #pulsan


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
            "cut_threshold": self.pruner.cut_threshold  # questo va bene se cut_threshold è attributo di pruner
        }

        return params, weights

    def show_values_on_GUI(self):
        self.entries = {}

        row = 0
        ttk.Label(self, text="PARAMETRI PER LA MISURAZIONE DELL' ALBERO", font=("Arial", 11, "bold")).grid(row=row, column=0, columnspan=2,
                                                                                      pady=(5, 2))
        row += 1

        for key, value in self.params.items():
            ttk.Label(self, text=key).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(self)
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, padx=5, pady=2)
            self.entries[key] = entry
            row += 1

        ttk.Label(self, text="PESI DELLE CARATTERISTICHE NELLA DECISIONE DEL TAGLIO", font=("Arial", 11, "bold")).grid(row=row, column=0, columnspan=2,
                                                                                pady=(10, 2))
        row += 1

        for key, value in self.weights.items():
            ttk.Label(self, text=key).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(self)
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, padx=5, pady=2)
            self.entries[key] = entry
            row += 1

    def get_parameters(self):
        updated = {}
        for key, entry in self.entries.items():
            try:
                updated[key] = float(entry.get())
            except ValueError:
                updated[key] = entry.get()
        return updated
