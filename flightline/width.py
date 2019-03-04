# Module that calculates the minimum and maximum widths between the edges of a polygon


class Line(object):
    """Represents a simple line feature"""

    def __init__(self, start_point, end_point):
        """Initiates a simple line feature
        Parameters
        ----------
        start_point : list<float, float>
        end_point : list<float, float>
        """

        self.x1 = start_point[0]
        self.y1 = start_point[1]
        self.x2 = end_point[0]
        self.y2 = end_point[1]

    @property
    def mid_point(self):
        """Midpoint coordinate of the line"""
        return [self.x1 + ((self.x2 - self.x1)/2), self.y1 + ((self.y2 - self.y2)/2)]
    @property
    def gradient(self):
        """Returns the gradient in y = mx + c formula"""
        return (self.y2 - self.y1) / (self.x2 - self.x1)

    @property
    def perpindicular_x_axis(self):
        """
        Returns the value that a perpindicular line at the midpoint
        crosses the x axis
        """
