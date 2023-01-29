"""Cost basis"""

import os
import glob

import pandas as pd

from funance.common.logger import get_logger

logger = get_logger('holdings')


class PriceNotFoundError(Exception):
    """Thrown when a price is not found"""
    pass


class Holdings:
    """Holdings"""

    def __init__(self, export_dir: str) -> None:
        self._export_dir = export_dir

    @classmethod
    def _get_symbol_prices(cls, tickers: list) -> dict:
        """get prices for the given symbols"""

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
        logger.info(summary_df)
        if summary_df['current_price'].isnull().values.any():
            raise PriceNotFoundError('Found nulls in current_price column')

    def df_holdings(self) -> pd.DataFrame:
        """Holdings dataframe"""
        # Merges all CSVs with the pattern "holdings.*.csv" into one dataframe.
        all_files = glob.glob(os.path.join(self._export_dir, "holdings.*.csv"))
        df = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
        return df

    def df_allocation(self) -> pd.DataFrame:
        """Allocation dataframe"""
        holdings_df = self.df_holdings()
        summary_df = holdings_df.copy() \
            .groupby(['account', 'symbol']) \
            .agg({'quantity': 'sum'}) \
            .reset_index()

        unique_symbols = summary_df['symbol'].unique()
        symbol_prices = self._get_symbol_prices(unique_symbols)

        summary_df['current_price'] = summary_df['symbol'].map(symbol_prices)
        summary_df['current_value'] = summary_df['current_price'] * summary_df['quantity']
        summary_df['allocation'] = (summary_df['current_value'] / summary_df.groupby('account')['current_value']
                                    .transform('sum')) * 100

        Holdings.validate_allocation_df(summary_df)
        return summary_df
