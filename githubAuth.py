import os
import dotenv
import platform
import re
from github import Github, Auth
from PyQt6 import QtWidgets


def clean_github_link(link: str) -> str:
    """
    Removes everything from a GitHub link after the repository name.

    Args:
        link (str): The GitHub URL.

    Returns:
        str: The cleaned GitHub URL.
    """
    pattern = r"(https://github\.com/[^/]+/[^/]+)/?.*"
    match = re.match(pattern, link)
    return match.group(1) if match else link

def arch_variants(arch):
    arch = arch.lower()
    if arch in ['32bit', '32-bit', 'x86', 'i386', 'i686']:
        return ['32bit', '32-bit', 'x86', 'i386', 'i686']
    elif arch in ['64bit', '64-bit', 'x64', 'x86_64', 'amd64']:
        return ['64bit', '64-bit', 'x64', 'x86_64', 'amd64']
    elif arch in ['arm', 'armhf', 'arm64', 'armv7', 'armv8', 'aarch64']:
        return ['arm', 'armhf', 'arm64', 'armv7', 'armv8', 'aarch64']
    else:
        return [arch]        

class GitHub():
    def __init__(self):
        dotenv.load_dotenv()

        self.auth = Auth.Token(dotenv.get_key(".env", "GITHUB_ACCESS_TOKEN"))
        self.g = Github(auth=self.auth)

        self.g.get_user().login
        
        self.current_os = platform.system().lower()
        self.current_arch = platform.machine().lower()
        print(f"OS: {self.current_os}, Architecture: {self.current_arch}")
    
    def get_latest_release_url(self, repo_url):
        repo_name = repo_url.split('/')[3] + '/' + repo_url.split('/')[4]
        repo = self.g.get_repo(repo_name)
        latest_release = repo.get_latest_release()
        return latest_release
    
    def get_asset_version(self, asset, page):
        # Try to extract version number from the release title
        version_pattern = re.compile(r'\d+(\.\d+)+')
        match = version_pattern.search(page.title)
        
        if match:
            return match.group(0)
        else:
            # If no version number is found, use the upload date
            return asset.updated_at.astimezone().strftime("%Y-%m-%d")
        
    def find_correct_asset_in_list(self, latest_release, parent_widget, correct_package_name=None):
        current_os = platform.system().lower()
        current_arch = platform.machine().lower()
        arch_variants_list = arch_variants(current_arch)       
        
        os_filtered_assets = [asset for asset in latest_release.get_assets() if current_os in asset.name.lower()]
        
        if correct_package_name:
            # Replace * with a regex pattern to match any version number
            correct_package_name_pattern = re.escape(correct_package_name).replace(r'\*', r'\d+(\.\d+)*')
            for asset in os_filtered_assets:
                if re.match(correct_package_name_pattern, asset.name):
                    return asset, correct_package_name
        
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
        return None, None