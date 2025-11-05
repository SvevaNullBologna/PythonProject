from pathlib import Path
import json
from data_structure.Branch import Branch

class GrapeVine:
    def __init__(self):
        self.basefolder = None
        self.tree_elements = []

    def set_basefolder(self, basefolder):
        folder = Path(basefolder)/ "output"
        if basefolder and folder.is_dir():
            self.basefolder = folder
            print(f"basefolder: {self.basefolder}")
        else:
            print(f"errore folder : {basefolder}")

    def _retrieve_json_file_(self, filename: str):
        if not self.basefolder:
            return None
        json_path = self.basefolder / filename
        if json_path.is_file():
            return json_path
        else:
            print(f"nessun file trovato con quella data")
            return None

    def load_grapevine_from_file(self, filename: str):
        self.tree_elements.clear()

        json_file = self._retrieve_json_file_(filename)
        if not json_file:
            print(f"Errore, no json file: {filename}")
            return
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e :
            print(f"Errore nel parsing del JSON {json_file.name}: {e}")
            return

        branches = data.get("branches",[])

        for element in branches:
            branch = Branch(
                classTitle=element.get("classTitle", "Unknown"),
                length=element.get("length", None),
                diameter=element.get("diameter", None),
                age=element.get("age", None),
                num_buds=element.get("num_buds", None),
                curvature=element.get("curvature", None),
                center=element.get("center", []),
                main_axis=element.get("main_axis", []),
                numPoints=element.get("numPoints", 0),
                points=element.get("points", [])
            )
            self.tree_elements.append(branch)
        print(f"created grapevine from file {json_file.name}")

    def __str__(self):
        if not self.tree_elements:
            return "Grapevine vuota"
        return "\n".join(str(branch) for branch in self.tree_elements)




if __name__ == "__main__":
    g = GrapeVine()
    g.set_basefolder(r"C:\Users\Sveva\Desktop\Materiale")
    g.load_grapevine_from_file("dataset 2025-10-09 10-36-06_albero.json")
    print(g)