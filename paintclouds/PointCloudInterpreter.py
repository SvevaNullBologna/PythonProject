import json

import open3d as o3d #per leggere i pointcloud
from pathlib import Path
import numpy as np


class PointCloudInterpreter:
    def __init__(self): #tutto questo è un safe-getting-source per sapere se ci sono problemi all'apertura del pointcloud. Ovviamente non copre tutto
        self.base = None
        self.datasets_path = None
        self.current_dataset_index = 0
        self.current_dataset_name = None
        self.pcd_path = None
        self.ann_path = None
        self.branch_table = None
        self.points = None
        self.output_folder = None
        self.output_file = None
        self.retrieved_data = None

    def set_base_path(self, basefolder): #importa la cartella principale
        base = Path(basefolder)
        if not base.exists():
            print("base folder not found")
            return False
        else :
            #crea file txt dove mettere i risultati grezzi
            self.base = base
            self.output_folder = self.base/"output"
            self.output_folder.mkdir(exist_ok=True)
            # trova tutte le sottocartelle che iniziano con il nome dataset
            self.datasets_path = sorted([f for f in self.base.rglob("dataset*") if f.is_dir()]) #le salva in self.datasets_path
            if not self.datasets_path: #se non ci sono datasets, dà errore
                print("dataset's folder not found")
                return False
            else: #carica il primo dataset
                print(f"Found {len(self.datasets_path)} datasets")
                self.current_dataset_index = 0
                return self.load_current_dataset()

    def load_current_dataset(self): #prende il dataset corrente usando l'indice
        if self.current_dataset_index>= len(self.datasets_path):
            print("no more datasets to load")
            return False
        else:
            dataset = self.datasets_path[self.current_dataset_index]
            self.current_dataset_name = dataset.name

            self.pcd_path = next((dataset/"pointcloud").glob("*.pcd"), None)
            self.ann_path = next((dataset / "ann").glob("*.json"), None)

            if not self.pcd_path:
                print("pointcloud folder not found")
                return False

            if not self.ann_path:
                print("annotation folder not found")
                return False

            if self.pcd_path and self.ann_path:
                self.load_pointclouds()
                self.group_points_by_branch()
                print(f"Loaded {self.current_dataset_name}")
                return True
            else:
                print("missing files in pcd_path or ann_path ")
                return False

    def update_pointer(self):
        self.current_dataset_index += 1
        return self.load_current_dataset()

    def load_pointclouds(self):
        pcd = o3d.io.read_point_cloud(Path(self.pcd_path)) #legge la point cloud
        self.points = np.asarray(pcd.points) #prende tutti i punti della pointcloud in ordine
        print(f"Loaded {len(self.points)} points from {self.pcd_path.name}")

    def group_points_by_branch(self):
        with open(self.ann_path, 'r') as f:
            ann_data = json.load(f)

        objects = ann_data.get("objects", [])
        figures = ann_data.get("figures", [])

        # mappa objectKey -> figure[]
        figure_map = {}
        for fig in figures:
            if fig.get("geometryType") == "point_cloud":
                key = fig["objectKey"]
                figure_map.setdefault(key, []).append(fig)

        self.branch_table = {}
        branches = []

        for obj in objects:
            obj_key = obj["key"]
            class_title = obj["classTitle"]

            all_indices = []
            for fig in figure_map.get(obj_key, []):
                all_indices.extend(fig["geometry"]["indices"])

            if all_indices:
                unique_indices = sorted(set(all_indices))
                branch_points = self.points[unique_indices]

                length, diameter = self.compute_branch_metrics(branch_points)

                branch_info = {
                    "classTitle": class_title,
                    "length": length,
                    "diameter": diameter,
                    "numPoints": len(branch_points),
                    "points": [[float(pt[0]), float(pt[1]), float(pt[2])] for pt in branch_points]
                }

                branches.append(branch_info)
                self.branch_table[obj_key] = branch_info
        self.retrieved_data = {
            "dataset": self.current_dataset_name,
            "branches": branches
        }

    def read_point_cloud(self, basefolder):
        if self.set_base_path(basefolder):
            return True
        else:
            print("error with loading a single point cloud")
            return False

    def compute_branch_metrics(self, branch_points):
        """
        Calcola lunghezza e diametro di un ramo usando Open3D.
        - Lunghezza: distanza massima lungo la curvatura (asse principale)
        - Diametro: distanza massima perpendicolare all'asse
        """
        if len(branch_points) < 2:
            return 0.0, 0.0

        branch_pcd = o3d.geometry.PointCloud()
        branch_pcd.points = o3d.utility.Vector3dVector(branch_points)
        branch_pcd = branch_pcd.voxel_down_sample(voxel_size=0.001)

        pts = np.asarray(branch_pcd.points)
        center = pts.mean(axis=0)
        _, _, Vt = np.linalg.svd(pts - center)
        main_axis = Vt[0]

        proj = (pts - center) @ main_axis
        length = proj.max() - proj.min()

        diffs = pts - center
        cross_prod = np.linalg.norm(np.cross(diffs, main_axis), axis=1)
        diameter = 2 * cross_prod.max()

        return float(length), float(diameter)

    def print_branch_table(self):
        print(self.branch_table)

    def write_json_file(self, json_data):
        if json_data is not None:
            json_output_file = self.output_folder / f"{self.current_dataset_name}_albero.json"
            with open(json_output_file, "w") as out_json:
                json.dump(json_data, out_json, indent=2)
        print(f"Tabella con {len(self.branch_table)} rami creata.")
        print(f"File salvato in: {json_output_file}")

if __name__ == '__main__':
    interpreter = PointCloudInterpreter()
    interpreter.read_point_cloud(basefolder=r"C:\Users\Sveva\Desktop\Materiale")
    interpreter.write_json_file(interpreter.retrieved_data)


