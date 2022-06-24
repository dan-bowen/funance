import attr
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output

from funance.common.logger import get_logger

logger = get_logger('chart')


@attr.define(kw_only=True)
class InvestAllocationChart:
    df: pd.DataFrame = attr.ib()
    id: str = attr.ib()
    name: str = attr.ib()

    def get_children(self):
        children = []
        logger.debug('chart name in loop=%s', self.name)
        children.append(html.Div([
            html.H1(children=self.name, ),
            dcc.Dropdown(id=f"invest_allocation_dropdown_{self.id}", multi=True,
                         options=[{'label': a, 'value': a} for a in self.df.account_name.unique()],
                         value=[a for a in self.df.account_name.unique()]),
            dcc.Graph(id=f"invest_allocation_{self.id}", figure={}),
        ]))
        return children

    def register_callback(self, app):
        @app.callback(
            Output(f"invest_allocation_{self.id}", "figure"),
            Input(f"invest_allocation_dropdown_{self.id}", "value"))
        def get_figure(account_names):
            logger.debug('callback received account_names=%s', account_names)
            logger.debug('chart name in callback=%s', self.name)
            df = self.df.copy()
            df = df.loc[df['account_name'].isin(account_names)]
            pie_fig = go.Figure(
                data=[
                    go.Pie(labels=df['ticker'], values=df['current_value'])
                ]
            )
            pie_fig.update_traces(textposition='inside', textinfo='percent+label')
            pie_fig.update_layout(height=800, uniformtext_minsize=10, uniformtext_mode='hide')
            return pie_fig
