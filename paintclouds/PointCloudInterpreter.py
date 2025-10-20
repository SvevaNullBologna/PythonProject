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

        with open(self.ann_path, 'r') as f:
            ann_data = json.load(f)

            objects = ann_data.get("objects", [])
            figures = ann_data.get("figures", [])

            # mappa bjectKey -> figure[]
            figure_map = {}
            for fig in figures:
                if fig.get("geometryType") == "point_cloud":
                    key = fig["objectKey"]
                    figure_map.setdefault(key, []).append(fig)

            self.branch_table = {}

            #file di output per questo dataset
            txt_output_file = self.output_folder / f"{self.current_dataset_name}_albero.txt"
            with open(txt_output_file, "w") as out:
                # intestazione dataset
                out.write(f'dataset ="{self.current_dataset_name}" {{\n\n')

                for obj in objects:
                    obj_key = obj["key"]
                    class_title = obj["classTitle"]

                    all_indices = []
                    for fig in figure_map.get(obj_key, []):
                        all_indices.extend(fig["geometry"]["indices"])

                    if all_indices:
                        unique_indices = sorted(set(all_indices))
                        branch_points = self.points[unique_indices]

                        self.branch_table[obj_key] = {
                            "classTitle": class_title,
                            "points": branch_points
                        }

                        # Scrittura in formato leggibile
                        out.write(f'  branch "{class_title}" : {{\n')
                        for pt in branch_points:
                            out.write(f'    ({pt[0]:.5f}, {pt[1]:.5f}, {pt[2]:.5f});\n')
                        out.write(f'    # punti: {len(branch_points)}\n')
                        out.write(f'  }}\n\n')

                out.write('}\n')

        print(f"Tabella con {len(self.branch_table)} rami creata.")
        print(f"File salvato in: {txt_output_file}")

    def read_point_cloud(self, basefolder):
        if self.set_base_path(basefolder):
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



