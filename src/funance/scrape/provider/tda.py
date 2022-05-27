import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException, NoSuchWindowException
from funance.scrape.export import BrokerageWriter


class Tda:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.writer = BrokerageWriter('tda')

    def wait_for_login(self):
        self.driver.get('https://invest.ameritrade.com/')
        # Wait for the account switcher to appear. This is the hint that the user has logged in
        try:
            is_authenticated = True
            account_switcher = WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.ID, 'accountSwitcherContainer'))
            )
        except TimeoutException:
            is_authenticated = False

        print(f"[DEBUG] Logged On: {is_authenticated}")

    def _switch_account(self, account_name):
        account_switcher_select = self.driver.find_element_by_id('accountSwitcherSelectBox')
        actions = ActionChains(self.driver)
        actions.move_to_element(account_switcher_select)
        actions.click(account_switcher_select)
        actions.perform()

        # there is no unique identifier to get only trs with accounts, so we grab them all and slice the list
        account_switcher_trs = self.driver.find_elements_by_css_selector('#accountSwitcherSelect_menu tr')
        """
        Slice away unneeded trs
        
        - Select Account    Throw away
        - Account 1         Keep
        - Account 2         Keep
        - Account N         Keep
        - Separator         Throw away
        - Link Accounts     Throw away
        - Edit Nickname     Throw away
        """
        account_switcher_trs = account_switcher_trs[1:len(account_switcher_trs)-3]
        for tr in account_switcher_trs:
            account_nickname_cell = tr.find_element_by_css_selector('td.dijitMenuItemLabel span.accountNickname')
            account_nickname = account_nickname_cell.text
            if account_name == account_nickname:
                actions = ActionChains(self.driver)
                actions.move_to_element(tr)
                actions.click(tr)
                actions.perform()
                break

    def _get_account_switcher_data(self):
        account_switcher_select = self.driver.find_element_by_id('accountSwitcherSelectBox')
        dojo_props = account_switcher_select.get_attribute('data-dojo-props')
        # print(dojo_props)
        """
        This data structure is almost JSON. With a little string manipulation this becomes JSON 
        and a useful data structure.
        
         uuid:"***REMOVED***",
        savedNavId: "portfolioGain",
        link_account_url: "/grid/p/site#r=linkAccounts",
        editNickNameUrl:"/grid/p/site#r=jPage/cgi-bin/apps/u/AccountManagement",
        selected_account: "***REMOVED***",
        accountsMap: {
        "***REMOVED***": "Brokerage",
        "***REMOVED***": "***REMOVED***",
        isChanged : "yes",
        active: "***REMOVED***"
        },
        fromModule: "",
        tradePermissionChanged: false
        """

        dojo_props = '{' + dojo_props.strip() + '}'
        dojo_props = dojo_props.replace('uuid:', '"uuid":')
        # this property isn't always present
        dojo_props = dojo_props.replace('savedNavId:', '"savedNavId":')
        dojo_props = dojo_props.replace('link_account_url:', '"link_account_url":')
        dojo_props = dojo_props.replace('editNickNameUrl:', '"editNickNameUrl":')
        dojo_props = dojo_props.replace('selected_account:', '"selected_account":')
        dojo_props = dojo_props.replace('accountsMap:', '"accountsMap":')
        dojo_props = dojo_props.replace('isChanged :', '"isChanged":')
        dojo_props = dojo_props.replace('active:', '"active":')
        dojo_props = dojo_props.replace('fromModule:', '"fromModule":')
        dojo_props = dojo_props.replace('tradePermissionChanged:', '"tradePermissionChanged":')
        dojo_json = json.loads(dojo_props)
        # print(f'[DEBUG] Dojo JSON: {dojo_json}')

        accounts_map = dojo_json['accountsMap']
        active_account_id = accounts_map['active']
        my_accounts = []
        for key in accounts_map:
            if key.isdigit():
                account_id = key
                account_name = accounts_map[account_id]
                my_accounts.append(dict(
                    account_id=account_id,
                    account_name=account_name,
                    is_active=active_account_id == account_id
                ))
        print(f'[DEBUG] All Accounts: {my_accounts}')
        return my_accounts

    def _get_current_account(self):
        accounts = self._get_account_switcher_data()
        current_account = None
        for account in accounts:
            if account['is_active']:
                current_account = account
                break
        print(f"[INFO] Current Account: {current_account['account_name']}")
        return current_account

    def _visit_stock_lots(self):
        # Move to "My Account" element and click it
        my_account_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, 'My Account'))
        )
        actions = ActionChains(self.driver)
        actions.move_to_element(my_account_link)
        actions.click(my_account_link)
        actions.perform()

        # Move to "Cost Basis" link and click it
        cost_basis_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, 'Cost Basis'))
        )
        actions = ActionChains(self.driver)
        actions.move_to_element(cost_basis_link)
        actions.click(cost_basis_link)
        actions.perform()

    def get_cost_basis(self):
        self._visit_stock_lots()
        self._get_cost_basis_for_current_account()
        for account in self._get_account_switcher_data():
            # The active account was already scraped above, so skip it in this loop
            if not account['is_active']:
                print(f"[INFO] Switching account: {account['account_name']}")
                self._switch_account(account['account_name'])
                self._get_cost_basis_for_current_account()

    def _switch_to_main_frame(self):
        # Switch to the "main" frame where cost basis tables are located
        main_frame = self.wait.until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, 'main'))
        )
        return main_frame

    def _click_and_wait_for_cost_basis(self):
        # Move to "Cost Basis" link and click it. This assumes the driver has been switched to the "main" frame.
        try:
            # unrealized_link = self.driver.find_element_by_link_text('Unrealized Gain/Loss')
            unrealized_link = self.wait.until(
                EC.presence_of_element_located((By.LINK_TEXT, 'Unrealized Gain/Loss'))
            )
            actions = ActionChains(self.driver)
            actions.move_to_element(unrealized_link)
            actions.click(unrealized_link)
            actions.perform()
        except NoSuchElementException:
            # the clicked tab is no longer a link or clickable since it is the active tab.
            pass

        cost_basis_table = self.wait.until(
            EC.presence_of_element_located((By.XPATH, '//div[@id="sectionL01"]/table'))
        )
        return cost_basis_table

    def _get_cost_basis_for_current_account(self):
        current_account = self._get_current_account()['account_name']
        print(f'[INFO] Getting cost basis for account: {current_account}')

        acct = dict(account_name=current_account, cash='', cost_basis=[])

        # FIXME
        # For an unknown reason NoSuchWindowException is being thrown when selecting an element inside the frame
        # after clicking the tab. Also, the clicked tab is no longer a link or clickable since it is the active tab.
        while True:
            try:
                self.driver.switch_to.default_content()
                self._switch_to_main_frame()
                cost_basis_table = self._click_and_wait_for_cost_basis()
                break
            except NoSuchWindowException:
                print('[DEBUG] NoSuchWindowException while getting cost basis')
                continue

        cost_basis_rows = cost_basis_table.find_elements_by_css_selector('tr.headerrows')
        for row in cost_basis_rows:
            # get summary data from the main row
            ticker = row.find_element_by_css_selector('td.Symbol').text
            company_name = row.find_element_by_css_selector('td.Security').text
            date_acquired = row.find_element_by_css_selector('td.OpenDate').text
            num_shares = row.find_element_by_css_selector('td.Quantity').text
            cost_per_share = row.find_element_by_css_selector('td.AmountPerShare').text
            total_cost = row.find_element_by_css_selector('td.Amount').text
            term = row.find_element_by_css_selector('td.Term').text

            print(f"[INFO] Getting cost basis for ticker: {ticker}")

            ticker_data = dict(
                company_name=company_name,
                ticker=ticker,
                total_shares=num_shares,
                lots=[]
            )

            # if the .showCell column has a link "opener" in it, then there are multiple lots
            try:
                is_single_lot = False
                show_cell_link = row.find_element_by_css_selector('td.showCell a')
            except NoSuchElementException:
                is_single_lot = True

            if is_single_lot:
                single_lot_dict = dict(
                    date_acquired=date_acquired,
                    num_shares=num_shares,
                    cost_per_share=cost_per_share,
                    total_cost=total_cost,
                    # term=term
                )
                ticker_data['lots'].append(single_lot_dict)
            else:
                header_row_id = row.get_attribute('id')
                lots_row_id = header_row_id.replace('SUM_', 'L_')
                lots_rows = self.driver.find_elements_by_css_selector(f"#{lots_row_id} tr")
                for lots_row in lots_rows:
                    # lots rows are hidden so the .text attribute is empty. Use .get_attribute('textContent')
                    # to get text content of hidden elements.
                    date_acquired = lots_row.find_element_by_css_selector('td.OpenDate').get_attribute('textContent')
                    num_shares = lots_row.find_element_by_css_selector('td.Quantity').get_attribute('textContent')
                    cost_per_share = lots_row.find_element_by_css_selector('td.AmountPerShare').get_attribute('textContent')
                    total_cost = lots_row.find_element_by_css_selector('td.Amount').get_attribute('textContent')

                    lots_dict = dict(
                        date_acquired=date_acquired,
                        num_shares=num_shares,
                        cost_per_share=cost_per_share,
                        total_cost=total_cost
                    )
                    ticker_data['lots'].append(lots_dict)
            acct['cost_basis'].append(ticker_data)
        self.writer.add_account(acct)

        # switch driver back to default content
        self.driver.switch_to.default_content()

    def write_export(self):
        self.writer.write()
