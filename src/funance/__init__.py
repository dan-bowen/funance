import os
from dotenv import load_dotenv
from pathlib import Path


_this_dir = Path(__file__).parent.absolute()
ROOT_DIR = _this_dir.parent.parent.absolute()
HOME_DIR = str(Path.home())
PROJECT_DIR = os.path.join(HOME_DIR, '.funance')
ENV_FILE = os.path.join(PROJECT_DIR, '.env')

load_dotenv(dotenv_path=Path(ENV_FILE))
