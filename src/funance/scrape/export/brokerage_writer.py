import time
import json
from datetime import date
from marshmallow import Schema, fields, post_load, pre_dump, ValidationError
from funance.scrape.common import Paths


class StockLotSchema(Schema):
    date_acquired = fields.Str(required=True)
    num_shares = fields.Str(required=True)
    cost_per_share = fields.Str(required=True)
    total_cost = fields.Str(required=True)

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
    cost_basis = fields.List(fields.Nested(StockTickerSchema), required=True)

    class Meta:
        ordered = True


class MetaSchema(Schema):
    version = fields.Str(required=True)
    brokerage = fields.Str(required=True)

    class Meta:
        ordered = True


class JsonSchema(Schema):
    _meta = fields.Nested(MetaSchema)
    accounts = fields.List(fields.Nested(AccountSchema), required=True)

    class Meta:
        ordered = True


class BrokerageWriter:
    def __init__(self, brokerage):
        self.brokerage = brokerage
        self.accounts = []

    def add_account(self, account):
        self.accounts.append(account)

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
        today = date.today().strftime("%Y-%m-%d")
        with open(f"{Paths.EXPORT_DIR_BROKERAGE}/{today}.{self.brokerage}.json", 'w') as fp:
            json.dump(self.dump_schema(), fp, indent=4)
