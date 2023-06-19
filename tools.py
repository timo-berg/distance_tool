from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QPen, QBrush, QColor, QTransform
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsSceneMouseEvent, QInputDialog, QDialog, QVBoxLayout, QLineEdit, QLabel, QComboBox, QPushButton
from abc import ABC, abstractmethod
from points import ReferenceLandmark, TrueLandmark, EstimatedLandmark, EdgePoint


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
        self.signalEmitter = SignalHolder()


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
                ref_landmark = ReferenceLandmark(self.firstPoint.x(), self.firstPoint.y(), id, self.viewer.scene(), point.x(), point.y())
                self.signalEmitter.signal.emit(ref_landmark)

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

class EstimatedLandmarkTool(Tool):
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
    def __init__(self, viewer):
        super().__init__(viewer)
        self.signalEmitter = SignalHolder()

    # Detect the item that is clicked on and emit it to the MainWindow
    def mousePressEvent(self, event):
        point = self.viewer.mapToScene(event.pos())
        item = self.viewer.scene().itemAt(point, QTransform())
        if item:
            print(type(item))
            if isinstance(item, QGraphicsEllipseItem):
                self.signalEmitter.signal.emit(item)

class SetScaleTool(Tool):
    def __init__(self, viewer):
        super().__init__(viewer)
        self.first_point = None
        self.signalEmitter = SignalHolder()

    def mousePressEvent(self, event):
        point = self.viewer.mapToScene(event.pos())
        if self.first_point is None:
            self.first_point = point
        else:
            second_point = point

            true_distance, ok = QInputDialog.getText(self.viewer, 'Scale', 'Enter the distance between the two points in meters')
            if ok:
                # Get the distance between the two points
                scene_distance = ((second_point.x() - self.first_point.x()) ** 2 + (second_point.y() - self.first_point.y()) ** 2) ** 0.5

                # Calculate the scale value
                scale_value = float(true_distance) / scene_distance

                self.signalEmitter.signal.emit(scale_value)

            self.first_point = None


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
