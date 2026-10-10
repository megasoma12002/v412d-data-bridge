import unittest
from dd_switch_resumed_delivery_review import secondary_hn_schedule


class SecondaryLeadTests(unittest.TestCase):
    def setUp(self):
        self.event = dict(code='2880', fiscal_year='101年', stock_ex_date='2013-08-15',
                          stock_payment_date='2013-09-16', stock_dividend='0.5')
        self.text = ('華南金:本公司102年增資股票配發暨上市日期公告'
                     '提撥101年度盈餘原已上市股票:普通股8,625,030,143股'
                     '本次增資上市股票:普通股431,251,507股'
                     '預定增資新股股票發放及上市日期:102年9月16日'
                     '本次增資股票採無實體發行於股票發放當日直接撥入貴股東之集保帳戶')

    def test_general_delivery_is_only_a_secondary_lead(self):
        result = secondary_hn_schedule(self.text, self.event)
        self.assertEqual(result['candidate_general_delivery_date'], '2013-09-16')
        self.assertTrue(result['allocation_amount_matches'])
        self.assertFalse(result['primary_delivery_certified'])
        self.assertFalse(result['gap_closed'])

    def test_wrong_allocation_rejected(self):
        self.assertIsNone(secondary_hn_schedule(self.text, dict(self.event, stock_dividend='0.4')))

    def test_wrong_fiscal_year_rejected(self):
        self.assertIsNone(secondary_hn_schedule(self.text, dict(self.event, fiscal_year='100年')))

    def test_wrong_issuer_rejected(self):
        self.assertIsNone(secondary_hn_schedule(self.text, dict(self.event, code='2886')))

    def test_listing_without_delivery_rejected(self):
        self.assertIsNone(secondary_hn_schedule(self.text.replace('股票發放及上市日期', '上市日期'), self.event))

    def test_holder_specific_delivery_rejected(self):
        self.assertIsNone(secondary_hn_schedule(self.text.replace('貴股東', '教育部'), self.event))

    def test_rights_stage_rejected(self):
        self.assertIsNone(secondary_hn_schedule(self.text.replace('本次增資股票採', '權利證書本次增資股票採'), self.event))
