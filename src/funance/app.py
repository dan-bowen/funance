"""The main entry point for the app"""

import os
import typing as t
from datetime import date
from pathlib import Path
import shutil

import yaml
from dash import Dash, html
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

from funance.common.logger import get_logger
from funance.scrape.driver.updater import Updater
from funance.dashboard.components import ForecastLineAIO, EmergencyFundAIO, TickerAllocationAIO
from funance.forecast.datespec import DATE_FORMAT
from funance.forecast.forecast import Forecast
from funance.invest import CostBasis
from .config import Config

logger = get_logger('app')


class Funance:
    """The Funance object.

    Once created it will act as a central registry for configuration, dataframes and more.
    """

    # Default configuration parameters.
    default_config = {}

    def __init__(self):
        this_dir = Path(__file__).parent.absolute()

        # base paths
        self._root_dir = this_dir.parent.parent.absolute()
        self._home_dir = str(Path.home())
        self._project_dir = os.path.join(self._home_dir, '.funance')
        self._env_file = os.path.join(self._project_dir, '.env')

        # load env file immediately after locating it so additional configuration will be able to utilize the env vars
        load_dotenv(dotenv_path=Path(self._env_file))

        # spec file; loaded from env var
        self._spec_file = os.path.join(self._project_dir, os.getenv('SPEC_FILE'))

        # dist files
        self._env_dist_file = os.path.join(self._root_dir, '.env.dist')
        self._spec_dist_file = os.path.join(self._root_dir, 'funance.dist.yml')

        # scraper dirs
        self._chromedriver_dir = os.path.join(self._project_dir, 'chromedriver')
        self._export_dir = os.path.join(self._project_dir, 'export')

        # The configuration dictionary as :class:`Config`
        self.config: Config = self._make_config()
        self.spec = self._get_spec()

    def _make_config(self) -> Config:
        """Used to create the config attribute by the Funance constructor.
        """
        defaults = dict(self.default_config)
        return Config(defaults)

    def _get_spec(self) -> dict:
        """Get the spec file"""
        spec_file = self._spec_file if os.path.exists(self._spec_file) else self._spec_dist_file
        with open(spec_file, "r") as stream:
            return yaml.safe_load(stream)

    def _get_watch_files(self) -> list:
        return [self._spec_dist_file, self._spec_file]

    def _get_forecast_charts(self) -> t.List[t.Union[ForecastLineAIO, EmergencyFundAIO, TickerAllocationAIO]]:
        """get forecast charts"""
        forecast_spec = self.spec['forecast']
        ef_spec = self.spec['forecast']['emergency_fund']
        chart_spec = self.spec['charts']
        charts = []

        start_date = date.today() + relativedelta(days=1)
        end_date = start_date + relativedelta(years=1)
        forecast = Forecast.from_spec(forecast_spec,
                                      start_date.strftime(DATE_FORMAT),
                                      end_date.strftime(DATE_FORMAT))

        # emergency fund
        ef_report = Forecast.get_runway_report(ef_spec)

        for chart in chart_spec:
            if chart['type'] == 'forecast':
                accounts = list(
                    map(
                        lambda a: dict(
                            name=forecast.get_account(a).name,
                            df=forecast.get_account(a).get_running_balance_grouped()
                        ),
                        chart['account_ids']
                    )
                )
                charts.append(ForecastLineAIO(title=chart['title'], accounts=accounts))
            if chart['type'] == 'emergency-fund':
                charts.append(EmergencyFundAIO(
                    title=chart['title'],
                    df=ef_report['df'],
                    runway_mos_goal=ef_report['runway_mos_goal'],
                    runway_mos_actual=ef_report['runway_mos_actual'],
                    amt_goal=ef_report['amt_goal'],
                    amt_actual=ef_report['amt_actual']
                ))
        return charts

    def _get_invest_charts(self) -> t.List[t.Union[ForecastLineAIO, EmergencyFundAIO, TickerAllocationAIO]]:
        """get invest charts"""
        invest_spec = self.spec['invest']  # not used, yet
        charts = self.spec['charts']
        allocation_df = CostBasis(self._export_dir).df_allocation()

        # allocation charts
        charts = [
            TickerAllocationAIO(df=allocation_df, title=chart['title'])
            for chart in charts if chart['type'] == 'stock-allocation'
        ]
        return charts

    def init(self):
        """Initialize the project"""
        # create project directory
        Path(self._project_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"created directory {self._project_dir}")

        Path(self._chromedriver_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"created directory {self._chromedriver_dir}")

        Path(self._export_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"created directory {self._export_dir}")

        # copy .env file, if it doesn't exist
        if not Path(self._env_file).is_file():
            shutil.copyfile(self._env_dist_file, self._env_file)
            logger.info(f"copied env file {self._env_file}")

        # copy spec file, if it doesn't exist
        if not Path(self._spec_file).is_file():
            shutil.copyfile(SPEC_DIST_FILE, self._spec_file)
            logger.info(f"copied funance file {self._spec_file}")

        Updater(self._chromedriver_dir).update()

    def run(self):
        """Run the dash app"""
        forecast_charts = self._get_forecast_charts()
        invest_charts = self._get_invest_charts()
        charts = forecast_charts + invest_charts

        app = Dash(__name__)
        children = []
        for chart_id, chart in enumerate(charts):
            children.append(chart)

        app.layout = html.Div(
            children=[
                html.H1(children="Funance", ),
                html.P(
                    children="Fun with personal finance data exploration.",
                ),
                html.Div(children=children)
            ]
        )
        app.run_server(debug=True, extra_files=self._get_watch_files())
