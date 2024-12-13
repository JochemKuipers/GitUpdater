import argparse
import json
import sys
import os
from PyQt6 import QtWidgets, uic, QtCore, QtGui
from datetime import datetime
import logging
from apscheduler.schedulers.qt import QtScheduler

# noinspection PyUnresolvedReferences
from assets import resources_rc

from components.button import ClickableElidedLabel
from components.addrepoframe import AddRepoDialog
from components.updatesframe import UpdatesFrame
from components.trayicon import SystemTrayIcon

from src.githubAuth import GitHub, clean_github_link
from src.settings import SettingsWindow
from src.updater import DownloadWorker
from src.utils import get_config_path, get_setting, get_setting_repo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='gitupdater.log', filemode='w')
logger = logging.getLogger(__name__)


def resource_path(relative_path):
    """Get absolute path to resource for both dev and packaged versions"""
    if hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    # Running in development
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("Starting GitUpdater")
        
        # Load UI file using resource path
        ui_file = resource_path('components/mainwindow.ui')
        if not os.path.exists(ui_file):
            raise FileNotFoundError(f"UI file not found: {ui_file}")
            
        try:
            uic.loadUi(ui_file, self)
        except Exception as e:
            logging.error(f"Error loading UI: {e}")
            raise
        
        self.setWindowTitle("GitUpdater")
        
        self.config_path = get_config_path('config.json')
        self.repos_path = get_config_path('repos.json')

        if not os.path.exists(self.config_path):
            logging.info("Creating config.json")
            with open('src/config_template.json', 'r') as template:
                with open(self.config_path, 'w') as f:
                    f.write(template.read())
        if not os.path.exists(self.repos_path):
            logging.info("Creating repos.json")
            with open(self.repos_path, 'w') as f:
                f.write('{"repos": []}')
                
        self.git = GitHub()
        self.git.selector.selection_needed.connect(self.show_package_selection_dialog)
            

        self.repoButtonsScrollAreaContents = self.findChild(QtWidgets.QWidget, "repoButtonsScrollAreaContents")
        self.repoButtonsScrollAreaContentsLayout = QtWidgets.QVBoxLayout(self.repoButtonsScrollAreaContents)
        self.updatesScrollAreaContents = self.findChild(QtWidgets.QWidget, "updatesScrollAreaContents")
        self.updatesScrollAreaContentsLayout = QtWidgets.QVBoxLayout(self.updatesScrollAreaContents)
        
        self.refreshButton = self.findChild(QtWidgets.QPushButton, "refreshButton")
        self.refreshButton.clicked.connect(lambda: self.check_for_updates())

        self.addRepoButton = self.findChild(QtWidgets.QPushButton, "addRepoButton")
        self.addRepoButton.clicked.connect(self.open_add_repo_dialog)

        self.settingsButton = self.findChild(QtWidgets.QPushButton, "settingsButton")
        self.settingsButton.clicked.connect(self.open_settings)

        self.settingswindow = None
        self.assets = {}
        
        logging.info("Starting Tray Icon")
        self.tray_icon = SystemTrayIcon(self)
        self.tray_icon.show()
        
        try:
            self.update_repo_buttons()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error loading repositories: {e}")
            logging.error(f"Error loading repositories: {e}")
        
        interval = int(get_setting(self.config_path, 'check_updates'))
        if interval > 0:
            scheduler = QtScheduler()
            scheduler.add_job(self.check_for_updates, 'interval', hours=interval)
            scheduler.start()
        self.check_for_updates()
                
        if get_setting(self.config_path, 'start_minimized'):
            self.hide()
        else: 
            self.show()
        self.shownbefore = False

    def show_package_selection_dialog(self, asset_names, title):
        try:
            selected_name, ok = QtWidgets.QInputDialog.getItem(
                self,
                title,
                "Multiple packages found. Please select the correct one:",
                asset_names,
                0,
                False
            )
            if ok and selected_name:
                # Directly call handle_selection to avoid signal issues
                self.git.selector._handle_selection(selected_name)
                
        except Exception as e:
            logging.error(f"Error in package selection dialog: {e}")
            
    def handle_package_selection(self, selected_name: str) -> None:
        """Handle package selection from dialog
        
        Args:
            selected_name: Name of selected asset package
        """
        try:
            # Store selection in GitHub instance
            self.git.selector.selected_package = selected_name
            
            # Signal selection is complete
            self.git.selector.selection_complete.emit(selected_name)
            
            logging.debug(f"Package selected: {selected_name}")
            
        except Exception as e:
            logging.error(f"Error handling package selection: {e}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Error handling package selection: {e}")

    def open_settings(self):
        if not isinstance(self.settingswindow, SettingsWindow):
            self.settingswindow = SettingsWindow(self.assets)
        self.settingswindow.load_settings()
        self.settingswindow.show()

    def open_add_repo_dialog(self):
        dialog = AddRepoDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            dialog_data = dialog.get_data()
            github_link = clean_github_link(dialog_data['url'])
            try:
                if not github_link.startswith("https://github.com/"):
                    raise ValueError("Invalid GitHub link")

                parts = github_link.split('/')                    

                name = parts[3] + '/' + parts[4]

                with open(self.repos_path, 'r+', encoding='utf-8') as f:
                    repo_data = json.load(f)
                    repos = repo_data.get('repos', [])
                    for repo in repos:
                        if repo['name'] == name:
                            if repo['url'] == github_link:
                                raise ValueError("Repository already exists")
                            else:
                                raise ValueError("Repository with the same name already exists")

                    repo_data['repos'].append({"name": name, "url": github_link, "path": dialog_data['path'], "correct_package_name": "", "version": "", "auto_update": dialog_data['auto_update']})
                    f.seek(0)
                    json.dump(repo_data, f, indent=4)
                    f.truncate()
                    self.update_repo_buttons()
                    self.check_for_updates()

            except FileNotFoundError:
                logging.info("Creating repos.json")
                with open(self.repos_path, 'w', encoding='utf-8') as f:
                    json.dump({"repos": [{"name": name, "url": github_link, "path": dialog_data['path'], "correct_package_name": "", "version": "", "auto_update": dialog_data['auto_update']}]}, f, indent=4)

            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, "Error", str(e))
                self.open_add_repo_dialog()

            QtWidgets.QMessageBox.information(self, "Repository Added", "The repository has been added.")
        else:
            dialog.deleteLater()
            
    def closeEvent(self, event):
        if get_setting(self.config_path, 'minimize_to_tray'):
            self.minimizeEvent(event)
        else:
            result = QtWidgets.QMessageBox.question(
                self,
                "Confirm Exit", 
                "Are you sure you want to exit?",
                QtWidgets.QMessageBox.StandardButton.Yes | 
                QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No
            )
            
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                QtWidgets.QApplication.quit()
            else:
                event.ignore()
            
    def minimizeEvent(self, event):
        if self.tray_icon.isVisible():
            if self.isVisible() and not self.shownbefore:
                QtWidgets.QMessageBox.information(
                    self, 
                    "GitUpdater",
                    "The application will keep running in the system tray. "
                    "To restore, click the tray icon."
                )
                self.shownbefore = True
            self.hide()
            event.ignore()
        else:
            event.accept()

        

        
    class UpdateWorker(QtCore.QObject):
        # Signals
        update_found = QtCore.pyqtSignal(dict)  # Emits update data when found
        finished = QtCore.pyqtSignal()  # Emits when all updates checked
        error = QtCore.pyqtSignal(str)  # Emits error messages
        
        def __init__(self, git, repos_path, assets):
            super().__init__()
            self.git = git
            self.repos_path = repos_path
            self.assets = assets

        def run(self):
            try:
                with open(self.repos_path, 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    repos = data.get('repos', [])
                    
                    for repo in repos:
                        try:
                            latest_release = self.git.get_latest_release_url(repo['url'])
                            self.assets[repo['name']] = latest_release.get_assets()
                            
                            asset, correct_package_name = self.git.find_correct_asset_in_list(
                                latest_release,
                                self,
                                repo.get('correct_package_name')
                            )
                            
                            if asset:
                                version = self.git.get_asset_version(asset=asset, page=latest_release)
                                old_version = repo['version']
                                
                                if old_version == version:
                                    continue
                                    
                                if old_version == "":
                                    old_version = "N/A"
                                
                                update_data = {
                                    "name": repo['name'],
                                    "old_version": old_version,
                                    "new_version": version,
                                    "updated_at": asset.updated_at.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                                    "asset_url": asset.browser_download_url,
                                    "path": repo['path'],
                                    "correct_package_name": correct_package_name
                                }
                                
                                self.update_found.emit(update_data)
                                
                                if correct_package_name:
                                    repo['correct_package_name'] = correct_package_name
                                    
                                f.seek(0)
                                json.dump(data, f, indent=4)
                                f.truncate()
                                
                        except Exception as e:
                            self.error.emit(f"Error updating {repo['name']}: {str(e)}")
                            logging.error(f"Error updating {repo['name']}: {e}")
                            
            except Exception as e:
                self.error.emit(f"Error updating updates: {str(e)}")
                logging.error(f"Error updating updates: {e}")
                
            self.finished.emit()

        @staticmethod
        def sanitize_package_name(package_name: str) -> str:
            """Replace version number in package name with *"""
            import re
            version_pattern = re.compile(r'\d+(\.\d+)+(-\w+)?')
            return version_pattern.sub('*', package_name)
        
    def check_for_updates(self):
        self.settingsButton.setEnabled(False)
        if self.updatesScrollAreaContentsLayout.count() > 0:
            self.clear_layout(self.updatesScrollAreaContentsLayout)
        # Create thread and worker
        self.update_thread = QtCore.QThread()
        self.update_worker = self.UpdateWorker(self.git, self.repos_path, self.assets)
        
        # Move worker to thread
        self.update_worker.moveToThread(self.update_thread)
        
        # Connect signals
        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.finished.connect(self.update_thread.quit)
        self.update_worker.finished.connect(self.update_worker.deleteLater)
        self.update_worker.finished.connect(self.updatesScrollAreaContentsLayout.addStretch)
        self.update_worker.finished.connect(lambda: self.settingsButton.setEnabled(True))
        self.update_thread.finished.connect(self.update_thread.deleteLater)
        
        self.update_worker.update_found.connect(self.update_updates_ui)
        self.update_worker.error.connect(lambda msg: logging.error(msg))
        
        # Start thread
        self.update_thread.start()
        
        
    def update_updates_ui(self, data):
        if data:
            frame = UpdatesFrame(
                data['name'],
                data['old_version'],
                data['new_version'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data['updated_at'],
                data['correct_package_name'],
                connection=lambda: self.update_repo(data['name'], data['asset_url'], data['path'], data['new_version'])
            )
            self.updatesScrollAreaContentsLayout.addWidget(frame)
            
            auto_update = get_setting_repo(self.repos_path, data['name'], 'auto_update')
            if auto_update:
                self.update_repo(data['name'], data['asset_url'], data['path'], data['new_version'])
        else:
            QtWidgets.QMessageBox.information(self, "No Updates", "No updates available.")                       
            
    def update_repo(self, name, url, path, version):
        # Store references
        self.download_thread = QtCore.QThread()
        self.download_worker = DownloadWorker(url, path)
        
        # Move worker to thread
        self.download_worker.moveToThread(self.download_thread)
        
        frame = None
        for i in range(self.updatesScrollAreaContentsLayout.count()):
            widget = self.updatesScrollAreaContentsLayout.itemAt(i).widget()
            if isinstance(widget, UpdatesFrame) and widget.label.text() == name:
                frame = widget
                break
        
        # Connect signals
        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.progress.connect(lambda p: logger.info(f"Download progress: {p}%"))
        
        def cleanup():
            if frame:
                self.updatesScrollAreaContentsLayout.removeWidget(frame)
            self.update_version(name, version)
        
        self.download_worker.finished.connect(cleanup)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        
        # Handle errors
        self.download_worker.error.connect(
            lambda e: QtWidgets.QMessageBox.warning(self, "Error", f"Download error: {e}")
        )
        
        # Start download
        self.download_thread.start()

    def update_version(self, name, version):
        """Update version in repos.json after successful download"""
        try:
            with open(self.repos_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                repos = data.get('repos', [])
                for repo in repos:
                    if repo['name'] == name:
                        repo['version'] = version
                        break

                data['repos'] = repos
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                
            self.update_repo_buttons()
            QtWidgets.QMessageBox.information(
                self, "Update Complete", 
                f"Repository {name} updated successfully"
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Error", 
                f"Error updating version: {e}"
            )
            logging.error(f"Error updating version: {e}")
        
    def update_repo_buttons(self):
        logger.info("Updating repository buttons")
        if self.repoButtonsScrollAreaContentsLayout.count() > 0:
            self.clear_layout(self.repoButtonsScrollAreaContentsLayout)
        with open(self.repos_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            repos = data.get('repos', [])
            for repo in repos:
                def make_connection(url):
                    return lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
                button = ClickableElidedLabel(repo['name'], repo['url'], connection=make_connection(repo['url']))
                button.setObjectName(repo['name'])
                button.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
                button.customContextMenuRequested.connect(self.context_menu)
                self.repoButtonsScrollAreaContentsLayout.addWidget(button)

            self.repoButtonsScrollAreaContentsLayout.addStretch()


    def context_menu(self):
        menu = QtWidgets.QMenu(self)
        button = self.sender()
        repo_name = button.objectName()

        # Change Name
        change_name = QtGui.QAction("Change Name", self)
        change_name.triggered.connect(lambda: self.change_repo_name_dialog(repo_name))
        menu.addAction(change_name)

        # Change Path
        change_path = QtGui.QAction("Change Path", self)
        change_path.triggered.connect(lambda: self.change_repo_path_dialog(repo_name))
        menu.addAction(change_path)

        # Change URL 
        change_url = QtGui.QAction("Change URL", self)
        change_url.triggered.connect(lambda: self.change_repo_url_dialog(repo_name))
        menu.addAction(change_url)

        # Delete
        delete = QtGui.QAction("Delete", self)
        delete.triggered.connect(lambda: self.delete_repo_dialog(repo_name))
        menu.addAction(delete)

        menu.exec(QtGui.QCursor.pos())
    
    def change_repo_name_dialog(self, name):
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Change Repository Name", "Enter new name:", text=name)
        if ok:
            self.change_repo_name(name, new_name)
            
    def change_repo_path_dialog(self, name):
        new_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if new_path:
            self.change_local_path(name, new_path)
            
    def change_repo_url_dialog(self, name):
        new_url, ok = QtWidgets.QInputDialog.getText(self, "Change Repository URL", "Enter new URL:")
        if ok:
            self.change_repo_url(name, new_url)
            
    def delete_repo_dialog(self, name):
        result = QtWidgets.QMessageBox.question(
            self,
            "Delete Repository",
            f"Are you sure you want to delete {name}?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            self.delete_repo(name)
            
    def change_local_path(self, name, new_path):
        try:
            with open(self.repos_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                repos = data.get('repos', [])
                for repo in repos:
                    if repo['name'] == name:
                        repo['path'] = new_path
                        break

                data['repos'] = repos
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                self.update_repo_buttons()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error changing local path: {e}")
            logging.error(f"Error changing local path: {e}")


    def change_repo_name(self, old_name, new_name):
        try:
            with open(self.repos_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                repos = data.get('repos', [])
                for repo in repos:
                    if repo['name'] == old_name:
                        repo['name'] = new_name
                        break

                data['repos'] = repos
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                self.update_repo_buttons()
                
                # Update the name in the updates frame if present
                for i in range(self.updatesScrollAreaContentsLayout.count()):
                    item = self.updatesScrollAreaContentsLayout.itemAt(i)
                    if item and item.widget() and isinstance(item.widget(), UpdatesFrame):
                        frame = item.widget()
                        name_label = frame.findChild(QtWidgets.QLabel, "label")
                        if name_label and name_label.text() == old_name:
                            name_label.setText(new_name)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error changing repository name: {e}")
            logging.error(f"Error changing repository: {e}")

    def change_repo_url(self, name, new_url):
        try:
            with open(self.repos_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                repos = data.get('repos', [])
                for repo in repos:
                    if repo['name'] == name:
                        repo['url'] = new_url
                        break

                data['repos'] = repos
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                self.update_repo_buttons()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error changing repository URL: {e}")
            logging.error(f"Error changing repository URL: {e}")


    def delete_repo(self, name):
        try:
            with open(self.repos_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                repos = data.get('repos', [])
                for repo in repos:
                    if repo['name'] == name:
                        repos.remove(repo)
                        break

                data['repos'] = repos
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                self.update_repo_buttons()
                self.check_for_updates()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error deleting repository: {e}")
            logging.error(f"Error deleting repository: {e}")

    def clear_layout(self, layout):
        try:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    self.clear_layout(child.layout())
        except Exception as e:
            logging.error(f"Error clearing layout: {e}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Error clearing layout: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitUpdater")
    parser.add_argument("--headless", action="store_true", help="Run headless update check")
    args = parser.parse_args()
    
    if args.headless:
        from src.updater import run_headless_updates
        git = GitHub()
        logger.info("Running headless updates")
        sys.exit(run_headless_updates(git, get_config_path('repos.json')))
    else:
        app = QtWidgets.QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())