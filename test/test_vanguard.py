import json
import unittest

from funance.scrape.provider.vanguard import clean_account_name


class TestCleanAccountName(unittest.TestCase):
    def test_clean_account_name(self):
        expected = 'Ralph D Malf Traditional IRA Brokerage Account 7777777'
        actual = clean_account_name('Ralph D. Malf—Traditional IRA Brokerage Account—7777777*')
        self.assertEqual(expected, actual)
