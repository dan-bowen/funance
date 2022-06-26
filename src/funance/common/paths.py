import os
import pathlib


_this_dir = pathlib.Path(__file__).parent.absolute()

ROOT_DIR = _this_dir.parent.parent.parent.absolute()

HOME_DIR = str(pathlib.Path.home())
PROJECT_DIR = os.path.join(HOME_DIR, '.funance')

ENV_DIST_FILE = os.path.join(ROOT_DIR, '.env.dist')
ENV_FILE = os.path.join(PROJECT_DIR, '.env')

SPEC_DIST_FILE = os.path.join(ROOT_DIR, 'funance.dist.yml')
SPEC_FILE = os.path.join(PROJECT_DIR, 'funance.yml')

SESSION_FILE = os.path.join(PROJECT_DIR, 'session.json')

CHROMEDRIVER_DIR = os.path.join(PROJECT_DIR, 'chromedriver')
EXPORT_DIR = os.path.join(PROJECT_DIR, 'export')
