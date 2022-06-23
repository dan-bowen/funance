import attr
import pandas as pd

from funance.invest.cost_basis import get_allocation_report


@attr.define(kw_only=True)
class Chart:
    name: str = attr.ib()
    type: str = attr.ib()
    df: pd.DataFrame = attr.ib()


def get_charts(chart_spec):
    allocation_df = get_allocation_report()
    charts = [
        Chart(name=chart['name'], type=chart_type, df=allocation_df)
        for chart_type, chart in chart_spec.items()
    ]
    return charts
