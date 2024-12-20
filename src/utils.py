import os
import json
import platform

def get_setting(config_path, setting_name):
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for category in data['categories']:
            if 'General' in category:
                settings = category['General'][0]['settings'][0]
                if setting_name in settings and settings[setting_name][0]['type'] != 'select':
                    return settings[setting_name][0]['default']
                else:
                    setting = settings[setting_name][0]
                    default = setting.get('default')
                    for option in setting['options']:
                        if option['label'] == default:
                            return option['value']
        raise ValueError(f"Setting {setting_name} not found")

def get_setting_repo(repos_path, repo_name, setting_name):
    with open(repos_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for repo in data['repos']:
            if repo['name'] == repo_name:
                if setting_name in repo:
                    return repo[setting_name]
        raise ValueError(f"Setting {setting_name} not found")
    
def get_config_dir():
    """Get user config directory"""
    if platform.system() == 'Windows':
        config_dir = os.path.join(os.getenv('APPDATA'), 'GitUpdater')
    elif platform.system() == 'Linux':
        config_dir = os.path.join(os.getenv('HOME'), '.config', 'GitUpdater')
    else:
        raise OSError(f"Unsupported OS: {platform.system()}")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_path(filename):
    """Get full path for a config file"""
    return os.path.join(get_config_dir(), filename)