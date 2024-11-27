from PyQt6 import QtWidgets, QtGui

class AddRepoDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Repository")
        self.setWindowIcon(QtGui.QIcon(":/assets/giticon.svg"))
        
        # Create layout
        layout = QtWidgets.QVBoxLayout()
        
        # URL input
        url_layout = QtWidgets.QHBoxLayout()
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setStyleSheet("QLineEdit { color: white; }")
        self.url_input.setPlaceholderText("Enter GitHub repository URL")
        url_layout.addWidget(QtWidgets.QLabel("Repository URL:"))
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Path input
        path_layout = QtWidgets.QHBoxLayout()
        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setStyleSheet("QLineEdit { color: white; }")
        self.path_input.setPlaceholderText("Select download directory")
        self.filepicker = QtWidgets.QFileDialog()
        self.filepicker.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        self.filepicker.setOption(QtWidgets.QFileDialog.Option.ReadOnly, True)
        self.filepicker.fileSelected.connect(lambda path: self.path_input.setText(path))
        self.filepicker_button = QtWidgets.QPushButton('...')
        self.filepicker_button.clicked.connect(lambda: self.filepicker.open())
        self.filepicker_button.setFixedWidth(30)
        path_layout.addWidget(QtWidgets.QLabel("Download Path:"))
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.filepicker_button)
        layout.addLayout(path_layout)
        
        # Auto-update checkbox
        auto_update_layout = QtWidgets.QHBoxLayout()
        self.auto_update_label = QtWidgets.QLabel("Auto-update:")
        self.auto_update = QtWidgets.QCheckBox()
        self.auto_update.setChecked(True)
        auto_update_layout.addWidget(self.auto_update_label, 9)
        auto_update_layout.addWidget(self.auto_update, 1)
        layout.addLayout(auto_update_layout)
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | 
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_data(self):
        return {
            'url': self.url_input.text().strip(),
            'path': self.path_input.text().strip(),
            'auto_update': self.auto_update.isChecked()
        }
        

