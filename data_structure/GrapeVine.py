from pathlib import Path
import numpy as np
from sklearn.neighbors import NearestNeighbors

class Grapevine:
    def __init__(self):
        self.basefolder = None
        self.elements = []

    '''
        def load_grape_vine(self,basefolder):
            self.basefolder = Path(basefolder/"dataset")
            #find
    '''
    class Branch:
        def __init__(self, classTitle, length, diameter, age, num_buds, curvature, center, main_axis,numPoints, points):
            self.classTitle = classTitle
            self.length = length
            self.diameter = diameter
            self.age = age
            self.num_buds = num_buds
            self.curvature = curvature
            self.center = center
            self.main_axis = main_axis
            self.numPoints = numPoints
            self.points = points



