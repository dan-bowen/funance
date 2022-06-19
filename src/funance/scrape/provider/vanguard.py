from datetime import datetime

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from funance.common.logger import get_logger
from funance.scrape.export import BrokerageWriter

logger = get_logger('vanguard')


date_foramt = '%m/%d/%Y'


def clean_account_name(account_name: str):
    """
    Clean the account name

    NOTE account_name can be slightly different (extra characters
    like '*' or ' ') on each scraped page due to selectors being
    inconsistent (or other reasons).

    The inconsistent account_name causes problems with:
        - the writer due to the account_name being used as a dictionary key
        - later analysis due to multiple name for the same account

    This method cleans up the account name for consistency.
    """

    clean_string = account_name.replace('—', ' ')

    # list comprehension that filters out bad characters
    clean_string = [s for s in clean_string if s.isalnum() or s.isspace()]
    # rejoin intermediate list into a string
    clean_string = "".join(clean_string)

    # delete repeated spaces
    clean_string = " ".join(clean_string.split())
    return clean_string.strip()


class Vanguard:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.writer = BrokerageWriter('vanguard')

    def scrape(self):
        self._wait_for_login()
        self._get_cash()
        self._get_cost_basis()
        self._write_export()

    def _wait_for_login(self):
        self.driver.get('https://investor.vanguard.com/my-account/log-on')
        # Wait for the "Log out" link to appear. This is the hint that the user has logged in.
        try:
            is_authenticated = True
            log_off_link = WebDriverWait(self.driver, 300).until(
                # NOTE: By.LINK_TEXT appears to take into account case-sensitivity as well as CSS text transformations.
                EC.presence_of_element_located((By.LINK_TEXT, 'Log out'))
            )
        except TimeoutException:
            is_authenticated = False

        logger.info(f"Logged On: {is_authenticated}")

    def _get_cash(self):
        self.driver.get('https://personal.vanguard.com/us/myaccounts/balancesholdings')

        # wait
        el = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.t-unit'))
        )

        # account tables
        account_tables = self.driver.find_elements(By.CSS_SELECTOR, "div.t-unit")

        for t in account_tables:
            account_name = t.find_element(By.CSS_SELECTOR, 'h3').text
            account_name = clean_account_name(account_name)
            logger.info(f'getting cash for {account_name}')

            data_tables = t.find_elements(By.CSS_SELECTOR, '.dataTable')
            # 3rd datatable
            table = data_tables[2]

            trs = table.find_elements(By.CSS_SELECTOR, 'table tr')
            # 2nd tr
            tr = trs[1]

            tds = tr.find_elements(By.CSS_SELECTOR, 'td')
            # 2nd td
            cash = tds[1].text
            cash = cash.replace('$', '').replace(',', '').strip()
            logger.debug(f'cash abalance: {cash}')

            self.writer.set_account(dict(account_name=account_name))
            self.writer.set_cash(account_name, cash)

            self.writer.set_ticker(account_name, dict(
                ticker='X_CASH',
                company_name='CASH',
                total_shares=cash,
            ))
            self.writer.add_cost_basis(account_name, 'X_CASH', dict(
                date_acquired=datetime.today().strftime('%Y-%m-%d'),
                num_shares=cash,
                cost_per_share='1.00',
                total_cost=cash,
                term='long'
            ))

    def _wait_for_cost_basis_tables(self):
        """
        Wait for cost basis tables to get loaded via Ajax

        :return:
        """
        xpath = '//div[@id="unrealizedTabForm"]'
        cost_basis_tables = self.wait.until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return cost_basis_tables

    def _get_cost_basis(self):
        self.driver.get('https://personal.vanguard.com/us/XHTML/com/vanguard/costbasisnew/xhtml/CostBasisSummary.xhtml')
        self._wait_for_cost_basis_tables()

        account_tables = self.driver.find_elements_by_xpath('//table[contains(@class, "dataTable")]')
        for account_table in account_tables:
            # account name
            account_name = account_table.find_element_by_tag_name('h1').text
            account_name = clean_account_name(account_name)
            logger.info(f"Getting cost basis for account: {account_name}")

            # get all rows that have a .linkBarWrapper
            rows = account_table.find_elements_by_tag_name('tr')
            for row in rows:
                try:
                    # Check if this row has a Buy link. This row has our ticker data.
                    row.find_element_by_link_text('Buy')
                except NoSuchElementException:
                    # skip this row
                    continue

                # ticker
                ticker_cell = row.find_element_by_css_selector('td:nth-child(1)')
                ticker = ticker_cell.text
                logger.info(f"Getting cost basis for ticker: {ticker}")

                """
                Company name

                This cell's text contains more than just the company name.

                ex (newline after company name):
                BROOKFIELD INFRASTRUCTURE PARTNERS UNIT LTD PARTNERSHIP
                First in, first out (FIFO)

                So we split on a \n newline to get the company name.
                """
                company_cell = row.find_element_by_css_selector('td:nth-child(2)')
                company_name = company_cell.text.partition('\n')[0]

                # populate total shares
                total_shares_cell = row.find_element_by_css_selector('td:nth-child(3)')
                total_shares = total_shares_cell.text

                stock_ticker = dict(
                    ticker=ticker,
                    company_name=company_name,
                    total_shares=total_shares
                )

                self.writer.set_ticker(account_name, stock_ticker)

                # Populate stock lots
                try:
                    # Lots are shown in the tr adjacent to the Ticker (current) tr
                    lots_row = row.find_element_by_xpath('./following-sibling::tr')

                    lots_container = lots_row.find_element_by_css_selector('.vg-Navbox.vg-NavboxClosed')
                    lots_container_id = lots_container.get_attribute('id')

                    # This is the clickable "Show details" link that, when clicked, will load the stock
                    # lots into the DOM.
                    show_details_element = lots_row.find_element_by_xpath('.//label[contains(.,"Show details")]')

                    # Move to the "Show details" element and click it
                    actions = ActionChains(self.driver)
                    actions.move_to_element(show_details_element)
                    actions.perform()
                    show_details_element.click()

                    # Wait for the lots to be loaded into the DOM
                    css_path_lots_table = f"[id='{lots_container_id}'] .vg-NavboxBody .dataTable"
                    # TODO handle selenium.common.exceptions.TimeoutException
                    lots_table = self.wait.until(
                        lambda x: x.find_element_by_css_selector(css_path_lots_table)
                    )

                    # parse lots
                    lots_table_rows = lots_table.find_elements_by_tag_name('tr')
                    for lots_table_row in lots_table_rows:
                        date_acquired = lots_table_row.find_element_by_css_selector('td:nth-child(1)').text
                        logger.debug(f"date_acquired:{date_acquired}")

                        # The table has a header (most cases).
                        if date_acquired == 'Date acquired (noncovered shares)':
                            # Discard this row since it doesn't contain cost-basis data.
                            continue

                        """
                        The table does not have a header.
                        
                        This appears to be the case for Mutual Funds only, but may have something to do 
                        with "Noncovered shares" rather than Mutual Funds vs. other securities, since that is what is 
                        actually checked for the edge case.
                              
                        The page popup says:
                              
                            Noncovered shares include shares acquired before the effective date for cost basis 
                            reporting requirements or shares acquired in an account that isn't subject to Form 1099-B 
                            reporting, such as an IRA or C-corporation account. In these cases, Vanguard doesn't 
                            report cost basis information to the IRS.
                              
                        TLDR; Noncovered shares don't have a date_acquired value. This makes sense from a cost-basis 
                        perspective but the schema must still be satisfied with a date.
                        """
                        if date_acquired == 'Noncovered shares':
                            """
                            Use today's date to satisfy the schema, although this is not technically accurate as
                            stated above.
                            
                            Use Vanguard native date format, since conversion to the schema format happens below.
                            """
                            date_acquired = datetime.today().strftime(date_foramt)

                        num_shares = lots_table_row.find_element_by_css_selector('td:nth-child(2)').text
                        cost_per_share = lots_table_row.find_element_by_css_selector('td:nth-child(3)').text
                        total_cost = lots_table_row.find_element_by_css_selector('td:nth-child(4)').text

                        # determine short/long term basis
                        short_term = lots_table_row.find_element_by_css_selector('td:nth-child(6)').text
                        logger.debug(f"short_term:{short_term}")
                        long_term = lots_table_row.find_element_by_css_selector('td:nth-child(7)').text
                        logger.debug(f"long_term:{long_term}")

                        if '$' in short_term and '$' in long_term:
                            # this seems to be the case when shares have passed the date for cost-basis reporting;
                            # AKA non-covered shares. See comments above.
                            term = 'long'
                        elif '—' == short_term and '$' in long_term:
                            term = 'long'
                        elif '$' in short_term and '—' == long_term:
                            term = 'short'
                        else:
                            raise ValueError('"term" not found')

                        stock_lot = dict(
                            date_acquired=datetime.strptime(date_acquired, date_foramt).date().strftime('%Y-%m-%d'),
                            num_shares=num_shares,
                            cost_per_share=cost_per_share.replace('$', '').replace(',', '').strip(),
                            total_cost=total_cost.replace('$', '').replace(',', '').strip(),
                            term=term
                        )

                        self.writer.add_cost_basis(account_name, stock_ticker['ticker'], stock_lot)
                        logger.info(f"stock lot {stock_lot}")

                    # Close stock lots by clicking "Show details" again.
                    # NOTE: Closing this seems to help with .click() not working in
                    # certain cases (reasons unknown) on the next iteration.
                    show_details_element.click()
                except NoSuchElementException:
                    logger.warn('NoSuchElementException')
                    raise

    def _write_export(self):
        self.writer.write()
