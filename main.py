import sys
from PyQt6 import QtWidgets, uic
# noinspection PyUnresolvedReferences
from assets import resources_rc

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("components/mainwindow.ui", self) # type: ignore

        self.settingsButton = self.findChild(QtWidgets.QPushButton, "settingsButton")
        self.settingsButton.clicked.connect(self.open_settings)
        
        self.settingswindow = None

        self.show()

    def open_settings(self):
        if not self.settingswindow:
            self.settingswindow = SettingsWindow()
        self.settingswindow.show()
        
class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("components/settings.ui", self) # type: ignore
        
        self.backButton = self.findChild(QtWidgets.QPushButton, "backButton")
        self.backButton.clicked.connect(self.close)

        self.show()
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
