from PyQt6.QtCore import QObject, QPointF, QLineF, Qt
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPolygonF
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsPolygonItem
from math import cos, sin, pi


class Point(QObject):
    def __init__(self, x: float, y: float, color: str, id: str, scene: QGraphicsScene):
        self.x = x
        self.y = y
        self.id = id
        self.scene = scene

        # Create visual marker
        ellipse = QGraphicsEllipseItem(x-5, y-5, 10, 10)
        ellipse.setBrush(QBrush(QColor(color)))
        ellipse.setPen(QPen(QColor(color)))
        ellipse.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.scene.addItem(ellipse)

        # Create label
        label = QGraphicsTextItem(id, ellipse)
        label.setDefaultTextColor(QColor('black'))
        label.setFont(QFont('Arial', 10))
        label.setPos(x+5, y+5)
        self.scene.addItem(label)

        self.marker = ellipse

class TrueLandmark(Point):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene):
        super().__init__(x, y, '#77dd77', id, scene)

class ReferenceLandmark(Point):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene, dir_x: float, dir_y: float):
        super().__init__(x, y, '#a1caf1', id, scene)
        self.dir_x = dir_x
        self.dir_y = dir_y

        # Draw an arrow pointing from the origin to the reference landmark
        line = QGraphicsLineItem(x, y, dir_x, dir_y, self.marker)
        line.setPen(QPen(QColor('black')))
        line.setZValue(-1)
        self.scene.addItem(line)
        self.line = line

        # Draw the arrow head
        arrow_head = self.create_arrow_head(x, y, dir_x, dir_y)
        arrow = QGraphicsPolygonItem(arrow_head, line)
        arrow.setBrush(QBrush(QColor('black')))
        arrow.setZValue(-1)
        self.arrow = arrow

    def create_arrow_head(self, x, y, dir_x, dir_y):
        line = QLineF(x, y, dir_x, dir_y)
        angle = line.angle()  # Get the angle of the line
        arrow_size = 10  # Set the size of the arrow head

        # Calculate the points of the arrow head
        p1 = QPointF(dir_x, dir_y)
        p2 = QPointF(dir_x + arrow_size * cos((angle + 150) * pi / 180),
                    dir_y - arrow_size * sin((angle + 150) * pi / 180))  # Flip y-coordinate
        p3 = QPointF(dir_x + arrow_size * cos((angle - 150) * pi / 180),
                    dir_y - arrow_size * sin((angle - 150) * pi / 180))  # Flip y-coordinate

        # Create a QPolygonF from the points
        arrow_head = QPolygonF([p1, p2, p3])

        return arrow_head   

class EstimatedPoint(Point):
    def __init__(self, x: float, y: float, color: str, id: str, scene: QGraphicsScene, true_x: float, true_y: float, participant: str):
        super().__init__(x, y, color, id, scene)
        self.true_x = true_x
        self.true_y = true_y

        # Create line between true and estimated landmark
        line = QGraphicsLineItem(x, y, true_x, true_y, self.marker)
        line.setPen(QPen(QColor('black')))
        line.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)
        line.setZValue(-1)
        self.scene.addItem(line)

        self.line = line

        self.participant = participant

    
    # Remove line from scene when object is deleted
    def __delattr__(self, __name: str) -> None:
        self.line.scene().removeItem(self.line)
        super().__delattr__(__name)

    # Calculate euclidean error between true and estimated landmark
    def getDistanceError(self):
        return ((self.x - self.true_x)**2 + (self.y - self.true_y)**2)**0.5

    # Calculate angle error between reference and estimated landmark
    def getAngleError(self, ref_x: float, ref_y: float, dir_x: float, dir_y: float):
        estimate_line = QLineF(self.x, self.y, ref_x, ref_y)
        reference_line = QLineF(ref_x, ref_y, dir_x, dir_y)
        
        angle = estimate_line.angleTo(reference_line)
        # Make sure angle is between 0 and 180 degrees
        if angle < 0:
            angle += 360
        if angle > 180:
            angle = 360 - angle

        return angle
    
class EstimatedLandmark(EstimatedPoint):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene, true_x: float, true_y: float, participant: str):
        super().__init__(x, y, '#fd7c6e',id, scene, true_x, true_y, participant)

class EdgePoint(EstimatedPoint):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene, true_x: float, true_y: float, participant: str):
        super().__init__(x, y, '#b39eb5', id, scene, true_x, true_y, participant)

