import datetime
import unittest

import numpy as np
import pandas as pd
from parameterized import parameterized

from funance.forecast.account import Account
from funance.forecast.datespec import DateSpec
from funance.forecast.exceptions import OutOfBoundsException
from funance.forecast.forecast import Forecast
from funance.forecast.transaction import Transaction
from test.helpers import FixtureHelper


class TestAccount(unittest.TestCase):
    def test_balance_date_out_of_range(self):
        account = Account(account_id='checking', name='Checking', start_date='2022-01-01', balance=1000)
        account.add_transactions([
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 14, 0, 0), amount=-250.0, name='Savings', type='transfer'),
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 28, 0, 0), amount=-250.0, name='Savings', type='transfer')
        ])
        # before start_date of the account
        self.assertRaises(OutOfBoundsException, account.get_balance, '2021-12-31')

    def test_no_transactions_returns_current_balance(self):
        account = Account(account_id='checking', name='Checking', start_date='2022-01-01', balance=1000)
        self.assertEqual(account.get_balance('2022-01-14'), 1000)

    def test_no_transactions_lt_balance_date_returns_current_balance(self):
        account = Account(account_id='checking', name='Checking', start_date='2022-01-01', balance=1000)
        account.add_transactions([
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 14, 0, 0), amount=-250.0, name='Savings', type='transfer'),
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 28, 0, 0), amount=-250.0, name='Savings', type='transfer')
        ])
        self.assertEqual(account.get_balance('2022-01-05'), 1000)

    def test_get_balance_for_date(self):
        account = Account(account_id='checking', name='Checking', start_date='2022-01-01', balance=1000)
        account.add_transactions([
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 14, 0, 0), amount=-250.0, name='Savings', type='transfer'),
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 28, 0, 0), amount=-250.0, name='Savings', type='transfer')
        ])
        self.assertEqual(account.get_balance('2022-01-05'), 1000)
        self.assertEqual(account.get_balance('2022-01-14'), 750)
        self.assertEqual(account.get_balance('2022-01-15'), 750)
        self.assertEqual(account.get_balance('2022-01-16'), 750)
        self.assertEqual(account.get_balance('2022-01-28'), 500)
        self.assertEqual(account.get_balance('2025-01-01'), 500)

    def test_add_previous_transaction_updates_balance(self):
        account = Account(account_id='checking', name='Checking', start_date='2022-01-01', balance=7500)
        account.add_transactions([
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 14, 0, 0), amount=-250.0, name='Savings', type='transfer'),
            Transaction(transaction_id='bi_weekly_transfer', account_id='checking',
                        date=datetime.datetime(2022, 1, 28, 0, 0), amount=-250.0, name='Savings', type='transfer')
        ])
        self.assertEqual(account.get_balance('2022-01-05'), 7500)
        self.assertEqual(account.get_balance('2022-01-14'), 7250)
        self.assertEqual(account.get_balance('2022-01-15'), 7250)
        self.assertEqual(account.get_balance('2022-01-16'), 7250)
        self.assertEqual(account.get_balance('2022-01-28'), 7000)
        self.assertEqual(account.get_balance('2025-01-01'), 7000)
        account.add_transaction(
            Transaction(transaction_id='mountain_bike', account_id='checking',
                        date=datetime.datetime(2022, 1, 18, 0, 0), amount=-1000, name='Mountain Bike', type='transfer'))
        self.assertEqual(account.get_balance('2022-01-05'), 7500)
        self.assertEqual(account.get_balance('2022-01-14'), 7250)
        self.assertEqual(account.get_balance('2022-01-15'), 7250)
        self.assertEqual(account.get_balance('2022-01-16'), 7250)
        self.assertEqual(account.get_balance('2022-01-28'), 6000)
        self.assertEqual(account.get_balance('2025-01-01'), 6000)


