import json

import open3d as o3d #per leggere i pointcloud
from pathlib import Path
import numpy as np


class BranchEstimator:
    def __init__(self):
        #
    def clean_branch_points(self, branch_points, outlier_radius=None, nb_points = 10 ,voxel_size=0.001):
        branch_pcd = o3d.geometry.PointCloud()
        branch_pcd.points = o3d.utility.Vector3dVector(branch_points)

        if outlier_radius is not None:  # nel caso in cui si aggiunge un filtro outlier per ridurre ulteriormente il rumore
            branch_pcd, _ = branch_pcd.remove_radius_outlier(nb_points=nb_points, outlier_radius=outlier_radius)

        branch_pcd = branch_pcd.voxel_down_sample(
            voxel_size=voxel_size)  # rimozione rumore e densità. Elimina punti ridondanti senza cambiare forma.

        pts = np.asarray(branch_pcd.points)

    def compute_branch_metrics(self, branch_points, voxel_size = 0.001, min_points_branch=5, diameter_scale = 2, curvature_threshold=0.1, outlier_radius=None,  nb_points=10):
        """
        Calcola lunghezza e diametro di un ramo usando Open3D.
        - Lunghezza: distanza massima lungo la curvatura (asse principale)
        - Diametro: distanza massima perpendicolare all'asse
        """
        if len(branch_points) < min_points_branch:
            return 0.0, 0.0

        branch_pcd = o3d.geometry.PointCloud()
        branch_pcd.points = o3d.utility.Vector3dVector(branch_points)

        if outlier_radius is not None: #nel caso in cui si aggiunge un filtro outlier per ridurre ulteriormente il rumore
            branch_pcd, _ = branch_pcd.remove_radius_outlier(nb_points=nb_points, outlier_radius= outlier_radius)

        branch_pcd = branch_pcd.voxel_down_sample(voxel_size=voxel_size)  #rimozione rumore e densità. Elimina punti ridondanti senza cambiare forma.

        pts = np.asarray(branch_pcd.points)
        center = pts.mean(axis=0) #calcola l'asse principale. Usando PCA per trovare la direzione di massima varianza dei punti, cioè, l'asse principale del ramo
        _, _, Vt = np.linalg.svd(pts - center)
        main_axis = Vt[0]

        proj = (pts - center) @ main_axis #proiettiam tutti i punti sull'asse principale e prendo la distanza max lungo tale asse per la lunghezza
        length = proj.max() - proj.min()

        diffs = pts - center
        cross_prod = np.linalg.norm(np.cross(diffs, main_axis), axis=1) #calcolo la distanza perpendicolare max dei punti all'asse principale
        diameter = diameter_scale * cross_prod.max()

        return float(length), float(diameter)

    def estimate_curvature_pre_pca(self, branch_points, min_number_points=3):
        pts = np.asarray(branch_points)
        if len(pts) < min_number_points:
            return 0.0