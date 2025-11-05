import shutil

from data_structure.GrapeVine import GrapeVine
from data_structure.Branch import Branch
import json
import os
from pathlib import Path

class BranchPruner:
    def __init__(self, cut_threshold=1.0):
        self.cut_threshold = cut_threshold
        self.weights = {
            "length": 1.0,
            "diameter": 0.5,
            "age": 0.2,
            "num_buds" : 0.1,
            "curvature": 0.3
        }

        self.old_weight_file = Path(r"C:\Users\Sveva\PycharmProjects\PythonProject\BestCutAlgorithm\weights_old.json")
        self.new_weight_file = Path(r"C:\Users\Sveva\PycharmProjects\PythonProject\BestCutAlgorithm\weights_new.json")
        self.__set_starting_weights()

    def __set_starting_weights(self):
        if not self.new_weight_file.exists() or os.stat(self.new_weight_file).st_size == 0 :
            if not self.old_weight_file.exists() or os.stat(self.old_weight_file).st_size == 0:
                self.__write_weights_on_file(use_old=True)
                print("starting weight's file created")
            else:
                print("starting weight's file already exists")
                self.__read_weights(use_old=True)
        else:
            print("starting weight's file already exists")
            self.__read_weights(use_old=False)


    def __write_weights_on_file(self, use_old : bool):
        filename = self.old_weight_file if use_old else self.new_weight_file
        data = {**self.weights, "cut_threshold": self.cut_threshold}
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"weight's file written on {filename}")

    def __read_weights(self, use_old: bool):
        filename = self.old_weight_file if use_old else self.new_weight_file
        with open(filename, "r") as f:
            data = json.load(f)
        for key, value in data.items():
            if key in self.weights:
                self.weights[key] = value
            elif key == "cut_threshold":
                self.cut_threshold = value

        print(f"weights updated from {filename}")


    def __discard_weights(self, use_old: bool):
        filename = self.old_weight_file if use_old else self.new_weight_file
        if filename.exists():
            filename.unlink()

    def __promote_new_weights(self):
        if not self.new_weight_file.exists() or (os.stat(self.new_weight_file).st_size == 0) :
            print("no new weights file found to promote")
        else:
            shutil.move(self.new_weight_file, self.old_weight_file)
            print(f"new weights promoted to old")

    def calculate_best_cut_from_file(self, interpreted_supervisely: str):
        gv = GrapeVine()
        gv.load_grapevine_from_file(interpreted_supervisely)
        return self.calculate_best_cut(gv)

    def calculate_best_cut(self, grapevine: GrapeVine ):
        branches_to_cut = []
        for branch in grapevine.tree_elements:
            if branch.classTitle != "Tree":
                branch.score = self._calculate_branch_score(branch)
                if branch.score >= self.cut_threshold :
                    branches_to_cut.append(branch)
        return branches_to_cut

    def _calculate_branch_score(self, branch: Branch):
        score = 0.0
        for key, weight in self.weights.items():
            value = getattr(branch, key,0) or 0
            score += weight * value
        return score

    def calculate_new_weights_and_treshold(self, weight_feedback):
        """
        Aggiorna i pesi e la soglia di taglio in base al feedback.
        weight_feedback: dict con chiavi già tradotte e valori numerici (-1,0,1)
        """
        print("Feedback ricevuto per aggiornamento pesi:", weight_feedback)

        # coefficiente di aggiornamento (quanto modificare i pesi)
        learning_rate = 0.05

        for key, delta in weight_feedback.items():
            if key == "cut_threshold":
                # Aggiorno la soglia di taglio direttamente
                self.cut_threshold += delta * learning_rate
                # limito la soglia a valori sensati
                self.cut_threshold = max(0.0, self.cut_threshold)
            elif key in self.weights:
                self.weights[key] += delta * learning_rate
                # limito i pesi a valori >= 0
                self.weights[key] = max(0.0, self.weights[key])

        # Scrivo le nuove configurazioni su file
        self.__write_weights_on_file(use_old=False)


