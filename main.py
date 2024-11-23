import sys
from PyQt6 import QtWidgets, uic
# noinspection PyUnresolvedReferences
from assets import resources_rc

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("components/mainwindow.ui", self)

        self.settingsButton = self.findChild(QtWidgets.QPushButton, "settingsButton")
        self.settingsButton.clicked.connect(self.open_settings)

        self.show()

    @staticmethod
    def open_settings():
        print("Settings button clicked")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
