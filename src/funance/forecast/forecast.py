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
class Forecast:
    spec: dict = attr.ib(factory=dict)
    start_date: str = attr.ib(factory=str)
    end_date: str = attr.ib(factory=str)
    accounts: Accounts = attr.ib()

    @classmethod
    def from_spec(cls, spec, start_date, end_date):
        accounts = Accounts.from_spec(spec, start_date, end_date)
        accounts.apply_scheduled_transactions(ScheduledTransactions.from_spec(spec, start_date, end_date))
        return Forecast(spec=spec, start_date=start_date, end_date=end_date, accounts=accounts)

    def get_account(self, account_id):
        return self.accounts.get_account(account_id)
