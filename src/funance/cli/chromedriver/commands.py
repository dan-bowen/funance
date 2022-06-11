import subprocess
import time

import click
from selenium.common.exceptions import WebDriverException

from funance.scrape.driver import create_driver
from funance.scrape.driver.updater import do_update


@click.command(
    short_help='Chromedriver service manager'
)
@click.argument('command', type=click.Choice(['start', 'status']))
def service(command):
    """Manages a standalone Chromedriver process, which provides a re-usable session.

    This is useful during development when there may be errors, and re-using an existing
    session will save some cycles.
    """

    if command == 'status':
        output = subprocess.check_output("ps aux | grep chromedriver", shell=True)
        click.echo(output)

    if command == 'start':
        driver = create_driver(session=False, detached=True)
        click.echo(f"[INFO] You may now use the --session flag to re-use this session.")
        click.echo(f"[INFO] Switch to another tab to keep the service alive.")
        # driver will have a service attribute if this script is the one that started the chromedriver service
        # TODO do we need the if statement?
        if hasattr(driver, 'service'):
            # keep script running so we can re-use the session
            while True:
                time.sleep(1)
                try:
                    # throws WebDriverException if chromedriver service is not running
                    driver.service.assert_process_still_running()
                except (WebDriverException, KeyboardInterrupt):
                    driver.quit()


@click.command(
    short_help='Update Chromedriver'
)
def update():
    """Update Chromedriver version to match locally installed Chrome version"""

    do_update()
