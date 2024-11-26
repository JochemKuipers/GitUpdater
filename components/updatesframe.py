from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

class UpdatesFrame(QFrame):
    def __init__(self, label: str, old_version: str, new_version: str, last_check: str, last_updated: str, tooltip: str, connection: callable):
        super().__init__()
        
        self.main_layout = QHBoxLayout()
        
        self.setLayout(self.main_layout)
        
        self.label = QLabel(label)
        self.main_layout.addWidget(self.label)
        
        self.main_layout.addStretch(1)
        
        self.version = QLabel(f'{old_version} -> {new_version}')
        self.main_layout.addWidget(self.version)
               
        self.main_layout.addStretch(1)
        
        self.last_check = QLabel(last_check)
        self.main_layout.addWidget(self.last_check)
        
        self.main_layout.addStretch(1)
        
        self.last_updated = QLabel(last_updated)
        self.main_layout.addWidget(self.last_updated)
        
        self.main_layout.addStretch(1)
        
        self.update_button = QPushButton('Update')
        if connection:
            self.update_button.clicked.connect(connection)
        self.main_layout.addWidget(self.update_button)
        
        self.main_layout.addStretch(1)
        
        self.setStyleSheet('''
            UpdatesFrame {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: rgb(57,62,70);
                color: white;
            }
            QToolTip {
                background-color: rgb(57,62,70);
                border: 1px solid #ccc;
            }
            
            QLabel {
                background-color: transparent;
                border: 0;
            }
            
            QPushButton {
                background-color: rgb(57,62,70);
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgb(47,52,60);
            }
            QPushButton:pressed {
                background-color: rgb(37,42,50);
            }
        ''')
        
        self.setToolTip(tooltip)