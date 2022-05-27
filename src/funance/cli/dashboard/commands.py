import os
from datetime import date

import click
import yaml
from dateutil.relativedelta import relativedelta

from funance.dashboard.dash_app import create_app
from funance.forecast.datespec import DATE_FORMAT
from funance.forecast.projector import Projector


def get_watch_files():
    dir_path = os.getcwd()
    dist_file = f"{dir_path}/forecast.dist.yml"
    user_file = f"{dir_path}/forecast.yml"
    return [dist_file, user_file]


def get_yaml():
    dir_path = os.getcwd()
    dist_file = f"{dir_path}/forecast.dist.yml"
    user_file = f"{dir_path}/forecast.yml"
    spec_file = user_file if os.path.exists(user_file) else dist_file
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
    spec = get_yaml()
    projector = Projector.from_spec(spec,
                                    start_date.strftime(DATE_FORMAT),
                                    end_date.strftime(DATE_FORMAT))
    charts = projector.get_charts()
    app = create_app(*charts)
    app.run_server(debug=True, extra_files=get_watch_files())