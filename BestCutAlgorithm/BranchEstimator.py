import json
import os
import shutil

import open3d as o3d #per leggere i pointcloud
import numpy as np
from pathlib import Path

class BranchEstimator:
    def __init__(self):
        self.outlier_radius = None
        self.nb_points = 10
        self.voxel_size = 0.001

        self.min_number_points = 3
        self.min_points_branch = 3
        self.curvature_threshold = 0.01

        self.diameter_scale = 2

        self.age_factor = 5.0
        self.length_factor = 2.5
        self.bud_length_factor = 10.0
        self.bud_curvature_factor = 0.8

        # if file does not exist, create branch_parameters_old and write data -> starting point
        self.project_root = Path(__file__).resolve().parents[1]
        self.old_param_file = Path(self.project_root / "BestCutAlgorithm" / "branch_parameters_old.json")
        self.new_param_file = Path(self.project_root / "BestCutAlgorithm" / "branch_parameters_new.json")
        self.__set_starting_parameters_in_json()


    """
        FOR THE AI EVOLUTION ALGORITHM AND FILE MANAGING
    """

    def __set_starting_parameters_in_json(self):
        if not self.new_param_file.exists() or os.stat(self.new_param_file).st_size == 0:
            if not self.old_param_file.exists() or os.stat(self.old_param_file).st_size == 0:
                self.__write_params_on_file(use_old=True)
                print("starting param's file created")
            else:
                self.__read_params_on_file(use_old=True)
                print("starting param's file already exists")
        else:
            self.__read_params_on_file(use_old=False)
            print("starting parameter's file already exists")


    def __write_params_on_file(self, use_old: bool):
        filename = self.old_param_file if use_old else self.new_param_file
        data = {
            "outlier_radius": self.outlier_radius,
            "nb_points": self.nb_points,
            "voxel_size": self.voxel_size,
            "min_number_points": self.min_number_points,
            "min_points_branch": self.min_points_branch,
            "curvature_threshold": self.curvature_threshold,
            "diameter_scale": self.diameter_scale,
            "age_factor": self.age_factor,
            "length_factor": self.length_factor,
            "bud_length_factor": self.bud_length_factor,
            "bud_curvature_factor": self.bud_curvature_factor
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"starting parameter's file created: {filename}")

    def __read_params_on_file(self, use_old: bool):
        filename = self.old_param_file if use_old else self.new_param_file
        with open(filename, 'r') as f:
            data = json.load(f)
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        print(f"Parameters loaded from: {filename}")


    def __discard_parameters(self, use_old: bool):
        filename = self.old_param_file if use_old else self.new_param_file
        if filename.exists():
            filename.unlink()

    def promote_new_params(self):
        if not self.new_param_file.exists() or (os.stat(self.new_param_file).st_size == 0) :
            print("no new parameters file found to promote")
            return

        shutil.move(self.new_param_file, self.old_param_file)
        print(f"new parameters promoted to old")

    """
        FOR THE ALGORITHM ESTIMATING LENGTH, DIAMETER, AGE, ECC... 
    """

    def _clean_branch_points(self, branch_points):
        branch_pcd = o3d.geometry.PointCloud()
        branch_pcd.points = o3d.utility.Vector3dVector(branch_points)

        if self.outlier_radius is not None:  # nel caso in cui si aggiunge un filtro outlier per ridurre ulteriormente il rumore
            branch_pcd, _ = branch_pcd.remove_radius_outlier(nb_points=self.nb_points, radius=self.outlier_radius)

        branch_pcd = branch_pcd.voxel_down_sample(voxel_size=self.voxel_size)  # rimozione rumore e densità. Elimina punti ridondanti senza cambiare forma.
        return np.asarray(branch_pcd.points)

    def _estimate_curvature(self, points):
        if len(points) < self.min_number_points:
            return 0.0

        # ordina lungo l'asse di maggiore estensione
        ranges = points.max(axis=0) - points.min(axis=0)
        main_dim = np.argmax(ranges)
        ordered_pts = points[np.argsort(points[:, main_dim])]

        # vettori tra punti consecutivi
        directions = np.diff(ordered_pts, axis=0)
        norms = np.linalg.norm(directions, axis=1)
        directions = directions[norms > 0] / norms[norms > 0][:, None]

        if len(directions) < 2:
            return 0.0

        cosines = np.einsum('ij,ij->i', directions[:-1], directions[1:])
        cosines = np.clip(cosines, -1.0, 1.0)
        curvature = 1 - np.mean(np.abs(cosines))
        return float(curvature)

    def _get_main_axis(self, points, center):
          # calcola l'asse principale. Usando PCA per trovare la direzione di massima varianza dei punti, cioè, l'asse principale del ramo
        _, _, vt = np.linalg.svd(points - center)
        return vt[0]

    def _get_center(self, points):
        return points.mean(axis=0)

    def _compute_length_and_diameter_along_curve(self, points, main_axis):
        # Calcolo del centro
        center = points.mean(axis=0)

        # PROIEZIONE sull'asse principale (ordinamento molto più robusto)
        t = (points - center) @ main_axis
        ordered_pts = points[np.argsort(t)]

        # LUNGHEZZA a spezzata
        diffs = np.diff(ordered_pts, axis=0)
        length = np.sum(np.linalg.norm(diffs, axis=1))

        # DIAMETRO robusto (usa la mediana invece del max)
        diffs_centered = points - center
        dist_perp = np.linalg.norm(np.cross(diffs_centered, main_axis), axis=1)
        diameter = self.diameter_scale * np.median(dist_perp)

        return float(length), float(diameter)

    def _compute_length_and_diameter_linear_pca(self, points, main_axis, center):
        # Lunghezza PCA (la lasciamo invariata)
        proj = (points - center) @ main_axis
        length = proj.max() - proj.min()

        # DIAMETRO robusto (mediana invece del max)
        diffs = points - center
        dist_perp = np.linalg.norm(np.cross(diffs, main_axis), axis=1)
        diameter = self.diameter_scale * np.median(dist_perp)

        return float(length), float(diameter)

    def _estimate_age(self, length, diameter):
        # Modello più stabile e realistico
        age = self.age_factor * np.log(1 + 10 * diameter) + 0.1 * self.length_factor * length
        return float(age)

    def _estimate_number_of_buds(self, length, diameter, curvature):
        # Densità media: 7 gemme per metro
        base_density = 7.0

        # Vigore basato sul diametro
        vigor = 1 + 0.3 * (diameter / max(0.4, diameter))

        # Penalità: rami molto curvi hanno meno gemme utili
        curvature_penalty = max(0.1, 1 - curvature)

        buds = length * base_density * vigor * curvature_penalty
        return float(buds)

    def compute_branch_metrics(self, branch_points):
        """
        Calcola lunghezza e diametro di un ramo usando Open3D.
        - Lunghezza: distanza massima lungo la curvatura (asse principale)
        - Diametro: distanza massima perpendicolare all'asse
        """
        pts = self._clean_branch_points(branch_points)

        if len(pts) < self.min_points_branch:
            return{
                "length": 0.0,
                "diameter": 0.0,
                "age": 0.0,
                "num_buds": 0.0,
                "curvature": 0.0,
                "center": np.zeros(3),
                "main_axis": np.zeros(3)
            }

        curvature = self._estimate_curvature(pts)
        center = self._get_center(pts)
        main_axis = self._get_main_axis(pts,center)

        if curvature >= self.curvature_threshold:
            '''curvature algorithm'''
            length, diameter = self._compute_length_and_diameter_along_curve(pts, main_axis)
        else:
            '''PCA algorithm for linear'''
            length, diameter = self._compute_length_and_diameter_linear_pca(pts, main_axis, center)

        age = self._estimate_age(length, diameter)
        num_buds = self._estimate_number_of_buds(length, diameter, curvature)

        return {"length" : float(length),
                "diameter" : float(diameter),
                "age" : float(age),
                "num_buds": float(num_buds),
                "curvature": float(curvature),
                "center": center.tolist(),
                "main_axis": main_axis.tolist()}

    def calculate_new_parameters(self, parameters_feedback):
        """
        Aggiorna i parametri dell'estimatore in base al feedback.
        parameters_feedback: dict con chiavi già tradotte e valori numerici (-1,0,1)
        """
        print("Feedback ricevuto per aggiornamento parametri:", parameters_feedback)

        # coefficiente di aggiornamento (quanto modificare i parametri)
        learning_rate = 0.05

        for key, delta in parameters_feedback.items():
            if hasattr(self, key):
                current_value = getattr(self, key)
                if current_value is not None:
                    # aggiorna il parametro moltiplicando per un piccolo delta relativo
                    new_value = current_value * (1 + delta * learning_rate)
                    # limiti ragionevoli per evitare valori negativi o eccessivi
                    if isinstance(current_value, (int, float)):
                        new_value = max(0.0, new_value)
                    setattr(self, key, new_value)

        # Scrive i nuovi parametri su file
        self.__write_params_on_file(use_old=False)
