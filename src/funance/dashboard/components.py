import uuid

import pandas as pd
import plotly.graph_objects as go
from dash import Output, Input, State, html, dcc, callback, MATCH

from funance.common.logger import get_logger
from funance.common.redis import RedisStore

logger = get_logger('component')


# All-in-One Components should be suffixed with 'AIO'
class TickerAllocationAIO(html.Div):  # html.Div will be the "parent" component

    # A set of functions that create pattern-matching callbacks of the subcomponents
    class ids:
        dropdown = lambda aio_id: {
            'component':    'TickerAllocationAIO',
            'subcomponent': 'dropdown',
            'aio_id':       aio_id
        }
        pie_chart = lambda aio_id: {
            'component':    'TickerAllocationAIO',
            'subcomponent': 'pie_chart',
            'aio_id':       aio_id
        }
        store = lambda aio_id: {
            'component':    'TickerAllocationAIO',
            'subcomponent': 'store',
            'aio_id':       aio_id
        }

    # Make the ids class a public class
    ids = ids

    # Define the arguments of the All-in-One component
    def __init__(
            self,
            df: pd.DataFrame,
            title: str,
            aio_id=None
    ):
        """An All-in-One component pie chart for ticker allocation"""

        store = {
            'df': RedisStore.save(df)
        }

        # Allow developers to pass in their own `aio_id` if they're
        # binding their own callback to a particular component.
        if aio_id is None:
            # Otherwise use a uuid that has virtually no chance of collision.
            # Uuids are safe in dash deployments with processes
            # because this component's callbacks
            # use a stateless pattern-matching callback:
            # The actual ID does not matter as long as its unique and matches
            # the PMC `MATCH` pattern..
            aio_id = str(uuid.uuid4())

        # Define the component's layout
        super().__init__([  # Equivalent to `html.Div([...])`
            dcc.Store(data=store, id=self.ids.store(aio_id)),
            html.H1(children=title),
            dcc.Dropdown(id=self.ids.dropdown(aio_id), multi=True,
                         options=[{'label': a, 'value': a} for a in df.account_name.unique()],
                         value=[a for a in df.account_name.unique()]),
            dcc.Graph(id=self.ids.pie_chart(aio_id), figure={}),
        ])

    # Define this component's stateless pattern-matching callback
    # that will apply to every instance of this component.
    @callback(
        Output(ids.pie_chart(MATCH), 'figure'),
        Input(ids.dropdown(MATCH), 'value'),
        State(ids.store(MATCH), 'data')
    )
    def get_figure(account_names, store):
        logger.debug('callback received: account_names=%s', account_names)
        df = RedisStore.load(store['df'])
        df = df.loc[df['account_name'].isin(account_names)]
        pie_fig = go.Figure(
            data=[
                go.Pie(labels=df['ticker'], values=df['current_value'])
            ]
        )
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')
        pie_fig.update_layout(height=800, uniformtext_minsize=10, uniformtext_mode='hide')
        return pie_fig


# All-in-One Components should be suffixed with 'AIO'
class ForecastLineAIO(html.Div):  # html.Div will be the "parent" component

    # A set of functions that create pattern-matching callbacks of the subcomponents
    class ids:
        line_chart = lambda aio_id: {
            'component':    'ForecastLineAIO',
            'subcomponent': 'line_chart',
            'aio_id':       aio_id
        }

    # Make the ids class a public class
    ids = ids

    # Define the arguments of the All-in-One component
    def __init__(
            self,
            title: str,
            accounts: list,
            aio_id=None
    ):
        """An All-in-One component pie chart for ticker allocation"""

        # Allow developers to pass in their own `aio_id` if they're
        # binding their own callback to a particular component.
        if aio_id is None:
            # Otherwise use a uuid that has virtually no chance of collision.
            # Uuids are safe in dash deployments with processes
            # because this component's callbacks
            # use a stateless pattern-matching callback:
            # The actual ID does not matter as long as its unique and matches
            # the PMC `MATCH` pattern..
            aio_id = str(uuid.uuid4())

        fig = go.Figure()
        fig.update_layout(title=title)
        for account in accounts:
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

        # TODO Add tabs for raw datatable and CSV download
        # for account in accounts:
        #     transactions_df = account['df']
        #     fig = dash_table.DataTable(
        #         columns=[
        #             dict(name='Date', id='Date', type='datetime'),
        #             # Unfortunately there is no formatting on datetime types.
        #             # https://community.plotly.com/t/is-it-any-way-to-set-format-of-date-time-in-datatable/29514
        #             # https://dash.plotly.com/datatable/typing
        #             dict(name='Description', id='Description'),
        #             dict(name='Amount', id='Amount', type='numeric', format=dash_table.FormatTemplate.money(2)),
        #             dict(name='Balance', id='Balance', type='numeric', format=dash_table.FormatTemplate.money(2))
        #         ],
        #         data=[
        #             {
        #                 'Date':        row[0],
        #                 'Description': row[1].replace('<br>', '\n'),
        #                 # <br> works in tooltips, not datatable.
        #                 # Using \n combined with style_cell={'whiteSpace': 'pre-line'} accomplishes the goal.
        #                 # https://community.plotly.com/t/creating-new-line-within-datatable-cell/44145/3
        #                 'Amount':      row[2],
        #                 'Balance':     row[3]
        #             }
        #             for row in zip(transactions_df.index, transactions_df.amt_desc, transactions_df.amount,
        #                            transactions_df.balance)
        #         ],
        #         editable=False,
        #         filter_action='native',
        #         sort_action='native',
        #         sort_mode='single',
        #         page_action='native',
        #         page_current=0,
        #         page_size=25,
        #         style_cell={'minWidth': 95, 'maxWidth': 95, 'width': 95, 'whiteSpace': 'pre-line'},
        #         style_cell_conditional=[
        #             {
        #                 'if':        {'column_id': c},
        #                 'textAlign': 'left'
        #             } for c in ['Date', 'Description']
        #         ],
        #         style_data={'whitespace': 'normal', 'height': 'auto'}
        #     )

        # Define the component's layout
        super().__init__([  # Equivalent to `html.Div([...])`
            html.H1(children='Forecast'),
            dcc.Graph(id=self.ids.line_chart(aio_id), figure=fig),
        ])


