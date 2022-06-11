import os

import yaml


def get_root_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class FixtureHelper:
    def __init__(self):
        pass

    @classmethod
    def get_spec_fixture(cls):
        root_path = get_root_path()
        with open(f"{root_path}/forecast.dist.yml", "r") as stream:
            return yaml.safe_load(stream)
