from pathlib import Path
import numpy as np
from sklearn.neighbors import NearestNeighbors

class Grapevine:
    def __init__(self):
        self.basefolder = None

    '''
        def load_grape_vine(self,basefolder):
            self.basefolder = Path(basefolder/"dataset")
            #find
    '''
    class Branch:
        def __init__(self, father, name, object_key, coordinates, age_parameter):
            self.father = father
            self.name = name
            self.object_key = object_key
            self.coordinates = np.array(coordinates)
            self.num_points = len(coordinates)

            self.distance_to_trunk = self.distance_from_trunk()
            self.length = 0
            self.diameter = self.compute_diameter()
            self.age_estimate = self.estimate_age(age_parameter)
            self.has_buds = 0
            self.is_bud = False

        def compute_diameter(self):
            return np.linalg.norm(self.coordinates.max(axis=0)) - self.coordinates.min(axis=0)

        def estimate_age(self, age_parameter):
            return self.diameter * age_parameter

        def distance_from_trunk(self):
            if self.father is None :
                return 0
            else:
                return self.father.distance_from_trunk() + 1

        def compute_length_of_branch(self):
            return



