import click

from funance.scrape.export import FormatterFactory


@click.command(
    name='format',
    short_help='Format exported data'
)
@click.argument('type_', type=click.Choice(['brokerage'], case_sensitive=True))
@click.argument('fmt_', type=click.Choice(['csv'], case_sensitive=True))
def format_exports(type_, fmt_):
    """Format exported data into custom formats"""
    formatter = FormatterFactory().get_formatter(type_, fmt_)
    result = formatter.format()
