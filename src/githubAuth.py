import sys
import dotenv
import platform
import re
from github import Github, Auth
from PyQt6 import QtWidgets
import time
from functools import lru_cache
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='gitupdater.log', filemode='w')
logger = logging.getLogger(__name__)

def timed_cache(seconds: int):
    def wrapper_decorator(func):
        func = lru_cache(maxsize=128)(func)
        func.lifetime = seconds
        func.expiration = time.time() + seconds
        return func
    return wrapper_decorator


def clean_github_link(link: str) -> str:
    pattern = r"(https://github\.com/[^/]+/[^/]+)/?.*"
    match = re.match(pattern, link)
    return match.group(1) if match else link

def arch_variants(arch: str) -> list:
    arch = arch.lower()
    if arch in ['32bit', '32-bit', 'x86', 'i386', 'i686']:
        return ['32bit', '32-bit', 'x86', 'i386', 'i686']
    elif arch in ['64bit', '64-bit', 'x64', 'x86_64', 'amd64']:
        return ['64bit', '64-bit', 'x64', 'x86_64', 'amd64']
    elif arch in ['arm', 'armhf', 'arm64', 'armv7', 'armv8', 'aarch64']:
        return ['arm', 'armhf', 'arm64', 'armv7', 'armv8', 'aarch64']
    else:
        return [arch]        

def resource_path(relative_path):
    """Get absolute path to resource"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class GitHub():
    def __init__(self):
        # Load env from executable directory or current directory
        env_path = resource_path('.env')
        try:
            if not dotenv.load_dotenv(env_path):
                raise FileNotFoundError(".env file not found")
                
            token = os.getenv("GITHUB_ACCESS_TOKEN")
            if not token:
                raise ValueError("GitHub access token not found in .env")
                
            self.auth = Auth.Token(token)
            self.g = Github(auth=self.auth)
            # Test connection
            self.g.get_user().login
            
            self.current_os = platform.system().lower()
            logger.info(f"OS: {self.current_os}")
            self.current_arch = platform.machine().lower()
            logger.info(f"Architecture: {self.current_arch}")
            
        except Exception as e:
            logger.error(f"GitHub initialization failed: {e}")
            raise
    
    @timed_cache(300)
    def get_latest_release_url(self, repo_url):
        logger.info(f"Getting latest release URL for {repo_url}")
        repo_name = repo_url.split('/')[3] + '/' + repo_url.split('/')[4]
        repo = self.g.get_repo(repo_name)
        if not repo:
            logger.error(f"Repository not found for {repo_name}")
            return None
        latest_release = repo.get_latest_release()
        if not latest_release:
            logger.error(f"Latest release not found for {repo_name}")
            return None
        return latest_release
    
    def get_asset_version(self, asset, page):
        logger.info(f"Getting asset version for {asset.name}")
        # Try to extract version number from the release title
        version_pattern = re.compile(r'\d+(\.\d+)+')
        match = version_pattern.search(page.title)
        
        if match:
            return match.group(0)
        else:
            # If no version number is found, use the upload date
            return asset.updated_at.astimezone().strftime("%Y-%m-%d")
        
    def find_correct_asset_in_list(self, latest_release, parent_widget, correct_package_name=None):
        logger.info(f"Finding correct asset in list for {latest_release.html_url}")
        arch_variants_list = arch_variants(self.current_arch)       
        
        os_filtered_assets = []
        for asset in latest_release.get_assets():
            asset_name = asset.name.lower()
            if self.current_os in asset_name:
                os_filtered_assets.append(asset)
            elif self.current_os == 'linux' and asset_name.endswith('.appimage'):
                os_filtered_assets.append(asset)
            elif self.current_os == 'windows' and asset_name.endswith('.exe'):
                os_filtered_assets.append(asset)
            elif self.current_os == 'darwin' and asset_name.endswith('.dmg'):
                os_filtered_assets.append(asset)
        
        if correct_package_name:
            # Replace * with a regex pattern to match any version number
            correct_package_name_pattern = re.escape(correct_package_name).replace(r'\*', r'\d+(\.\d+)*')
            for asset in os_filtered_assets:
                if re.match(correct_package_name_pattern, asset.name):
                    return asset, None
        
        if len(os_filtered_assets) == 1:
            return os_filtered_assets[0], None
        elif len(os_filtered_assets) > 1:
            # Further filter by current architecture variants if more than one asset is found
            arch_filtered_assets = [asset for asset in os_filtered_assets if any(variant in asset.name.lower() for variant in arch_variants_list)]
            
            if len(arch_filtered_assets) == 1:
                return arch_filtered_assets[0], None
            elif len(arch_filtered_assets) > 1:
                # Create a dialog to choose the correct asset
                items = [asset.name for asset in arch_filtered_assets]
                item, ok = QtWidgets.QInputDialog.getItem(parent_widget, "Select Asset", "Multiple assets found. Please select the correct asset:", items, 0, False)
                if ok and item:
                    for asset in arch_filtered_assets:
                        if asset.name == item:
                            return asset, item
        QtWidgets.QMessageBox.warning(parent_widget, "Info", "No assets found for the current OS and architecture.")
        logger.error(f"No assets found for the current OS and architecture.")
        return None, None