from __future__ import annotations

from datetime import datetime
from typing import List, Union, TYPE_CHECKING

import attr
from dateutil.relativedelta import relativedelta as drel

from .datespec import DateSpec
from funance.common.logger import get_logger

logger = get_logger('transaction')

if TYPE_CHECKING:
    from .account import Accounts


@attr.define(kw_only=True)
class Transfer:
    direction: str = attr.ib()
    account_id: str = attr.ib()


@attr.define(kw_only=True)
class Transaction:
    transaction_id: str = attr.ib()
    account_id: str = attr.ib()
    date: datetime = attr.ib()
    amount: float = attr.ib()
    name: str = attr.ib()
    type: str = attr.ib()


@attr.define(kw_only=True)
class CCBalanceAmount:
    account_id: str = attr.ib()
    index: int = attr.ib()

    @classmethod
    def from_spec(cls, spec: dict, index: int):
        instructions = spec['cc_balance']
        return CCBalanceAmount(account_id=instructions['account_id'], index=index)


@attr.define(kw_only=True)
class DynamicTransaction(Transaction):
    amount: CCBalanceAmount = attr.ib()
    transfer: Union[Transfer, None] = attr.ib()

    def exchange(self, accounts: Accounts) -> List[Transaction]:
        amount = self.amount
        account = accounts.get_account(amount.account_id)
        last_month = self.date + drel(months=-1)
        close_date = last_month + drel(day=account.stmt_close_dom)
        is_pmt_plan = account.pmt_plan is not None

        do_logging = is_pmt_plan

        if do_logging:
            logger.debug('--------------exchanging DynamicTransaction------------------')
            logger.debug('%s', {
                'amount':     amount,
                'date':       self.date.strftime('%Y-%m-%d'),
                # today+1
                'last_month': last_month.strftime('%Y-%m-%d'),
                'acct_start_date': account.start_date.strftime('%Y-%m-%d'),
                # 'today': today,
                'close_date': close_date.strftime('%Y-%m-%d')
            })

        if amount.index == 0:
            balance = account.stmt_balance
        else:
            if is_pmt_plan:
                main_balance = account.get_balance(close_date)
                ref_acct = accounts.get_account(account.pmt_plan['ref_account_id'])
                ref_balance = ref_acct.get_balance(close_date)
                balance = main_balance - ref_balance

                logger.debug('%s', {
                    'main_balance': main_balance,
                    'ref_balance': ref_balance,
                    'new_balance': balance,
                })
            else:
                balance = account.get_balance(close_date)

        if balance >= 0:
            balance = 0

        t = ScheduledTransaction.create_plain_transaction(transaction_id=self.transaction_id,
                                                          account_id=self.account_id,
                                                          name=self.name,
                                                          ttype=self.type,
                                                          date=self.date,
                                                          amount=balance,
                                                          transfer=self.transfer)

        # if do_logging:
        #     logger.debug('%s', t)

        return t


@attr.define(kw_only=True)
class ScheduledTransactions:
    plain: list = attr.ib(factory=list)
    dynamic: list = attr.ib(factory=list)

    @classmethod
    def from_spec(cls, spec, start_date: datetime, end_date: datetime):
        transactions = []
        for account_id, account_spec in spec['accounts'].items():
            if account_spec['scheduled_transactions']:
                for trans_id, trans in account_spec['scheduled_transactions'].items():
                    st = ScheduledTransaction.from_spec(account_id, trans_id, trans)
                    transactions.extend(st.generate_transactions(start_date, end_date))
        plain = [t for t in transactions if type(t).__name__ == 'Transaction']
        dynamic = [t for t in transactions if type(t).__name__ == 'DynamicTransaction']
        return ScheduledTransactions(plain=plain, dynamic=dynamic)


