import os
import json
from PyQt6 import QtWidgets, QtCore
from components.settingframe import SettingsFrame

class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setting_inputs = {}
        self.tab_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.save_button = QtWidgets.QPushButton("Save")
        self.tab_widget.setCornerWidget(self.save_button, QtCore.Qt.Corner.TopRightCorner)

    def load_settings(self):
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        try:
            if not os.path.exists('data/config.json'):
                with open('data/config.json', 'w') as f:
                    json.dump({"categories": []}, f)
                    
            if not os.path.exists('data/repos.json'):
                with open('data/repos.json', 'w') as f:
                    json.dump({"repos": []}, f)
                    
            with open('data/config.json', 'r') as f:
                config = json.load(f)

            for category in config['categories']:
                if category['name'] == 'Repositories':
                    self._load_repo_category(category)
                else:
                    category_tab = QtWidgets.QWidget()
                    category_layout = QtWidgets.QVBoxLayout()
                    self.setting_inputs[category['name']] = {
                        'widgets': {},
                        'settings': {}
                    }

                    for setting in category['settings']:
                        setting_frame = SettingsFrame(
                            label=setting['label'],
                            setting_type=setting['type'],
                            default_value=setting['value']
                        )
                        category_layout.addWidget(setting_frame)
                        
                        self.setting_inputs[category['name']]['settings'][setting['label']] = setting['value']
                        self.setting_inputs[category['name']]['widgets'][setting['label']] = setting_frame.get_widget()

                    category_tab.setLayout(category_layout)
                    self.tab_widget.addTab(category_tab, category['name'])

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error loading settings: {e}")

    def save_settings(self):
        try:
            # Save repository settings
            with open('data/repos.json', 'r+') as f:
                data = json.load(f)
                
                for i, repo in enumerate(data['repos']):
                    if repo['name'] in self.setting_inputs:
                        repo_widgets = self.setting_inputs[repo['name']]['widgets']
                        
                        # Update each setting from its widget
                        for key, widget in repo_widgets.items():
                            if isinstance(widget, QtWidgets.QCheckBox):
                                data['repos'][i][key] = widget.isChecked()
                            else:
                                data['repos'][i][key] = widget.text()

                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()

            # Save general settings
            general_settings = {"categories": []}
            for category_name, category_data in self.setting_inputs.items():
                if not '/' in category_name:  # Skip repository settings
                    category = {
                        "name": category_name,
                        "settings": category_data['settings']
                    }
                    general_settings["categories"].append(category)

            with open('data/config.json', 'w') as f:
                json.dump(general_settings, f, indent=4)

            QtWidgets.QMessageBox.information(self, "Success", "Settings saved successfully")

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error saving settings: {e}")

    def _load_repo_category(self, category):
        with open('data/repos.json', 'r') as f:
                repos_data = json.load(f)
        if repos_data['repos']:
            repo_tab = QtWidgets.QWidget()
            repo_layout = QtWidgets.QVBoxLayout()
            self.repo_tab_widget = QtWidgets.QTabWidget()

            for repo in repos_data['repos']:
                repo_sub_tab = QtWidgets.QWidget()
                repo_sub_layout = QtWidgets.QVBoxLayout()

                # Initialize repository settings structure
                self.setting_inputs[repo['name']] = {
                    'widgets': {},
                    'settings': {}
                }

                # Create setting frames for each setting
                settings_map = {
                    'path': ('Path', 'path'),
                    'url': ('URL', 'url'),
                    'correct_package_name': ('Correct Package Name', 'text'),
                    'version': ('Version', 'text'),
                    'auto_update': ('Auto Update', 'checkbox')
                }

                for key, (label, setting_type) in settings_map.items():
                    setting_frame = SettingsFrame(
                        label=label,
                        setting_type=setting_type,
                        default_value=repo.get(key, '')
                    )
                    repo_sub_layout.addWidget(setting_frame)
                    
                    self.setting_inputs[repo['name']]['settings'][key] = repo.get(key, '')
                    self.setting_inputs[repo['name']]['widgets'][key] = setting_frame.get_widget()

                repo_sub_tab.setLayout(repo_sub_layout)
                self.repo_tab_widget.addTab(repo_sub_tab, repo['name'].split('/')[-1])

            repo_layout.addWidget(self.repo_tab_widget)
            repo_tab.setLayout(repo_layout)
            self.tab_widget.addTab(repo_tab, "Repositories")