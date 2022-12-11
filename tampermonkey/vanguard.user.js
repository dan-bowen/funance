// ==UserScript==
// @name         Funance: Vanguard Holdings
// @namespace    https://www.danbuilds.us
// @version      0.1
// @description  Download holdings from your Vanguard account.
// @author       Dan Bowen
// @match        https://holdings.web.vanguard.com/
// @grant        none
// @require      https://code.jquery.com/jquery-3.6.1.slim.min.js
// ==/UserScript==

// downloaded filename
const FILENAME = 'holdings.vanguard.csv'
// download link that will be added to the page
const DOWNLOAD_LINK = '<a id="funance-download-holdings">Download Holdings</a>'
// element to wait for before starting the script
const HOLDINGS_SELECTOR = "app-holdings-table:eq(1)"
// download link is added here
const SECONDARY_NAV_SELECTOR = "div.secondary-nav"
// holds each individual account
const ACCOUNTS_SELECTOR = "span[data-testid^=account-id]"
// holds title of the account
const ACCOUNT_TITLE_SELECTOR = "h2:eq(0) span[class$=__heading]"
// holds settlement fund account balance
const X_CASH_SELECTOR = "app-settlement-fund div.settlement-fund-info:eq(2) span.settlement-fund-value"
// holds account holdings
const ACCOUNT_HOLDINGS_SELECTOR = "table.holdings-table";
// holds account holdings groups
const ACCOUNT_HOLDINGS_GROUPS_SELECTOR = "tbody[app-holdings-table-body-grouping]"

    ; (function () {
        'use strict';
        // When the page loads
        $(document).ready(function () {
            // wait until the main holdings are loaded
            waitForEl(HOLDINGS_SELECTOR, onInitHoldingsLoaded)
        })
    })()

// Callback when HOLDINGS_SELECTOR is loaded
function onInitHoldingsLoaded(holdingsEl) {
    const $secondaryNav = $(SECONDARY_NAV_SELECTOR)
    const $downloadLink = $(DOWNLOAD_LINK)
    const holdings = getHoldings()
    console.log(holdings)
    const csvContent = createCsv(holdings)

    // assemble download link
    $downloadLink
        //.attr('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent))
        .attr('href', URL.createObjectURL(new Blob([csvContent], { type: 'text/csv;charset=utf-8,' })))
        .attr('download', FILENAME)
        .appendTo($secondaryNav.find('nav'))
}

/**
 * Get holdings from the DOM
 * 
 * @returns Array
 */
function getHoldings() {
    const $holdingsContainer = $(HOLDINGS_SELECTOR)
    const $accountContainers = $holdingsContainer.find(ACCOUNTS_SELECTOR)

    // process each account
    const allHoldings = $accountContainers.map(function () {
        const $acctEl = $(this)
        const $heading = $acctEl.find(ACCOUNT_TITLE_SELECTOR)
        const accountName = $heading[0].textContent
        const $holdingsTable = $acctEl.find(ACCOUNT_HOLDINGS_SELECTOR)
        const $holdingsGroups = $holdingsTable.find(ACCOUNT_HOLDINGS_GROUPS_SELECTOR)
        const cashBalance = $acctEl.find(X_CASH_SELECTOR)[0].textContent
        const X_CASH = createHolding(accountName, 'X_CASH', sanitizeDollarAmount(cashBalance))

        // process each group (ETFs, Stocks, etc.)
        const groups = $holdingsGroups.map(function () {
            const $groupEl = $(this)

            // all rows in group
            const $allRows = $groupEl.find('tr')
            const rows = $allRows.map(function () {
                const $row = $(this)
                const $tds = $row.find('td')

                // check if the first cell has ticker data
                const $tickerCell = $tds.eq(0).find('app-holdings-ticker')
                if ($tickerCell.length !== 1) {
                    console.log('not a ticker row. Skipping...')
                    return null
                }

                // symbol + company name
                const symbol = $tickerCell.find('span.holding_ticker')[0].textContent
                const company = $tickerCell.find('span.holding_name')[0].textContent

                // quantity
                const quantity = $tds[4].textContent

                // holding
                const holding = createHolding(accountName, symbol, quantity)

                return holding
            });

            return rows.get()
        });

        const accountHoldings = groups.get()
        // push cash onto holdings
        accountHoldings.push(X_CASH)

        return accountHoldings
    });

    return allHoldings.get()
}

/**
 * Create CSV string from holdings array
 * 
 * @param {Array} holdings 
 * @returns 
 */
function createCsv(holdings) {
    // get keys from first object
    const csvKeys = Object.keys(holdings[0])
    const csvData = []
    let csvContent = ''

    // push keys as first row
    csvData.push(csvKeys);

    // push holdings
    holdings.forEach(item => {
        csvData.push(Object.values(item))
    });

    // assemble csv string
    csvData.forEach(row => {
        csvContent += '"' + row.join('","') + '"\n'
    })

    return csvContent
}

/**
 * Create a holding object
 * 
 * @param {string} account 
 * @param {string} symbol 
 * @param {string} quantity 
 * @returns 
 */
function createHolding(account, symbol, quantity) {
    return {
        'account': sanitizeAccountName(account),
        'symbol': sanitizeSymbol(symbol),
        'quantity': sanitizeQuantity(quantity)
    };
}

/**
 * Round
 * 
 * @param {int|float} num 
 * @returns 
 */
function round(num) {
    return Math.round(num * 100) / 100
}

/**
 * Sanitize account name
 * 
 * @param {string} text 
 * @returns string
 */
function sanitizeAccountName(text) {
    // regex to replace non-alphanumeric characters with whitespace
    // @see https://stackoverflow.com/questions/20864893/replace-all-non-alphanumeric-characters-new-lines-and-multiple-white-space-wit
    const nonAlpha = /\W+/g;
    return text.replace(nonAlpha, ' ')
        .trim()
}

/**
 * Sanitize symbol
 * 
 * @param {string} text 
 * @returns string
 */
function sanitizeSymbol(text) {
    return text.trim()
}

/**
 * Sanitize quantity
 * 
 * @param {string} text 
 * @returns string
 */
function sanitizeQuantity(text) {
    return text.replace(",", "").trim()
}

/**
 * Sanitize dollar amount
 * 
 * @param {string} text 
 * @returns string
 */
function sanitizeDollarAmount(text) {
    return text.replace("$", "").replace(",", "").trim()
}

/**
 * Wait for the specified element to appear in the DOM. When the element appears,
 * provide it to the callback.
 *
 * @param selector a jQuery selector (eg, 'div.container img')
 * @param callback function that takes selected element (null if timeout)
 * @param maxtries number of times to try (return null after maxtries, false to disable, if 0 will still try once)
 * @param interval ms wait between each try
 */
function waitForEl(selector, callback, maxtries = false, interval = 100) {
    const poller = setInterval(() => {
        const $el = $(selector)
        const retry = maxtries === false || maxtries-- > 0
        if (retry && $el.length < 1) return // will try again
        clearInterval(poller)
        callback($el || null)
    }, interval)
}
