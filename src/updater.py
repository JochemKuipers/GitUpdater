from concurrent.futures import ThreadPoolExecutor
import requests
import os
import patoolib
import platform

def download_file(url, path):
    """Download a single file from URL to specified path"""
    try:
        if not os.path.exists(path):
            raise FileNotFoundError("Download path does not exist")
            
        filename = url.split('/')[-1]
        full_path = os.path.join(path, filename)
        
        # Skip if file already exists
        if os.path.exists(full_path):
            return full_path
            
        # Download file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(full_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
        
        return full_path
                
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Path does not exist: {path}") from e
    except requests.exceptions.RequestException as e:
        raise Exception(f"Download failed: {str(e)}") from e
    except Exception as e:
        raise Exception(f"Error downloading file: {str(e)}") from e

def download_files(urls, paths):
    """Download multiple files concurrently"""
    try:
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(download_file, urls, paths))
        return results
    except Exception as e:
        raise Exception(f"Error downloading files: {str(e)}") from e
        
def unarchive_file(file_path, output_path):
    """Extract archive to specified output path"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archive file not found: {file_path}")
            
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        patoolib.extract_archive(file_path, outdir=output_path)
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {str(e)}") from e
    except Exception as e:
        raise Exception(f"Error extracting archive: {str(e)}") from e
    
def update(url, path):
    """Download and process update file"""
    try:
        # Download file
        file_path = download_file(url, path)
        if not file_path:
            raise Exception("Download failed")
            
        # Handle different file types
        if file_path.endswith('.exe'):
            if platform.system() == 'Windows':
                windows_exe_execute(file_path)
            else:
                raise Exception("Cannot execute .exe file on non-Windows system")
        elif any(file_path.endswith(ext) for ext in ['.zip', '.tar.gz', '.rar', '.7z']):
            unarchive_file(file_path, path)
        else:
            raise Exception("Unsupported file type")
            
    except Exception as e:
        raise Exception(f"Update failed: {str(e)}") from e

def windows_exe_execute(exe_path):
    if platform.system().lower() == 'windows':
        try:
            os.chdir(os.path.dirname(exe_path))
            os.system(f'{exe_path}')
        except Exception as e:
            raise "Error executing Windows executable: " + str(e)
    else:
        raise "This function is only available on Windows"