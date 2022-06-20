import os
import pathlib


_this_dir = pathlib.Path(__file__).parent.absolute()

ROOT_DIR = _this_dir.parent.parent.parent.absolute()

HOME_DIR = str(pathlib.Path.home())
PROJECT_DIR = os.path.join(HOME_DIR, '.funance')

FORECAST_DIST_FILE = os.path.join(ROOT_DIR, 'forecast.dist.yml')
FORECAST_FILE = os.path.join(PROJECT_DIR, 'forecast.yml')

INVEST_DIST_FILE = os.path.join(ROOT_DIR, 'invest.dist.yml')
INVEST_FILE = os.path.join(PROJECT_DIR, 'invest.yml')

SESSION_FILE = os.path.join(PROJECT_DIR, 'session.json')

CHROMEDRIVER_DIR = os.path.join(PROJECT_DIR, 'chromedriver')
EXPORT_DIR = os.path.join(PROJECT_DIR, 'export')
