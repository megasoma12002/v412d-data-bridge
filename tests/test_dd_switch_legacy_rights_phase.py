import unittest
from dd_switch_legacy_rights_phase import parse_phase


class LegacyPhaseTests(unittest.TestCase):
    def setUp(self):
        self.event = dict(code='2886', stock_ex_date='2012-08-08', stock_payment_date='2012-09-13', stock_dividend='0.15')
        self.text = ('公司代號2886本公司101年增資股票發放及上市日期公告'
                     '原已上市普通股股票:11,280,614,762股本次增資上市普通股股票:169,209,221股'
                     '普通股股票訂於民國101年9月13日(星期四)正式上市買賣，'
                     '原101年9月6日(星期四)發行之新股權利證書亦同時終止上市')

    def test_explicit_stages_are_not_general_delivery_certification(self):
        r = parse_phase(self.text, self.event)
        self.assertEqual((r['rights_issue_date'], r['ordinary_listing_date']), ('2012-09-06','2012-09-13'))
        self.assertFalse(r['general_ordinary_delivery_certified'])
        self.assertFalse(r['gap_closed'])

    def test_wrong_allocation_rejected(self):
        with self.assertRaises(ValueError): parse_phase(self.text, dict(self.event,stock_dividend='0.2'))

    def test_listing_only_rejected(self):
        with self.assertRaises(ValueError): parse_phase(self.text.split('，')[0], self.event)

    def test_wrong_issuer_and_reversed_stage_rejected(self):
        with self.assertRaises(ValueError): parse_phase(self.text,dict(self.event,code='2880'))
        with self.assertRaises(ValueError): parse_phase(self.text.replace('9月6日','9月20日'),self.event)
