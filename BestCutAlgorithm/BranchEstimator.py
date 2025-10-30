import open3d as o3d #per leggere i pointcloud
import numpy as np


class BranchEstimator:
    def __init__(self):
        pass

    def _clean_branch_points(self, branch_points, outlier_radius=None, nb_points = 10 ,voxel_size=0.001):
        branch_pcd = o3d.geometry.PointCloud()
        branch_pcd.points = o3d.utility.Vector3dVector(branch_points)

        if outlier_radius is not None:  # nel caso in cui si aggiunge un filtro outlier per ridurre ulteriormente il rumore
            branch_pcd, _ = branch_pcd.remove_radius_outlier(nb_points=nb_points, radius=outlier_radius)

        branch_pcd = branch_pcd.voxel_down_sample(voxel_size=voxel_size)  # rimozione rumore e densità. Elimina punti ridondanti senza cambiare forma.
        return np.asarray(branch_pcd.points)

    def _estimate_curvature(self, points, min_number_points=3):
        if len(points) < min_number_points:
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

    def _compute_length_and_diameter_along_curve(self, points, diameter_scale=2):
        #lunghezza lungo la curva
        ranges = points.max(axis=0) - points.min(axis=0)
        main_dim = np.argmax(ranges)
        ordered_pts = points[np.argsort(points[:, main_dim])]
        diffs = np.diff(ordered_pts, axis=0)
        length = np.sum(np.linalg.norm(diffs, axis=1))

        #diametro rispetto al centro medio
        center = points.mean(axis=0)
        cross_prod = np.linalg.norm(np.cross(points - center, np.array([1, 0, 0])), axis=1)
        diameter = diameter_scale * cross_prod.max()

        return length, diameter

    def _compute_length_and_diameter_linear_pca(self,points, diameter_scale = 2):
        center = points.mean(axis=0)  # calcola l'asse principale. Usando PCA per trovare la direzione di massima varianza dei punti, cioè, l'asse principale del ramo
        _, _, vt = np.linalg.svd(points - center)
        main_axis = vt[0]

        proj = (points - center) @ main_axis  # proiettiam tutti i punti sull'asse principale e prendo la distanza max lungo tale asse per la lunghezza
        length = proj.max() - proj.min()

        diffs = points - center
        cross_prod = np.linalg.norm(np.cross(diffs, main_axis),axis=1)  # calcolo la distanza perpendicolare max dei punti all'asse principale
        diameter = diameter_scale * cross_prod.max()

        return length, diameter


    def compute_branch_metrics(self, branch_points, voxel_size = 0.001, min_points_branch=3, diameter_scale = 2, curvature_threshold=0.1, outlier_radius=None,  nb_points=10):
        """
        Calcola lunghezza e diametro di un ramo usando Open3D.
        - Lunghezza: distanza massima lungo la curvatura (asse principale)
        - Diametro: distanza massima perpendicolare all'asse
        """

        pts = self._clean_branch_points(branch_points, outlier_radius, nb_points, voxel_size)
        curvature = self._estimate_curvature(pts, min_points_branch)
        if curvature >= curvature_threshold:
            '''curvature algorithm'''
            length, diameter = self._compute_length_and_diameter_along_curve(pts, diameter_scale)
            return float(length), float(diameter)
        else:
            '''PCA algorithm for linear'''
            length, diameter = self._compute_length_and_diameter_linear_pca(pts, diameter_scale)
            return float(length), float(diameter)


