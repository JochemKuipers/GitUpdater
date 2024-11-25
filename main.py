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
        self.repoButtonsScrollAreaContentsLayout = QtWidgets.QVBoxLayout(self.repoButtonsScrollAreaContents)
        try:
            update_repo_buttons(self)
        except FileNotFoundError:
            pass

        self.addRepoButton = self.findChild(QtWidgets.QPushButton, "addRepoButton")
        self.addRepoButton.clicked.connect(self.open_add_repo_dialog)

        self.settingsButton = self.findChild(QtWidgets.QPushButton, "settingsButton")
        self.settingsButton.clicked.connect(self.open_settings)

        self.settingswindow = None

        self.show()

    def open_settings(self):
        if not self.settingswindow:
            self.settingswindow = SettingsWindow()
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
            github_link = dialog.textValue()
            name = github_link.split('/')[4]
            try:
                if not github_link.startswith("https://github.com/"):
                    raise ValueError("Invalid GitHub link")

                try:
                    with open('repos.json', 'r+', encoding='utf-8') as f:
                        data = json.load(f)
                        repos = data.get('repos', [])
                        for repo in repos:
                            if repo['name'] == name:
                                if repo['url'] == github_link:
                                    raise ValueError("Repository already exists")
                                else:
                                    raise ValueError("Repository with the same name already exists")

                        data['repos'].append({"name": name, "url": github_link})
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()
                        update_repo_buttons(self)

                except json.JSONDecodeError:
                    with open('repos.json', 'w', encoding='utf-8') as f:
                        json.dump([github_link], f, indent=4)

                except FileNotFoundError:
                    with open('repos.json', 'w', encoding='utf-8') as f:
                        json.dump([github_link], f, indent=4)
                except ValueError as e:
                    if e.args[0] == 'Repository already exists':
                        QtWidgets.QMessageBox.warning(self, "Error", str(e))
                        return
                    if e.args[0] == 'Repository with the same name already exists':
                        overwrite_dialog = QtWidgets.QMessageBox()
                        overwrite_dialog.setWindowTitle("Repository Already Exists")
                        overwrite_dialog.setText("The repository already exists. Do you want to overwrite it?")
                        overwrite_dialog.setStandardButtons(
                            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                        overwrite_dialog.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
                        overwrite_dialog.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                        if overwrite_dialog.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                            with open('repos.json', 'r+', encoding='utf-8') as f:
                                data = json.load(f)
                                repos = data.get('repos', [])
                                for repo in repos:
                                    if repo['url'] == github_link or repo['name'] == name:
                                        repos.remove(repo)
                                        break

                                data['repos'].append({"name": name, "url": github_link})
                                f.seek(0)
                                json.dump(data, f, indent=4)
                                f.truncate()
                                update_repo_buttons(self)
                        else:
                            return


            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, "Error", str(e))
                return

            QtWidgets.QMessageBox.information(self, "Repository Added", "The repository has been added.")
        dialog.deleteLater()


def update_repo_buttons(self):
    if self.repoButtonsScrollAreaContentsLayout.count() > 0:
        clear_layout(self.repoButtonsScrollAreaContentsLayout)
    with open('repos.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        repos = data.get('repos', [])
        for repo in repos:
            button = CustomButton(
                text=repo['name'],
                tooltip=repo['url'],
                parent=self.repoButtonsScrollAreaContents
            )
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
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Change Repository Name", "Enter the new name:")
        if ok:
            confirm = QtWidgets.QMessageBox()
            confirm.setWindowTitle("Change Repository Name")
            confirm.setText("Are you sure you want to change the name of this repository?")
            confirm.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            confirm.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
            confirm.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            if confirm.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                change_repo_name(self, self.sender().text(), new_name)
    elif action == change_url_action:  # Change URL action
        new_url, ok = QtWidgets.QInputDialog.getText(self, "Change Repository URL", "Enter the new URL:")
        if ok:
            confirm = QtWidgets.QMessageBox()
            confirm.setWindowTitle("Change Repository URL")
            confirm.setText("Are you sure you want to change the URL of this repository?")
            confirm.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            confirm.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
            confirm.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            if confirm.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
                change_repo_url(self, self.sender().text(), new_url)
    elif action == chage_local_path_action:  # Change local path action
        new_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Change Local Path", "")
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
    with open('repos.json', 'r+', encoding='utf-8') as f:
        data = json.load(f)
        repos = data.get('repos', [])
        for repo in repos:
            if repo['name'] == name:
                repo['local_path'] = new_path
                break

        data['repos'] = repos
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
        update_repo_buttons(self)


def change_repo_name(self, old_name, new_name):
    with open('repos.json', 'r+', encoding='utf-8') as f:
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
        update_repo_buttons(self)


def change_repo_url(self, name, new_url):
    with open('repos.json', 'r+', encoding='utf-8') as f:
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
        update_repo_buttons(self)


def delete_repo(self, name):
    with open('repos.json', 'r+', encoding='utf-8') as f:
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
        update_repo_buttons(self)


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
        elif child.layout():
            clear_layout(child.layout())








class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings")

        self.tab_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.setting_inputs = {}
        self.load_settings()

    def load_settings(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)

            for category in config['categories']:
                tab = QtWidgets.QWidget()
                layout = QtWidgets.QVBoxLayout()

                for setting in category['settings']:
                    setting_frame = SettingsFrame(
                        label=setting['label'],
                        setting_type=setting['type'],
                        default_value=setting['default'],
                        options=setting.get('options')
                    )
                    layout.addWidget(setting_frame)

                    if category['name'] not in self.setting_inputs:
                        self.setting_inputs[category['name']] = {
                            'settings': category['settings'],
                            'widgets': {}
                        }

                    self.setting_inputs[category['name']]['widgets'][setting['key']] = {
                        'widget': setting_frame.get_widget()
                    }

                layout.addStretch()
                tab.setLayout(layout)
                self.tab_widget.addTab(tab, category['name'])

        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            settings = {"categories": []}

            for category_name, category_data in self.setting_inputs.items():
                category = {
                    "name": category_name,
                    "settings": []
                }

                for setting in category_data['settings']:
                    widget = category_data['widgets'].get(setting['key'], {}).get('widget')
                    if widget:
                        setting_type = setting['type']
                        new_setting = {
                            "type": setting_type,
                            "label": setting['label'],
                            "key": setting['key'],
                            "default": widget.isChecked() if setting_type == 'checkbox' else widget.text()
                        }
                        category["settings"].append(new_setting)

                settings["categories"].append(category)

            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)

        except Exception as e:
            print(f"Error saving settings: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
