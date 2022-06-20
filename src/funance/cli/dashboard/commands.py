import os
from datetime import date

import click
import yaml
from dateutil.relativedelta import relativedelta

from funance.dashboard.dash_app import create_app
from funance.forecast.datespec import DATE_FORMAT
from funance.forecast.projector import Projector
from funance.common.paths import FORECAST_DIST_FILE, FORECAST_FILE, INVEST_DIST_FILE, INVEST_FILE


def get_watch_files():
    return [FORECAST_DIST_FILE, FORECAST_FILE, INVEST_DIST_FILE, INVEST_FILE]


def get_yaml(type_):
    if type_ == 'forecast':
        spec_file = FORECAST_FILE if os.path.exists(FORECAST_FILE) else FORECAST_DIST_FILE
    if type_ == 'invest':
        spec_file = INVEST_FILE if os.path.exists(INVEST_FILE) else INVEST_DIST_FILE
    with open(spec_file, "r") as stream:
        return yaml.safe_load(stream)


def get_start_date():
    return date.today() + relativedelta(days=1)


def get_end_date(start_date):
    return start_date + relativedelta(years=1)


@click.command(short_help='Run the dashboard')
def dashboard():
    """Open the dashboard"""

    start_date = get_start_date()
    end_date = get_end_date(start_date)
    forecast_spec = get_yaml('forecast')
    projector = Projector.from_spec(forecast_spec,
                                    start_date.strftime(DATE_FORMAT),
                                    end_date.strftime(DATE_FORMAT))
    forecast_charts = projector.get_charts()

    invest_charts = []

    charts = forecast_charts + invest_charts
    app = create_app(*charts)
    app.run_server(debug=True, extra_files=get_watch_files())