@attr.define(kw_only=True)
class ScheduledTransaction:
    transaction_id: str = attr.ib()
    account_id: str = attr.ib()
    name: str = attr.ib()
    amount: Union[float, dict] = attr.ib()
    type: str = attr.ib()
    date_spec: DateSpec = attr.ib()
    transfer: Union[Transfer, None] = attr.ib()

    @classmethod
    def from_spec(cls, account_id: str, transaction_id: str, spec: dict):
        transfer = None if spec['transfer'] is None else Transfer(direction=spec['transfer']['direction'],
                                                                  account_id=spec['transfer']['account_id'])
        st = ScheduledTransaction(transaction_id=transaction_id, account_id=account_id,
                                  name=spec['name'], amount=spec['amount'], type=spec['type'],
                                  date_spec=DateSpec.from_spec(spec['date_spec']), transfer=transfer)
        return st

    def generate_transactions(self, start_date: datetime, end_date: datetime) -> list:
        """
        Generate transactions

        This process may generate transactions for any other account
        """
        transactions = []
        dates = self.date_spec.generate_dates(start_date, end_date)
        for i, d in enumerate(dates):
            transactions.extend(
                self.create_root_transaction(
                    index=i,
                    transaction_id=self.transaction_id,
                    account_id=self.account_id,
                    name=self.name,
                    ttype=self.type,
                    date=d,
                    amount=self.amount,
                    transfer=self.transfer
                ))
        return transactions

    @classmethod
    def create_root_transaction(cls, *, index: int, transaction_id: str, account_id: str, name: str, ttype: str,
                                date: datetime, amount: Union[float, dict], transfer: Union[Transfer, None]) -> list:
        if type(amount) == dict:
            return cls.create_dynamic_transaction(index=index, transaction_id=transaction_id, account_id=account_id,
                                                  name=name, ttype=ttype, date=date, amount=amount, transfer=transfer)
        return cls.create_plain_transaction(transaction_id=transaction_id, account_id=account_id,
                                            name=name, ttype=ttype, date=date, amount=amount, transfer=transfer)

    @classmethod
    def create_plain_transaction(cls, *, transaction_id: str, account_id: str, name: str, ttype: str, date: datetime,
                                 amount: float, transfer: Transfer) -> List[Transaction]:
        if ttype == 'transfer':
            return cls.create_plain_transfer(transaction_id=transaction_id, account_id=account_id,
                                             name=name, ttype=ttype, date=date, amount=amount, transfer=transfer)
        if ttype == 'income':
            return cls.create_plain_credit(transaction_id=transaction_id, account_id=account_id,
                                           name=name, ttype=ttype, date=date, amount=amount)
        if ttype == 'expense':
            return cls.create_plain_debit(transaction_id=transaction_id, account_id=account_id,
                                          name=name, ttype=ttype, date=date, amount=amount)

    @classmethod
    def create_plain_transfer(cls, *, transaction_id: str, account_id: str, name: str, ttype: str, date: datetime,
                              amount: float, transfer: Transfer) -> List[Transaction]:
        transactions = []
        # determine sending and receiving account
        if transfer.direction == 'to':
            sending_account_id = account_id
            receiving_account_id = transfer.account_id
        elif transfer.direction == 'from':
            sending_account_id = transfer.account_id
            receiving_account_id = account_id
        else:
            raise ValueError(f'Transfer direction must be one of "to", "from". Received: {transfer.direction}')
        # debit sending account
        transactions.append(
            Transaction(transaction_id=transaction_id, type=ttype, account_id=sending_account_id, date=date,
                        amount=-abs(amount), name=name)
        )
        # credit receiving account
        transactions.append(
            Transaction(transaction_id=transaction_id, type=ttype, account_id=receiving_account_id, date=date,
                        amount=abs(amount), name=name)
        )
        return transactions

    @classmethod
    def create_plain_credit(cls, *, transaction_id: str, account_id: str, name: str, ttype: str, date: datetime,
                            amount: float) -> List[Transaction]:
        return [Transaction(transaction_id=transaction_id, type=ttype, account_id=account_id, date=date,
                            amount=abs(amount), name=name)]

    @classmethod
    def create_plain_debit(cls, *, transaction_id: str, account_id: str, name: str, ttype: str,
                           date: datetime, amount: float) -> List[Transaction]:
        return [Transaction(transaction_id=transaction_id, type=ttype, account_id=account_id, date=date,
                            amount=-abs(amount), name=name)]

    @classmethod
    def create_dynamic_transaction(cls, *, index: int, transaction_id: str, account_id: str, name: str, ttype: str,
                                   date: datetime, amount: dict, transfer: Transfer) -> List[DynamicTransaction]:
        return [DynamicTransaction(transaction_id=transaction_id, type=ttype, account_id=account_id,
                                   date=date, amount=CCBalanceAmount.from_spec(amount, index), name=name,
                                   transfer=transfer)]
