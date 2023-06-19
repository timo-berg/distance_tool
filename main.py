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


from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QGraphicsTextItem
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QGraphicsEllipseItem, QGraphicsLineItem, QComboBox, QInputDialog, QGraphicsPolygonItem
from PyQt6.QtGui import QPixmap, QPen, QColor, QBrush, QCursor, QPolygonF, QFont, QTransform
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF, pyqtSignal, QObject
from abc import ABC, abstractmethod
from math import cos, sin, pi
import copy

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
    
    # Remove marker from scene when object is deleted
    def __delattr__(self, __name: str) -> None:
        self.marker.scene().removeItem(self.marker)
        super().__delattr__(__name)

class TrueLandmark(Point):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene):
        super().__init__(x, y, '#77dd77', id, scene)

class ReferenceLandmark(Point):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene, ref_x: float, ref_y: float):
        super().__init__(x, y, '#a1caf1', id, scene)
        self.ref_x = ref_x
        self.ref_y = ref_y

        # Draw an arrow pointing from the origin to the reference landmark
        line = QGraphicsLineItem(x, y, ref_x, ref_y)
        line.setPen(QPen(QColor('black')))
        line.setZValue(-1)
        self.scene.addItem(line)
        self.line = line

        # Draw the arrow head
        arrow_head = self.create_arrow_head(x, y, ref_x, ref_y)
        arrow = QGraphicsPolygonItem(arrow_head, line)
        arrow.setBrush(QBrush(QColor('black')))
        arrow.setZValue(-1)
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
    def __init__(self, x: float, y: float, color: str, id: str, scene: QGraphicsScene, true_x: float, true_y: float, participant: str):
        super().__init__(x, y, color, id, scene)
        self.true_x = true_x
        self.true_y = true_y

        # Create line between true and estimated landmark
        line = QGraphicsLineItem(x, y, true_x, true_y)
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
    def getError(self):
        return (self.x - self.true_x)**2 + (self.y - self.true_y)**2
    
class EstimatedLandmark(EstimatedPoint):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene, true_x: float, true_y: float, participant: str):
        super().__init__(x, y, '#fd7c6e',id, scene, true_x, true_y, participant)

class EdgePoint(EstimatedPoint):
    def __init__(self, x: float, y: float, id: str, scene: QGraphicsScene, true_x: float, true_y: float, participant: str):
        super().__init__(x, y, '#b39eb5', id, scene, true_x, true_y, participant)



class Participant():
    def __init__(self, id: str):
        self.id = id
        self.estimates = []

    def addEstimate(self, estimate: EstimatedLandmark):
        self.estimates.append(estimate)

    def removeEstimate(self, estimate: EstimatedLandmark):
        self.estimates.remove(estimate)
        del estimate



class SignalHolder(QObject):
    signal = pyqtSignal(object)

class Tool(ABC):
    def __init__(self, viewer):
        self.viewer = viewer

    @abstractmethod
    def mousePressEvent(self, event):
        pass

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
            ellipse.setBrush(QBrush(QColor('#a1caf1')))
            ellipse.setPen(QPen(QColor('#a1caf1')))
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

class TrueLandmarkTool(Tool):

    def __init__(self, viewer):
        super().__init__(viewer)
        self.signalEmitter = SignalHolder()

    def mousePressEvent(self, event):
        point = self.viewer.mapToScene(event.pos())
        id, ok = QInputDialog.getText(self.viewer, 'True Landmark', 'Enter ID for true landmark')
        if ok:
            true_landmark = TrueLandmark(point.x(), point.y(), id, self.viewer.scene())
            self.signalEmitter.signal.emit(true_landmark)

class EstimatedPointTool(Tool):
    def __init__(self, viewer, true_landmarks, participantSelector):
        super().__init__(viewer)
        self.true_landmarks = true_landmarks
        self.participantSelector = participantSelector
        self.signalEmitter = SignalHolder()


    def mousePressEvent(self, event):
        # Position of the estimation
        point = self.viewer.mapToScene(event.pos())

        # True landmark which is estimated
        # Get the ids of the true landmarks
        true_landmark_ids = [true_landmark.id for true_landmark in self.true_landmarks]
        dialog = ReferenceDialog(true_landmark_ids)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the data
            estimation_id, estimation_type, true_landmark_id = dialog.get_data()
            # Get the position of the true landmark
            true_x, true_y = [(true_landmark.x, true_landmark.y) for true_landmark in self.true_landmarks if true_landmark.id == true_landmark_id][0]
            # Current participant
            current_participant = self.participantSelector.currentText()

            # Create the estimated landmark or edge point
            if estimation_type == "Landmark":
                estimated_point = EstimatedLandmark(point.x(), point.y(), estimation_id, self.viewer.scene(), true_x, true_y, current_participant)
            elif estimation_type == "Edge":
                estimated_point = EdgePoint(point.x(), point.y(), estimation_id, self.viewer.scene(), true_x, true_y, current_participant)
            # Emit the point to be picked up by the MainWindow
            self.signalEmitter.signal.emit(estimated_point)

