from funance.dashboard.components import TickerAllocationAIO

from .cost_basis import get_allocation_report


def get_charts(chart_spec):
    allocation_df = get_allocation_report()
    charts = [
        TickerAllocationAIO(df=allocation_df, title=chart['name'])
        for chart_type, chart in chart_spec.items()
    ]
    return charts
