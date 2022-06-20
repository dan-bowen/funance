import os

import pandas as pd

from funance.common.paths import EXPORT_DIR


class PriceNotFoundError(Exception):
    pass


def _get_cost_basis_df():
    return pd.read_csv(os.path.join(EXPORT_DIR, 'brokerage.csv'))


def _get_ticker_prices(tickers: list) -> dict:
    # TODO replace with live data from API call or db
    current_prices = {
        'ABBV':   149.40,
        'ADRNY':  26.75,
        'ALLY':   36.15,
        'X_CASH': 1.00
    }
    return current_prices


def _validate_summary_df(summary_df: pd.DataFrame) -> None:
    if summary_df['current_price'].isnull().values.any():
        raise PriceNotFoundError('Found nulls in current_price column')


def get_allocation_report() -> pd.DataFrame:
    cost_basis_df = _get_cost_basis_df()
    summary_df = cost_basis_df.copy() \
        .drop(columns=['date_acquired', 'cost_per_share', 'term']) \
        .groupby(['account_name', 'ticker']) \
        .agg({'num_shares': 'sum', 'total_cost': 'sum'}) \
        .reset_index()

    unique_tickers = summary_df['ticker'].unique()
    ticker_prices = _get_ticker_prices(unique_tickers)

    summary_df['current_price'] = summary_df['ticker'].map(ticker_prices)

    summary_df['current_value'] = summary_df['current_price'] * summary_df['num_shares']
    summary_df['gain'] = summary_df['current_value'] - summary_df['total_cost']
    summary_df['gain_pct'] = ((summary_df['current_value'] - summary_df['total_cost']) / summary_df['total_cost']) * 100
    summary_df['allocation'] = (summary_df['current_value'] / summary_df.groupby('account_name')['current_value']
                                .transform('sum')) * 100

    _validate_summary_df(summary_df)
    return summary_df
