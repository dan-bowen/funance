import uuid

import pandas as pd
import plotly.graph_objects as go
from dash import Output, Input, State, html, dcc, callback, MATCH

from funance.common.logger import get_logger
from .redis import RedisStore

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
            'subcomponent': 'graph',
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
