from pathlib import Path
import shutil
import click

from funance.common.paths import PROJECT_DIR, CHROMEDRIVER_DIR, EXPORT_DIR, FORECAST_DIST_FILE, FORECAST_FILE
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

    # copy forecast file, if it doesn't exist
    if not Path(FORECAST_FILE).is_file():
        shutil.copyfile(FORECAST_DIST_FILE, FORECAST_FILE)
        click.echo(f"copied forecast file {FORECAST_FILE}")

    do_update()
