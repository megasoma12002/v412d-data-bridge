import unittest
from dd_switch_scoped_delivery_evidence import public_holder_row, late_call_dates
from dd_switch_revision_audit import delivery_clauses


class ScopedDeliveryTests(unittest.TestCase):
    def report(self):
        return ('教育部學產基金中華民國101年度決算\f資金轉投資及其餘絀明細表'
                '華 南 金 控 有限公司原有股數3,257,439股，本年度配發現金股利每股0.5元。'
                '101年9月21日發放股票股利162,871股。臺新金控有限公司')

    def ledger(self):
        return [dict(code='2880', stock_ex_date='2012-08-15', stock_payment_date='2012-09-21',
                     cash_dividend='0.5', stock_dividend='0.5')]

    def meta(self):
        return dict(id='moe', url='https://ws.moe.edu.tw/report.pdf', path='report.pdf', response_sha256='hash')

    def test_public_receiver_report_remains_scoped(self):
        row = public_holder_row(self.report(), self.meta(), self.ledger())
        self.assertEqual(row['reported_distribution_shares'], 162871)
        self.assertTrue(row['ledger_date_corroborated'])
        self.assertEqual(row['holder_scope'], 'MOE_SCHOOL_ASSET_FUND')
        self.assertFalse(row['issuer_general_schedule_certified'])
        self.assertFalse(row['model_holder_credit_certified'])
        self.assertFalse(row['publication_vintage_certified'])

    def test_recipient_date_does_not_drive_event_identity(self):
        ledger = self.ledger(); ledger[0]['stock_payment_date'] = '2012-09-22'
        row = public_holder_row(self.report(), self.meta(), ledger)
        self.assertEqual(row['event_id'], '2880:stock:2012-08-15')
        self.assertFalse(row['ledger_date_corroborated'])

    def test_wrong_allocation_cannot_attach_same_year(self):
        ledger = self.ledger(); ledger[0]['stock_dividend'] = '0.6'
        with self.assertRaises(ValueError):
            public_holder_row(self.report(), self.meta(), ledger)

    def test_late_call_date_does_not_become_general_delivery(self):
        text = '本次現金增資股份已於112年5月3日以股款繳納憑證劃撥。另於催繳期間繳款之股東，本公司將於催繳期間屆滿後，於112年6月1日將所認購之股數，撥入指定之集保帳戶。'
        self.assertEqual(late_call_dates(text), ['2023-06-01'])
        self.assertEqual(delivery_clauses(text)[0], [])

    def test_undated_account_correction_does_not_gain_credit_date(self):
        self.assertEqual(late_call_dates('本公司112年6月1日上市。帳號錯誤之股東請辦理劃撥。'), [])


if __name__ == '__main__':
    unittest.main()
