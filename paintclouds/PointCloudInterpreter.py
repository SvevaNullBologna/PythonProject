import json

import open3d as o3d #per leggere i pointcloud
from pathlib import Path
import numpy as np


class PointCloudInterpreter:
    def __init__(self): #tutto questo è un safe-getting-source per sapere se ci sono problemi all'apertura del pointcloud. Ovviamente non copre tutto
        self.base = None
        self.pcd_path = None
        self.ann_path = None
        self.branch_table = None
        self.points = None

    def set_paths(self, basefolder):
        base = Path(basefolder)
        if not base.exists():
            print("base folder not found")
            return False

        pointcloud_folder = next(base.rglob("pointcloud"), None)
        if pointcloud_folder is None or not pointcloud_folder.exists():
            print("pointcloud folder not found")
            return False
        else:
            self.pcd_path = next(pointcloud_folder.glob("*.pcd"), None)

        ann_folder = next(base.rglob("ann"), None)
        if ann_folder is None or not ann_folder.exists():
            print("annotation folder not found")
            return False
        else:
            self.ann_path = next(ann_folder.glob("*.json"), None)  # salviamo il path

        if self.pcd_path and self.ann_path:
            self.load_pointclouds()
            self.group_points_by_branch()
            return True
        else:
            print("pcd_path e ann_path nulli")
            return False

    def load_pointclouds(self):
        pcd = o3d.io.read_point_cloud(Path(self.pcd_path)) #legge la point cloud
        self.points = np.asarray(pcd.points) #prende tutti i punti della pointcloud in ordine
        print(f"Loaded points")

    def group_points_by_branch(self):

        """
            il json è fatto così:
            {
                "description" : "",
                "key" : "mix di numeri e lettere minuscole",
                "tags" : [],
                "objects" : [ -> entità logiche annotate (Branch 1, Tree, ...) . Cosa stiamo etichettando
                    {
                        "key": "mix di numeri e lettere minuscole", -> identificatore univoco
                        "classTitle" : "Branch 1", -> tipo di ramo, tronco, ecc...
                        "tags" : [],
                        "labelerLogin" : "OresteGino",
                        "updatedAt" : "data",
                        "createdAt" : "data"
                    },
                    ... altri oggetti
                ]
                "figures": [ -> dove si trovano nella point cloud
                    {
                        "key": "mix di numeri e lettere minuscole",
                        "objectKey": "mix di numeri e lettere minuscole",
                        "geometryTime": "point_cloud",
                        "geometry": {
                            "indices": [
                                numero,
                                numero,
                                numero,
                                ...
                            ]
                        },
                        "labelerLogin" : "OresteGino",
                        "updatedAt" : "data",
                        "createdAt" : "data"
                    },
                    ... altre figure
                ]
            }

        """
        with open(self.ann_path,'r') as f: #apriamo in lettura le annotazioni
            ann_data = json.load(f)
            #separiamo gli oggetti dalle figure del json
            objects = ann_data.get("objects",[]) #ogni oggetto rappresenta un ramo
            figures = ann_data.get("figures",[]) #ogni figura è un gruppo di punti ed è associata ad un ramo tramite l'id

            #indicizzo le figure per object key: costruisco un dizionario che permetta di accedere velocemente alle figure associate a ciascun oggetto
            figure_map = {}
            for fig in figures:
                if fig.get("geometryType") == "point_cloud":
                    key = fig["objectKey"]
                    figure_map.setdefault(key,[]).append(fig)

            self.branch_table = {}
            for obj in objects:
                obj_key = obj["key"]
                if obj["classTitle"].startswith("Branch"):
                    all_indices = []
                    for fig in figure_map.get(obj_key,[]):
                        all_indices.extend(fig["geometry"]["indices"])

                    if all_indices:
                        unique_indices = sorted(set(all_indices))
                        self.branch_table[obj_key] = {
                            "classTitle": obj["classTitle"],
                            "points": self.points[unique_indices]
                        }

            print(f"Tabella dei rami creata con {len(self.branch_table)} voci.")

    def read_point_cloud(self, basefolder):
        if self.set_paths(basefolder):
            self.load_pointclouds()
            self.group_points_by_branch()
            return True
        else:
            print("error with loading a single point cloud")
            return False

    def print_branch_table(self):
        print(self.branch_table)

if __name__ == '__main__':
    interpreter = PointCloudInterpreter()
    interpreter.read_point_cloud(basefolder=r"C:\Users\Sveva\Desktop\Materiale")
    interpreter.print_branch_table()



