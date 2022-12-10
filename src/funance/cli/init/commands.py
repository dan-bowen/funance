import click

from funance import create_app


@click.command(
    short_help='Initialize the project'
)
def init():
    """Initialize the project"""
    app = create_app()
    app.init()
