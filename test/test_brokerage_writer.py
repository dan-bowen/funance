import json
import unittest

from funance.scrape.export import BrokerageWriter


class TestBrokerageWriter(unittest.TestCase):
    def test_seralization(self):
        self.maxDiff = None

        account_name = 'Freedom'

        writer = BrokerageWriter('vanguard')
        writer.set_account(dict(account_name=account_name))
        writer.set_cash(account_name, '500.00')

        stock_ticker = dict(
            ticker='CRLBF',
            company_name='Cresco Labs',
            total_shares='73',
        )
        stock_lot = dict(
            date_acquired='12/27/2018',
            num_shares='16.0000',
            cost_per_share='39.21',
            total_cost='627.32',
            term='long'
        )

        writer.set_ticker(account_name, stock_ticker)
        writer.add_cost_basis(account_name, stock_ticker['ticker'], stock_lot)

        expected = dict(
            _meta=dict(brokerage='vanguard', version='0.0.1'),
            accounts=dict(
                [
                    (
                        account_name,
                        dict(
                            account_name=account_name,
                            cash='500.00',
                            cost_basis=dict(
                                [
                                    (
                                        'CRLBF',
                                        dict(
                                            ticker='CRLBF',
                                            company_name='Cresco Labs',
                                            total_shares='73',
                                            lots=[
                                                dict(
                                                    date_acquired='12/27/2018',
                                                    num_shares='16.0000',
                                                    cost_per_share='39.21',
                                                    total_cost='627.32',
                                                    term='long'
                                                )
                                            ]
                                        )
                                    )
                                ]
                            )
                        )
                    )
                ]
            )
        )
        actual = json.loads(json.dumps(writer.dump_schema()))
        self.assertEqual(expected, actual)

        if __name__ == '__main__':
            unittest.main()