import pathlib

_this_dir = pathlib.Path(__file__).parent.absolute()
_root_dir = _this_dir.parent.absolute()


class Paths(object):
    CHROMEDRIVER_DIR = f"{_root_dir}/.drivers/chromedriver"
    TMP_DIR = f"{_root_dir}/.tmp"
    EXPORT_DIR_BROKERAGE = f"{_root_dir}/.tmp/export-brokerage"
