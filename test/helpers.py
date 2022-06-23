import os

import yaml
import pandas as pd


def get_root_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_fixture_path():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, 'fixtures')


class FixtureHelper:
    def __init__(self):
        pass

    @classmethod
    def get_spec_fixture(cls):
        root_path = get_root_path()
        with open(f"{root_path}/forecast.dist.yml", "r") as stream:
            return yaml.safe_load(stream)

    @classmethod
    def get_dataframe(cls, filename):
        return pd.read_csv(os.path.join(get_fixture_path(), filename))
