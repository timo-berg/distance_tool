# TODO:
# 0. Set scale
# 1. Set reference landmark
# 2. Orient reference landmark
# 3. Set true landmark
# 4. Give id to true landmark
# 5. Create a participant with a given id
# 6. Select participant from list
# 7. Set estimated landmark
# 8. Give id to estimated landmark
# 9. Select corresponding true landmark for estimated landmark
# 10. Calculate distance between estimated landmark and true landmark
# 12. Calculate angle between reference landmark and true landmark
# 13. Calculate angle between reference landmark and estimated landmark
# 14. Set edge point
# 15. Select corresponding true landmark for edge point
# 16. Calculate distance between edge point and true landmark
# 17. Set ID for image
# 18. Save information to file



from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QGraphicsEllipseItem, QGraphicsLineItem, QComboBox, QInputDialog, QGraphicsPolygonItem
from PyQt6.QtGui import QPixmap, QPen, QColor, QBrush, QCursor, QPolygonF
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF
from abc import ABC, abstractmethod
from math import cos, sin, pi

class Point():
    def __init__(self,x: float, y: float, id: str, scene: QGraphicsScene):
        self.x = x
        self.y = y
        self.id = id
        self.scene = scene

        # Create visual marker
        ellipse = QGraphicsEllipseItem(x-5, y-5, 10, 10)
        ellipse.setBrush(QBrush(QColor('red')))
        ellipse.setPen(QPen(QColor('red')))
        ellipse.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.scene.addItem(ellipse)

        self.marker = ellipse
    
    # Remove marker from scene when object is deleted
    def __delattr__(self, __name: str) -> None:
        self.marker.scene().removeItem(self.marker)
        super().__delattr__(__name)

class TrueLandmark(Point):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene):
        super().__init__(x, y, id, scene)

class ReferenceLandmark(Point):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene, ref_x: float, ref_y: float):
        super().__init__(x, y, id, scene)
        self.ref_x = ref_x
        self.ref_y = ref_y

        # Draw an arrow pointing from the origin to the reference landmark
        line = QGraphicsLineItem(x, y, ref_x, ref_y)
        line.setPen(QPen(QColor('black')))
        self.scene.addItem(line)
        self.line = line

        # Draw the arrow head
        arrow_head = self.create_arrow_head(x, y, ref_x, ref_y)
        arrow = QGraphicsPolygonItem(arrow_head, line)
        arrow.setBrush(QBrush(QColor('black')))
        self.arrow = arrow

    # Remove arrow from scene when object is deleted
    def __delattr__(self, __name: str) -> None:
        self.line.scene().removeItem(self.line)
        self.arrow.scene().removeItem(self.arrow)
        super().__delattr__(__name)

    def create_arrow_head(self, x, y, ref_x, ref_y):
        line = QLineF(x, y, ref_x, ref_y)
        angle = line.angle()  # Get the angle of the line
        arrow_size = 10  # Set the size of the arrow head

        # Calculate the points of the arrow head
        p1 = QPointF(ref_x, ref_y)
        p2 = QPointF(ref_x + arrow_size * cos((angle + 150) * pi / 180),
                    ref_y - arrow_size * sin((angle + 150) * pi / 180))  # Flip y-coordinate
        p3 = QPointF(ref_x + arrow_size * cos((angle - 150) * pi / 180),
                    ref_y - arrow_size * sin((angle - 150) * pi / 180))  # Flip y-coordinate

        # Create a QPolygonF from the points
        arrow_head = QPolygonF([p1, p2, p3])

        return arrow_head   

class EstimatedPoint(Point):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene, true_x: float, true_y: float):
        super().__init__(x, y, id, scene)
        self.true_x = true_x
        self.true_y = true_y

        # Create line between true and estimated landmark
        line = QGraphicsLineItem(x, y, true_x, true_y)
        line.setPen(QPen(QColor('blue')))
        line.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.scene.addItem(line)

        self.line = line
    
    # Remove line from scene when object is deleted
    def __delattr__(self, __name: str) -> None:
        self.line.scene().removeItem(self.line)
        super().__delattr__(__name)

    # Calculate euclidean error between true and estimated landmark
    def getError(self):
        return (self.x - self.true_x)**2 + (self.y - self.true_y)**2
    
class EstimatedLandmark(EstimatedPoint):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene, true_x: float, true_y: float):
        super().__init__(x, y, id, scene, true_x, true_y)

class EdgePoint(EstimatedPoint):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene, true_x: float, true_y: float):
        super().__init__(x, y, id, scene, true_x, true_y)



