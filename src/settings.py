import os
import json
from PyQt6 import QtWidgets, QtCore
from components.settingframe import SettingsFrame

class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setting_inputs = {}  # This should be initialized with your settings structure
        self.tab_widget = QtWidgets.QTabWidget()
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

            with open('data/repos.json', 'r') as repo_file:
                repos = json.load(repo_file)

            for category in config['categories']:
                if category['name'] == 'Repositories' and repos['repos'] != []:
                    repo_tab = QtWidgets.QWidget()
                    repo_layout = QtWidgets.QVBoxLayout()
                    self.repo_tab_widget = QtWidgets.QTabWidget()

                    for repo in repos['repos']:
                        repo_sub_tab = QtWidgets.QWidget()
                        repo_sub_layout = QtWidgets.QVBoxLayout()

                        # Convert settings list to dictionary
                        repo_settings_dict = {setting['key']: setting for setting in repo['settings']}

                        for setting in category['settings']:
                            repo_value = repo_settings_dict.get(setting['key'], {}).get('default', setting['default'])
                            setting_frame = SettingsFrame(
                                label=setting['label'],
                                setting_type=setting['type'],
                                default_value=repo_value,
                                options=setting.get('options')
                            )
                            repo_sub_layout.addWidget(setting_frame)

                            if repo['name'] not in self.setting_inputs:
                                self.setting_inputs[repo['name']] = {
                                    'settings': category['settings'],
                                    'widgets': {}
                                }

                            self.setting_inputs[repo['name']]['widgets'][setting['key']] = {
                                'widget': setting_frame.get_widget()
                            }

                        repo_sub_tab.setLayout(repo_sub_layout)
                        self.repo_tab_widget.addTab(repo_sub_tab, repo['name'])

                    repo_layout.addWidget(self.repo_tab_widget)
                    repo_tab.setLayout(repo_layout)
                    self.tab_widget.addTab(repo_tab, "Repositories")

                else:
                    general_tab = QtWidgets.QWidget()
                    general_layout = QtWidgets.QVBoxLayout()

                    for setting in category['settings']:
                        setting_frame = SettingsFrame(
                            label=setting['label'],
                            setting_type=setting['type'],
                            default_value=setting['default'],
                            options=setting.get('options')
                        )
                        general_layout.addWidget(setting_frame)

                        if category['name'] not in self.setting_inputs:
                            self.setting_inputs[category['name']] = {
                                'settings': category['settings'],
                                'widgets': {}
                            }

                        self.setting_inputs[category['name']]['widgets'][setting['key']] = {
                            'widget': setting_frame.get_widget()
                        }

                    general_tab.setLayout(general_layout)
                    self.tab_widget.addTab(general_tab, category['name'])

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error loading settings: {e}")
        except FileNotFoundError:
            with open('data/config.json', 'w') as f:
                json.dump({"categories": []}, f)
    def save_settings(self):
        try:
            # Save general settings to config.json
            general_settings = {"categories": []}

            for category_name, category_data in self.setting_inputs.items():
                if category_name == "Repositories":
                    continue  # Skip repository settings for now

                category = {
                    "name": category_name,
                    "settings": []
                }

                for setting in category_data['settings']:
                    widget = category_data['widgets'].get(setting['key'], {}).get('widget')
                    if widget:
                        setting_type = setting['type']
                        if isinstance(widget, QtWidgets.QCheckBox):
                            value = widget.isChecked()
                        elif isinstance(widget, QtWidgets.QComboBox):
                            value = widget.currentText()
                        else:
                            value = widget.text()

                        if setting_type == 'select':
                            new_setting = {
                                "type": setting_type,
                                "label": setting['label'],
                                "key": setting['key'],
                                "options": setting.get('options'),
                                "default": value
                            }
                        else:
                            new_setting = {
                                "type": setting_type,
                                "label": setting['label'],
                                "key": setting['key'],
                                "default": value
                            }
                        category["settings"].append(new_setting)

                general_settings["categories"].append(category)

            with open('data/config.json', 'w', encoding='utf-8') as f:
                json.dump(general_settings, f, indent=4)

            # Save repository settings to repos.json
            with open('data/repos.json', 'r+', encoding='utf-8') as f:
                data = json.load(f)
                repos = data.get('repos', [])

                for repo in repos:
                    repo_name = repo['name']
                    if repo_name in self.setting_inputs.get("Repositories", {}):
                        repo_settings = self.setting_inputs["Repositories"][repo_name]
                        repo['settings'] = []

                        for setting in repo_settings['settings']:
                            widget = repo_settings['widgets'].get(setting['key'], {}).get('widget')
                            if widget:
                                setting_type = setting['type']
                                if isinstance(widget, QtWidgets.QCheckBox):
                                    value = widget.isChecked()
                                elif isinstance(widget, QtWidgets.QComboBox):
                                    value = widget.currentText()
                                else:
                                    value = widget.text()

                                if setting_type == 'select':
                                    new_setting = {
                                        "type": setting_type,
                                        "label": setting['label'],
                                        "key": setting['key'],
                                        "options": setting.get('options'),
                                        "default": value
                                    }
                                else:
                                    new_setting = {
                                        "type": setting_type,
                                        "label": setting['label'],
                                        "key": setting['key'],
                                        "default": value
                                    }
                                repo['settings'].append(new_setting)

                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()

            QtWidgets.QMessageBox.information(self, "Settings Saved", "The settings have been saved successfully.")

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error saving settings: {e}")