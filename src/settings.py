import os
import json
from PyQt6 import QtWidgets, QtCore
from components.settingframe import SettingsFrame
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='gitupdater.log', filemode='w')
logger = logging.getLogger(__name__)

def get_config_dir():
    """Get user config directory"""
    config_dir = os.path.join(
        os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')),
        'gitupdater'
    )
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_path(filename):
    """Get full path for a config file"""
    return os.path.join(get_config_dir(), filename)

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
        self.config_path = get_config_path('config.json')
        self.repos_path = get_config_path('repos.json')

    def load_settings(self):
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        try:
            if not os.path.exists(self.config_path):
                logging.info("Creating config.json")
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    with open(os.path.join(os.path.dirname(__file__), 'config_template.json'), 'r') as template:
                        json.dump(json.load(template), f)
                    
            if not os.path.exists(self.repos_path):
                logging.info("Creating repos.json")
                os.makedirs(os.path.dirname(self.repos_path), exist_ok=True)
                with open(self.repos_path, 'w') as f:
                    json.dump({"repos": []}, f)
                    
            with open(self.config_path, 'r') as f:
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
                                            self.manage_startup_service(new_value)
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

    def _load_repo_category(self, category):
        logging.info("Loading repository settings")
        try:
            with open(self.repos_path, 'r') as f:
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
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "No repositories found")
                logging.error("No repositories found")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error loading repository settings: {e}")
            logging.error(f"Error loading repository settings: {e}")
            
    def manage_startup_service(self, enable: bool) -> bool:
        """Manage systemd user service for startup"""
        try:
            service_dir = os.path.expanduser('~/.config/systemd/user')
            service_path = os.path.join(service_dir, 'gitupdater.service')
            autostart_dir = os.path.expanduser('~/.config/autostart')
            desktop_path = os.path.join(autostart_dir, 'gitupdater.desktop')

            if enable:
                os.makedirs(service_dir, exist_ok=True)
                os.makedirs(autostart_dir, exist_ok=True)
                
                # Create service file
                with open(service_path, 'w') as f:
                    f.write(self._get_service_content())
                
                # Create desktop entry
                with open(desktop_path, 'w') as f:
                    f.write(self._get_desktop_content())
                    
                os.chmod(service_path, 0o644)
                os.chmod(desktop_path, 0o644)
                os.system('systemctl --user enable gitupdater.service')
                os.system('systemctl --user start gitupdater.service')
            else:
                os.system('systemctl --user stop gitupdater.service')
                os.system('systemctl --user disable gitupdater.service')
                if os.path.exists(service_path):
                    os.remove(service_path)
                if os.path.exists(desktop_path):
                    os.remove(desktop_path)
            
            return True
        except Exception as e:
            logging.error(f"Error managing startup service: {e}")
            return False

    def _get_service_content(self) -> str:
        """Get systemd service file content"""
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_path = os.popen('which python3').read().strip()
        venv_path = os.path.join(app_dir, '.venv')
        
        return f"""[Unit]
Description=GitUpdater Application
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
Environment=DISPLAY=:0
Environment=XAUTHORITY={os.path.expanduser('~/.Xauthority')}
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{os.getuid()}/bus
Environment=XDG_RUNTIME_DIR=/run/user/{os.getuid()}
Environment=PYTHONPATH={app_dir}
Environment=PATH={os.path.dirname(python_path)}:/usr/local/bin:/usr/bin:/bin
WorkingDirectory={app_dir}
ExecStartPre=/bin/bash -c 'test -d {venv_path} || python3 -m venv {venv_path}'
ExecStartPre=/bin/bash -c '{venv_path}/bin/pip install -r {app_dir}/requirements.txt'
ExecStart={venv_path}/bin/python3 {os.path.join(app_dir, 'main.py')}
Restart=on-failure
RestartSec=30

[Install]
WantedBy=graphical-session.target
"""
    
    def _get_desktop_content(self) -> str:
        """Get desktop entry file content"""
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        return f"""[Desktop Entry]
Type=Application
Name=GitUpdater
Exec=/usr/bin/python3 {os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))}
Path={app_dir}
Icon={app_dir}/assets/giticon.svg
Terminal=false
Categories=Utility;
"""