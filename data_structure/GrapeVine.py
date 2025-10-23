from pathlib import Path
import numpy as np

class Grapevine:
    def __init__(self):
        self.basefolder = None

    '''
        def load_grape_vine(self,basefolder):
            self.basefolder = Path(basefolder/"dataset")
            #find
    '''
    class Branch:
        def __init__(self, father, name, object_key, coordinates):
            self.father = father
            self.name = name
            self.object_key = object_key
            self.coordinates = np.array(coordinates)
            self.num_points = len(coordinates)

            self.distance_to_trunk = None
            self.diameter = None
            self.age_estimate = None
            self.has_buds = None
            self.is_bud = False

        def compute_diameter(self):
            self.diameter = np.linalg.norm(self.coordinates.max(axis=0)) - self.coordinates.min(axis=0)

        def estimate_age(self, age_parameter):
            self.age_estimate = self.diameter * age_parameter

        def distance_from_trunk(self):
            if self.father is None :
                return 0
            else:
                return self.distance_from_trunk() + 1