class TestDates(unittest.TestCase):
    @parameterized.expand([
        (
                # Every Month on the 31st
                "monthly_31st",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     '2022-11-05',
                    'frequency':    'monthly',
                    'interval':     1,
                    'day_of_week':  None,
                    'day_of_month': 31
                },
                {
                    'start_date': '2021-11-05',
                    'end_date':   '2022-11-05'
                },
                [
                    datetime.datetime(2021, 11, 30, 0, 0, 0),
                    datetime.datetime(2021, 12, 31, 0, 0, 0),
                    datetime.datetime(2022, 1, 31, 0, 0, 0),
                    datetime.datetime(2022, 2, 28, 0, 0, 0),
                    datetime.datetime(2022, 3, 31, 0, 0, 0),
                    datetime.datetime(2022, 4, 30, 0, 0, 0),
                    datetime.datetime(2022, 5, 31, 0, 0, 0),
                    datetime.datetime(2022, 6, 30, 0, 0, 0),
                    datetime.datetime(2022, 7, 31, 0, 0, 0),
                    datetime.datetime(2022, 8, 31, 0, 0, 0),
                    datetime.datetime(2022, 9, 30, 0, 0, 0),
                    datetime.datetime(2022, 10, 31, 0, 0, 0)
                ]
        ),
        (
                # Every Month on the 30th
                "monthly_30th",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     '2022-11-05',
                    'frequency':    'monthly',
                    'interval':     1,
                    'day_of_week':  None,
                    'day_of_month': 30
                },
                {
                    'start_date': '2021-11-05',
                    'end_date':   '2022-11-05'
                },
                [
                    datetime.datetime(2021, 11, 30, 0, 0, 0),
                    datetime.datetime(2021, 12, 31, 0, 0, 0),
                    datetime.datetime(2022, 1, 31, 0, 0, 0),
                    datetime.datetime(2022, 2, 28, 0, 0, 0),
                    datetime.datetime(2022, 3, 31, 0, 0, 0),
                    datetime.datetime(2022, 4, 30, 0, 0, 0),
                    datetime.datetime(2022, 5, 31, 0, 0, 0),
                    datetime.datetime(2022, 6, 30, 0, 0, 0),
                    datetime.datetime(2022, 7, 31, 0, 0, 0),
                    datetime.datetime(2022, 8, 31, 0, 0, 0),
                    datetime.datetime(2022, 9, 30, 0, 0, 0),
                    datetime.datetime(2022, 10, 31, 0, 0, 0)
                ]
        ),
        (
                # every other Friday
                "every_other_friday",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     '2022-11-05',
                    'frequency':    'weekly',
                    'interval':     2,
                    'day_of_week':  'fri',
                    'day_of_month': None
                },
                {
                    'start_date': '2021-11-05',
                    'end_date':   '2022-11-05'
                },
                [
                    datetime.datetime(2021, 11, 5, 0, 0),
                    datetime.datetime(2021, 11, 19, 0, 0),
                    datetime.datetime(2021, 12, 3, 0, 0),
                    datetime.datetime(2021, 12, 17, 0, 0),
                    datetime.datetime(2021, 12, 31, 0, 0),
                    datetime.datetime(2022, 1, 14, 0, 0),
                    datetime.datetime(2022, 1, 28, 0, 0),
                    datetime.datetime(2022, 2, 11, 0, 0),
                    datetime.datetime(2022, 2, 25, 0, 0),
                    datetime.datetime(2022, 3, 11, 0, 0),
                    datetime.datetime(2022, 3, 25, 0, 0),
                    datetime.datetime(2022, 4, 8, 0, 0),
                    datetime.datetime(2022, 4, 22, 0, 0),
                    datetime.datetime(2022, 5, 6, 0, 0),
                    datetime.datetime(2022, 5, 20, 0, 0),
                    datetime.datetime(2022, 6, 3, 0, 0),
                    datetime.datetime(2022, 6, 17, 0, 0),
                    datetime.datetime(2022, 7, 1, 0, 0),
                    datetime.datetime(2022, 7, 15, 0, 0),
                    datetime.datetime(2022, 7, 29, 0, 0),
                    datetime.datetime(2022, 8, 12, 0, 0),
                    datetime.datetime(2022, 8, 26, 0, 0),
                    datetime.datetime(2022, 9, 9, 0, 0),
                    datetime.datetime(2022, 9, 23, 0, 0),
                    datetime.datetime(2022, 10, 7, 0, 0),
                    datetime.datetime(2022, 10, 21, 0, 0),
                    datetime.datetime(2022, 11, 4, 0, 0)
                ]
        ),
        (
                # One-time
                "one_time",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     '2021-11-05',
                    'frequency':    'daily',
                    'interval':     1,
                    'day_of_week':  None,
                    'day_of_month': None
                },
                {
                    'start_date': '2021-11-05',
                    'end_date':   '2021-11-05'
                },
                [
                    datetime.datetime(2021, 11, 5, 0, 0)
                ]
        )
    ])
    def test_create_dates_fixed(self, name, spec, date_filter, expected):
        datespec = DateSpec.from_spec(spec)
        actual = datespec.generate_dates(start_date=date_filter['start_date'], end_date=date_filter['end_date'])
        self.assertEqual(actual, expected)

    @parameterized.expand([
        (
                # Every Month on the 31st
                "monthly_31st_fixed",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     '2022-11-05',
                    'frequency':    'monthly',
                    'interval':     1,
                    'day_of_week':  None,
                    'day_of_month': 31
                },
                {
                    'start_date': '2022-01-01',
                    'end_date':   '2022-06-30'
                },
                [
                    datetime.datetime(2022, 1, 31, 0, 0, 0),
                    datetime.datetime(2022, 2, 28, 0, 0, 0),
                    datetime.datetime(2022, 3, 31, 0, 0, 0),
                    datetime.datetime(2022, 4, 30, 0, 0, 0),
                    datetime.datetime(2022, 5, 31, 0, 0, 0),
                    datetime.datetime(2022, 6, 30, 0, 0, 0)
                ]
        ),
        (
                # Every Month on the 30th
                "monthly_30th_infinite",
                {
                    'start_date':   '2021-11-05',
                    'end_date':     None,
                    'frequency':    'monthly',
                    'interval':     1,
                    'day_of_week':  None,
                    'day_of_month': 30
                },
                {
                    'start_date': '2022-01-01',
                    'end_date':   '2022-06-30'
                },
                [
                    datetime.datetime(2022, 1, 31, 0, 0, 0),
                    datetime.datetime(2022, 2, 28, 0, 0, 0),
                    datetime.datetime(2022, 3, 31, 0, 0, 0),
                    datetime.datetime(2022, 4, 30, 0, 0, 0),
                    datetime.datetime(2022, 5, 31, 0, 0, 0),
                    datetime.datetime(2022, 6, 30, 0, 0, 0)
                ]
        )
    ])
    def test_create_dates_filtered(self, name, spec, date_filter, expected):
        datespec = DateSpec.from_spec(spec)
        actual = datespec.generate_dates(start_date=date_filter['start_date'], end_date=date_filter['end_date'])
        self.assertEqual(actual, expected)


