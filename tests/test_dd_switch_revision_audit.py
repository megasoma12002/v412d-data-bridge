import unittest
from dd_switch_revision_audit import numbered_fields, declared_amounts, revision_snapshot, subscription_identity, statutory_subscription_identity, statutory_dividend_identity, cash_schedule_dates, explicit_date_after, dates, delivery_clauses, stock_issue_bridge, ordinary_cash_amounts, stock_issue_units


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

    def test_transfer_date_is_not_cash_payment_date(self):
        text='111/09/16為現金股利發放日茲因最後過戶日111年8月14日適逢星期例假日'
        self.assertEqual(cash_schedule_dates(text),['2022-09-16'])
        self.assertEqual(explicit_date_after('99年8月6日為現金股利發放日。二、自99年7月19日停止過戶',['現金股利發放日']),[])

    def test_notice_title_does_not_supply_shareholder_meeting_date(self):
        text='主旨公告盈餘轉增資新股發放日期公告內容本公司於102年6月21日股東會通過。二、增資股發放日期：102年9月13日'
        self.assertEqual(explicit_date_after(text,['新股發放日期','增資股發放日期']),['2013-09-13'])

    def test_preferred_dividend_is_not_ordinary_dividend(self):
        event=dict(code='2881',cash_ex_date='2019-07-04',record_date='2019-07-12',fiscal_year='107年')
        filing=dict(code='2881',title='分派107年度乙種特別股股息',ex_dates=[],record_dates=[],announcement_date='2019-08-06',fiscal_years=['107'],compact_text='分派107年度乙種特別股股息')
        self.assertFalse(statutory_dividend_identity(event,'cash',filing))

    def test_ordinary_conversion_notice_requires_matching_ratio_and_close_date(self):
        event=dict(code='2801',stock_ex_date='2026-08-05',record_date='2026-08-11',stock_dividend='0.25',fiscal_year='114年')
        filing=dict(code='2801',title='增資新股上市暨新股權利證書終止上市',ex_dates=[],record_dates=[],announcement_date='2026-08-27',ordinary_conversion_dates=['2026-09-08'],stock_amount_candidates=['0.25'],fiscal_years=[],compact_text='換發普通股')
        self.assertTrue(statutory_dividend_identity(event,'stock',filing))
        filing['stock_amount_candidates']=['0.7']
        self.assertFalse(statutory_dividend_identity(event,'stock',filing))

    def test_subscription_conversion_is_not_same_fiscal_year_stock_dividend(self):
        event=dict(code='5880',stock_ex_date='2015-08-13',record_date='2015-08-21',stock_dividend='0.6',fiscal_year='103年')
        filing=dict(code='5880',title='103年度現金增資普通股股票上市',ex_dates=[],record_dates=[],announcement_date='2015-04-10',fiscal_years=['103'],compact_text='現金增資，股利權義相同')
        self.assertFalse(statutory_dividend_identity(event,'stock',filing))

    def test_joint_delivery_listing_label(self):
        text='４、增資新股股票發放及上市日期：113年9月13日。５、股票簽證機構'
        self.assertEqual(explicit_date_after(text,['增資新股股票發放及上市日期']),['2024-09-13'])

    def test_voucher_does_not_supply_ordinary_delivery(self):
        text='本次現金增資股款繳納憑證訂於112年5月3日劃撥至認股繳款人指定之帳戶，並於同日上市買賣。'
        self.assertEqual(delivery_clauses(text),([],[]))

    def test_explicit_conversion_and_listing_remain_separate(self):
        text='並訂於103年1月7日(星期二)普通股上市暨股款繳納憑證終止上市。集保公司自動於103年1月7日(星期二)換發為普通股股票。'
        self.assertEqual(delivery_clauses(text),(['2014-01-07'],['2014-01-07']))
        text='並訂於103年1月7日(星期二)普通股上市暨股款繳納憑證終止上市。'
        self.assertEqual(delivery_clauses(text),([],['2014-01-07']))

    def test_issue_amount_matches_without_fiscal_year_label(self):
        event=dict(code='2892',stock_ex_date='2012-08-10',record_date='2012-08-18',stock_dividend='0.6',fiscal_year='101年')
        filing=dict(code='2892',title='盈餘及資本公積轉增資股發放',ex_dates=[],record_dates=[],announcement_date='2012-08-28',stock_payment_dates=['2012-09-21'],stock_amount_candidates=['0.6'],fiscal_years=[],compact_text='每仟股配發60股普通股')
        self.assertTrue(statutory_dividend_identity(event,'stock',filing))
        filing['stock_amount_candidates']=['0.5']
        self.assertFalse(statutory_dividend_identity(event,'stock',filing))

    def test_issue_count_bridge_uses_latest_declaration_and_security_scope(self):
        event=dict(code='2886',stock_ex_date='2012-08-08')
        filing=dict(code='2886',title='盈餘轉增資新股發放',announcement_date='2012-09-01',compact_text='公告內容每股面額10元，發行新股100股')
        old=dict(id='original',reported_at='2012-06-01',fields={'發放股利種類及金額':'股票股利新台幣900元'})
        revised=dict(id='revised',reported_at='2012-06-02',fields={'發放股利種類及金額':'股票股利新台幣1000元'})
        self.assertEqual(stock_issue_bridge(event,filing,[old,revised]),['revised'])
        self.assertEqual(stock_issue_bridge(event,filing,[old]),[])
        self.assertEqual(stock_issue_bridge(event,dict(filing,title='現金增資新股發放'),[revised]),[])
        self.assertEqual(stock_issue_bridge(event,dict(filing,title='合併換股'),[revised]),[])
        self.assertEqual(stock_issue_bridge(event,dict(filing,announcement_date='2013-09-01'),[revised]),[])
        self.assertEqual(stock_issue_units('增資後資本額1000元，發行股份總數100股'),set())

    def test_mixed_preferred_notice_requires_ordinary_rate(self):
        event=dict(code='2881',cash_ex_date='2016-07-01',record_date='2016-07-09',fiscal_year='104年',cash_dividend='2')
        filing=dict(code='2881',title='普通股及甲種特別股股息',ex_dates=['2016-07-01'],record_dates=[],announcement_date='2016-06-10',fiscal_years=[],compact_text='普通股現金股利每股配發2元，甲種特別股每股配發6元')
        self.assertEqual(ordinary_cash_amounts(filing['compact_text']),['2'])
        self.assertTrue(statutory_dividend_identity(event,'cash',filing))
        self.assertFalse(statutory_dividend_identity(dict(event,cash_dividend='6'),'cash',filing))

    def test_corrected_conversion_keeps_each_notice_date(self):
        original='集保自動於101年2月8日將股款繳納憑證轉換為普通股股票。'
        revised='集保自動於101年2月10日將股款繳納憑證轉換為普通股股票。'
        self.assertEqual(delivery_clauses('本次增資之普通股股票訂於民國100年9月21日(星期三)正式上市買賣，原100年9月16日發行之新股權利證書終止上市。'),([],['2011-09-21']))
        self.assertEqual(delivery_clauses(original),(['2012-02-08'],[]))
        self.assertEqual(delivery_clauses(revised),(['2012-02-10'],[]))

    def test_date_before_cash_distribution_is_scoped_to_distribution(self):
        text='本公司預訂103年7月30日發放現金股利。最後過戶日103年6月24日。'
        self.assertEqual(cash_schedule_dates(text),['2014-07-30'])
        self.assertEqual(cash_schedule_dates('訂於103年6月24日辦理股票過戶，現金股利另行通知。'),[])

    def test_sinopac_cash_record_date_and_preferred_rate_are_separate(self):
        event=dict(code='2890',cash_ex_date='2012-07-10',record_date='2012-07-16',fiscal_year='100年',cash_dividend='0.13547466')
        filing=dict(code='2890',title='發放一○一年現金股利',ex_dates=[],record_dates=['2012-07-16'],announcement_date='2012-07-23',fiscal_years=[],compact_text='普通股每股分派新台幣0.13547466元；甲種特別股每股約0.10850792元')
        self.assertTrue(statutory_dividend_identity(event,'cash',filing))
        self.assertEqual(ordinary_cash_amounts(filing['compact_text']),['0.13547466'])

    def test_named_preferred_share_direct_credit_is_delivery(self):
        text='本次增資之記名式甲種特別股，訂於105年05月31日(星期二)直接劃撥至股東之證券存摺帳戶，並於同日上市買賣。'
        self.assertEqual(delivery_clauses(text),(['2016-05-31'],['2016-05-31']))


if __name__=='__main__':unittest.main()