class DeleteTool(Tool):
    # This doesn't work because the item detected is the ellipse and not the point
    def __init__(self, viewer):
        super().__init__(viewer)
        self.signalEmitter = SignalHolder()

    def mousePressEvent(self, event):
        point = self.viewer.mapToScene(event.pos())
        item = self.viewer.scene().itemAt(point, QTransform())
        if item:
            print(type(item))
            if isinstance(item, QGraphicsEllipseItem):
                self.signalEmitter.signal.emit(item)

                # CONTINUE: Remove the item from the appropriate list in the main window

class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setScene(QGraphicsScene(self))
        self.currentTool = None

    def loadImage(self, filename):
        pixmap = QPixmap(filename)
        self.scene().clear()
        pixmap_item = self.scene().addPixmap(pixmap)
        pixmap_item.setZValue(-10)
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
        self.true_landmarks = []
        self.estimated_landmarks = []
        self.estimated_edges = []

        # Marking tools
        self.toolSelector = QComboBox()
        self.toolSelector.addItem('None')
        self.referenceTool = ReferenceMarkingTool(self.viewer)
        self.toolSelector.addItem('Set Reference')
        self.trueLandmarkTool = TrueLandmarkTool(self.viewer)
        self.toolSelector.addItem('True Landmark')
        self.estimatedPointTool = EstimatedPointTool(self.viewer, self.true_landmarks, self.participantSelector)
        self.toolSelector.addItem('Estimate Point')
        self.deleteTool = DeleteTool(self.viewer)
        self.toolSelector.addItem('Delete')

        self.toolSelector.setCurrentIndex(0)


        # Connect UI elements to functions
        self.loadBtn.clicked.connect(self.loadImage)
        self.createParticipantBtn.clicked.connect(self.createParticipant)
        self.toolSelector.currentTextChanged.connect(self.onToolSelectionChanged)
        self.trueLandmarkTool.signalEmitter.signal.connect(self.handle_true_landmark_created)
        self.estimatedPointTool.signalEmitter.signal.connect(self.handle_estimated_point_created)
        self.deleteTool.signalEmitter.signal.connect(self.handle_item_deleted)

        # Set up UI
        layout = QVBoxLayout()
        layout.addWidget(self.loadBtn)
        layout.addWidget(self.createParticipantBtn)
        layout.addWidget(self.participantSelector)
        layout.addWidget(self.toolSelector)
        layout.addWidget(self.viewer)
        

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
        elif text == 'True Landmark':
            self.viewer.setTool(self.trueLandmarkTool)
        elif text == 'Estimate Point':
            self.viewer.setTool(self.estimatedPointTool)
        elif text == 'Delete':
            self.viewer.setTool(self.deleteTool)

    # Catch the true landmark creation event
    def handle_true_landmark_created(self, true_landmark):
        # Add the TrueLandmark object to the list
        self.true_landmarks.append(true_landmark)

    # Catch the estimated point creation event
    def handle_estimated_point_created(self, estimated_point):
        if isinstance(estimated_point, EstimatedLandmark):
            self.estimated_landmarks.append(estimated_point)
        elif isinstance(estimated_point, EdgePoint):
            self.estimated_edges.append(estimated_point)
            print("Edge point created")

    # Catch the item deletion event
    def handle_item_deleted(self, item):
        # Find the point to which the item belongs and remove it
        for true_landmark in self.true_landmarks:
            if item in true_landmark.markers:
                true_landmark.items.remove(item)
                return
        



# Dialog for creating an estimation

class ReferenceDialog(QDialog):
    def __init__(self, reference_landmarks):
        super().__init__()

        # Set up the dialog layout
        layout = QVBoxLayout()

        # Add a label and line edit for entering the ID
        id_label = QLabel("Enter ID:")
        self.id_edit = QLineEdit()
        layout.addWidget(id_label)
        layout.addWidget(self.id_edit)

        # Add a combo box for selecting the type of reference
        type_label = QLabel("Select reference type:")
        self.type_combo = QComboBox()
        self.type_combo.addItem("Landmark")
        self.type_combo.addItem("Edge")
        layout.addWidget(type_label)
        layout.addWidget(self.type_combo)

        # Add a combo box for selecting the reference landmark
        landmark_label = QLabel("Select reference landmark:")
        self.landmark_combo = QComboBox()
        self.landmark_combo.addItems(reference_landmarks)
        layout.addWidget(landmark_label)
        layout.addWidget(self.landmark_combo)

        # Add a button to accept the dialog
        accept_button = QPushButton("OK")
        accept_button.clicked.connect(self.accept)
        layout.addWidget(accept_button)

        # Set the dialog layout
        self.setLayout(layout)

    def get_data(self):
        # Return the entered ID, reference type, and reference landmark/edge
        return self.id_edit.text(), self.type_combo.currentText(), self.landmark_combo.currentText()

        
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