class Participant():
    def __init__(self, id: str):
        self.id = id
        self.estimates = []

    def addEstimate(self, estimate: EstimatedLandmark):
        self.estimates.append(estimate)

    def removeEstimate(self, estimate: EstimatedLandmark):
        self.estimates.remove(estimate)
        del estimate



class Tool(ABC):
    def __init__(self, viewer):
        self.viewer = viewer

    @abstractmethod
    def mousePressEvent(self, event):
        pass

class TrueMarkingTool(Tool):
    def mousePressEvent(self, event):
        point = self.viewer.mapToScene(event.pos())
        id, ok = QInputDialog.getText(self.viewer, 'True Landmark', 'Enter ID for true landmark')
        if ok:
            TrueLandmark(point.x(), point.y(), id, self.viewer.scene())

class ReferenceMarkingTool(Tool):
    def __init__(self, viewer):
        super().__init__(viewer)
        self.firstPoint = None
        self.tempMarker = None


    def mousePressEvent(self, event):
        # Select a the position of a reference landmark if
        if self.firstPoint is None:
            # Set first point
            self.firstPoint = self.viewer.mapToScene(event.pos())
            # Create a temporary marker
            ellipse = QGraphicsEllipseItem(self.firstPoint.x()-5, self.firstPoint.y()-5, 10, 10)
            ellipse.setBrush(QBrush(QColor('red')))
            ellipse.setPen(QPen(QColor('red')))
            self.viewer.scene().addItem(ellipse)
            self.tempMarker = ellipse
        
        # Select the orientation of the reference landmark
        else:
            point = self.viewer.mapToScene(event.pos())
            id, ok = QInputDialog.getText(self.viewer, 'Reference Landmark', 'Enter ID for reference landmark')
            if ok:
                ReferenceLandmark(self.firstPoint.x(), self.firstPoint.y(), id, self.viewer.scene(), point.x(), point.y())

            # Remove temporary marker
            self.viewer.scene().removeItem(self.tempMarker)
            self.tempMarker = None
            self.firstPoint = None

        


class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setScene(QGraphicsScene(self))
        self.currentTool = None

    def loadImage(self, filename):
        pixmap = QPixmap(filename)
        self.scene().clear()
        self.scene().addPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def setTool(self, tool):
        self.currentTool = tool

    def mousePressEvent(self, event):
        if self.currentTool:
            self.currentTool.mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def enterEvent(self, event):
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.CrossCursor))

    def leaveEvent(self, event):
        QApplication.restoreOverrideCursor()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.resize(800, 600)
        self.viewer = ImageViewer()
        self.loadBtn = QPushButton('Load Image')
        # Participant stuff
        self.createParticipantBtn = QPushButton('Create Participant')
        self.participantSelector = QComboBox()
        self.participants = []

        # Marking tools
        self.toolSelector = QComboBox()
        self.toolSelector.addItem('None')
        self.referenceTool = ReferenceMarkingTool(self.viewer)
        self.toolSelector.addItem('Set Reference')
        
        self.toolSelector.setCurrentIndex(0)


        # Connect UI elements to functions
        self.loadBtn.clicked.connect(self.loadImage)
        self.createParticipantBtn.clicked.connect(self.createParticipant)
        self.toolSelector.currentTextChanged.connect(self.onToolSelectionChanged)

        layout = QVBoxLayout()
        layout.addWidget(self.loadBtn)
        layout.addWidget(self.viewer)
        layout.addWidget(self.createParticipantBtn)
        layout.addWidget(self.participantSelector)
        layout.addWidget(self.toolSelector)
        

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def loadImage(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Image", "", "Image Files (*.png *.jpg *.bmp)")
        if filename:
            self.viewer.loadImage(filename)

    # Participant handling
    # Create participant and add to participant selector
    def createParticipant(self):
        id, ok = QInputDialog.getText(self, 'Create Participant', 'Enter participant ID:')
        if ok:
            self.participantSelector.addItem(id)
            self.participantSelector.setCurrentIndex(self.participantSelector.count()-1)
            self.participants.append(Participant(id))

    # Get currently selected participant
    def getCurrentParticipant(self):
        return self.participants[self.participantSelector.currentIndex()]
    
    # Tool handling
    def onToolSelectionChanged(self, text):
        if text == 'None':
            self.viewer.setTool(None)
        elif text == 'Set Reference':
            self.viewer.setTool(self.referenceTool)

    

        
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
