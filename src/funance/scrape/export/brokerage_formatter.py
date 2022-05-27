import json
import csv
import os
from funance.scrape.common import Paths


class CsvFormatter:
    def __init__(self):
        pass

    def format(self):
        filenames = [
            f for f in os.listdir(Paths.EXPORT_DIR_BROKERAGE) if f.endswith('.json')
        ]
        filenames.sort(reverse=True)
        print(f"[DEBUG] Found exported filenames: {filenames}")
        # set prefix to that of the first element of the first filename
        prefix = filenames[0].split('.')[0]
        matching_filenames = [
            f for f in filenames if f.startswith(prefix)
        ]
        print(f"[DEBUG] Found matching filenames: {matching_filenames}")
        exported_filename = f'{Paths.EXPORT_DIR_BROKERAGE}/{prefix}.csv'
        with open(exported_filename, mode='w') as csv_file:
            fieldnames = ['account_name', 'ticker', 'date_acquired', 'num_shares', 'cost_per_share', 'total_cost']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for filename in matching_filenames:
                print(f'[DEBUG] Processing file {filename}')
                with open(f"{Paths.EXPORT_DIR_BROKERAGE}/{filename}", "r") as src_file:
                    data = json.load(src_file)
                    for a in data['accounts']:
                        for cb in a['cost_basis']:
                            for lot in cb['lots']:
                                writer.writerow(dict(
                                    ticker=cb['ticker'],
                                    date_acquired=lot['date_acquired'],
                                    num_shares=lot['num_shares'],
                                    cost_per_share=lot['cost_per_share'],
                                    total_cost=lot['total_cost'],
                                    account_name=a['account_name']
                                ))
        print(f'[INFO] Generated file: {exported_filename}')


class UnsupportedFormatterException(Exception):
    pass


class BrokerageFormatterFactory:
    formatters = {
        'csv': CsvFormatter
    }

    def get_supported_formatters(self):
        return self.formatters.keys()

    def get_formatter(self, formatter_name):
        formatter_class = self.formatters.get(formatter_name)
        if formatter_class is None:
            supported_formatters = ', '.join(self.get_supported_formatters())
            raise UnsupportedFormatterException(f"Formatter must be one of {supported_formatters}")
        return formatter_class()
