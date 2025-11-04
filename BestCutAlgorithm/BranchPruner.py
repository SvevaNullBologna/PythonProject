from data_structure.GrapeVine import GrapeVine
from data_structure.Branch import Branch
import json
import os
from pathlib import Path

class BranchPruner:
    def __init__(self, cut_treshold=1.0):
        self.cut_treshold = cut_treshold
        self.weights = {
            "length": 1.0,
            "diameter": 0.5,
            "age": 0.2,
            "num_buds" : 0.1,
            "curvature": 0.3
        }

        self.old_weight_file = Path("weights_old.json")
        self.new_weight_file = Path("weights_new.json")
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
        data = {
            **self.weights, "cut_threshold": self.cut_treshold
        }
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
                elif key == "cut_treshold":
                    self.cut_treshold = value

        print("weights updated")

    def calculate_new_branch_estimator_parameters(self):
        pass

    def calculate_new_cut_criteria_parameters(self):
        pass

    def calculate_best_cut(self, grapevine: GrapeVine ):
        branches_to_cut = []
        for branch in grapevine.tree_elements:
            if branch.classTitle != "tree" and self._calculate_branch_score(branch) >= self.cut_treshold :
                branches_to_cut.append(branch)
        return branches_to_cut

    def _calculate_branch_score(self, branch: Branch):
        score = 0.0
        for key, weight in self.weights.items():
            value = getattr(branch, key,0) or 0
            score += weight * value
        return score