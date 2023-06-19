# TODO:
# 0. Set scale
# + 1. Set reference landmark
# + 2. Orient reference landmark
# + 3. Set true landmark
# + 4. Give id to true landmark
# + 5. Create a participant with a given id
# + 6. Select participant from list
# + 7. Set estimated landmark
# + 8. Give id to estimated landmark
# + 9. Select corresponding true landmark for estimated landmark
# 10. Calculate distance between estimated landmark and true landmark
# 12. Calculate angle between reference landmark and true landmark
# 13. Calculate angle between reference landmark and estimated landmark
# + 14. Set edge point
# + 15. Select corresponding true landmark for edge point
# 16. Calculate distance between edge point and true landmark
# 17. Set ID for image
# 18. Save information to file
# 19. Make the UI look nice

# CONTINUE: do the calculation tool and export

from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QGraphicsTextItem
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QGraphicsEllipseItem, QGraphicsLineItem, QComboBox, QInputDialog, QGraphicsPolygonItem
from PyQt6.QtGui import QPixmap, QPen, QColor, QBrush, QCursor, QPolygonF, QFont, QTransform
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF, pyqtSignal, QObject
from abc import ABC, abstractmethod
from math import cos, sin, pi
import copy
from tools import ReferenceMarkingTool, TrueLandmarkTool, EstimatedLandmarkTool, DeleteTool, SetScaleTool
from points import ReferenceLandmark, TrueLandmark, EstimatedLandmark, EdgePoint

class Participant():
    def __init__(self, id: str):
        self.id = id
        self.estimates = []

    def addEstimate(self, estimate: EstimatedLandmark):
        self.estimates.append(estimate)

    def removeEstimate(self, estimate: EstimatedLandmark):
        self.estimates.remove(estimate)
        del estimate



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
        self.reference_point = None
        self.scale_value = None

        # Tools
        self.toolSelector = QComboBox()
        self.toolSelector.addItem('None')
        self.referenceTool = ReferenceMarkingTool(self.viewer)
        self.toolSelector.addItem('Set Reference')
        self.trueLandmarkTool = TrueLandmarkTool(self.viewer)
        self.toolSelector.addItem('True Landmark')
        self.estimatedLandmarkTool = EstimatedLandmarkTool(self.viewer, self.true_landmarks, self.participantSelector)
        self.toolSelector.addItem('Estimate Point')
        self.deleteTool = DeleteTool(self.viewer)
        self.toolSelector.addItem('Delete')
        self.scaleTool = SetScaleTool(self.viewer)
        self.toolSelector.addItem('Set Scale')

        self.toolSelector.setCurrentIndex(0)


        # Connect UI elements to functions
        self.loadBtn.clicked.connect(self.loadImage)
        self.createParticipantBtn.clicked.connect(self.createParticipant)
        self.toolSelector.currentTextChanged.connect(self.onToolSelectionChanged)
        self.trueLandmarkTool.signalEmitter.signal.connect(self.handle_point_created)
        self.estimatedLandmarkTool.signalEmitter.signal.connect(self.handle_point_created)
        self.referenceTool.signalEmitter.signal.connect(self.handle_point_created)
        self.deleteTool.signalEmitter.signal.connect(self.handle_item_deleted)
        self.scaleTool.signalEmitter.signal.connect(self.handle_scale_set)

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
            self.viewer.setTool(self.estimatedLandmarkTool)
        elif text == 'Delete':
            self.viewer.setTool(self.deleteTool)
        elif text == 'Set Scale':
            self.viewer.setTool(self.scaleTool)

    # Catch the point creation event
    def handle_point_created(self, point):
        participant = self.getCurrentParticipant()

        if isinstance(point, EstimatedLandmark):
            participant.addEstimate(point)
        elif isinstance(point, EdgePoint):
            participant.addEstimate(point)
        elif isinstance(point, ReferenceLandmark):
            if self.reference_point:
                 # Remove the old reference point
                self.handle_item_deleted(self.reference_point.marker)
            self.reference_point = point
        elif isinstance(point, TrueLandmark):
            self.true_landmarks.append(point)

    # Catch the item deletion event
    def handle_item_deleted(self, item):
        # Find the point to which the item belongs and remove it
        for true_landmark in self.true_landmarks:
            if item == true_landmark.marker:
                # Remove the true_landmark from the list
                self.true_landmarks.remove(true_landmark)
                item.scene().removeItem(item)
                break

        if self.reference_point and item == self.reference_point.marker:
            self.reference_point = None
            item.scene().removeItem(item)

        # Loop through all participants and look for the item
        for participant in self.participants:
            for estimate in participant.estimates:
                if item == estimate.marker:
                    # Remove the estimate from the participant
                    participant.removeEstimate(estimate)
                    item.scene().removeItem(item)
                    break
 
    # Catch the scale set event
    def handle_scale_set(self, scale):
        self.scale_value = scale

    def calculateError(self):
        # Calculate the error for each participant
        for participant in self.participants:
            participant.calculateError(self.reference_point, self.scale_value)

    # Save the data to a file
    def saveData(self):
        pass
        
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
