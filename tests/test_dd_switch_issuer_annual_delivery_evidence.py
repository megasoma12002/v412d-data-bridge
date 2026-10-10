import unittest
from dd_switch_issuer_annual_delivery_evidence import parse_tbb
class AnnualDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.event=dict(code='2834',fiscal_year='100年',stock_dividend='0.4')
        self.pages=['股票代號：2834 臺灣中小企業銀行 發放100年度股票股利每股0.4元',
                    '為配合100年度盈餘分配 於101年8月27日撥交股票予股東及新股上市買賣']
    def test_completed_general_delivery(self):
        r=parse_tbb(self.pages,self.event)
        self.assertEqual(r['payment_date'],'2012-08-27')
        self.assertFalse(r['publication_vintage_certified'])
    def test_wrong_issuer(self):
        self.assertIsNone(parse_tbb([self.pages[0].replace('2834','2880'),self.pages[1]],self.event))
    def test_wrong_rate(self):
        self.assertIsNone(parse_tbb(self.pages,dict(self.event,stock_dividend='0.5')))
    def test_wrong_fiscal_year(self):
        self.assertIsNone(parse_tbb(self.pages,dict(self.event,fiscal_year='99年')))
    def test_listing_only(self):
        self.assertIsNone(parse_tbb([self.pages[0],self.pages[1].replace('撥交股票予股東及','')],self.event))
    def test_holder_only(self):
        self.assertIsNone(parse_tbb([self.pages[0],self.pages[1].replace('予股東','予財政部')],self.event))
    def test_proposed_rate(self):
        self.assertIsNone(parse_tbb([self.pages[0].replace('發放100','擬議100'),self.pages[1]],self.event))
    def test_wrong_execution_year(self):
        self.assertIsNone(parse_tbb([self.pages[0],self.pages[1].replace('101年','102年')],self.event))
    def test_verified_official_index_binds_scanned_cover(self):
        pages=[self.pages[0].replace('股票代號：2834','www.tbb.com.tw'), self.pages[1]]
        self.assertIsNone(parse_tbb(pages,self.event))
        self.assertEqual(parse_tbb(pages,self.event,official_index_verified=True)['payment_date'],'2012-08-27')
    def test_previous_year_rate(self):
        pages=[self.pages[0].replace('發放100','發放前(100)'),self.pages[1]]
        self.assertEqual(parse_tbb(pages,self.event)['payment_date'],'2012-08-27')
    def test_explicit_other_code_rejected_with_index(self):
        pages=[self.pages[0].replace('2834','2880')+' www.tbb.com.tw',self.pages[1]]
        self.assertIsNone(parse_tbb(pages,self.event,official_index_verified=True))