class TestForecast(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_checking_transactions(self):
        spec = FixtureHelper.get_spec_fixture()
        forecast = Forecast.from_spec(spec['forecast'], '2022-01-01', '2022-12-31')
        df = forecast.get_account('checking').get_transactions_df()

        # Spot-check some rows
        mask = ((df['date'] >= '2022-02-01') & (df['date'] <= '2022-03-01'))
        t = df[mask]

        actual = t.to_numpy()
        expected = pd.DataFrame(
                [
                    {
                        'account_id': 'checking',
                        'date':       datetime.datetime(2022, 2, 1, 0, 0, 0),
                        'amount':     -149.82999999999993,
                        'name':       'Credit Card Pmt'
                    },
                    {
                        'account_id': 'checking',
                        'date':       datetime.datetime(2022, 2, 1, 0, 0, 0),
                        'amount':     -1500.0,
                        'name':       'Rent'
                    },
                    {
                        'account_id': 'checking',
                        'date':       datetime.datetime(2022, 2, 11, 0, 0, 0),
                        'amount':     -500.00,
                        'name':       '401k'
                    },
                    {
                        'account_id': 'checking',
                        'date':       datetime.datetime(2022, 2, 11, 0, 0, 0),
                        'amount':     2500.00,
                        'name':       'Paycheck'
                    },
                    {
                        'account_id': 'checking',
                        'date':       datetime.datetime(2022, 2, 11, 0, 0, 0),
                        'amount':     -500.00,
                        'name':       'Savings'
                    },
                    {
                        'account_id': 'checking',
                        'date':       datetime.datetime(2022, 2, 25, 0, 0, 0),
                        'amount':     -500.00,
                        'name':       '401k'
                    },
                    {
                        'account_id': 'checking',
                        'date':       datetime.datetime(2022, 2, 25, 0, 0, 0),
                        'amount':     2500.00,
                        'name':       'Paycheck'
                    },
                    {
                        'account_id': 'checking',
                        'date':       datetime.datetime(2022, 2, 25, 0, 0, 0),
                        'amount':     -500.00,
                        'name':       'Savings'
                    },
                    {
                        'account_id': 'checking',
                        'date':       datetime.datetime(2022, 3, 1, 0, 0, 0),
                        'amount':     -1100.3400000000001,
                        'name':       'Credit Card Pmt'
                    },
                    {
                        'account_id': 'checking',
                        'date':       datetime.datetime(2022, 3, 1, 0, 0, 0),
                        'amount':     -1500.00,
                        'name':       'Rent'
                    }
                ]
            ).to_numpy()

        np.testing.assert_array_equal(
            actual,
            expected
        )

    def test_cc_transactions(self):
        spec = FixtureHelper.get_spec_fixture()
        forecast = Forecast.from_spec(spec['forecast'], '2022-01-01', '2022-12-31')
        df = forecast.get_account('credit_card').get_transactions_df()

        # Spot-check some rows
        mask = ((df['date'] >= '2022-02-01') & (df['date'] <= '2022-03-01'))
        t = df[mask]

        actual = t.to_numpy()
        expected = pd.DataFrame(
                [
                    {
                        'account_id': 'credit_card',
                        'date':       datetime.datetime(2022, 2, 1, 0, 0, 0),
                        'amount':     149.82999999999993,
                        'name':       'Credit Card Pmt'
                    },
                    {
                        'account_id': 'credit_card',
                        'date':       datetime.datetime(2022, 2, 15, 0, 0, 0),
                        'amount':     -150.00,
                        'name':       'Gas'
                    },
                    {
                        'account_id': 'credit_card',
                        'date':       datetime.datetime(2022, 2, 15, 0, 0, 0),
                        'amount':     -750.00,
                        'name':       'Groceries'
                    },
                    {
                        'account_id': 'credit_card',
                        'date':       datetime.datetime(2022, 2, 15, 0, 0, 0),
                        'amount':     -500.00,
                        'name':       'Slush Fund'
                    },
                    {
                        'account_id': 'credit_card',
                        'date':       datetime.datetime(2022, 3, 1, 0, 0, 0),
                        'amount':     1100.3400000000001,
                        'name':       'Credit Card Pmt'
                    },
                ]
            ).to_numpy()

        np.testing.assert_array_equal(actual, expected)


if __name__ == "__main__":
    unittest.main()
