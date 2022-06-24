import os

import click
import yaml

from funance.common.paths import (
    FORECAST_DIST_FILE,
    FORECAST_FILE,
    INVEST_DIST_FILE,
    INVEST_FILE
)
from funance.dashboard.dash_app import get_forecast_charts, get_invest_charts, create_app


def get_watch_files():
    return [FORECAST_DIST_FILE, FORECAST_FILE, INVEST_DIST_FILE, INVEST_FILE]


def get_yaml(type_):
    if type_ == 'forecast':
        spec_file = FORECAST_FILE if os.path.exists(FORECAST_FILE) else FORECAST_DIST_FILE
    if type_ == 'invest':
        spec_file = INVEST_FILE if os.path.exists(INVEST_FILE) else INVEST_DIST_FILE
    with open(spec_file, "r") as stream:
        return yaml.safe_load(stream)


@click.command(short_help='Run the dashboard')
def dashboard():
    """Open the dashboard"""

    forecast_spec = get_yaml('forecast')
    forecast_charts = get_forecast_charts(forecast_spec)

    invest_spec = get_yaml('invest')
    invest_charts = get_invest_charts(invest_spec['chart_spec'])

    charts = forecast_charts + invest_charts
    app = create_app(*charts)
    app.run_server(debug=True, extra_files=get_watch_files())
