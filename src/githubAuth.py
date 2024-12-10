import sys
import dotenv
import platform
import re
from github import Github, Auth
from PyQt6 import QtWidgets
from PyQt6.QtCore import QObject, pyqtSignal, QEventLoop
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

class AssetSelector(QObject):
    selection_needed = pyqtSignal(list, str)
    selection_complete = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._selected_asset = None
        self._selection_event = None
        self.selection_complete.connect(self._handle_selection)
    
    def wait_for_selection(self):
        """Wait for user selection"""
        self._selection_event = QEventLoop()
        self._selection_event.exec()
        result = self._selected_asset
        self._selected_asset = None
        return result
        
    def _handle_selection(self, asset_name):
        """Handle selection completion"""
        self._selected_asset = asset_name
        if self._selection_event and self._selection_event.isRunning():
            self._selection_event.quit()

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
            
            self.selector = AssetSelector()
            
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
        
    def find_correct_asset_in_list(self, latest_release, parent: QtWidgets.QWidget = None, correct_package_name: str = None):
        try:
            """Find correct asset from release assets list
        
            Args:
                latest_release: GitHub release object
                parent (QWidget): Parent widget for dialogs
                correct_package_name (str): Previously selected package name pattern
            """
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

            if not os_filtered_assets:
                QtWidgets.QMessageBox.warning(parent, "Info", "No assets found for the current OS and architecture.")
                logger.error("No assets found for the current OS and architecture.")
                return None, None
            
            if correct_package_name:
                # Filter assets by package name pattern
                correct_package_name_pattern = re.escape(correct_package_name).replace(r'\*', r'\d+(\.\d+)*')
                for asset in os_filtered_assets:
                    if re.match(correct_package_name_pattern, asset.name):
                        return asset, None

            if len(os_filtered_assets) == 1:
                return os_filtered_assets[0], None

            # Emit selection needed signal and return None to wait for callback
            if len(os_filtered_assets) > 1:
                self.selector.selection_needed.emit(
                    [asset.name for asset in os_filtered_assets],
                    "Select Package"
                )
                selected_name = self.selector.wait_for_selection()
                if selected_name:
                    selected_asset = next(
                        (a for a in os_filtered_assets if a.name == selected_name),
                        None
                    )
                    return selected_asset, selected_name
                    
            return os_filtered_assets[0], os_filtered_assets[0].name
            
        except Exception as e:
            logger.error(f"Error finding correct asset: {e}")
            return None, None