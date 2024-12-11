import os
import json

def get_setting(config_path, setting_name, value=None):
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for category in data['categories']:
            if 'General' in category:
                settings = category['General'][0]['settings'][0]
                if setting_name in settings:
                    return settings[setting_name][0].get('value', value)
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
    config_dir = os.path.join(
        os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')),
        'gitupdater'
    )
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_path(filename):
    """Get full path for a config file"""
    return os.path.join(get_config_dir(), filename)