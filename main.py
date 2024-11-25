import json
import sys
from PyQt6 import QtWidgets, uic, QtCore, QtGui
# noinspection PyUnresolvedReferences
from assets import resources_rc
from components.button import CustomButton
from components.settingframe import SettingsFrame

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("components/mainwindow.ui", self)  # type: ignore

        self.repoButtonsScrollAreaContents = self.findChild(QtWidgets.QWidget, "repoButtonsScrollAreaContents")

        # Create primary button
        self.button = CustomButton(
            text="Click Me",
            connection=self.open_settings
        )

        self.repoButtonsLayout = QtWidgets.QVBoxLayout()
        self.repoButtonsLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.repoButtonsLayout.setSpacing(10)
        self.repoButtonsLayout.setContentsMargins(0, 0, 0, 0)

        for i in range(5):
            # Create custom button
            button = CustomButton(
                text=f"Button {i + 1}",
                connection=self.open_settings
            )

            # Add button to layout
            self.repoButtonsLayout.addWidget(button)

        self.repoButtonsLayout.addStretch()
        # Set layout to scroll area contents
        self.repoButtonsScrollAreaContents.setLayout(self.repoButtonsLayout)

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
        uic.loadUi("components/settings.ui", self)  # type: ignore

        self.backButton = self.findChild(QtWidgets.QPushButton, "backButton")
        self.backButton.clicked.connect(self.close)

        self.saveButton = self.findChild(QtWidgets.QPushButton, "saveButton")
        self.saveButton.clicked.connect(self.save_settings)

        self.categoriesButtonsScrollAreaContents = self.findChild(QtWidgets.QWidget,
                                                                  "categoriesButtonsScrollAreaContents")
        self.settingsScrollAreaContents = self.findChild(QtWidgets.QWidget, "settingsScrollAreaContents")

        # Initialize layouts
        self.categoriesLayout = QtWidgets.QVBoxLayout()
        self.categoriesLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.categoriesLayout.setSpacing(10)
        self.categoriesLayout.setContentsMargins(10, 10, 10, 10)

        self.settingsLayout = QtWidgets.QVBoxLayout()
        self.settingsLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.settingsLayout.setSpacing(10)
        self.settingsLayout.setContentsMargins(10, 10, 10, 10)

        # Store references
        self.setting_inputs = {}
        self.current_category = None

        # Load settings
        self.load_settings()

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                config = json.load(f)

            # Create category buttons
            for category in config['categories']:
                # Create closure to capture category correctly
                def make_callback(cat):
                    return lambda: self.show_category_settings(cat)

                # Create button for this category
                category_button = CustomButton(
                    text=category['name'],
                    connection=make_callback(category)  # Use closure instead of direct lambda
                )
                self.categoriesLayout.addWidget(category_button)

                # Initialize storage for this category
                self.setting_inputs[category['name']] = {
                    'settings': category['settings'],
                    'widgets': {}
                }

            self.categoriesLayout.addStretch()
            self.categoriesButtonsScrollAreaContents.setLayout(self.categoriesLayout)
            self.settingsScrollAreaContents.setLayout(self.settingsLayout)

        except Exception as e:
            print(f"Error loading settings: {e}")

    def show_category_settings(self, category: dict):
        # Clear previous settings
        while self.settingsLayout.count():
            widget = self.settingsLayout.takeAt(0)
            if widget:
                w = widget.widget()
                if w:
                    w.deleteLater()

        # Get stored settings for this category
        category_data = self.setting_inputs[category['name']]

        # Create widgets for each setting
        for setting in category_data['settings']:
            setting_frame = SettingsFrame(
                label=setting['label'],
                setting_type=setting['type'],
                default_value=setting['default'],
                options=setting.get('options')
            )
            self.settingsLayout.addWidget(setting_frame)

            # Store widget reference
            category_data['widgets'][setting['key']] = {
                'widget': setting_frame.get_widget()
            }

        self.settingsLayout.addStretch()
        self.current_category = category['name']

    def save_settings(self):
        try:
            settings = {"categories": []}

            # Iterate through stored settings
            for category_name, category_data in self.setting_inputs.items():
                category = {
                    "name": category_name,
                    "settings": []
                }

                # Access the settings from stored data
                for setting in category_data['settings']:
                    widget = category_data['widgets'].get(setting['key'], {}).get('widget')
                    if widget:
                        setting_type = setting['type']
                        # Create new setting with updated value
                        new_setting = {
                            "type": setting_type,
                            "label": setting['label'],
                            "key": setting['key'],
                            "default": widget.isChecked() if setting_type == 'checkbox' else widget.text()
                        }
                        category["settings"].append(new_setting)

                settings["categories"].append(category)

            # Save to file
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=4)

        except Exception as e:
            print(f"Error saving settings: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
