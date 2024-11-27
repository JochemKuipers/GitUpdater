from PyQt6 import QtWidgets, QtGui
from PyQt6.QtGui import QAction

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setIcon(QtGui.QIcon(":/assets/giticon.svg"))
        self.setToolTip("GitUpdater")
        
        # Create context menu
        self.menu = QtWidgets.QMenu()
        
        # Show/Hide action
        self.show_hide_action = QAction("Hide", self.menu)
        self.show_hide_action.triggered.connect(self.toggle_window)
        self.menu.addAction(self.show_hide_action)
        
        # Settings action
        settings_action = QAction("Settings", self.menu)
        settings_action.triggered.connect(self.main_window.open_settings)
        self.menu.addAction(settings_action)
        
        # Add separator
        self.menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(QtWidgets.QApplication.quit)
        self.menu.addAction(exit_action)
        
        # Set context menu
        self.setContextMenu(self.menu)
        
        # Connect signals
        self.activated.connect(self.on_tray_icon_activated)
        
    def toggle_window(self):
        if self.main_window.isVisible():
            self.main_window.hide()
            self.show_hide_action.setText("Show")
        else:
            self.main_window.show()
            self.show_hide_action.setText("Hide")
            
    def on_tray_icon_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window()