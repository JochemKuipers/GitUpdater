import os
import json
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from components.settingframe import SettingsFrame
import logging
from src.startupservices import manage_startup_service
from src.utils import get_config_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='gitupdater.log', filemode='w')
logger = logging.getLogger(__name__)


class SettingsLoader(QObject):
    # Add signal for widget data
    category_data_ready = pyqtSignal(str, dict)  # category, settings_data
    repo_data_ready = pyqtSignal(dict)  # New signal for repo data
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, settings_window):
        super().__init__()
        self.settings_window = settings_window  # Correct assignment
        self.config_path = get_config_path('config.json')
        self.repos_path = get_config_path('repos.json')

    def _load_general_category(self, category: str):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            categories = config.get('categories', [])
            category_data = None
            settings_data = {}

            # Find and process category data
            for cat in categories:
                if category in cat:
                    category_data = cat[category]
                    if isinstance(category_data, list) and category_data:
                        settings_list = category_data[0].get('settings', [])
                        if settings_list and isinstance(settings_list[0], dict):
                            settings_data = settings_list[0]
                    break

            # Emit data instead of creating widgets
            self.category_data_ready.emit(category, settings_data)

        except Exception as e:
            self.error.emit(f"Error loading general settings: {str(e)}")

    def _load_repo_category(self):
        try:
            with open(self.repos_path, 'r') as f:
                repos_data = json.load(f)
            if 'repos' in repos_data and repos_data['repos']:
                self.repo_data_ready.emit(repos_data)
        except Exception as e:
            self.error.emit(f"Error loading repository settings: {str(e)}")

    def run(self):
        try:
            # Load categories from config file
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Get list of categories from config
            categories = []
            for cat_dict in config.get('categories', []):
                # Each category is a dict with one key
                categories.extend(cat_dict.keys())
            
            logger.debug(f"Found categories: {categories}")

            # Process each category once
            processed = set()
            for category in categories:
                if category in processed:
                    continue
                    
                processed.add(category)
                if category == 'Repositories':
                    self._load_repo_category()
                else:
                    self._load_general_category(category)

        except Exception as e:
            self.error.emit(f"Error loading categories: {str(e)}")
            logger.error(f"Error loading categories: {e}")
        finally:
            self.finished.emit()

class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self, assets):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setting_inputs = {}
        self.tab_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.tab_widget.setCornerWidget(self.save_button, QtCore.Qt.Corner.BottomRightCorner)
        self.assets = assets
        
        self.config_path = get_config_path('config.json')
        self.repos_path = get_config_path('repos.json')

    def clear_tabs(self):
        """Clear all existing tabs"""
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        self.setting_inputs.clear()

    def load_settings(self):
        """Initialize settings loading"""
        # Clear existing tabs first
        self.clear_tabs()
        
        self.loader_thread = QThread()
        self.loader = SettingsLoader(self)
        self.loader.moveToThread(self.loader_thread)
        
        # Connect signals
        self.loader_thread.started.connect(self.loader.run)
        self.loader.category_data_ready.connect(self.create_category_widgets)
        self.loader.repo_data_ready.connect(self.create_repo_widgets)
        self.loader.finished.connect(self.loader_thread.quit)
        self.loader.error.connect(lambda msg: logger.error(msg))
        
        self.loader_thread.start()
        
    def create_repo_widgets(self, repos_data: dict):
        """Create widgets for repository settings"""
        try:
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
                    'version': ('Installed Version', 'text'),
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
        except Exception as e:
            logger.error(f"Error creating repository widgets: {e}")

    def create_category_widgets(self, category: str, settings_data: dict):
        """Create widgets in the main thread"""
        try:
            category_tab = QtWidgets.QWidget()
            category_layout = QtWidgets.QVBoxLayout()
            
            self.setting_inputs[category] = {
                'widgets': {},
                'settings': {}
            }

            for setting_key, setting_list in settings_data.items():
                if not isinstance(setting_list, list) or not setting_list:
                    continue

                setting = setting_list[0]
                
                label = str(setting.get('label', setting_key))
                setting_type = str(setting.get('type', 'text'))
                default_value = setting.get('value', setting.get('default', ''))
                
                options = {}
                if setting_type == 'select' and 'options' in setting:
                    options = setting['options']

                setting_frame = SettingsFrame(
                    label=label,
                    setting_type=setting_type,
                    default_value=default_value,
                    options=options
                )
                category_layout.addWidget(setting_frame)

                self.setting_inputs[category]['settings'][setting_key] = setting
                self.setting_inputs[category]['widgets'][setting_key] = setting_frame.get_widget()

            category_tab.setLayout(category_layout)
            self.tab_widget.addTab(category_tab, category)

        except Exception as e:
            logger.error(f"Error creating widgets: {e}")

    def _add_tab(self, name: str, widget: QtWidgets.QWidget):
        self.tab_widget.addTab(widget, name)

    def _show_error(self, error: str):
        QtWidgets.QMessageBox.warning(self, "Error", f"Error loading settings: {error}")

    def _on_loading_finished(self):
        self.loading_bar.hide()
        self.save_button.setEnabled(True)

    def save_settings(self):
        try:
            logging.info("Saving settings")
            # Save general settings to config.json
            with open(self.config_path, 'r+') as f:
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
                                    if setting_key == 'start_on_boot':
                                        old_value = setting.get('value', False)
                                        new_value = widget.isChecked()
                                        if old_value != new_value:
                                            manage_startup_service(new_value)
                                    else:
                                        setting['value'] = widget.isChecked()
                                elif isinstance(widget, QtWidgets.QComboBox):
                                    setting['value'] = widget.currentText()
                                else:
                                    setting['value'] = widget.text()
                
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()

            # Save repository settings to repos.json
            with open(self.repos_path, 'r+') as f:
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