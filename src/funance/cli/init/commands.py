from pathlib import Path
import shutil
import click

from funance.common.paths import (
    PROJECT_DIR,
    CHROMEDRIVER_DIR,
    EXPORT_DIR,
    FORECAST_DIST_FILE,
    FORECAST_FILE,
    INVEST_DIST_FILE,
    INVEST_FILE,
    ENV_DIST_FILE,
    ENV_FILE
)
from funance.scrape.driver.updater import do_update


@click.command(
    short_help='Initialize the project'
)
def init():
    """Initialize the project"""

    # create project directory
    Path(PROJECT_DIR).mkdir(parents=True, exist_ok=True)
    click.echo(f"created directory {PROJECT_DIR}")

    Path(CHROMEDRIVER_DIR).mkdir(parents=True, exist_ok=True)
    click.echo(f"created directory {CHROMEDRIVER_DIR}")

    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    click.echo(f"created directory {EXPORT_DIR}")

    # copy .env file, if it doesn't exist
    click.echo(ENV_FILE)
    if not Path(ENV_FILE).is_file():
        shutil.copyfile(ENV_DIST_FILE, ENV_FILE)
        click.echo(f"copied env file {ENV_FILE}")

    # copy forecast file, if it doesn't exist
    if not Path(FORECAST_FILE).is_file():
        shutil.copyfile(FORECAST_DIST_FILE, FORECAST_FILE)
        click.echo(f"copied forecast file {FORECAST_FILE}")

    # copy invest file, if it doesn't exist
    if not Path(INVEST_FILE).is_file():
        shutil.copyfile(INVEST_DIST_FILE, INVEST_FILE)
        click.echo(f"copied invest file {INVEST_FILE}")

    do_update()
