from datetime import date

import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table
from dateutil.relativedelta import relativedelta

from funance.common.logger import get_logger
from funance.dashboard.chart import InvestAllocationChart
from funance.forecast.datespec import DATE_FORMAT
from funance.forecast.projector import Projector
from funance.invest.cost_basis import get_allocation_report

logger = get_logger('dash-app')


def get_forecast_charts(spec):
    start_date = date.today() + relativedelta(days=1)
    end_date = start_date + relativedelta(years=1)
    projector = Projector.from_spec(spec,
                                    start_date.strftime(DATE_FORMAT),
                                    end_date.strftime(DATE_FORMAT))
    return projector.get_charts()


def get_invest_charts(chart_spec):
    allocation_df = get_allocation_report()
    charts = [
        InvestAllocationChart(df=allocation_df, name=chart['name'], id=chart_type)
        for chart_type, chart in chart_spec.items()
    ]
    return charts


def create_app(*charts):
    app = Dash(__name__)
    children = []
    for chart_id, chart in enumerate(charts):
        if isinstance(chart, InvestAllocationChart):
            children.extend(chart.get_children())
            chart.register_callback(app)
        elif chart.type == 'line':
            fig = go.Figure()
            fig.update_layout(title=chart.name)
            for account in chart.accounts:
                transactions_df = account['df']
                fig.add_trace(
                    go.Scatter(
                        name=account['name'],
                        x=transactions_df.index, y=transactions_df['balance'].round(0),
                        mode='lines+markers',
                        line_shape='spline',
                        hovertext=transactions_df['amt_desc'],
                        hovertemplate=
                        '<b>$%{y:.2f}</b> (%{x})<br><br>' +
                        '%{hovertext}'
                    )
                )
            children.append(dcc.Graph(figure=fig))

        elif chart.type == 'datatable':
            for account in chart.accounts:
                transactions_df = account['df']
                fig = dash_table.DataTable(
                    columns=[
                        dict(name='Date', id='Date', type='datetime'),
                        # Unfortunately there is no formatting on datetime types.
                        # https://community.plotly.com/t/is-it-any-way-to-set-format-of-date-time-in-datatable/29514
                        # https://dash.plotly.com/datatable/typing
                        dict(name='Description', id='Description'),
                        dict(name='Amount', id='Amount', type='numeric', format=dash_table.FormatTemplate.money(2)),
                        dict(name='Balance', id='Balance', type='numeric', format=dash_table.FormatTemplate.money(2))
                    ],
                    data=[
                        {
                            'Date':        row[0],
                            'Description': row[1].replace('<br>', '\n'),
                            # <br> works in tooltips, not datatable.
                            # Using \n combined with style_cell={'whiteSpace': 'pre-line'} accomplishes the goal.
                            # https://community.plotly.com/t/creating-new-line-within-datatable-cell/44145/3
                            'Amount':      row[2],
                            'Balance':     row[3]
                        }
                        for row in zip(transactions_df.index, transactions_df.amt_desc, transactions_df.amount,
                                       transactions_df.balance)
                    ],
                    editable=False,
                    filter_action='native',
                    sort_action='native',
                    sort_mode='single',
                    page_action='native',
                    page_current=0,
                    page_size=25,
                    style_cell={'minWidth': 95, 'maxWidth': 95, 'width': 95, 'whiteSpace': 'pre-line'},
                    style_cell_conditional=[
                        {
                            'if':        {'column_id': c},
                            'textAlign': 'left'
                        } for c in ['Date', 'Description']
                    ],
                    style_data={'whitespace': 'normal', 'height': 'auto'}
                )
                children.append(html.Div([
                    html.H1(account['name']),
                    fig
                ]))

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
