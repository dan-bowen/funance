from .brokerage_writer import BrokerageWriter
from .brokerage_formatter import BrokerageFormatterFactory


class UnsupportedTypeException(Exception):
    pass


class UnsupportedFormatException(Exception):
    pass


class FormatterFactory:
    types = {
        'brokerage': BrokerageFormatterFactory,
    }

    def get_supported_types(self):
        return self.types.keys()

    def get_formatter(self, type_, format_):
        type_class = self.types.get(type_)
        if type_class is None:
            supported_types = ', '.join(self.get_supported_types())
            raise UnsupportedTypeException(f"type must be one of {supported_types}")

        return type_class().get_formatter(format_)
