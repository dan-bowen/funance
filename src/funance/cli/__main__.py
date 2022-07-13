"""
https://codeburst.io/building-beautiful-command-line-interfaces-with-python-26c7e1bb54df
"""

import click

from .chromedriver import commands as chromedriver_group
from .dashboard import commands as dash_group
from .format import commands as format_group
from .init import commands as init_group
from .scrape import commands as scrape_group


@click.group()
def cli():
    """Funance is a collection of tools for personal finance data exploration"""
    pass


@cli.group(
    short_help='Manages Chromedriver stuff')
def chromedriver():
    """Manages Chromedriver stuff"""
    pass


cli.add_command(init_group.init)
cli.add_command(scrape_group.scrape)
cli.add_command(format_group.format_exports)
cli.add_command(dash_group.dashboard)

chromedriver.add_command(chromedriver_group.update)
chromedriver.add_command(chromedriver_group.service)

if __name__ == '__main__':
    cli()
