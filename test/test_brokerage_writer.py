import unittest
import json
from funance.scrape.export import BrokerageWriter


class TestBrokerageWriter(unittest.TestCase):
    def test_seralization(self):
        self.maxDiff = None

        writer = BrokerageWriter('vanguard')

        account = dict(account_name='Freedom', cash='', cost_basis=[])

        writer.set_cash('Freedom', '500.00')

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

        writer.set_cost_basis('Freedom', stock_ticker, [stock_lot])

        expected = dict(
            _meta=dict(brokerage='vanguard', version='0.0.1'),
            accounts=[
                dict(account_name='Freedom', cash='500.00', cost_basis=[
                    dict(
                        ticker='CRLBF',
                        company_name='Cresco Labs',
                        total_shares='73',
                        lots=[dict(
                            date_acquired='12/27/2018',
                            num_shares='16.0000',
                            cost_per_share='39.21',
                            total_cost='627.32',
                            term='long'
                        )]
                    )
                ])
            ]
        )
        actual = json.loads(json.dumps(writer.dump_schema()))
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
