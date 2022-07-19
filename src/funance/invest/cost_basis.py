"""Cost basis"""

import os

import pandas as pd

from funance.common.logger import get_logger

logger = get_logger('cost-basis')


class PriceNotFoundError(Exception):
    """Thrown when a price is not found"""
    pass


class CostBasis:
    """Cost Basis"""

    def __init__(self, export_dir: str) -> None:
        self._export_dir = export_dir

    @classmethod
    def _get_ticker_prices(cls, tickers: list) -> dict:
        """get prices for the given tickers"""

        filled = dict.fromkeys(tickers, None)
        # TODO get this from config
        sheet_url = os.getenv('GOOGLE_SHEETS_PRICES_URL')
        # change the sharing url to the export url
        sheet_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv')
        logger.debug('loading prices from %s', sheet_url)
        prices_df = pd.read_csv(sheet_url)
        current_prices = {r['ticker']: r['price'] for r in prices_df.to_dict('records')}
        merged = {**filled, **current_prices}
        return merged

    @classmethod
    def validate_allocation_df(cls, summary_df: pd.DataFrame) -> None:
        """Validate allocation df"""
        if summary_df['current_price'].isnull().values.any():
            raise PriceNotFoundError('Found nulls in current_price column')

    def df_cost_basis(self) -> pd.DataFrame:
        """Cost basis dataframe"""
        return pd.read_csv(os.path.join(self._export_dir, 'brokerage.csv'))

    def df_allocation(self) -> pd.DataFrame:
        """Allocation dataframe"""
        cost_basis_df = self.df_cost_basis()
        summary_df = cost_basis_df.copy() \
            .drop(columns=['date_acquired', 'cost_per_share', 'term']) \
            .groupby(['account_name', 'ticker']) \
            .agg({'num_shares': 'sum', 'total_cost': 'sum'}) \
            .reset_index()

        unique_tickers = summary_df['ticker'].unique()
        ticker_prices = self._get_ticker_prices(unique_tickers)

        summary_df['current_price'] = summary_df['ticker'].map(ticker_prices)

        summary_df['current_value'] = summary_df['current_price'] * summary_df['num_shares']
        summary_df['gain'] = summary_df['current_value'] - summary_df['total_cost']
        summary_df['gain_pct'] = ((summary_df['current_value'] - summary_df['total_cost']) / summary_df['total_cost']) * 100
        summary_df['allocation'] = (summary_df['current_value'] / summary_df.groupby('account_name')['current_value']
                                    .transform('sum')) * 100

        CostBasis.validate_allocation_df(summary_df)
        return summary_df
