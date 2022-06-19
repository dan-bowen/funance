import json

from marshmallow import Schema, fields, validate, ValidationError

from funance.common.paths import EXPORT_DIR

PREFIX = 'brokerage'


class StockLotSchema(Schema):
    date_acquired = fields.Str(required=True)
    num_shares = fields.Str(required=True)
    cost_per_share = fields.Str(required=True)
    total_cost = fields.Str(required=True)
    term = fields.Str(required=True, validate=validate.OneOf(["short", "long"]))

    class Meta:
        ordered = True


class StockTickerSchema(Schema):
    ticker = fields.Str(required=True)
    company_name = fields.Str(required=True)
    total_shares = fields.Str(required=True)
    lots = fields.List(fields.Nested(StockLotSchema), required=True)

    class Meta:
        ordered = True


class AccountSchema(Schema):
    account_name = fields.Str(required=True)
    cash = fields.Str()
    cost_basis = fields.Dict(keys=fields.Str(required=True), values=fields.Nested(StockTickerSchema))

    class Meta:
        ordered = True


class MetaSchema(Schema):
    version = fields.Str(required=True)
    brokerage = fields.Str(required=True)

    class Meta:
        ordered = True


class JsonSchema(Schema):
    _meta = fields.Nested(MetaSchema)
    accounts = fields.Dict(keys=fields.Str(required=True), values=fields.Nested(AccountSchema))

    class Meta:
        ordered = True


class BrokerageWriter:
    def __init__(self, brokerage):
        self.brokerage = brokerage
        self.accounts = {}

    def set_account(self, account: dict):
        self.accounts[account['account_name']] = account
        self.accounts[account['account_name']]['cost_basis'] = {}

    def set_cash(self, account_name: str, cash: str):
        self.accounts[account_name]['cash'] = cash

    def set_ticker(self, account_name: str, ticker: dict):
        self.accounts[account_name]['cost_basis'][ticker['ticker']] = ticker
        self.accounts[account_name]['cost_basis'][ticker['ticker']]['lots'] = []

    def add_cost_basis(self, account_name: str, ticker: str, stock_lot: dict):
        self.accounts[account_name]['cost_basis'][ticker]['lots'].append(stock_lot)

    def dump_schema(self):
        try:
            result = JsonSchema().load(dict(
                _meta=dict(
                    version='0.0.1',
                    brokerage=self.brokerage
                ),
                accounts=self.accounts
            ))
        except ValidationError as e:
            # print(err.messages)
            # print(err.valid_data)
            raise e

        return JsonSchema().dump(result)

    def write(self):
        with open(f"{EXPORT_DIR}/{PREFIX}.{self.brokerage}.json", 'w') as fp:
            json.dump(self.dump_schema(), fp, indent=4)
