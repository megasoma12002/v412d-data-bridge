import unittest
from dd_switch_revision_audit import numbered_fields, declared_amounts, revision_snapshot, subscription_identity, statutory_subscription_identity, dates


class RevisionAuditTests(unittest.TestCase):
    def test_nested_subscription_subitems_do_not_truncate_window(self):
        text='說明\n1.董事會決議日期:112/3/20\n16.股款繳納期間:\n1.原股東繳納：112年4月19日起至112年4月24日止。\n2.特定人繳納：112/4/25至112/4/26\n17.與代收銀行訂約日期:112/3/28\n以上資料'
        fields=numbered_fields(text)
        self.assertEqual(dates(fields['股款繳納期間'])[:2],['2023-04-19','2023-04-24'])
        self.assertIn('與代收銀行訂約日期',fields)

    def test_cash_capital_reserve_and_stock_components_do_not_double_count_total(self):
        fields={'股東配發內容':'(1)盈餘分配之現金股利(元/股)：4.62950000(2)法定盈餘公積、資本公積發放之現金(元/股)：0.72050000(3)股東配發之現金(股利)總金額(元)：41502339016(4)盈餘轉增資配股(元/股)：0.3(5)法定盈餘公積、資本公積轉增資配股(元/股)：0.2'}
        values=declared_amounts(fields)
        self.assertEqual(values['cash'],'5.35000000')
        self.assertEqual(values['stock'],'0.5')

    def test_ambiguous_prose_amount_remains_missing(self):
        self.assertEqual(declared_amounts({'發放股利種類及金額':'每股4.5元及每股0.5元現金'})['cash'],'')

    def test_date_only_notice_not_backdated_to_request_record_date_or_close(self):
        row=dict(event_id='2880:stock:2010-08-12',id='statutory',announcement_date='2010-09-01',request_record_date='20100831',stock_payment_dates=['2010-09-15'],ex_dates=[])
        self.assertEqual(revision_snapshot([row],'2010-09-01T13:30:00+08:00'),[])
        result=revision_snapshot([row],'2010-09-02T00:00:00+08:00')[0]
        self.assertEqual(result['payment_date'],'2010-09-15')
        self.assertFalse(result['publication_vintage_certified'])

    def test_future_revision_does_not_change_old_prefix(self):
        base=dict(event_id='3045:cash:2025-07-09',id='a',reported_at='2025-06-02T15:30:43+08:00',declared_cash_amount='4.5',amount_stage='CONDITIONAL_DECLARATION',cash_payment_dates=['2025-07-31'],ex_dates=['2025-07-09'])
        later=dict(base,id='b',reported_at='2025-06-24T16:39:46+08:00',declared_cash_amount='4.6',amount_stage='DECLARATION_UNCERTIFIED')
        old=revision_snapshot([base],'2025-06-02T16:00:00+08:00')
        self.assertEqual(revision_snapshot([base,later],'2025-06-02T16:00:00+08:00'),old)
        self.assertNotIn('amount',old[0]);self.assertEqual(old[0]['estimated_amount'],'4.5')
        self.assertEqual(revision_snapshot([base,later],'2025-06-24T17:00:00+08:00')[0]['amount'],'4.6')

    def test_subscription_ratio_does_not_link_a_different_year_or_subsidiary(self):
        action=dict(code='2884',record_date='2023-04-15',ex_date='2023-04-07',shares_per_1000='30')
        filing=dict(code='2884',record_dates=[],reported_at='2022-01-01T12:00:00+08:00',ratios_per_1000=['30'],issuer_subject=True)
        self.assertFalse(subscription_identity(action,filing))
        filing.update(reported_at='2023-03-20T14:00:00+08:00',issuer_subject=False)
        self.assertFalse(subscription_identity(action,filing))

    def test_preferred_delivery_does_not_turn_into_ordinary_delivery(self):
        action=dict(code='2881',record_date='2016-03-30',ex_date='2016-03-24',issued_security_class='PREFERRED_A',subscription_shares='800000000')
        filing=dict(code='2881',record_dates=[],ex_dates=[],announcement_date='2016-05-26',compact_text='發行普通股800000000股',issued_share_count_candidates=['800000000'])
        self.assertFalse(statutory_subscription_identity(action,filing))
        filing['compact_text']='發行甲種特別股800000000股'
        self.assertTrue(statutory_subscription_identity(action,filing))


if __name__=='__main__':unittest.main()
