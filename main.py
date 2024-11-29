import json
import sys
from PyQt6 import QtWidgets, uic, QtCore, QtGui
from datetime import datetime

# noinspection PyUnresolvedReferences
from assets import resources_rc

from components.button import ClickableElidedLabel
from components.addrepoframe import AddRepoDialog
from components.updatesframe import UpdatesFrame
from components.trayicon import SystemTrayIcon

from src.githubAuth import GitHub, clean_github_link
from src.settings import SettingsWindow
from concurrent.futures import ThreadPoolExecutor
import math
import src.updater


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("components/mainwindow.ui", self)  # type: ignore
        
        self.setWindowTitle("GitUpdater")
        
        
        try:
            with open('data/config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:    
            template = open('src/config_template.json', 'r')
            with open('data/config.json', 'w') as f:
                f.write(template.read())
                f.close()
            with open('data/config.json', 'r') as f:
                self.config = json.load(f)        
            

        self.repoButtonsScrollAreaContents = self.findChild(QtWidgets.QWidget, "repoButtonsScrollAreaContents")
        self.repoButtonsScrollAreaContentsLayout = QtWidgets.QVBoxLayout(self.repoButtonsScrollAreaContents)
        self.updatesScrollAreaContents = self.findChild(QtWidgets.QWidget, "updatesScrollAreaContents")
        self.updatesScrollAreaContentsLayout = QtWidgets.QVBoxLayout(self.updatesScrollAreaContents)
        
        self.refreshButton = self.findChild(QtWidgets.QPushButton, "refreshButton")
        self.refreshButton.clicked.connect(lambda: self.update_updates())

        self.addRepoButton = self.findChild(QtWidgets.QPushButton, "addRepoButton")
        self.addRepoButton.clicked.connect(self.open_add_repo_dialog)

        self.settingsButton = self.findChild(QtWidgets.QPushButton, "settingsButton")
        self.settingsButton.clicked.connect(self.open_settings)

        self.settingswindow = None
        self.assets = {}
        
        self.tray_icon = SystemTrayIcon(self)
        self.tray_icon.show()
        
        try:
            self.update_repo_buttons()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error loading repositories: {e}")
        
        if self.get_setting('check_updates', True):
            try:
                self.update_updates()
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Error updating repositories: {e}")
 
                


        self.show()
        
    def show_loading(self):
        self.loading = QtWidgets.QLabel("Loading...")
        movie = QtGui.QMovie(":/loading.gif")
        self.loading.setMovie(movie)
        movie.start()
        self.setCentralWidget(self.loading)

    def open_settings(self):
        if not isinstance(self.settingswindow, SettingsWindow):
            self.settingswindow = SettingsWindow(self.assets)
        self.settingswindow.load_settings()
        self.settingswindow.show()

    def open_add_repo_dialog(self):
        dialog = AddRepoDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            github_link = clean_github_link(data['url'])
            try:
                if not github_link.startswith("https://github.com/"):
                    raise ValueError("Invalid GitHub link")

                parts = github_link.split('/')                    

                name = parts[3] + '/' + parts[4]

                with open('data/repos.json', 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    repos = data.get('repos', [])
                    for repo in repos:
                        if repo['name'] == name:
                            if repo['url'] == github_link:
                                raise ValueError("Repository already exists")
                            else:
                                raise ValueError("Repository with the same name already exists")

                    data['repos'].append({"name": name, "url": github_link, "path": data['path'], "correct_package_name": "", "version": "", "auto_update": data['auto_update']})
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()
                    self.update_repo_buttons()

            except FileNotFoundError:
                with open('data/repos.json', 'w', encoding='utf-8') as f:
                    json.dump({"repos": [{"name": name, "url": github_link, "path": data['path'], "correct_package_name": "", "version": "", "auto_update": data['auto_update']}]}, f, indent=4)

            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, "Error", str(e))
                self.open_add_repo_dialog()

            QtWidgets.QMessageBox.information(self, "Repository Added", "The repository has been added.")
        else:
            dialog.deleteLater()
            
    def closeEvent(self, event):
        if self.get_setting('tray_on_close', True):
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
            if self.isVisible():
                QtWidgets.QMessageBox.information(
                    self, 
                    "GitUpdater",
                    "The application will keep running in the system tray. "
                    "To restore, click the tray icon."
                )
            self.hide()
            event.ignore()

        
    def get_setting(self, setting_name, value=None):
        """Helper method to get settings from config.json"""
        for category in self.config.get('categories', []):
            if 'General' in category:
                settings = category['General'][0]['settings'][0]
                if setting_name in settings:
                    return settings[setting_name][0].get('value', value)
        return None
        
    class UpdateWorker(QtCore.QObject):
        finished = QtCore.pyqtSignal()
        progress = QtCore.pyqtSignal(object)
        error = QtCore.pyqtSignal(str)

        def __init__(self, repos, git):
            super().__init__()
            self.repos = repos
            self.git = git
            self.assets = {}
            
        def process_repo(self, repo):
            try:
                latest_release = self.git.get_latest_release_url(repo['url'])
                self.assets[repo['name']] = latest_release.get_assets()
                asset, correct_package_name = self.git.find_correct_asset_in_list(latest_release, None, repo.get('correct_package_name'))
                
                if asset:
                    version = self.git.get_asset_version(asset=asset, page=latest_release)
                    old_version = repo['version']
                    if old_version == version:
                        return None
                    if old_version == "":
                        old_version = "N/A"
                        
                    result = {
                        'name': repo['name'],
                        'old_version': old_version,
                        'new_version': version,
                        'asset_name': asset.name,
                        'asset_url': asset.browser_download_url,
                        'path': repo['path'],
                        'updated_at': asset.updated_at.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                        'correct_package_name': correct_package_name
                    }
                    return result
            except Exception as e:
                self.error.emit(f"Error updating {repo['name']}: {str(e)}")
                return None

        def run(self):
            BATCH_SIZE = 5
            with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
                for result in executor.map(self.process_repo, self.repos):
                    if result:
                        self.progress.emit(result)
            self.finished.emit()

    def update_updates(self):
        if self.updatesScrollAreaContentsLayout.count() > 0:
            self.clear_layout(self.updatesScrollAreaContentsLayout)
            
        with open('data/repos.json', 'r+', encoding='utf-8') as f:
            data = json.load(f)
            git = GitHub()
            repos = data.get('repos', [])

            # Create thread and worker
            self.thread = QtCore.QThread()
            self.worker = self.UpdateWorker(repos, git)
            self.worker.moveToThread(self.thread)

            # Connect signals
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.finished.connect(self.updatesScrollAreaContentsLayout.addStretch)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.handle_update_progress)
            self.worker.error.connect(lambda msg: QtWidgets.QMessageBox.warning(self, "Error", msg))

            # Start thread
            self.thread.start()

    def handle_update_progress(self, result):
        def make_connection(name, url, path, version):
            return lambda: self.update_repo(name, url, path, version)
            
        updates_frame = UpdatesFrame(
            label=result['name'],
            old_version=result['old_version'],
            new_version=result['new_version'],
            last_check=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            last_updated=result['updated_at'],
            tooltip=result['asset_name'],
            connection=make_connection(result['name'], 
                                    result['asset_url'], 
                                    result['path'], 
                                    result['new_version'])
        )
        
        self.updatesScrollAreaContentsLayout.addWidget(updates_frame)

        # Update repos.json
        with open('data/repos.json', 'r+', encoding='utf-8') as f:
            data = json.load(f)
            for repo in data['repos']:
                if repo['name'] == result['name']:
                    if result['correct_package_name']:
                        repo['correct_package_name'] = result['correct_package_name']
                    # repo['version'] = result['new_version']
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
            
    def update_repo(self, name, url, path, version):
        try:
            src.updater.update(url, path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error updating {name}: {e}")
            return
        
        with open('data/repos.json', 'r+', encoding='utf-8') as f:
            data = json.load(f)
            repo = [repo for repo in data.get('repos', []) if repo['name'] == name][0]
            repo['version'] = version
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
            self.update_repo_buttons()
        
        QtWidgets.QMessageBox.information(self, "Repository Updated", "The repository has been updated.")
        
    def update_repo_buttons(self):
        if self.repoButtonsScrollAreaContentsLayout.count() > 0:
            self.clear_layout(self.repoButtonsScrollAreaContentsLayout)
        with open('data/repos.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            repos = data.get('repos', [])
            for repo in repos:
                def make_connection(url):
                    return lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
                button = ClickableElidedLabel(repo['name'], repo['url'], connection=make_connection(repo['url']))
                button.setObjectName(repo['name'])
                button.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
                button.customContextMenuRequested.connect(lambda: self.context_menu(self, QtGui.QCursor.pos()))
                self.repoButtonsScrollAreaContentsLayout.addWidget(button)

            self.repoButtonsScrollAreaContentsLayout.addStretch()


    def context_menu(self, pos):
        menu = QtWidgets.QMenu()
        delete_action = menu.addAction("Delete Repository")
        change_name_action = menu.addAction("Change Repository Name")
        change_url_action = menu.addAction("Change Repository URL")
        chage_local_path_action = menu.addAction("Change Local Path")
        action = menu.exec(pos)
        if action == delete_action:  # Delete action
            confirm = QtWidgets.QMessageBox()
            confirm.setWindowTitle("Delete Repository")
            confirm.setText("Are you sure you want to delete this repository?")
            confirm.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            confirm.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
            confirm.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            if confirm.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                repo_name = self.sender().text()
                self.delete_repo(self, repo_name)
        elif action == change_name_action:  # Change name action
            new_name, ok = QtWidgets.QInputDialog.getText(self, title="Change Repository Name", label="Enter the new name:", text=self.sender().objectName())
            if ok:
                confirm = QtWidgets.QMessageBox()
                confirm.setWindowTitle("Change Repository Name")
                confirm.setText("Are you sure you want to change the name of this repository?")
                confirm.setStandardButtons(
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                confirm.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
                confirm.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                if confirm.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                    objectName = self.sender().objectName()
                    self.change_repo_name(self, objectName, new_name)
        elif action == change_url_action:  # Change URL action
            new_url, ok = QtWidgets.QInputDialog.getText(self, "Change Repository URL", "Enter the new URL:", text=self.sender().toolTip())
            if ok:
                confirm = QtWidgets.QMessageBox()
                confirm.setWindowTitle("Change Repository URL")
                confirm.setText("Are you sure you want to change the URL of this repository?")
                confirm.setStandardButtons(
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                confirm.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
                confirm.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                if confirm.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                    self.change_repo_url(self, self.sender().toolTip(), new_url)
        elif action == chage_local_path_action:  # Change local path action
            new_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Change Local Path", "Pick a new local path:", QtWidgets.QFileDialog.Option.ShowDirsOnly)
            if new_path:
                confirm = QtWidgets.QMessageBox()
                confirm.setWindowTitle("Change Local Path")
                confirm.setText("Are you sure you want to change the local path of this repository?")
                confirm.setStandardButtons(
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                confirm.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
                confirm.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                if confirm.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                    self.change_local_path(self, self.sender().text(), new_path)
        else:
            return


    def change_local_path(self, name, new_path):
        with open('data/repos.json', 'r+', encoding='utf-8') as f:
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


    def change_repo_name(self, old_name, new_name):
        with open('data/repos.json', 'r+', encoding='utf-8') as f:
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


    def change_repo_url(self, name, new_url):
        with open('data/repos.json', 'r+', encoding='utf-8') as f:
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


    def delete_repo(self, name):
        with open('data/repos.json', 'r+', encoding='utf-8') as f:
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


    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet('''
        QToolTip {
            color: #FFFFFF;
        }
    ''')
    window = MainWindow()
    sys.exit(app.exec())
