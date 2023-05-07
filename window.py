from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QPushButton, QWidget
import webbrowser


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fudgify")
        layout = QVBoxLayout()
        label = QLabel("Fudgify is now running.")
        label.setMargin(10)
        layout.addWidget(label)

        close_button = QPushButton("Open in browser")
        close_button.pressed.connect(open_browser)
        layout.addWidget(close_button)

        hide_button = QPushButton("Hide")
        hide_button.pressed.connect(self.lower)
        layout.addWidget(hide_button)

        close_button = QPushButton("Quit")
        close_button.pressed.connect(self.close)
        layout.addWidget(close_button)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.show()
