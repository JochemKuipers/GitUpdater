from concurrent.futures import ThreadPoolExecutor
import requests
import os
import patoolib
import platform
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', filename='gitupdater.log', filemode='w')
logger = logging.getLogger(__name__)

def download_file(url, path):
    """Download a single file from URL to specified path"""
    try:
        logger.info(f"Downloading file: {url}")
        if not os.path.exists(path):
            raise FileNotFoundError("Download path does not exist")
            
        filename = url.split('/')[-1]
        full_path = os.path.join(path, filename)
        
        # Skip if file already exists
        if os.path.exists(full_path):
            logger.info(f"File already exists: {full_path}")
            os.remove(full_path)
            
        # Download file
        response = requests.get(url, stream=True)
        
        response.raise_for_status()
        
        with open(full_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
        logger.info(f"Downloaded file: {full_path}")
        return full_path
                
    except FileNotFoundError as e:
        logger.error(f"Path does not exist: {path}")
        raise FileNotFoundError(f"Path does not exist: {path}") from e
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {str(e)}")
        raise Exception(f"Download failed: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise Exception(f"Error downloading file: {str(e)}") from e

def download_files(urls, paths):
    """Download multiple files concurrently"""
    try:
        logger.info(f"Downloading files: {urls}")
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(download_file, urls, paths))
        logger.info(f"Downloaded files: {results}")
        return results
    except Exception as e:
        logger.error(f"Error downloading files: {str(e)}")
        raise Exception(f"Error downloading files: {str(e)}") from e
        
def unarchive_file(file_path, output_path):
    """Extract archive to specified output path"""
    try:
        logger.info(f"Checking archive file: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"Archive file not found: {file_path}")
            raise FileNotFoundError(f"Archive file not found: {file_path}")
            
        if not os.path.exists(output_path):
            logger.info(f"Creating output path: {output_path}")
            os.makedirs(output_path)
        logger.info(f"Extracting archive: {file_path}")
        patoolib.extract_archive(file_path, outdir=output_path)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise FileNotFoundError(f"File not found: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error extracting archive: {str(e)}")
        raise Exception(f"Error extracting archive: {str(e)}") from e
    
def update(url, path):
    """Download and process update file"""
    try:
        logger.info(f"Updating from: {url}")
        # Download file
        file_path = download_file(url, path)
        if not file_path:
            logger.error("Download failed")
            raise Exception("Download failed")
            
        # Handle different file types
        if file_path.endswith('.exe'):
            if platform.system() == 'Windows':
                windows_exe_execute(file_path)
            else:
                logger.error("Cannot execute .exe file on non-Windows system")
                raise Exception("Cannot execute .exe file on non-Windows system")
        elif any(file_path.endswith(ext) for ext in ['.zip', '.tar.gz', '.rar', '.7z']):
            logger.info(f"Extracting archive: {file_path}")
            unarchive_file(file_path, path)
        else:
            logger.error("Unsupported file type")
            raise Exception("Unsupported file type")
        
        logger.info(f"Update complete: {file_path}")
        os.remove(file_path)
            
    except Exception as e:
        logger.error(f"Update failed: {str(e)}")
        raise Exception(f"Update failed: {str(e)}") from e

def windows_exe_execute(exe_path):
    if platform.system().lower() == 'windows':
        logger.info(f"Executing Windows executable: {exe_path}")
        try:
            os.chdir(os.path.dirname(exe_path))
            os.system(f'{exe_path}')
        except Exception as e:
            logger.error(f"Error executing Windows executable: {str(e)}")
            raise "Error executing Windows executable: " + str(e)
    else:
        logger.error("This function is only available on Windows")
        raise "This function is only available on Windows"