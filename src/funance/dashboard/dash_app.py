import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table

from funance.common.logger import get_logger
from funance.forecast.dashboard import get_charts as get_forecast_charts
from funance.invest.dashboard import get_charts as get_invest_charts

logger = get_logger('dash-app')


def create_app(forecast_spec: dict, invest_spec: dict):
    forecast_charts = get_forecast_charts(forecast_spec)
    invest_charts = get_invest_charts(invest_spec['chart_spec'])
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
