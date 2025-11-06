from pathlib import Path
from data_structure.GrapeVine import GrapeVine
from paintclouds.PointCloudInterpreter import PointCloudInterpreter
from BestCutAlgorithm.BranchPruner import BranchPruner


class ModelBackend:
    """
    Logica pura senza GUI, pronta per Flask.
    """
    def __init__(self, pointcloudinterpreter: PointCloudInterpreter, pruner: BranchPruner):
        self.pointcloudinterpreter = pointcloudinterpreter
        self.pruner = pruner
        self.selected_basefolder: Path | None = None
        self.output_path: Path | None = None
        self.json_files: list[Path] = []
        self.current_json_index: int = 0
        self.current_grapevine: GrapeVine = GrapeVine()
        self.branches_to_cut = []

    #
    #   Metodi di supporto
    #

    def _clean_feedback(self, feedback: dict, use_weights: bool) -> dict:
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
            "curvatura": "curvature_threshold",
            "gemme per lunghezza": "bud_length_factor",
            "gemme su curvatura": "bud_curvature_factor"
        }
        translation_map = translation_map_weights if use_weights else translation_map_parameters
        cleaned = {}
        for key, value in feedback.items():
            eng_key = translation_map.get(key)
            if not eng_key:
                continue
            if value == "troppo alto":
                cleaned[eng_key] = -1
            elif value == "troppo basso":
                cleaned[eng_key] = 1
            else:
                cleaned[eng_key] = 0
        return cleaned

    # -------------------
    # Dataset management
    # -------------------
    def set_dataset_folder(self, folder: str):
        path = Path(folder).absolute()
        if not path or not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"Cartella non trovata: {folder}")
        self.selected_basefolder = path


    def load_dataset_folder(self):
        if self.selected_basefolder and self.selected_basefolder.is_dir():
            self.pointcloudinterpreter.interpreting_dataset(self.selected_basefolder)
            self.output_path = self.pointcloudinterpreter.output_folder
            self.json_files = sorted(self.output_path.glob("*_albero.json"))
            self.current_json_index = 0

            if self.json_files:
                # carica il primo dataset subito
                self.current_grapevine.set_basefolder(self.output_path.parent)
                self.current_grapevine.load_grapevine_from_file(self.json_files[0].name)
                self.branches_to_cut = self.pruner.calculate_best_cut(self.current_grapevine)

            return {"status": "ok", "num_files": len(self.json_files)}
        else:
            return {"status": "error", "error message": "non è stato selezionato alcun basefolder valido"}

    def reset_current_dataset(self):
        self.branches_to_cut = None
        self.current_json_index = 0

    def list_datasets(self):
        return [f.name for f in self.json_files]

    def show_dataset(self, index: int):
        self.reset_current_dataset()
        if not self.json_files:
            return {"error": "Nessun dataset caricato"}
        if index < 0 or index >= len(self.json_files):
            return {"error": "Indice fuori dal range dei file JSON"}

        filepath = self.json_files[index]
        self.current_grapevine.set_basefolder(self.output_path.parent)
        self.current_grapevine.load_grapevine_from_file(filepath.name)

        self.branches_to_cut = self.pruner.calculate_best_cut(self.current_grapevine)
        branches_str = []
        for b in self.branches_to_cut:
            branches_str.append(str(b))
        return {"file": filepath.name, "branches": branches_str}

    def show_next_dataset(self):
        if self.current_json_index + 1 < len(self.json_files):
            self.current_json_index += 1
        return self.show_dataset(self.current_json_index)

    def show_prev_dataset(self):
        if self.current_json_index > 0:
            self.current_json_index -= 1
        return self.show_dataset(self.current_json_index)

    # -------------------
    # Parametri e pesi
    # -------------------
    def get_parameters_weights(self):
        p = self.pointcloudinterpreter.estimator
        pr = self.pruner
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
        weights = {
            "length": pr.weights["length"],
            "diameter": pr.weights["diameter"],
            "age": pr.weights["age"],
            "num_buds": pr.weights["num_buds"],
            "curvature": pr.weights["curvature"],
            "cut_threshold": pr.cut_threshold
        }
        return {"parameters": params, "weights": weights}

    def save_algorithm(self):
        self.pointcloudinterpreter.estimator.promote_new_params()
        self.pruner.promote_new_weights()
        return {"status": "ok"}

    def better_algorithm(self, parameters_feedback: dict, weight_feedback: dict):
        parameters_feedback = self._clean_feedback(parameters_feedback, use_weights=False)
        weight_feedback = self._clean_feedback(weight_feedback, use_weights=True)

        self.pointcloudinterpreter.estimator.calculate_new_parameters(parameters_feedback)
        self.pruner.calculate_new_weights_and_treshold(weight_feedback)
        return {"status": "ok", "parameters_feedback": parameters_feedback, "weight_feedback": weight_feedback}

    def get_cut_document(self):
        if self.current_grapevine:
            branches = self.pruner.print_best_cut(self.current_grapevine, self.branches_to_cut)
            return {"branches": branches}
        else :
            return {"status" : "error"}
