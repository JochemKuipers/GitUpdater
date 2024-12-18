import os
import sys
import json
import logging
import requests
import patoolib
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.utils import get_config_path, get_setting_repo
from src.githubAuth import GitHub

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='gitupdater.log', filemode='w')
logger = logging.getLogger(__name__)

repo_path = get_config_path('repos.json')
class DownloadWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, url: str, path: str):
        super().__init__()
        self.url = url
        self.path = path
        
    def run(self):
        try:
            # Create all necessary directories
            os.makedirs(self.path, exist_ok=True)
            
            # Get filename from URL and create full download path
            filename = os.path.basename(self.url)
            full_path = os.path.join(self.path, filename)
            
            logger.info(f"Downloading to: {full_path}")
            
            # Download file
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            
            # Get total file size
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_progress = -1  # Track last reported progress
            
            with open(full_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    downloaded += len(chunk)
                    current_progress = int(downloaded / total_size * 100)
                    
                    # Only emit if progress changed by >= 1%
                    if current_progress > last_progress:
                        self.progress.emit(current_progress)
                        last_progress = current_progress
            
            filetype = filename.split('.')[-1]
            if filetype in ['zip', 'tar', 'gz', 'bz2', '7z']:
                try:
                    logger.info(f"Extracting {filetype} archive")
                    patoolib.extract_archive(full_path, outdir=self.path)
                    os.remove(full_path)
                except Exception as e:
                    logger.error(f"Error during extraction: {e}")
                    self.error.emit(str(e))
            self.finished.emit()
            
        except Exception as e:
            logger.error(f"Error during download/extract: {e}")
            self.error.emit(str(e))

def run_headless_updates(git: GitHub, repos_path: str):
    app = QApplication(sys.argv)
    
    def log_progress(p):
        logger.info(f"Download progress for {current_repo}: {p}%")
        
    def log_error(e):
        logger.error(f"Download error for {current_repo}: {e}")
        
    def quit_app():
        logger.info("Quitting application")
        app.quit()

    def on_worker_finished():
        logger.info("Worker finished")
        thread.quit()
    
    try:
        # Check if repos.json exists
        if not os.path.exists(repos_path):
            logger.error(f"repos.json not found at {repos_path}")
            with open(repos_path, 'w') as f:
                json.dump({"repos": []}, f, indent=4)
            logger.info(f"Created default repos.json at {repos_path}")
            quit_app()
        
        with open(repos_path, 'r') as f:
            data = json.load(f)
            repos = data.get('repos', [])
            
            for repo in repos:
                if get_setting_repo(repos_path, repo['name'], 'auto_update'):
                    current_repo = repo['name']
                    logger.info(f"Checking update for {current_repo}")
                    latest_release = git.get_latest_release_url(repo['url'])
                    asset, _ = git.find_correct_asset_in_list(
                        latest_release, 
                        None,
                        get_setting_repo(repos_path, repo['name'], 'correct_package_name')
                    )
                    
                    if asset:
                        version = git.get_asset_version(asset=asset, page=latest_release)
                        if version != repo['version']:
                            worker = DownloadWorker(asset.browser_download_url, repo['path'])
                            thread = QThread()
                            
                            worker.moveToThread(thread)
                            thread.started.connect(worker.run)
                            worker.progress.connect(log_progress)
                            worker.error.connect(log_error)
                            worker.finished.connect(on_worker_finished)
                            worker.finished.connect(worker.deleteLater)
                            thread.finished.connect(thread.deleteLater)
                            
                            thread.start()
                            while thread.isRunning():
                                app.processEvents()
                            
                            repo['version'] = version
                            with open(repos_path, 'w') as f:
                                json.dump(data, f, indent=4)
                else:
                    logger.info(f"Auto update disabled for {repo['name']}. Skipping")
        logger.info("All updates completed")
        QTimer.singleShot(0, quit_app)
        return app.exec()
        
    except Exception as e:
        logger.error(f"Error in headless update: {e}")
        quit_app()
        return 1
    
def check_for_app_update():
    """Check if the application is up to date"""
    try:
        git = GitHub()
        latest_release = git.get_latest_release_url("https://github.com/JochemKuipers/GitUpdater")
        asset, _ = git.find_correct_asset_in_list(latest_release)
        
        if asset:
            version = git.get_asset_version(asset=asset, page=latest_release)
            with open(os.path.join(os.path.dirname(__file__), "version"), 'r') as f:
                old_version = f.read().strip()
            if version != old_version:
                update_app(asset.browser_download_url)
            else:
                logger.info("No update available")
                QMessageBox.information(None, "No Updates", "You are already using the latest version.")
        else:
            logger.error("No assets found")
            QMessageBox.warning(None, "Error", "No assets found")
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        QMessageBox.warning(None, "Error", f"Error checking for updates: {e}")
def update_app(download_url, parent=None):
    """Update the application if an update is available"""
    try:
        if download_url:
            def log_progress(p):
                logger.info(f"Download progress: {p}%")
                
            def log_error(e):
                logger.error(f"Download error: {e}")
                QMessageBox.warning(parent, "Error", f"Download error: {e}")
                
            def on_worker_finished():
                logger.info("Worker finished")
                update_file = os.path.join(os.path.expanduser("~"), "GitUpdater_update.zip")
                try:
                    patoolib.extract_archive(update_file, outdir=os.path.dirname(__file__))
                    os.remove(update_file)
                    QMessageBox.information(parent, "Update", "The application has been updated. Please restart the application.")
                except Exception as e:
                    logger.error(f"Error applying update: {e}")
                    QMessageBox.warning(parent, "Error", f"Error applying update: {e}")
            
            worker = DownloadWorker(download_url, os.path.expanduser("~"))
            thread = QThread()
            
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            worker.progress.connect(log_progress)
            worker.error.connect(log_error)
            worker.finished.connect(on_worker_finished)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            
            thread.start()
        else:
            logger.info("No update available")
            QMessageBox.information(parent, "No Updates", "You are already using the latest version.")
    except Exception as e:
        logger.error(f"Error updating application: {e}")
        QMessageBox.warning(parent, "Error", f"Error updating application: {e}")
        
def update_app_version(new_version):
    try:
        with open(os.path.join(os.path.dirname(__file__), "version"), 'w') as f:
            f.write(new_version)
        logger.info(f"Updated version to {new_version}")
    except Exception as e:
        logger.error(f"Error updating version: {e}")
        QMessageBox.warning(None, "Error", f"Error updating version: {e}")