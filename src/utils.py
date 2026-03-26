import os
import json
import platform
import platformdirs

def get_setting(config_path, setting_name):
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for category in data['categories']:
            if 'General' in category:
                settings = category['General'][0]['settings'][0]
                if setting_name not in settings:
                    continue

                setting = settings[setting_name][0]
                setting_type = setting.get('type')

                # Non-select settings: prefer explicit "value" if present, otherwise fall back to default.
                if setting_type != 'select':
                    if 'value' in setting:
                        return setting['value']
                    return setting.get('default')

                # Select settings: default may be stored as a label or as a value. Be tolerant.
                default = setting.get('default')
                options = setting.get('options') or []

                # 1) Match by label
                for option in options:
                    if option.get('label') == default:
                        return option.get('value')

                # 2) Match by value
                for option in options:
                    if str(option.get('value')) == str(default):
                        return option.get('value')

                # 3) Common "Never/Off/None" convention for intervals -> 0
                if isinstance(default, str) and default.strip().lower() in {"never", "off", "none"}:
                    return "0"

                # 4) Last resort: if there's an obvious first option, use it
                if options:
                    return options[0].get('value')
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
        config_dir = platformdirs.user_config_dir('GitUpdater')
    elif platform.system() == 'Linux':
        config_dir = platformdirs.user_config_dir('GitUpdater')
    else:
        raise OSError(f"Unsupported OS: {platform.system()}")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_path(filename):
    """Get full path for a config file"""
    return os.path.join(get_config_dir(), filename)