import os

from funance.scrape.common import Paths
from funance.scrape.driver.session import Session
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException

"""
Additional imports of interest

from selenium.webdriver.chrome.service import Service

NOTES

SEE https://selenium-python.readthedocs.io/api.html#module-selenium.webdriver.common.service
chromedriver = Service(CHROMEDRIVER_EXECUTABLE)
chromedriver.start()
driver = webdriver.Remote(chromedriver.service_url)
"""


def attach_driver_session(session_id, executor_url):
    """
    Reuse exisitng browser session

    https://tarunlalwani.com/post/reusing-existing-browser-session-selenium/

    :param session_id:
    :param executor_url:
    :return:
    """
    from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

    # Save the original function, so we can revert our patch
    org_command_execute = RemoteWebDriver.execute

    def new_command_execute(self, command, params=None):
        if command == "newSession":
            # Mock the response
            return {'success': 0, 'value': None, 'sessionId': session_id}
        else:
            return org_command_execute(self, command, params)

    # Patch the function before creating the driver object
    RemoteWebDriver.execute = new_command_execute

    new_driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
    new_driver.session_id = session_id

    # Replace the patched function with original function
    RemoteWebDriver.execute = org_command_execute

    return new_driver


def create_driver(session=False, detached=False):
    sess = Session.from_file()

    if session:
        # connect to existing session
        driver = attach_driver_session(sess.session_id, sess.executor_url)
    else:
        # Without an existing session we manually create the driver
        chrome_options = webdriver.ChromeOptions()
        # Detach from script so browser does not automatically close when execution ends
        chrome_options.add_experimental_option("detach", detached)
        try:
            driver = webdriver.Chrome(get_chromedriver_executable(sess.chromedriver_version), port=4444, chrome_options=chrome_options)
        except SessionNotCreatedException as e:
            """
            TODO throw custom exception, additionally handling this message on Chrome/Chromedriver version mismatch
            
            selenium.common.exceptions.SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version 88
            Current browser version is 101.0.4951.64 with binary path /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
            """
            raise e

        sess.executor_url = driver.command_executor._url
        sess.session_id = driver.session_id
        sess.close()

    return driver


def get_chromedriver_executable(chromedriver_version):
    # TODO choose driver based on platform
    return os.path.join(
        Paths.CHROMEDRIVER_DIR,
        chromedriver_version,
        'chromedriver_mac64',
        'chromedriver'
    )
