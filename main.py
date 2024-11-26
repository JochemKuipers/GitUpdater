import json
import sys
from PyQt6 import QtWidgets, uic, QtCore, QtGui
# noinspection PyUnresolvedReferences
from assets import resources_rc
from components.button import ClickableElidedLabel
from src.settings import SettingsWindow
from components.updatesframe import UpdatesFrame
from src.githubAuth import GitHub, clean_github_link
from datetime import datetime

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("components/mainwindow.ui", self)  # type: ignore
        
        self.setWindowTitle("GitUpdater")

        self.repoButtonsScrollAreaContents = self.findChild(QtWidgets.QWidget, "repoButtonsScrollAreaContents")
        self.repoButtonsScrollAreaContentsLayout = QtWidgets.QVBoxLayout(self.repoButtonsScrollAreaContents)
        self.updatesScrollAreaContents = self.findChild(QtWidgets.QWidget, "updatesScrollAreaContents")
        self.updatesScrollAreaContentsLayout = QtWidgets.QVBoxLayout(self.updatesScrollAreaContents)
        try:
            update_repo_buttons(self)
            update_updates(self)
        except FileNotFoundError:
            pass

        self.addRepoButton = self.findChild(QtWidgets.QPushButton, "addRepoButton")
        self.addRepoButton.clicked.connect(self.open_add_repo_dialog)

        self.settingsButton = self.findChild(QtWidgets.QPushButton, "settingsButton")
        self.settingsButton.clicked.connect(self.open_settings)

        self.settingswindow = None

        self.show()

    def open_settings(self):
        if not isinstance(self.settingswindow, SettingsWindow):
            self.settingswindow = SettingsWindow()
        self.settingswindow.load_settings()
        self.settingswindow.show()

    def open_add_repo_dialog(self):
        dialog = QtWidgets.QInputDialog()
        dialog.setLabelText("Enter the GitHub repository link:")
        dialog.setWindowTitle("Add Repository")
        dialog.setTextValue(" ")
        dialog.setOkButtonText("Add")
        dialog.setCancelButtonText("Cancel")
        dialog.setWindowIcon(QtGui.QIcon(":/assets/giticon.svg"))
        dialog.exec()

        if dialog.result() == QtWidgets.QDialog.DialogCode.Accepted:
            github_link = clean_github_link(dialog.textValue())
            try:
                if not github_link.startswith("https://github.com/"):
                    raise ValueError("Invalid GitHub link")

                parts = github_link.split('/')                    

                name = parts[3] + '/' + parts[4]

                with open('data/repos.json', 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    repos = data.get('repos', [])
                    for repo in repos:
                        if repo['settings']['name'] == name:
                            if repo['settings']['url'] == github_link:
                                raise ValueError("Repository already exists")
                            else:
                                raise ValueError("Repository with the same name already exists")

                    data['repos'].append({"name": name, "url": github_link})
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()
                    update_repo_buttons(self)

            except json.JSONDecodeError:
                with open('data/repos.json', 'w', encoding='utf-8') as f:
                    json.dump({"repos": [{"name": name, "url": github_link}]}, f, indent=4)

            except FileNotFoundError:
                with open('data/repos.json', 'w', encoding='utf-8') as f:
                    json.dump({"repos": [{"name": name, "url": github_link}]}, f, indent=4)

            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, "Error", str(e))
                self.open_add_repo_dialog()

            QtWidgets.QMessageBox.information(self, "Repository Added", "The repository has been added.")
        dialog.deleteLater()
        
def update_updates(self):
    if self.updatesScrollAreaContentsLayout.count() > 0:
        clear_layout(self.updatesScrollAreaContentsLayout)
    with open('data/repos.json', 'r+', encoding='utf-8') as f:
        data = json.load(f)
        git = GitHub()
        repos = data.get('repos', [])
        updates_frame = None
        for repo in repos:
            try:
                latest_release = git.get_latest_release_url(repo['url'])
                asset, correct_package_name = git.find_correct_asset_in_list(latest_release, self, repo.get('correct_package_name'))
                if asset:
                    version = git.get_asset_version(asset=asset, page=latest_release)
                    old_version = repo['settings']['version']
                    if old_version == version:
                        continue
                    if old_version == "":
                        old_version = "N/A"
                    updates_frame = UpdatesFrame(
                        label=repo['settings']['name'],
                        old_version=old_version,
                        new_version=version,
                        last_check=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        last_updated=asset.updated_at.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                        tooltip=asset.name,
                        connection=lambda: print("clicked")
                    )
                    self.updatesScrollAreaContentsLayout.addWidget(updates_frame)
                    if correct_package_name:
                        repo['settings']['correct_package_name'] = correct_package_name
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Error updating {repo['settings']['name']}: {e}")
            self.updatesScrollAreaContentsLayout.addWidget(updates_frame)
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        self.updatesScrollAreaContentsLayout.addStretch()

def update_repo_buttons(self):
    if self.repoButtonsScrollAreaContentsLayout.count() > 0:
        clear_layout(self.repoButtonsScrollAreaContentsLayout)
    with open('data/repos.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        repos = data.get('repos', [])
        for repo in repos:
            button = ClickableElidedLabel(repo['settings']['name'], repo['settings']['url'], connection=lambda: print("clicked"))
            button.setObjectName(repo['settings']['name'])
            button.clicked.connect(lambda: print("clicked"))
            button.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda: context_menu(self, QtGui.QCursor.pos()))
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
            delete_repo(self, repo_name)
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
                change_repo_name(self, objectName, new_name)
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
                change_repo_url(self, self.sender().toolTip(), new_url)
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
                change_local_path(self, self.sender().text(), new_path)
    else:
        return


def change_local_path(self, name, new_path):
    with open('data/repos.json', 'r+', encoding='utf-8') as f:
        data = json.load(f)
        repos = data.get('repos', [])
        for repo in repos:
            if repo['settings']['name'] == name:
                repo['settings']['local_path'] = new_path
                break

        data['repos'] = repos
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        update_repo_buttons(self)


def change_repo_name(self, old_name, new_name):
    with open('data/repos.json', 'r+', encoding='utf-8') as f:
        data = json.load(f)
        repos = data.get('repos', [])
        for repo in repos:
            if repo['settings']['name'] == old_name:
                repo['settings']['name'] = new_name
                break

        data['repos'] = repos
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        update_repo_buttons(self)


def change_repo_url(self, name, new_url):
    with open('data/repos.json', 'r+', encoding='utf-8') as f:
        data = json.load(f)
        repos = data.get('repos', [])
        for repo in repos:
            if repo['settings']['name'] == name:
                repo['settings']['url'] = new_url
                break

        data['repos'] = repos
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        update_repo_buttons(self)


def delete_repo(self, name):
    with open('data/repos.json', 'r+', encoding='utf-8') as f:
        data = json.load(f)
        repos = data.get('repos', [])
        for repo in repos:
            if repo['settings']['name'] == name:
                repos.remove(repo)
                break

        data['repos'] = repos
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        update_repo_buttons(self)


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
        elif child.layout():
            clear_layout(child.layout())

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
