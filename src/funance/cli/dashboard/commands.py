import click

from funance import create_app


@click.command(short_help='Run the dashboard')
def dashboard():
    """Open the dashboard"""
    app = create_app()
    app.run()
