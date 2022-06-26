import os

import click
import yaml

from funance.common.paths import (
    SPEC_DIST_FILE,
    SPEC_FILE
)
from funance.dashboard.dash_app import create_app


def get_watch_files():
    return [SPEC_DIST_FILE, SPEC_FILE]


def get_yaml():
    spec_file = SPEC_FILE if os.path.exists(SPEC_FILE) else SPEC_DIST_FILE
    with open(spec_file, "r") as stream:
        return yaml.safe_load(stream)


@click.command(short_help='Run the dashboard')
def dashboard():
    """Open the dashboard"""
    spec = get_yaml()
    app = create_app(spec)
    app.run_server(debug=True, extra_files=get_watch_files())
