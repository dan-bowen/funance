import attr
import pandas as pd

from .account import Accounts
from .transaction import ScheduledTransactions


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

    @classmethod
    def get_runway_report(cls, spec: dict) -> dict:
        runway_goal_mos = spec['runway_goal_mos']
        monthly_spending_assumption = spec['monthly_spending_assumption']
        df = pd.DataFrame(spec['sources'])
        amt_actual = df['value'].sum()
        amt_goal = runway_goal_mos * monthly_spending_assumption
        runway_mos = amt_actual / monthly_spending_assumption
        return {
            'df':                df,
            'runway_mos_goal':   runway_goal_mos,
            'runway_mos_actual': runway_mos,
            'amt_goal':          amt_goal,
            'amt_actual':        amt_actual
        }
