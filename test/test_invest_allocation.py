import unittest
from unittest.mock import patch

import numpy as np
from parameterized import parameterized

from funance.invest.holdings import Holdings, PriceNotFoundError
from test.helpers import FixtureHelper


class TestAllocation(unittest.TestCase):

    def setUp(self) -> None:
        self.get_holdings_df = patch('funance.invest.holdings.Holdings.df_holdings').start()
        self.get_symbol_prices = patch('funance.invest.holdings.Holdings._get_symbol_prices').start()

    def tearDown(self) -> None:
        patch.stopall()

    @parameterized.expand([
        (
                "all_unique_prices",
                {
                    'VTIP':   50.22,
                    'VGLT':   66.75,
                    'VXUS':   51.43,
                    'VYM':    99.20,
                    'VIG':    138.64,
                    'VGSH':   58.22,
                    'X_CASH': 1.00
                },
                [
                    "array_equal"
                ]

        ),
        (
                # Prices in the fixture are not found. See "all_unique_prices" test for master list
                "missing_prices",
                {
                    # 'VTIP':   50.22,
                    'VGLT':   66.75,
                    'VXUS':   51.43,
                    'VYM':    99.20,
                    'VIG':    138.64,
                    'VGSH':   58.22,
                    'X_CASH': 1.00
                },
                [
                    "raises_price_not_found_error"
                ]
        ),
        (
                "extra_prices",
                {
                    # not in the fixture. pa.DataFrame.map() doesn't seem to care if you pass extra keys
                    'AAPL':   104.15,

                    # in the fixture
                    'VTIP':   50.22,
                    'VGLT':   66.75,
                    'VXUS':   51.43,
                    'VYM':    99.20,
                    'VIG':    138.64,
                    'VGSH':   58.22,
                    'X_CASH': 1.00
                },
                [
                    "array_equal"
                ]
        ),
    ])
    def test_summary_holdings(self, name, prices, assertions):
        fixture = FixtureHelper.get_dataframe('invest.holdings.csv')

        self.get_holdings_df.configure_mock(**{
            'return_value': fixture
        })
        self.get_symbol_prices.configure_mock(**{
            'return_value': prices
        })

        expected = fixture.copy() \
            .groupby(['account', 'symbol']) \
            .agg({'quantity': 'sum'}) \
            .reset_index()

        expected['current_price'] = expected['symbol'].map(prices)
        expected['current_value'] = expected['current_price'] * expected['quantity']
        expected['allocation'] = (expected['current_value'] / expected.groupby('account')['current_value']
                                  .transform('sum')) * 100

        for assertion in assertions:
            if assertion == 'array_equal':
                actual = Holdings('foo').df_allocation()
                np.testing.assert_array_equal(actual.to_numpy(), expected.to_numpy())
            if assertion == 'raises_price_not_found_error':
                with self.assertRaises(PriceNotFoundError) as context:
                    actual = Holdings('foo').df_allocation()
                self.assertIn('Found nulls in current_price column', str(context.exception))


if __name__ == '__main__':
    unittest.main()
