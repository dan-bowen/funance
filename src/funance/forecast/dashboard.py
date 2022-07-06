from datetime import date

from dateutil.relativedelta import relativedelta

from funance.dashboard.components import ForecastLineAIO, EmergencyFundAIO
from .datespec import DATE_FORMAT
from .projector import Projector
from .emergency_fund import get_runway_report


def get_charts(spec):
    forecast_spec = spec['forecast']
    ef_spec = spec['forecast']['emergency_fund']
    chart_spec = spec['charts']
    charts = []

    # forecast charts
    start_date = date.today() + relativedelta(days=1)
    end_date = start_date + relativedelta(years=1)
    projector = Projector.from_spec(forecast_spec,
                                    start_date.strftime(DATE_FORMAT),
                                    end_date.strftime(DATE_FORMAT))

    # emergency fund
    ef_report = get_runway_report(ef_spec)

    for chart in chart_spec:
        if chart['type'] == 'forecast':
            accounts = list(
                map(
                    lambda a: dict(
                        name=projector.get_account(a).name,
                        df=projector.get_account(a).get_running_balance_grouped()
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
