import json
from PyQt6 import QtWidgets, QtCore
from components.settingframe import SettingsFrame

class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Settings")
        
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setElideMode(QtCore.Qt.TextElideMode.ElideRight)
        self.setCentralWidget(self.tab_widget)

        self.setting_inputs = {}
        self.load_settings()
        
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.tab_widget.setCornerWidget(self.save_button, QtCore.Qt.Corner.TopRightCorner)

    def load_settings(self):
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)

            with open('repos.json', 'r') as repo_file:
                repos = json.load(repo_file)

            for category in config['categories']:
                if category['name'] == 'Repositories':
                    repo_tab = QtWidgets.QWidget()
                    repo_layout = QtWidgets.QVBoxLayout()
                    self.repo_tab_widget = QtWidgets.QTabWidget()

                    for repo in repos['repos']:
                        repo_sub_tab = QtWidgets.QWidget()
                        repo_sub_layout = QtWidgets.QVBoxLayout()

                        for setting in category['settings']:
                            repo_value = repo.get(setting['key'], setting['default'])
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

                        repo_sub_layout.addStretch()
                        repo_sub_tab.setLayout(repo_sub_layout)
                        repo_sub_tab.setObjectName(repo['name'])
                        self.repo_tab_widget.addTab(repo_sub_tab, repo['name'])

                    repo_layout.addWidget(self.repo_tab_widget)
                    repo_tab.setLayout(repo_layout)
                    self.tab_widget.addTab(repo_tab, category['name'])
                else:
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

                settings["categories"].append(category)

            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)

            QtWidgets.QMessageBox.information(self, "Settings Saved", "The settings have been saved successfully.")

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error saving settings: {e}")