"""
https://codeburst.io/building-beautiful-command-line-interfaces-with-python-26c7e1bb54df
"""

import click

from .dashboard import commands as dash_group
from .init import commands as init_group


@click.group()
def cli():
    """Funance is a collection of tools for personal finance data exploration"""
    pass


cli.add_command(init_group.init)
cli.add_command(dash_group.dashboard)

if __name__ == '__main__':
    cli()
