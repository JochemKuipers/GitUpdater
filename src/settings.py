import os
import json
from PyQt6 import QtWidgets, QtCore
from components.settingframe import SettingsFrame
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='gitupdater.log', filemode='w')
logger = logging.getLogger(__name__)
class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self, assets):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setting_inputs = {}
        self.tab_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.tab_widget.setCornerWidget(self.save_button, QtCore.Qt.Corner.TopRightCorner)
        self.assets = assets

    def load_settings(self):
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        try:
            if not os.path.exists('data/config.json'):
                logging.info("Creating config.json")
                with open('data/config.json', 'w') as f:
                    json.dump({"categories": []}, f)
                    
            if not os.path.exists('data/repos.json'):
                logging.info("Creating repos.json")
                with open('data/repos.json', 'w') as f:
                    json.dump({"repos": []}, f)
                    
            with open('data/config.json', 'r') as f:
                logging.info("Loading settings")
                config = json.load(f)

            for category in config['categories']:
                category_name = list(category.keys())[0]  # Get category name (General or Repositories)
                logging.info(f"Loading category: {category_name}")
                if category_name == 'Repositories':
                    try:
                        self._load_repo_category(category)
                    except Exception as e:
                        QtWidgets.QMessageBox.warning(self, "Error", f"Error loading repository settings: {e}")
                        logging.error(f"Error loading repository settings: {e}")
                else:
                    try:
                        logging.info("Loading general settings")
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
                        QtWidgets.QMessageBox.warning(self, "Error", f"Error loading general settings: {e}")
                        logging.error(f"Error loading general settings: {e}")

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error loading settings: {e}")
            logging.error(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            logging.info("Saving settings")
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
                        
                        for key, widget in widgets.items():
                            if isinstance(widget, QtWidgets.QCheckBox):
                                repo[key] = widget.isChecked()
                            elif isinstance(widget, QtWidgets.QComboBox):
                                repo[key] = widget.currentText()
                            else:
                                repo[key] = widget.text()

                f.seek(0)
                json.dump(repos_data, f, indent=4)
                f.truncate()

            QtWidgets.QMessageBox.information(self, "Success", "Settings saved successfully")
            logging.info("Settings saved successfully")

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error saving settings: {e}")
            logging.error(f"Error saving settings: {e}")

    def _load_repo_category(self, category):
        logging.info("Loading repository settings")
        try:
            with open('data/repos.json', 'r') as f:
                repos_data = json.load(f)
            if repos_data['repos']:
                repo_tab = QtWidgets.QWidget()
                repo_layout = QtWidgets.QVBoxLayout()
                self.repo_tab_widget = QtWidgets.QTabWidget()

                for repo in repos_data['repos']:
                    repo_sub_tab = QtWidgets.QWidget()
                    repo_sub_layout = QtWidgets.QVBoxLayout()

                    self.setting_inputs[repo['name']] = {
                        'widgets': {},
                        'settings': {}
                    }

                    # Format options correctly
                    asset_options = ["Auto Detect"]
                    if repo['name'] in self.assets:
                        asset_options.extend([asset.name for asset in self.assets[repo['name']]])
                        
                    settings_map = {
                        'path': ('Path', 'path'),
                        'url': ('URL', 'url'),
                        'correct_package_name': ('Correct Package Name', 'select', asset_options),  # Pass formatted options
                        'version': ('Version', 'text'),
                        'auto_update': ('Auto Update', 'checkbox')
                    }

                    for key, setting_info in settings_map.items():
                        label = setting_info[0]
                        setting_type = setting_info[1]
                        options = setting_info[2] if len(setting_info) > 2 else None
                        
                        setting_frame = SettingsFrame(
                            label=label,
                            setting_type=setting_type,
                            default_value=repo.get(key, ''),
                            options=options
                        )
                        repo_sub_layout.addWidget(setting_frame)
                        
                        self.setting_inputs[repo['name']]['settings'][key] = repo.get(key, '')
                        self.setting_inputs[repo['name']]['widgets'][key] = setting_frame.get_widget()

                    repo_sub_tab.setLayout(repo_sub_layout)
                    self.repo_tab_widget.addTab(repo_sub_tab, repo['name'].split('/')[-1])

                repo_layout.addWidget(self.repo_tab_widget)
                repo_tab.setLayout(repo_layout)
                self.tab_widget.addTab(repo_tab, "Repositories")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "No repositories found")
                logging.error("No repositories found")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error loading repository settings: {e}")
            logging.error(f"Error loading repository settings: {e}")