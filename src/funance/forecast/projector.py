import attr
import pandas as pd

from .account import Accounts
from .transaction import ScheduledTransactions


@attr.define(kw_only=True)
class Chart:
    name: str = attr.ib()
    type: str = attr.ib()
    accounts: list = attr.ib()


@attr.define(kw_only=True)
class Projector:
    spec: dict = attr.ib(factory=dict)
    start_date: str = attr.ib(factory=str)
    end_date: str = attr.ib(factory=str)
    accounts: Accounts = attr.ib()

    @classmethod
    def from_spec(cls, spec, start_date, end_date):
        accounts = Accounts.from_spec(spec, start_date, end_date)
        accounts.apply_scheduled_transactions(ScheduledTransactions.from_spec(spec, start_date, end_date))
        return Projector(spec=spec, start_date=start_date, end_date=end_date, accounts=accounts)

    def get_account(self, account_id):
        return self.accounts.get_account(account_id)

    def get_charts(self):
        charts = []
        for chart in self.spec['chart_spec']:
            accounts = list(
                map(
                    lambda a: dict(
                        name=self.get_account(a).name,
                        df=self.get_account(a).get_running_balance_grouped()), chart['account_ids']
                )
            )
            charts.append(Chart(name=chart['name'], type=chart['type'], accounts=accounts))
        return charts
