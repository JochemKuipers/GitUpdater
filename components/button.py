from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt


class CustomButton(QPushButton):
    def __init__(
            self,
            text="",
            tooltip="",
            parent=None,
            bg_color="#393E46",
            hover_color="#4A4F57",
            text_color="#FFFFFF",
            border_radius=5,
            connection=None
    ):
        super().__init__(text, parent)

        # Set button style
        self.setToolTip(tooltip)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                border-radius: {border_radius}px;
                padding: 8px 16px;
                font-size: 14px;
                white-space: normal;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {bg_color};
            }}
            
            QToolTip {{
                background-color: {bg_color};
                color: {text_color};
            }}
        """)

        # Optional: Set cursor to pointing hand
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if connection:
            self.clicked.connect(connection)