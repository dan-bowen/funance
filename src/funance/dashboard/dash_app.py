from dash import Dash, dcc, html, dash_table, Input, Output
import plotly.graph_objects as go

from funance.common.logger import get_logger

logger = get_logger('dash-app')

DATE_FORMAT = '%Y-%m-%d'


def create_app(*charts):
    app = Dash(__name__)
    children = []
    for chart_id, chart in enumerate(charts):
        if chart.type == 'line':
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

        if chart.type == 'datatable':
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

        if chart.type == 'ticker_allocation':
            logger.debug('chart name in loop=%s', chart.name)
            children.append(html.Div([
                html.H1(children=chart.name, ),
                dcc.Dropdown(id=f"invest_allocation_dropdown_{chart_id}", multi=True,
                             options=[{'label': a, 'value': a} for a in chart.df.account_name.unique()],
                             value=[a for a in chart.df.account_name.unique()]),
                dcc.Graph(id=f"invest_allocation_{chart_id}", figure={}),
            ]))

            @app.callback(
                Output(f"invest_allocation_{chart_id}", "figure"),
                Input(f"invest_allocation_dropdown_{chart_id}", "value"))
            def generate_ticker_allocation(account_names):
                logger.debug('callback received account_names=%s', account_names)
                logger.debug('chart name in callback=%s', chart.name)
                df = chart.df.copy()
                df = df.loc[df['account_name'].isin(account_names)]
                pie_fig = go.Figure(
                    data=[
                        go.Pie(labels=df['ticker'], values=df['current_value'])
                    ]
                )
                pie_fig.update_traces(textposition='inside', textinfo='percent+label')
                pie_fig.update_layout(height=800, uniformtext_minsize=10, uniformtext_mode='hide')
                return pie_fig

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
