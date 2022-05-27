from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from funance.scrape.export import BrokerageWriter


class Vanguard:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.writer = BrokerageWriter('vanguard')

    def wait_for_login(self):
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

        print(f"[DEBUG] Logged On: {is_authenticated}")

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

    def get_cost_basis(self):
        self.driver.get('https://personal.vanguard.com/us/XHTML/com/vanguard/costbasisnew/xhtml/CostBasisSummary.xhtml')
        self._wait_for_cost_basis_tables()

        account_tables = self.driver.find_elements_by_xpath('//table[contains(@class, "dataTable")]')
        for account_table in account_tables:
            # print(f"Account table: [id='{account_table.get_attribute('id')}']")
            # account name
            account_name_element = account_table.find_element_by_tag_name('h1')
            account_name = account_name_element.text
            print(f"[INFO] Getting cost basis for account: {account_name}")

            acct = dict(account_name=account_name, cash='', cost_basis=[])

            # get all rows that have a .linkBarWrapper
            rows = account_table.find_elements_by_tag_name('tr')
            for row in rows:
                try:
                    # Check if this row has a Buy link. This row has our ticker data.
                    row.find_element_by_link_text('Buy')
                except NoSuchElementException:
                    # we don't care about this row
                    continue

                # ticker
                ticker_cell = row.find_element_by_css_selector('td:nth-child(1)')
                ticker = ticker_cell.text
                print(f"[INFO] Getting cost basis for ticker: {ticker}")
                # print(f"Ticker row: [id='{account_table.get_attribute('id')}'] tr[index='{row.get_attribute('index')}']")

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
                    total_shares=total_shares,
                    lots=[]
                )

                # Populate stock lots
                # TODO This is not finding stock lots for tickers under Mutual funds.
                try:
                    # Lots are shown in the tr adjacent to the Ticker (current) tr
                    lots_row = row.find_element_by_xpath('./following-sibling::tr')

                    lots_container = lots_row.find_element_by_css_selector('.vg-Navbox.vg-NavboxClosed')
                    lots_container_id = lots_container.get_attribute('id')
                    # print(f"Lots container: [id='{lots_container_id}']")

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
                    # print(f"Lots table: {css_path_lots_table}")
                    # TODO handle selenium.common.exceptions.TimeoutException
                    lots_table = self.wait.until(
                        lambda x: x.find_element_by_css_selector(css_path_lots_table)
                    )

                    # parse lots
                    lots_table_rows = lots_table.find_elements_by_tag_name('tr')
                    # skip the first row as it is a header and does not have cost-basis data
                    lots_table_rows.pop(0)
                    for lots_table_row in lots_table_rows:
                        date_acquired = lots_table_row.find_element_by_css_selector('td:nth-child(1)').text
                        num_shares = lots_table_row.find_element_by_css_selector('td:nth-child(2)').text
                        cost_per_share = lots_table_row.find_element_by_css_selector('td:nth-child(3)').text
                        total_cost = lots_table_row.find_element_by_css_selector('td:nth-child(4)').text

                        stock_lot = dict(
                            date_acquired=date_acquired,
                            num_shares=num_shares,
                            cost_per_share=cost_per_share.replace('$', '').replace(',', '').strip(),
                            total_cost=total_cost.replace('$', '').replace(',', '').strip()
                        )

                        stock_ticker['lots'].append(stock_lot)

                    # Close stock lots by clicking "Show details" again.
                    # NOTE: Closing this seems to help with .click() not working in
                    # certain cases (reasons unknown) on the next iteration.
                    show_details_element.click()

                    acct['cost_basis'].append(stock_ticker)

                    self.writer.add_account(acct)

                except NoSuchElementException:
                    print('[DEBUG] NoSuchElementException')
                    raise

    def write_export(self):
        self.writer.write()
