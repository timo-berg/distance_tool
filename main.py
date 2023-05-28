from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QGraphicsEllipseItem, QGraphicsLineItem
from PyQt6.QtGui import QPixmap, QPen, QColor, QBrush, QCursor
from PyQt6.QtCore import Qt, QRectF
from abc import ABC, abstractmethod

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        

class Tool(ABC):
    def __init__(self, viewer):
        self.viewer = viewer

    @abstractmethod
    def activate(self):
        pass

    @abstractmethod
    def deactivate(self):
        pass

    @abstractmethod
    def mousePressEvent(self, event):
        pass


class MarkingTool(Tool):
    def activate(self):
        self.viewer.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    def deactivate(self):
        self.viewer.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mousePressEvent(self, event):
        point = self.viewer.mapToScene(event.pos())
        ellipse = QGraphicsEllipseItem(point.x()-5, point.y()-5, 10, 10)
        ellipse.setBrush(QBrush(QColor('red')))
        ellipse.setPen(QPen(QColor('red')))
        ellipse.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.viewer.scene().addItem(ellipse)
        self.viewer.points.append(ellipse)

class DistanceTool(Tool):
    # Implement these methods based on the logic for your Distance tool
    def __init__(self, viewer):
        super().__init__(viewer)
        self.points = []
    
    def activate(self):
        pass

    def deactivate(self):
        self.points = []

    def mousePressEvent(self, event):
        point = self.viewer.mapToScene(event.pos())
        item = self.viewer.scene().itemAt(point, self.viewer.transform())
        if item and isinstance(item, QGraphicsEllipseItem):
            # Make border black
            item.setPen(QPen(QColor('black')))
            self.points.append(item)
            
            if len(self.points) == 2:
                line = QGraphicsLineItem(self.points[0].rect().center().x(), self.points[0].rect().center().y(), 
                                         self.points[1].rect().center().x(), self.points[1].rect().center().y())
                line.setPen(QPen(QColor('blue')))
                line.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)
                self.viewer.scene().addItem(line)
                self.points = []
        
class DeleteTool(Tool):
    def activate(self):
        self.viewer.setCursor(QCursor(Qt.CursorShape.UpArrowCursor))

    def deactivate(self):
        self.viewer.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mousePressEvent(self, event):
        point = self.viewer.mapToScene(event.pos())
        item = self.viewer.scene().itemAt(point, self.viewer.transform())
        if item and (isinstance(item, QGraphicsEllipseItem) or isinstance(item, QGraphicsLineItem)):
            self.viewer.scene().removeItem(item)

class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setScene(QGraphicsScene(self))
        self.points = []
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
        self.saveBtn = QPushButton('Save Information')
        self.markBtn = QPushButton('Mark Points')
        self.distBtn = QPushButton('Mark Distance')
        self.delBtn = QPushButton('Delete Item')

        self.loadBtn.clicked.connect(self.loadImage)
        self.saveBtn.clicked.connect(self.saveInformation)
        self.markBtn.clicked.connect(self.toggleMarking)
        self.distBtn.clicked.connect(self.toggleDistance)
        self.delBtn.clicked.connect(self.toggleDelete)

        self.marking = False
        self.distancing = False
        self.deleting = False

        layout = QVBoxLayout()
        layout.addWidget(self.loadBtn)
        layout.addWidget(self.saveBtn)
        layout.addWidget(self.distBtn)
        layout.addWidget(self.markBtn)
        layout.addWidget(self.delBtn)
        layout.addWidget(self.viewer)
        

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def loadImage(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Image", "", "Image Files (*.png *.jpg *.bmp)")
        if filename:
            self.viewer.loadImage(filename)

    def saveInformation(self):
        # Save your information here.
        pass

    def toggleMarking(self):
        self.marking = not self.marking
        self.markBtn.setText('Stop Marking Points' if self.marking else 'Mark Points')
        if self.marking:
            self.viewer.setTool(MarkingTool(self.viewer))
        else:
            self.viewer.setTool(None)

        # Reset the UI for other tools
        self.resetToolsUI(self.viewer.currentTool)

    def toggleDistance(self):
        self.distancing = not self.distancing
        self.distBtn.setText('Stop Marking Distance' if self.marking else 'Mark Distance')
        if self.distancing:
            self.viewer.setTool(DistanceTool(self.viewer))
        else:
            self.viewer.setTool(None)

        # Reset the UI for other tools
        self.resetToolsUI(self.viewer.currentTool)

    def toggleDelete(self):
        self.deleting = not self.deleting
        self.delBtn.setText('Stop Deleting' if self.deleting else 'Delete Item')
        if self.deleting:
            self.viewer.setTool(DeleteTool(self.viewer))
        else:
            self.viewer.setTool(None)

        # Reset the UI for other tools
        self.resetToolsUI(self.viewer.currentTool)

    def resetToolsUI(self, tool):
        if isinstance(tool, MarkingTool):
            self.distancing = False
            self.distBtn.setText('Mark Distance')
            self.deleting = False
            self.delBtn.setText('Delete Item')
        elif isinstance(tool, DeleteTool):
            self.distancing = False
            self.distBtn.setText('Mark Distance')
            self.marking = False
            self.markBtn.setText('Mark Points')
        elif isinstance(tool, DistanceTool):
            self.marking = False
            self.markBtn.setText('Mark Points')
            self.deleting = False
            self.delBtn.setText('Delete Item')
        
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
