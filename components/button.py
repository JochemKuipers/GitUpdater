from PyQt6.QtWidgets import QPushButton, QSizePolicy, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics

class ClickableElidedLabel(QPushButton):
    def __init__(self, text: str, tooltip: str = None, connection: callable = None):
        super().__init__(text)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet('''
            QPushButton {
                background-color: rgb(57, 62, 70);
                border: none;
                color: #FFFFFF;
                text-align: center;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgb(47, 52, 60);
            }
        ''')
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(40)
        if tooltip:
            self.setToolTip(tooltip)
        
        if connection:
            self.clicked.connect(connection)

    def setText(self, text: str):
        super().setText(text)
        self.elide_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.elide_text()

    def elide_text(self):
        font_metrics = QFontMetrics(self.font())
        elided_text = font_metrics.elidedText(self.text(), Qt.TextElideMode.ElideRight, self.width() - 20)
        super().setText(elided_text)