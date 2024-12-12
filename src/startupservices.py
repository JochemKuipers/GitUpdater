import os
import logging
import platform

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='gitupdater.log', filemode='w')
logger = logging.getLogger(__name__)

def enable_task_scheduler():
    """Enable task scheduler"""
    if platform.system() == 'Windows':
        return _enable_task_scheduler_windows()
    elif platform.system() == 'Linux':
        return _enable_task_scheduler_linux()
    else:
        logging.error(f"Unsupported platform: {platform.system()}")
        return False
    
def _enable_task_scheduler_windows():
    """Enable Windows task scheduler"""
    try:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        task_name = 'GitUpdater'
        task_path = os.path.join(app_dir, 'main.py')
        task_trigger = 'AtLogon'
        task_cmd = f'python "{task_path}" --headless'
        
        os.system(f'schtasks /create /tn {task_name} /tr "{task_cmd}" /sc {task_trigger} /ru INTERACTIVE')
        return True
    except Exception as e:
        logging.error(f"Error enabling task scheduler: {e}")
        return False
    
def _enable_task_scheduler_linux():
    """Enable Linux task scheduler using cron"""
    try:
        cron_job = '@reboot /usr/bin/python3 {} --headless'.format(os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py')))
        cron_file = os.path.expanduser('~/.cronjob_gitupdater')
        
        with open(cron_file, 'w') as f:
            f.write(cron_job + '\n')
        
        os.system(f'crontab {cron_file}')
        return True
    except Exception as e:
        logging.error(f"Error enabling task scheduler: {e}")
        return False
    

def manage_startup_service(enable: bool) -> bool:
    """Manage startup service"""
    if platform.system() == 'Linux':
        return _manage_startup_service_linux(enable)
    elif platform.system() == 'Windows':
        return _manage_startup_service_windows(enable)
    else:
        logging.error(f"Unsupported platform: {platform.system()}")
        return False
    
def _manage_startup_service_windows(enable: bool) -> bool:
    """Manage Windows startup service"""
    import winreg
    try:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        key = winreg.HKEY_CURRENT_USER
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
        key_name = 'GitUpdater'
        key_value = f'"{os.path.join(app_dir, "main.py")}"'

        if enable:
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE) as reg_key:
                winreg.SetValueEx(reg_key, key_name, 0, winreg.REG_SZ, key_value)
        else:
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE) as reg_key:
                winreg.DeleteValue(reg_key, key_name)
        
        return True
    except Exception as e:
        logging.error(f"Error managing startup service: {e}")
        return False   
    

def _manage_startup_service_linux(enable: bool) -> bool:
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
                f.write(_get_service_content_linux())
            
            # Create desktop entry
            with open(desktop_path, 'w') as f:
                f.write(_get_desktop_content_linux())
                
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

def _get_service_content_linux() -> str:
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
    
def _get_desktop_content_linux() -> str:
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