class EmergencyFundAIO(html.Div):
    # A set of functions that create pattern-matching callbacks of the subcomponents
    class ids:
        runway_chart = lambda aio_id: {
            'component':    'EmergencyFundAIO',
            'subcomponent': 'runway_chart',
            'aio_id':       aio_id
        }
        amt_chart = lambda aio_id: {
            'component':    'EmergencyFundAIO',
            'subcomponent': 'amt_chart',
            'aio_id':       aio_id
        }
        sources_pie_chart = lambda aio_id: {
            'component':    'EmergencyFundAIO',
            'subcomponent': 'sources_pie_chart',
            'aio_id':       aio_id
        }

    # Make the ids class a public class
    ids = ids

    # Define the arguments of the All-in-One component
    def __init__(
            self,
            title: str,
            df: pd.DataFrame,
            runway_mos_goal: float,
            runway_mos_actual: float,
            amt_goal: float,
            amt_actual: float,
            aio_id=None
    ):
        """An All-in-One component pie chart for ticker allocation"""

        # Allow developers to pass in their own `aio_id` if they're
        # binding their own callback to a particular component.
        if aio_id is None:
            # Otherwise use a uuid that has virtually no chance of collision.
            # Uuids are safe in dash deployments with processes
            # because this component's callbacks
            # use a stateless pattern-matching callback:
            # The actual ID does not matter as long as its unique and matches
            # the PMC `MATCH` pattern..
            aio_id = str(uuid.uuid4())

        runway_chart = go.Figure(go.Indicator(
            mode="number+gauge+delta",
            value=runway_mos_actual,
            domain={'x': [0.1, 1], 'y': [0, 1]},
            title={'text': "<b>Runway</b>"},
            delta={'reference': runway_mos_goal},
            gauge={
                'shape': "bullet",
                'axis':  {'range': [None, runway_mos_goal]},
            }))
        runway_chart.update_layout(height=150, margin={'t': 0, 'b': 50})

        amt_chart = go.Figure(go.Indicator(
            mode="number+gauge+delta",
            value=amt_actual,  # TODO use real values
            domain={'x': [0.1, 1], 'y': [0, 1]},
            title={'text': "<b>Amount</b>"},
            delta={'reference': amt_goal},
            gauge={
                'shape': "bullet",
                'axis':  {'range': [None, amt_goal]},
            }))
        amt_chart.update_layout(height=150, margin={'t': 0, 'b': 50})

        pie_fig = go.Figure(
            data=[
                go.Pie(labels=df['name'], values=df['value'])
            ]
        )
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')
        pie_fig.update_layout(title={'text': 'Fund Sources'},
                              height=500,
                              uniformtext_minsize=10,
                              uniformtext_mode='hide')

        super().__init__([  # Equivalent to `html.Div([...])`
            html.H1(children=title),
            dcc.Graph(id=self.ids.runway_chart(aio_id), figure=runway_chart),
            dcc.Graph(id=self.ids.amt_chart(aio_id), figure=amt_chart),
            dcc.Graph(id=self.ids.sources_pie_chart(aio_id), figure=pie_fig),
        ])
