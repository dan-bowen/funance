from funance.dashboard.components import TickerAllocationAIO

from .cost_basis import get_allocation_report


def get_charts(spec):
    invest_spec = spec['invest']  # not used, yet
    charts = spec['charts']
    allocation_df = get_allocation_report()

    # allocation charts
    charts = [
        TickerAllocationAIO(df=allocation_df, title=chart['title'])
        for chart in charts if chart['type'] == 'stock-allocation'
    ]
    return charts
