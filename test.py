from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QGraphicsView, QWidget
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Create main layout
        main_layout = QHBoxLayout()

        # Create left column
        left_column = QVBoxLayout()

        # Create first container
        container1 = QVBoxLayout()
        load_image_btn = QPushButton("Load Image")
        facility_id_input = QLineEdit()
        facility_id_input.setPlaceholderText("Facility ID")
        container1.addWidget(load_image_btn)
        container1.addWidget(facility_id_input)

        # Create second container
        container2 = QVBoxLayout()
        combo_box_1 = QComboBox()
        create_participant_btn = QPushButton("Create Participant")
        container2.addWidget(combo_box_1)
        container2.addWidget(create_participant_btn)

        # Create third container
        container3 = QVBoxLayout()
        combo_box_2 = QComboBox()
        container3.addWidget(combo_box_2)

        # Create fourth container
        container4 = QVBoxLayout()
        export_btn = QPushButton("Export")
        container4.addWidget(export_btn)

        # Add all containers to the left column
        left_column.addLayout(container1)
        left_column.addLayout(container2)
        left_column.addLayout(container3)
        left_column.addLayout(container4)

        # Create right column
        graphics_view = QGraphicsView()


        # Make left column a fixed width
        left_column.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_column.setSpacing(10)

        # Create a widget to contain the left column and set its maximum and minimum width
        left_widget = QWidget()
        left_widget.setLayout(left_column)
        left_widget.setFixedWidth(200)

        # Add left column and right column to the main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(graphics_view)

        # Create a widget to set as the central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

# Create the application
app = QApplication([])
window = MainWindow()
window.show()
app.exec()