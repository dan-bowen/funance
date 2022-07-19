import unittest
from unittest.mock import patch

import numpy as np
from parameterized import parameterized

from funance.invest.cost_basis import CostBasis, PriceNotFoundError
from test.helpers import FixtureHelper


class TestAllocation(unittest.TestCase):

    def setUp(self) -> None:
        self.get_cost_basis_df = patch('funance.invest.cost_basis.CostBasis.df_cost_basis').start()
        self.get_ticker_prices = patch('funance.invest.cost_basis.CostBasis._get_ticker_prices').start()

    def tearDown(self) -> None:
        patch.stopall()

    @parameterized.expand([
        (
                "all_unique_prices",
                {
                    'ED':     86.88,
                    'CVX':    173.76,
                    'MA':     302.72,
                    'VIPSX':  59.00,
                    'VTIP':   50.22,
                    'VXUS':   51.43,
                    'VYM':    99.20,
                    'MGV':    93.26,
                    'VIG':    138.64,
                    'GLD':    171.15,
                    'V':      190.01,
                    'JPM':    113.03,
                    'BAC':    31.92,
                    'STOR':   25.52,
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
                    'ED':     86.88,
                    'CVX':    173.76,
                    'MA':     302.72,
                    'GLD':    171.15,
                    'V':      190.01,
                    'JPM':    113.03,
                    'BAC':    31.92,
                    'STOR':   25.52,
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
                    'ED':     86.88,
                    'CVX':    173.76,
                    'MA':     302.72,
                    'VIPSX':  59.00,
                    'VTIP':   50.22,
                    'VXUS':   51.43,
                    'VYM':    99.20,
                    'MGV':    93.26,
                    'VIG':    138.64,
                    'GLD':    171.15,
                    'V':      190.01,
                    'JPM':    113.03,
                    'BAC':    31.92,
                    'STOR':   25.52,
                    'X_CASH': 1.00
                },
                [
                    "array_equal"
                ]
        ),
    ])
    def test_summary_cost_basis(self, name, prices, assertions):
        fixture = FixtureHelper.get_dataframe('brokerage.csv')

        self.get_cost_basis_df.configure_mock(**{
            'return_value': fixture
        })
        self.get_ticker_prices.configure_mock(**{
            'return_value': prices
        })

        expected = fixture.copy() \
            .drop(columns=['date_acquired', 'cost_per_share', 'term']) \
            .groupby(['account_name', 'ticker']) \
            .agg({'num_shares': 'sum', 'total_cost': 'sum'}) \
            .reset_index()
        expected['current_price'] = expected['ticker'].map(prices)
        expected['current_value'] = expected['current_price'] * expected['num_shares']
        expected['gain'] = expected['current_value'] - expected['total_cost']
        expected['gain_pct'] = ((expected['current_value'] - expected['total_cost']) / expected['total_cost']) * 100
        expected['allocation'] = (expected['current_value'] / expected.groupby('account_name')['current_value']
                                  .transform('sum')) * 100

        for assertion in assertions:
            if assertion == 'array_equal':
                actual = CostBasis('foo').df_allocation()
                np.testing.assert_array_equal(actual.to_numpy(), expected.to_numpy())
            if assertion == 'raises_price_not_found_error':
                with self.assertRaises(PriceNotFoundError) as context:
                    actual = CostBasis('foo').df_allocation()
                self.assertIn('Found nulls in current_price column', str(context.exception))


if __name__ == '__main__':
    unittest.main()
