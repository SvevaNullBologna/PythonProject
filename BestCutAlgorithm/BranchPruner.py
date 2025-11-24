import shutil

from data_structure.GrapeVine import GrapeVine
from data_structure.Branch import Branch
import json
import os
from pathlib import Path

class BranchPruner:
    def __init__(self, result_folder = None):
        self.project_root = Path(__file__).resolve().parents[1]
        self.cut_threshold = 0.2
        self.weights = {
            "length": 0.3,
            "diameter": 0.5,
            "age": 0.5,
            "num_buds" : 1.0,
            "curvature": 0.5
        }

        self.signs = {
            "length": 1,  # rami lunghi → da tagliare
            "diameter": -1,  # rami grossi → da conservare
            "age": 1,  # vecchi → da tagliare
            "num_buds": -1,  # molti germogli → da conservare
            "curvature": 1  # molto curvi → da tagliare
        }

        self.old_weight_file = Path(self.project_root / "BestCutAlgorithm" / "weights_old.json")
        self.new_weight_file = Path(self.project_root / "BestCutAlgorithm" / "weights_new.json")

        if result_folder and result_folder.is_dir():
            self.best_cut_dir = Path(result_folder / "BestCutAlgorithm")
        else:
            self.best_cut_dir = self.project_root / "ResultingCuts"

        self.best_cut_dir.mkdir(exist_ok=True)

        self.__set_starting_weights()

    #  gestione file dei pesi

    def __set_starting_weights(self):
        if not self.new_weight_file.exists() or os.stat(self.new_weight_file).st_size == 0 :
            if not self.old_weight_file.exists() or os.stat(self.old_weight_file).st_size == 0:
                self.__write_weights_on_file(use_old=True)
                print("starting weight's file created")
            else:
                self.__read_weights(use_old=True)
                print("starting weight's file already exists")
        else:
            self.__read_weights(use_old=False)
            print("starting weight's file already exists")


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

    def promote_new_weights(self):
        if not self.new_weight_file.exists() or (os.stat(self.new_weight_file).st_size == 0) :
            print("no new weights file found to promote")
            return

        shutil.move(self.new_weight_file, self.old_weight_file)
        print(f"new weights promoted to old")

    # funzioni per il calcolo del taglio

    def calculate_best_cut(self, grapevine: GrapeVine ):
        branches_to_cut = []
        for branch in grapevine.tree_elements:
            print(f"branch classTitle in calculate best cut {branch.classTitle}")
            if branch.classTitle != "Tree":
                branch.score = self._calculate_branch_score(branch, grapevine)
                decision = branch.score >= self.cut_threshold
                print(f"branch score: {branch.score} >= {self.cut_threshold} : {decision}")
                if decision:
                    branches_to_cut.append(branch)
        return branches_to_cut

    def _normalize_branch_value(self, key, value, grapevine):
        # Trova min e max per ogni attributo in tutti i rami
        values = [getattr(b, key, 0) or 0 for b in grapevine.tree_elements if b.classTitle != "Tree"]
        min_val = min(values)
        max_val = max(values)
        if max_val - min_val == 0:
            return 0.5  # caso speciale: tutti uguali
        return (value - min_val) / (max_val - min_val)

    def _calculate_branch_score(self, branch: Branch, grapevine: GrapeVine):
        score = 0.0
        for key, weight in self.weights.items():
            raw_value = getattr(branch, key,0) or 0
            normalized_value = self._normalize_branch_value(key, raw_value, grapevine)
            sign = self.signs[key]
            score += sign * weight * normalized_value
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

    def print_best_cut(self, grapevine: GrapeVine, branches_to_cut):
        print("trying to print best cut!")
        if not grapevine.source_filename:
            print("Impossibile salvare: filename sorgente non disponibile")
            return
        output_filename = self.best_cut_dir / grapevine.source_filename
        data = {
            "branches_to_cut": [branch.to_dict() for branch in branches_to_cut]
        }

        with open(output_filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Best cut salvato in {output_filename}")


if __name__ == "__main__":
    g = GrapeVine()
    g.set_basefolder(r"C:\Users\Sveva\Desktop\Materiale")
    g.load_grapevine_from_file("dataset 2025-10-09 10-36-06_albero.json")

    result_path = Path("C:\\Users\Sveva\Desktop")
    bp = BranchPruner(result_path)

    branches_to_cut = bp.calculate_best_cut(g)
    if len(branches_to_cut) > 0 :
        print(f"there are {len(branches_to_cut)} branches to cut")
    else :
        print("no branches to cut")
    bp.print_best_cut(g, branches_to_cut)



