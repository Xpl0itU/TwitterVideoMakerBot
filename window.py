import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLineEdit,
    QComboBox,
)


class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fudgify - Dashboard")
        self.setWindowIcon(QIcon("static/img/App_Icon.png"))
        self.setStyleSheet("QLabel.small-text { font-size: small; }")
        self.setup_ui()

    def setup_ui(self):
        logo_label = QLabel(self)
        logo_label.setPixmap(QIcon("static/img/Group_2.png").pixmap(90, 90))

        # First Input
        first_input_layout = QHBoxLayout()
        first_input_layout.setContentsMargins(0, 0, 0, 0)

        add_input_button = QPushButton("+", self)
        add_input_button.setObjectName("add-input")
        add_input_button.clicked.connect(self.add_input)

        first_input = QLineEdit(self)
        first_input.setObjectName("input")
        first_input.setPlaceholderText("Enter your tweet's link here")

        submit_button = QPushButton("Submit", self)
        submit_button.setObjectName("submit")
        submit_button.clicked.connect(self.submit_clicked)

        first_input_layout.addWidget(add_input_button)
        first_input_layout.addWidget(first_input)
        first_input_layout.addWidget(submit_button)

        first_input_container = QWidget(self)
        first_input_container.setLayout(first_input_layout)

        self.inputs_layout = QVBoxLayout()

        self.inputs_container = QWidget(self)
        self.inputs_container.setObjectName("inputs")
        self.inputs_container.setLayout(self.inputs_layout)
        self.inputs_container.hide()

        modes_label = QLabel("Mode:", self)
        modes_dropdown = QComboBox(self)
        modes_dropdown.setObjectName("modes-dropdown")
        modes_dropdown.addItem("Tweet Screenshots + Captions")
        modes_dropdown.addItem("First Tweet Screenshot + Captions")
        modes_dropdown.addItem("Only Tweet Screenshots")
        modes_dropdown.addItem("Only Captions")

        modes_layout = QHBoxLayout()
        modes_layout.addWidget(modes_label)
        modes_layout.addWidget(modes_dropdown)

        modes_container = QWidget(self)
        modes_container.setLayout(modes_layout)

        progress_label = QLabel("Status:")
        stage_label = QLabel("Stage:")
        self.stage_value_label = QLabel("Starting")
        progress_value_label = QLabel("Progress:")
        self.progress_bar = QLabel("0%")
        self.progress_bar.setObjectName("progress-bar")
        self.progress_bar.setStyleSheet("QLabel#progress-bar { width: 0%; }")

        results_button = QPushButton("Download", self)
        results_button.setObjectName("export")
        results_button.clicked.connect(self.download_clicked)

        results_layout = QVBoxLayout()
        results_layout.addWidget(results_button)
        results_layout.addStretch()

        results_container = QWidget(self)
        results_container.setObjectName("results-container")
        results_container.setLayout(results_layout)

        progress_layout = QVBoxLayout()
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(stage_label)
        progress_layout.addWidget(self.stage_value_label)
        progress_layout.addWidget(progress_value_label)
        progress_layout.addWidget(results_container)

        progress_container = QWidget(self)
        progress_container.setObjectName("progress-container")
        progress_container.setLayout(progress_layout)

        small_text_label = QLabel(
            "Average wait time is 2 minutes for every 1 minute of video."
        )
        small_text_label.setObjectName("small-text")

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        main_layout.addWidget(first_input_container)
        main_layout.addWidget(self.inputs_container)
        main_layout.addWidget(modes_container)
        main_layout.addWidget(small_text_label)

        self.show_progress_container = False
        main_layout.addWidget(progress_container)
        progress_container.hide()

    def add_input(self):
        self.inputs_container.show()
        new_input = QLineEdit(self)
        new_input.setObjectName("input")
        new_input.setPlaceholderText("Enter your tweet's link here")

        remove_button = QPushButton("-", self)
        remove_button.setObjectName("remove-button")
        remove_button.clicked.connect(self.remove_input)

        input_layout = QHBoxLayout()
        input_layout.addWidget(remove_button)
        input_layout.addWidget(new_input)

        input_container = QWidget(self)
        input_container.setObjectName("input-container")
        input_container.setLayout(input_layout)

        self.inputs_layout.addWidget(input_container)

    def remove_input(self):
        remove_button = self.sender()
        input_container = remove_button.parent()
        self.inputs_layout.removeWidget(input_container)
        input_container.deleteLater()
        self.adjustSize()

    def submit_clicked(self):
        submit_button = self.findChild(QPushButton, "submit")
        submit_button.setDisabled(True)

        self.stage_value_label.setText("Starting")
        self.progress_bar.setText("0%")

        self.show_progress_container = True
        self.update_progress_container()

    def download_clicked(self):
        pass

    def update_progress_container(self):
        progress_container = self.findChild(QWidget, "progress-container")
        results_container = self.findChild(QWidget, "results-container")

        progress_container.setVisible(self.show_progress_container)
        results_container.setVisible(self.show_progress_container)
        self.adjustSize()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardWindow()
    window.show()
    sys.exit(app.exec())
