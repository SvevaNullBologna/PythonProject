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
        self.curvature_threshold = 0.1

        self.diameter_scale = 2

        self.age_factor = 25.0
        self.length_factor = 2.5
        self.bud_length_factor = 15.0
        self.bud_curvature_factor = 0.8

        # if file does not exist, create branch_parameters_old and write data -> starting point
        self.old_param_file = Path("branch_parameters_old.json")
        self.new_param_file = Path("branch_parameters_new.json")
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
                self.__read_params_on_file(use_old=False)
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

    def __promote_new_weights(self):
        if not self.new_param_file.exists() or (os.stat(self.new_param_file).st_size == 0) :
            print("no new parameters file found to promote")
        else:
            shutil.move(self.new_param_file, self.old_param_file)
            print(f"new parameters promoted to old")


    def evolve_parameters(self):
        pass

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
        #lunghezza lungo la curva
        ranges = points.max(axis=0) - points.min(axis=0)
        main_dim = np.argmax(ranges)
        ordered_pts = points[np.argsort(points[:, main_dim])]
        diffs = np.diff(ordered_pts, axis=0)
        length = np.sum(np.linalg.norm(diffs, axis=1))

        #diametro rispetto al centro medio
        center = points.mean(axis=0)
        cross_prod = np.linalg.norm(np.cross(points - center, main_axis), axis=1)
        diameter = self.diameter_scale * cross_prod.max()

        return length, diameter


    def _compute_length_and_diameter_linear_pca(self,points, main_axis, center):
        proj = (points - center) @ main_axis  # proiettiamo tutti i punti sull'asse principale e prendo la distanza max lungo tale asse per la lunghezza
        length = proj.max() - proj.min()

        diffs = points - center
        cross_prod = np.linalg.norm(np.cross(diffs, main_axis),axis=1)  # calcolo la distanza perpendicolare max dei punti all'asse principale
        diameter = self.diameter_scale * cross_prod.max()

        return length, diameter


    def _estimate_age (self, length, diameter):
        return float(self.age_factor * diameter + self.length_factor * length)

    def _estimate_number_of_buds(self,length, curvature):
        return float(self.bud_length_factor * length + self.bud_curvature_factor * curvature * 100)

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
        num_buds = self._estimate_number_of_buds(length, curvature)

        return {"length" : float(length),
                "diameter" : float(diameter),
                "age" : float(age),
                "num_buds": float(num_buds),
                "curvature": float(curvature),
                "center": center.tolist(),
                "main_axis": main_axis.tolist()}

"""
    for test reasons
    
def test_branch_estimator():
    print("\n=== Testing BranchEstimator ===")
    be = BranchEstimator()
    print("Parameters loaded:")
    for k, v in be.__dict__.items():
        if not k.startswith("_"):
            print(f"  {k}: {v}")

if __name__ == "__main__":
    test_branch_estimator()

"""