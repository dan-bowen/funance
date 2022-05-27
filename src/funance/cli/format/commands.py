import click

from funance.scrape.export import BrokerageFormatterFactory


@click.command(
    name='format',
    short_help='Format exported data'
)
@click.argument('fmt', type=click.Choice(['csv'], case_sensitive=True))
def format_exports(fmt):
    """Format exported data into custom formats"""

    formatter = BrokerageFormatterFactory().get_formatter(fmt)
    result = formatter.format()
