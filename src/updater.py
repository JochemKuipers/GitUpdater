import os
import requests
import patoolib
import logging
import shutil
import platform
from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)

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
            # Download file
            logger.info(f"Downloading file: {self.url}")
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            
            # Get total file size
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            download_path = os.path.join(self.path, os.path.basename(self.url))
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            progress = int((downloaded / total_size) * 100)
                            self.progress.emit(progress)
                            
            filetype = os.path.splitext(download_path)[1]
            if filetype in ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.7z', '.rar']:
                # Extract archive
                logger.info(f"Extracting archive: {download_path}")
                try:
                    patoolib.extract_archive(download_path, outdir=self.path)
                except Exception as e:
                    logger.error(f"Error extracting archive: {e}")
                    self.error.emit(str(e))
            elif filetype in ['.exe', '.msi'] and platform.system().lower == 'windows':
                # Run installer
                try:
                    os.chdir(self.path)
                    os.system(download_path)
                except Exception as e:
                    logger.error(f"Error running installer: {e}")
                    self.error.emit(str(e))
            elif filetype in ['.deb'] and platform.system().lower() == 'linux' and shutil.which('dpkg'):
                # Install deb package
                try:
                    os.system(f'sudo dpkg -i {download_path}')
                except Exception as e:
                    logger.error(f"Error installing deb package: {e}")
                    self.error.emit(str(e))
            else:
                # Move file to destination
                try:
                    shutil.move(download_path, self.path)
                except Exception as e:
                    logger.error(f"Error moving file: {e}")
                    self.error.emit(str(e))
            # Cleanup
            os.remove(download_path)
            self.finished.emit()
        except Exception as e:
            logger.error(f"Error during download/extract: {e}")
            self.error.emit(str(e))