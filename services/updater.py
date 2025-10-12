"""
Update management module for BRT Shipping Management Application
Contains classes for checking and downloading application updates
"""

import platform
import json
import urllib.request
from pathlib import Path
from typing import List, Dict, Any

from PyQt5.QtCore import QThread, pyqtSignal

from core.constants import NetworkSettings
from core.utils import logger


class UpdateDownloader(QThread):
    """Thread to download the update"""
    download_progress = pyqtSignal(int)  # Download percentage
    download_complete = pyqtSignal(str)  # Downloaded file path
    download_failed = pyqtSignal(str)  # Error message

    def __init__(self, download_url: str, filename: str, download_path: str) -> None:
        super().__init__()
        self.download_url = download_url
        self.filename = filename
        self.download_path = download_path

    def run(self) -> None:
        """Download the file"""
        download_dir = Path(self.download_path)
        file_path = download_dir / self.filename

        try:
            # Download with progress
            req = urllib.request.Request(self.download_url)
            req.add_header('User-Agent', NetworkSettings.USER_AGENT)

            with urllib.request.urlopen(req, timeout=NetworkSettings.TIMEOUT_MEDIUM) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = NetworkSettings.CHUNK_SIZE

                with open(str(file_path), 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.download_progress.emit(progress)

            logger.info(f"Update downloaded successfully to {file_path}")
            self.download_complete.emit(str(file_path))

        except Exception as e:
            logger.error(f"Failed to download update from {self.download_url}: {e}", exc_info=True)
            self.download_failed.emit(str(e))


class UpdateChecker(QThread):
    """Thread to check for updates on GitHub"""
    update_available = pyqtSignal(str, str, str)  # (new_version, release_url, download_url)

    def __init__(self, current_version: str) -> None:
        super().__init__()
        self.current_version = current_version
        self.github_repo = NetworkSettings.GITHUB_REPO

    def run(self) -> None:
        """Check if there's a new version on GitHub"""
        try:
            # GitHub API call to get the latest release
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', NetworkSettings.USER_AGENT)

            with urllib.request.urlopen(req, timeout=NetworkSettings.TIMEOUT_SHORT) as response:
                data = json.loads(response.read().decode())

            latest_version = data.get('tag_name', '').lstrip('v')
            release_url = data.get('html_url', '')

            # Find the right file for the current platform
            download_url = self._get_platform_download_url(data.get('assets', []))

            # Compare versions
            if latest_version and self._is_newer_version(latest_version):
                self.update_available.emit(latest_version, release_url, download_url)

        except Exception as e:
            # Log update check failures (network errors are expected if offline)
            logger.debug(f"Update check failed (this is normal if offline): {e}")

    def _get_platform_download_url(self, assets: List[Dict[str, Any]]) -> str:
        """Find the correct download URL for the platform"""
        system = platform.system()

        for asset in assets:
            name = asset.get('name', '')
            name_lower = name.lower()

            if system == 'Windows':
                # Look for files with _win or windows in the name
                if ('_win' in name_lower or 'windows' in name_lower) and name_lower.endswith('.zip'):
                    return asset.get('browser_download_url', '')
            elif system == 'Darwin':
                # Look for files without _win/windows (so it's for macOS)
                if name_lower.endswith('.zip') and '_win' not in name_lower and 'windows' not in name_lower:
                    return asset.get('browser_download_url', '')

        return ''

    def _is_newer_version(self, latest: str) -> bool:
        """Compare versions (format: X.Y.Z)"""
        try:
            current_parts = [int(x) for x in self.current_version.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]

            # Compare major, minor, patch
            for curr, lat in zip(current_parts, latest_parts):
                if lat > curr:
                    return True
                elif lat < curr:
                    return False

            return False
        except Exception as e:
            logger.debug(f"Failed to compare versions (current: {self.current_version}, latest: {latest}): {e}")
            return False
