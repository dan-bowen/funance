"""
Handle updating Chromedriver

SEE https://sites.google.com/chromium.org/driver/downloads/version-selection
"""

import os
import plistlib
import shutil
import stat
import typing as t
import zipfile
from pathlib import Path

import requests

from funance.common.logger import get_logger
from funance.scrape.driver.session import Session

logger = get_logger('chromedriver')

CHROME_PATH = '/Applications/Google Chrome.app'
PLIST_PATH = f"{CHROME_PATH}/Contents/Info.plist"

# the files expected to be in the download folder
driver_files = [
    'chromedriver_linux64.zip',
    'chromedriver_mac64.zip',
    'chromedriver_mac64_m1.zip',
    'chromedriver_win32.zip',
    'notes.txt'
]


class Updater:
    """Logic for updating Chromedriver"""

    def __init__(self, chromedriver_dir: t.Union[str, bytes, os.PathLike]) -> None:
        self._chromedriver_dir = chromedriver_dir

    @staticmethod
    def get_chrome_version() -> str:
        """
        Get installed Chrome version

        :return:
        """
        ver = None

        # TODO get version based on platform
        if os.path.exists(PLIST_PATH):
            with open(PLIST_PATH, 'rb') as fp:
                pl = plistlib.load(fp)
            ver = pl["CFBundleShortVersionString"]
        return ver

    @staticmethod
    def get_chromedriver_upstream_version(chrome_version: str) -> str:
        """
        Find the latest upstream Chromedriver version

        :param chrome_version:
        :return:
        """
        v = Updater.parse_version(chrome_version)
        url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{v['major']}.{v['minor']}.{v['build']}"
        r = requests.get(url)
        latest = r.text
        return latest

    @staticmethod
    def download_file(url, local_filename) -> t.Union[str, bytes, os.PathLike]:
        """Download a file"""
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        return local_filename

    @staticmethod
    def parse_version(version: str) -> dict:
        """Parse version into dict"""
        parts = version.split('.')
        return dict(major=parts[0], minor=parts[1], build=parts[2], patch=parts[3])

    def local_chromedriver_exists(self, chromedriver_version: str) -> bool:
        """Check if local Chromedriver exists for a specific version"""
        return os.path.exists(self.get_chromedriver_dir(chromedriver_version))

    def get_chromedriver_dir(self, chromedriver_version: str) -> t.Union[str, bytes, os.PathLike]:
        """Get the path to chromedriver for a specific version"""
        return os.path.join(self._chromedriver_dir, chromedriver_version)

    def get_chromedriver_local_version(self, chrome_version: str) -> t.Union[str, None]:
        """
        Get latest installed major.minor.build version for the given chrome_version

        :param chrome_version: The Chrome version for which to find a matching Chromedriver version
        :type chrome_version: str

        :return: The latest installed chromedriver version, or None if no matching version
        :rtype: t.Union[str, None]
        """
        v = Updater.parse_version(chrome_version)
        # iterate directory where drivers are stored
        matching_dirs = {
            d: int(d.replace('.', ''))
            for d in os.listdir(self._chromedriver_dir)
            if d.startswith(f"{v['major']}.{v['minor']}.{v['build']}")
        }
        # get the key where the highest value is stored
        max_key = max(matching_dirs, key=matching_dirs.get)
        best_match = None if len(matching_dirs) == 0 else max_key
        return best_match

    def download_chromedriver(self, chromedriver_version: str) -> None:
        """Download chromedriver"""
        local_dir = self.get_chromedriver_dir(chromedriver_version)
        Path(local_dir).mkdir()
        for f in driver_files:
            url = f"https://chromedriver.storage.googleapis.com/{chromedriver_version}/{f}"
            logger.info(f'downloading file: {url}')
            local_file = self.download_file(url, os.path.join(local_dir, f))
            logger.info(f'downloaded local file: {local_file}')

    def extract_files(self, chromedriver_version: str) -> None:
        """Extract zip files"""
        local_dir = self.get_chromedriver_dir(chromedriver_version)
        matching_files = [
            f for f in os.listdir(local_dir) if f.endswith('.zip')
        ]
        for mf in matching_files:
            local_file = os.path.join(local_dir, mf)
            extract_dir = os.path.join(local_dir, mf.replace('.zip', ''))
            with zipfile.ZipFile(local_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # make the extracted files executable
            for ef in os.listdir(extract_dir):
                fname = os.path.join(extract_dir, ef)
                st = os.stat(fname)
                os.chmod(fname, st.st_mode | stat.S_IEXEC)

    def update(self) -> None:
        """Update Chromedriver"""
        chrome_version = self.get_chrome_version()
        logger.info(f'chrome version: {chrome_version}')

        chromedriver_upstream_version = self.get_chromedriver_upstream_version(chrome_version)
        logger.info(f'chromedriver upstream version: {chromedriver_upstream_version}')

        if not self.local_chromedriver_exists(chromedriver_upstream_version):
            logger.info('Local Chromedriver does not exist. Downloading....')
            self.download_chromedriver(chromedriver_upstream_version)
            self.extract_files(chromedriver_upstream_version)

        chromedriver_local_version = self.get_chromedriver_local_version(chrome_version)
        logger.info(f'chromedriver local version: {chromedriver_local_version}')

        # TODO set chromedriver version a different way. It's not relevant to the session
        sess = Session.from_file(self._chromedriver_dir)
        sess.session.chromedriver_version = chromedriver_local_version
        sess.close()
