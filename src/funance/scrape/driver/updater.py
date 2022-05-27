import os
import plistlib
import shutil
import stat
import zipfile
from pathlib import Path
from typing import Union

import requests
from funance.scrape.common import Paths
from funance.scrape.driver.session import Session

"""
Handle updating Chromedriver

SEE https://sites.google.com/chromium.org/driver/downloads/version-selection
"""

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


def get_chrome_version():
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


def get_chromedriver_local_version(chrome_version: str) -> Union[str, None]:
    """
    Get latest installed major.minor.build version for the given chrome_version

    :param chrome_version: The Chrome version for which to find a matching Chromedriver version
    :type chrome_version: str

    :return: The latest installed chromedriver version, or None if no matching version
    :rtype: Union[str, None]
    """
    v = parse_version(chrome_version)
    # iterate directory where drivers are stored
    matching_dirs = [
        d for d in os.listdir(Paths.CHROMEDRIVER_DIR)
        if d.startswith(f"{v['major']}.{v['minor']}.{v['build']}")
    ]
    matching_dirs = sorted(matching_dirs, reverse=True)
    # take the first since these are reverse sorted
    best_match = None if len(matching_dirs) == 0 else matching_dirs[0]
    return best_match


def get_chromedriver_upstream_version(chrome_version):
    """
    Find the latest upstream Chromedriver version

    :param chrome_version:
    :return:
    """
    v = parse_version(chrome_version)
    url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{v['major']}.{v['minor']}.{v['build']}"
    r = requests.get(url)
    latest = r.text
    return latest


def get_chromedriver_dir(chromedriver_version):
    return os.path.join(Paths.CHROMEDRIVER_DIR, chromedriver_version)


def local_chromedriver_exists(chromedriver_version):
    return os.path.exists(get_chromedriver_dir(chromedriver_version))


def download_chromedriver(chromedriver_version):
    local_dir = get_chromedriver_dir(chromedriver_version)
    Path(local_dir).mkdir()
    for f in driver_files:
        url = f"https://chromedriver.storage.googleapis.com/{chromedriver_version}/{f}"
        print('downloading file:', url)
        local_file = download_file(url, os.path.join(local_dir, f))
        print('downloaded local file:', local_file)


def download_file(url, local_filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    return local_filename


def extract_files(chromedriver_version):
    local_dir = get_chromedriver_dir(chromedriver_version)
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


def parse_version(version):
    parts = version.split('.')
    return dict(major=parts[0], minor=parts[1], build=parts[2], patch=parts[3])


def do_update():
    chrome_version = get_chrome_version()
    print('chrome version:', chrome_version)

    chromedriver_upstream_version = get_chromedriver_upstream_version(chrome_version)
    print('chromedriver upstream version:', chromedriver_upstream_version)

    if not local_chromedriver_exists(chromedriver_upstream_version):
        print('Local Chromedriver does not exist. Downloading....')
        download_chromedriver(chromedriver_upstream_version)
        extract_files(chromedriver_upstream_version)

    chromedriver_local_version = get_chromedriver_local_version(chrome_version)
    print('chromedriver local version:', chromedriver_local_version)

    sess = Session.from_file()
    sess.chromedriver_version = chromedriver_local_version
    sess.close()
