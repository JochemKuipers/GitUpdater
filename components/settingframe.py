from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QComboBox, QFileDialog, QPushButton
from PyQt6.QtCore import Qt


class SettingsFrame(QFrame):
    def __init__(self, label: str, setting_type: str, default_value=None, options=None):
        super().__init__()

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(10, 5, 10, 5)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)

        # Label
        self.label = QLabel(label)
        self.label.setMinimumWidth(120)
        self.main_layout.addWidget(self.label)

        self.main_layout.addStretch(1)

        # Input widget
        if setting_type == 'checkbox':
            self.input = QCheckBox()
            self.input.setChecked(bool(default_value))
            self.main_layout.addWidget(self.input)

        elif setting_type == 'select':
            self.input = QComboBox()
            if options:
                self.input.addItems(options)
            if default_value:
                self.input.setCurrentText(str(default_value))
            self.input.setMinimumWidth(150)
            self.main_layout.addWidget(self.input, stretch=3)
        elif setting_type == 'text':
            self.input = QLineEdit()
            if default_value is not None:
                self.input.setText(str(default_value))
            self.input.setMinimumWidth(150)
            self.input.setCursorPosition(0)
            self.main_layout.addWidget(self.input, stretch=3)
        elif setting_type == 'path':
            self.text = QLineEdit()
            self.text.setText(str(default_value))
            self.text.setMinimumWidth(150)
            self.text.setCursorPosition(0)
            self.filepicker = QFileDialog()
            self.filepicker.setFileMode(QFileDialog.FileMode.ExistingFile)
            self.filepicker.setOption(QFileDialog.Option.ReadOnly, True)
            self.filepicker.fileSelected.connect(lambda path: self.text.setText(path))
            self.input = self.text
            self.filepicker_button = QPushButton('Browse')
            self.filepicker_button.clicked.connect(lambda: self.filepicker.open())
            self.filepicker_button.setMaximumWidth(100)
            self.main_layout.addWidget(self.input, stretch=3)
            self.main_layout.addWidget(self.filepicker_button, stretch=1)
        elif setting_type == 'url':
            self.input = QLineEdit()
            self.input.setText(str(default_value))
            self.input.setMinimumWidth(150)
            self.input.setCursorPosition(0)
            self.main_layout.addWidget(self.input, stretch=3)
        elif setting_type == 'number':
            self.input = QLineEdit()
            self.input.setText(str(default_value))
            self.input.setMinimumWidth(150)
            self.input.setCursorPosition(0)
            self.input.setValidator(Qt.QIntValidator())
            self.main_layout.addWidget(self.input, stretch=3)
            

    def getValue(self):
        if isinstance(self.input, QCheckBox):
            return self.input.isChecked()
        elif isinstance(self.input, QComboBox):
            return self.input.currentText()
        return self.input.text()

    def setValue(self, value):
        if isinstance(self.input, QCheckBox):
            self.input.setChecked(value)
        elif isinstance(self.input, QComboBox):
            self.input.setCurrentText(str(value))
        else:
            self.input.setText(str(value))

    def get_widget(self):
        return self.input
