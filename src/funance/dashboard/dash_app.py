from datetime import date
from typing import Union, List

from dash import Dash, html
from dateutil.relativedelta import relativedelta

from funance.common.logger import get_logger
from funance.dashboard.components import ForecastLineAIO, EmergencyFundAIO, TickerAllocationAIO
from funance.forecast.datespec import DATE_FORMAT
from funance.forecast.forecast import Forecast
from funance.invest.cost_basis import get_allocation_report

logger = get_logger('dash-app')


def get_forecast_charts(spec: dict) -> List[Union[ForecastLineAIO, EmergencyFundAIO, TickerAllocationAIO]]:
    forecast_spec = spec['forecast']
    ef_spec = spec['forecast']['emergency_fund']
    chart_spec = spec['charts']
    charts = []

    # forecast charts
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


def get_invest_charts(spec: dict) -> List[Union[ForecastLineAIO, EmergencyFundAIO, TickerAllocationAIO]]:
    invest_spec = spec['invest']  # not used, yet
    charts = spec['charts']
    allocation_df = get_allocation_report()

    # allocation charts
    charts = [
        TickerAllocationAIO(df=allocation_df, title=chart['title'])
        for chart in charts if chart['type'] == 'stock-allocation'
    ]
    return charts


def create_app(spec: dict) -> Dash:
    forecast_charts = get_forecast_charts(spec)
    invest_charts = get_invest_charts(spec)
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

    return app
