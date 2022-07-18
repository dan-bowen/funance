from pathlib import Path
import shutil
import click

from funance.common.paths import (
    PROJECT_DIR,
    CHROMEDRIVER_DIR,
    EXPORT_DIR,
    SPEC_DIST_FILE,
    SPEC_FILE,
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

    # copy spec file, if it doesn't exist
    if not Path(SPEC_FILE).is_file():
        shutil.copyfile(SPEC_DIST_FILE, SPEC_FILE)
        click.echo(f"copied funance file {SPEC_FILE}")

    do_update()
