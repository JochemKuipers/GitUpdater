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
        self.save_button.clicked.connect(self.save_settings)
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
                category_name = list(category.keys())[0]  # Get category name (General or Repositories)
                if category_name == 'Repositories':
                    self._load_repo_category(category)
                else:
                    category_tab = QtWidgets.QWidget()
                    category_layout = QtWidgets.QVBoxLayout()
                    self.setting_inputs[category_name] = {
                        'widgets': {},
                        'settings': {}
                    }

                    settings_dict = category[category_name][0]['settings'][0]
                    for setting_key, setting_list in settings_dict.items():
                        setting = setting_list[0]  # Get first (and only) setting in list
                        setting_frame = SettingsFrame(
                            label=setting['label'],
                            setting_type=setting['type'],
                            default_value=setting.get('value', setting.get('default')),
                            options=[opt['value'] for opt in setting.get('options', [])]
                        )
                        category_layout.addWidget(setting_frame)
                        
                        self.setting_inputs[category_name]['settings'][setting_key] = setting
                        self.setting_inputs[category_name]['widgets'][setting_key] = setting_frame.get_widget()

                    category_tab.setLayout(category_layout)
                    self.tab_widget.addTab(category_tab, category_name)

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error loading settings: {e}")

    def save_settings(self):
        try:
            # Save general settings to config.json
            with open('data/config.json', 'r+') as f:
                config = json.load(f)
                
                for category in config['categories']:
                    category_name = list(category.keys())[0]
                    if category_name == 'General':
                        settings_dict = category[category_name][0]['settings'][0]
                        for setting_key, setting_list in settings_dict.items():
                            setting = setting_list[0]
                            widget = self.setting_inputs['General']['widgets'].get(setting_key)
                            if widget:
                                if isinstance(widget, QtWidgets.QCheckBox):
                                    setting['value' if 'value' in setting else 'default'] = widget.isChecked()
                                elif isinstance(widget, QtWidgets.QComboBox):
                                    setting['value'] = widget.currentText()
                                else:
                                    setting['value'] = widget.text()
                
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()

            # Save repository settings to repos.json
            with open('data/repos.json', 'r+') as f:
                repos_data = json.load(f)
                
                for repo in repos_data['repos']:
                    repo_name = repo['name']
                    if repo_name in self.setting_inputs:
                        widgets = self.setting_inputs[repo_name]['widgets']
                        
                        for key in ['path', 'url', 'correct_package_name', 'version']:
                            if key in widgets:
                                repo[key] = widgets[key].text()
                        
                        if 'auto_update' in widgets:
                            repo['auto_update'] = widgets['auto_update'].isChecked()

                f.seek(0)
                json.dump(repos_data, f, indent=4)
                f.truncate()

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