class Branch:
    def __init__(self, classTitle, length, diameter, age, num_buds, curvature, center, main_axis, numPoints, points):
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

    def __str__(self):
        return (
            f"Branch Class: {self.classTitle}\n"
            f"Length: {self.length}\n"
            f"Diameter: {self.diameter}\n"
            f"Age: {self.age}\n"
            f"Number of Buds: {self.num_buds}\n"
            f"Curvature: {self.curvature}\n"
            f"Center: {self.center}\n"
            f"Main Axis: {self.main_axis}\n"
            f"Number of Points: {self.numPoints}"
            "\n"
        )