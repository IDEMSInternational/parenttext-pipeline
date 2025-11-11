import requests
import subprocess
import os
import tempfile
from typing import List, Dict

def check_url_existence(url: str) -> bool:
    """
    Checks if a URL exists and is accessible without downloading the full content.
    """
    try:
        # Use HEAD request with allow_redirects=True
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error checking URL {url}: {e}")
        return False

def verify_media_integrity(url: str) -> str:
    """
    Downloads the media file to a temporary location and uses FFmpeg to check integrity.
    FFmpeg attempts to read the file and reports errors.
    """
    if not check_url_existence(url):
        return "Does not exist"

    # Use a temporary file for the download
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, os.path.basename(url))
        
        # Download the file
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except requests.exceptions.RequestException as e:
            return f"Download of {url} failed: {e}"

        # Use FFmpeg to check for corruption
        # -v error: set logging to error level
        # -i: input file
        # -f null -: output to null (standard output)
        # 2>&1: redirect stderr to stdout for capturing errors
        command = [
            'ffmpeg', '-v', 'error', '-i', temp_file_path, '-f', 'null', '-'
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "Valid and not corrupted"
        except subprocess.CalledProcessError as e:
            return f"Corrupted: {e.stderr.decode().strip()}"
        except FileNotFoundError:
            return "Error: FFmpeg not installed or not in PATH"
        except Exception as e:
            return f"An unexpected error occurred during FFmpeg check: {e}"

def process_media_urls(urls: List[str]) -> Dict[str, str]:
    """
    Processes a list of URLs and returns their verification status.
    """
    results = {}
    for url in urls:
        status = verify_media_integrity(url)
        results[url] = status
        if "Valid" not in status:
            print(f"\n--- {url} ---")
            print(f"Status: {status}")
    return results