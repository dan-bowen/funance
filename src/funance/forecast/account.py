from typing import Union

import attr
import dateutil.parser as dp
import pandas as pd

from .exceptions import InvalidAccountType, AccountNotFoundException, OutOfBoundsException
from .transaction import ScheduledTransactions

pd.options.mode.chained_assignment = None  # no warning message and no exception is raised


@attr.define(kw_only=True)
class Account:
    account_id: str = attr.ib()
    name: str = attr.ib()
    start_date: str = attr.ib()
    balance: float = attr.ib()
    transactions: list = attr.ib(factory=list)
    transactions_df: Union[pd.DataFrame, None] = attr.ib()

    @transactions_df.default
    def _default_transactions_df(self):
        return None

    def add_transactions(self, transactions):
        for t in transactions:
            self.add_transaction(t)

    def add_transaction(self, transaction):
        """
        Add a transaction to the Account

        :param transaction: Transaction
        :return:
        """
        if transaction.account_id != self.account_id:
            raise ValueError(f'Expected account id: {self.account_id} Received: {transaction.account_id}')
        self.transactions_df = None  # flip to None so it gets rebuilt on the next request
        self.transactions.append(transaction)

    def get_transactions_df(self):
        """
        Get master transactions_df

        :return: pd.DataFrame
        """
        if self.transactions_df is None:
            data = list(map(attr.asdict, self.transactions))
            df = pd.DataFrame(data, columns=['account_id', 'date', 'amount', 'name'])
            # round amount
            df['amount'].round(decimals=2)
            df = df.sort_values(by=['date', 'name'],
                                ascending=True,
                                ignore_index=True)
            self.transactions_df = df
        return self.transactions_df

    def get_balance(self, date):
        """
        Get balance for a date

        :param date: str
        :return: float
        """
        target_date = dp.parse(date)
        account_start = dp.parse(self.start_date)
        df = self.get_running_balance_grouped()
        if target_date < account_start:
            raise OutOfBoundsException(f'date {target_date} before start_date of the account: {account_start}')
        if len(df.index) == 0:
            return self.balance
        # slice everything after the target date
        sub_df = df[df.index.to_pydatetime() <= target_date]
        if len(sub_df.index) == 0:
            return self.balance
        last_row_df = sub_df.iloc[-1:]
        balance = last_row_df.iloc[0]['balance']
        return balance

    def get_running_balance(self):
        """
        Get running balance df with transactions as separate row

        :return: pd.DataFrame
        """
        trans_df = self.get_transactions_df().copy()
        return self.apply_running_balance(self.balance, trans_df)

    def get_running_balance_grouped(self):
        """
        Get running balance df with transactions grouped and indexed by date

        :return: pd.DataFrame
        """
        trans_df = self.get_running_balance()
        # create new column with "transaction: amount" string
        trans_df['amt_desc'] = trans_df['amount']
        trans_df['amt_desc'] = trans_df['amt_desc'].apply(lambda x: f'${x:.2f}')
        trans_df['amt_desc'] = trans_df['amt_desc'].str.cat(trans_df['name'], sep=': ')
        # group by date
        df_date_group = trans_df.groupby('date').agg({
            'amt_desc': '<br>'.join,
            'amount':   'sum'
        })
        return self.apply_running_balance(self.balance, df_date_group)

    @classmethod
    def apply_running_balance(cls, starting_balance, trans_df):
        trans_df['balance'] = starting_balance + trans_df['amount'].cumsum()
        return trans_df


@attr.define(kw_only=True)
class CreditCardAccount(Account):
    stmt_balance: float = attr.ib()
    stmt_close_dom: int = attr.ib()
    pmt_plan: Union[dict, None] = attr.ib()


@attr.define(kw_only=True)
class AccountFactory:
    @classmethod
    def from_spec(cls, spec):
        acct_type = spec['type']
        if acct_type == 'cc':
            return CreditCardAccount(account_id=spec['account_id'], name=spec['name'], start_date=spec['start_date'],
                                     balance=spec['balance'], stmt_balance=spec['stmt_balance'],
                                     stmt_close_dom=spec['stmt_close_dom'], pmt_plan=spec['pmt_plan'])
        elif acct_type in ['checking', 'savings', 'invest', 'loan']:
            return Account(account_id=spec['account_id'], name=spec['name'], start_date=spec['start_date'],
                           balance=spec['balance'])
        else:
            raise InvalidAccountType(f'Account type not found: {acct_type}')


@attr.define(kw_only=True)
class Accounts:
    accounts: dict = attr.ib(factory=dict)

    @classmethod
    def from_spec(cls, spec, start_date, end_date):
        accounts = dict()
        for account_id, account_spec in spec['accounts'].items():
            account_spec['account_id'] = account_id
            account_spec['start_date'] = start_date
            accounts[account_id] = AccountFactory.from_spec(account_spec)
        return Accounts(accounts=accounts)

    def get_account(self, account_id: str) -> Union[Account, CreditCardAccount]:
        account = self.accounts.get(account_id, None)
        if account is None:
            raise AccountNotFoundException(f'account not found: {account_id}')
        return account

    def add_transactions(self, transactions: list) -> None:
        for t in transactions:
            account = self.get_account(t.account_id)
            account.add_transaction(t)

    def apply_scheduled_transactions(self, st: ScheduledTransactions):
        # apply plain transactions
        self.add_transactions(st.plain)
        # Apply dynamic transactions: By sorting these by date and adding them sequentially,
        # the dynamic balance will be calculated correctly as each DynamicTransaction is
        # exchanged, and subsequent transactions are added to the account.
        dynamic = sorted(st.dynamic, key=lambda d: d.date)
        for dt in dynamic:
            transactions = dt.exchange(self)
            self.add_transactions(transactions)
