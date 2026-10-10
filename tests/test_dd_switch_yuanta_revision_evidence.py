import unittest
from dd_switch_yuanta_revision_evidence import parse_notice, stage_gaps
from dd_switch_revision_audit import revision_snapshot


class YuantaRevisionTests(unittest.TestCase):
    def meta(self, final=False):
        return dict(id='notice-final' if final else 'notice-estimate',
                    title='公告元大台灣卓越50基金' + ('實際配發金額' if final else '收益分配評價結果'),
                    url='https://api.yuantafunds.com/notice.pdf', path='notice.pdf',
                    response_sha256='hash', retrieved_at='2026-10-09T00:00:00+00:00',
                    announcement_date='2021/07/19' if final else '2021/07/06')

    def body(self, final=False, header='交易證券代號：0050'):
        issue = '110年07月19日' if final else '110年07月06日'
        amount = '每受益權單位實際配發金額為新臺幣0.35元' if final else '每受益權單位預估配發金額為新臺幣0.3元'
        return ('元大台灣卓越50證券投資信託基金分配收益公告' + header +
                '中華民國' + issue + '一、主旨：收益分配公告' + amount +
                '除息交易日：110年07月21日。收益分配發放日：110年08月24日。')

    def test_original_final_and_estimate_remain_separate(self):
        estimated = parse_notice(self.body(), self.meta())
        final = parse_notice(self.body(True), self.meta(True))
        self.assertEqual(estimated['declared_cash_amount'], '0.3')
        self.assertEqual(final['declared_cash_amount'], '0.35')
        self.assertEqual(estimated['amount_stage'], 'CONDITIONAL_DECLARATION')
        self.assertEqual(final['cash_payment_dates'], ['2021-08-24'])
        self.assertFalse(final['publication_vintage_certified'])

    def test_pdf_overlay_heading_preserves_exact_security(self):
        header = '交易證券代號交易證券代交易證券名稱：號：0050交易證券名稱：元大台灣50'
        self.assertEqual(parse_notice(self.body(header=header), self.meta())['code'], '0050')

    def test_legacy_pdf_without_code_needs_matching_issuer_index_title(self):
        self.assertEqual(parse_notice(self.body(header=''), self.meta())['code'], '0050')
        meta = self.meta(); meta['title'] = '元大台灣50正2基金收益分配評價結果'
        with self.assertRaises(ValueError):
            parse_notice(self.body(header=''), meta)

    def test_leveraged_security_cannot_use_ordinary_fund_name(self):
        with self.assertRaises(ValueError):
            parse_notice(self.body(header='交易證券代號：00631L'), self.meta())

    def test_missing_final_amount_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_notice(self.body(), self.meta(True))

    def test_schedule_only_estimate_does_not_invent_amount(self):
        text = self.body().replace('每受益權單位預估配發金額為新臺幣0.3元', '')
        self.assertEqual(parse_notice(text, self.meta())['declared_cash_amount'], '')

    def test_ambiguous_payment_dates_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_notice(self.body() + '收益分配發放日：110年08月25日。', self.meta())

    def test_discovery_estimate_cannot_hide_explicit_final_body(self):
        with self.assertRaises(ValueError):
            parse_notice(self.body(True), self.meta())

    def test_final_only_closes_chain_but_keeps_estimate_stage_gap(self):
        final = parse_notice(self.body(True), self.meta(True))
        event = dict(code='0050', cash_dividend='0.35', cash_ex_date='2021-07-21')
        gaps = stage_gaps([final], [event])
        self.assertEqual(gaps[0]['missing_stages'], 'ESTIMATE')
        self.assertEqual(gaps[0]['final_versions'], 1)
        self.assertFalse(gaps[0]['revision_inventory_complete'])

    def test_duplicate_stage_is_ambiguous_not_complete(self):
        estimate = parse_notice(self.body(), self.meta())
        final = parse_notice(self.body(True), self.meta(True))
        event = dict(code='0050', cash_dividend='0.35', cash_ex_date='2021-07-21')
        self.assertEqual(stage_gaps([estimate, final], [event]), [])
        self.assertEqual(stage_gaps([estimate, final, final], [event])[0]['ambiguous_stages'], 'FINAL')

    def test_legacy_signature_and_pdf_date_without_index_clock(self):
        meta = self.meta(True); meta.update(archive_source='SITCA_ISSUER_DISCLOSURE_PDF', announcement_date='')
        text = '元大證券投資信託股份有限公司元投信字第20170950號' + self.body(True, header='')
        row = parse_notice(text, meta)
        self.assertEqual(row['announcement_date'], '2021-07-19')
        self.assertEqual(row['issuer_index_date'], '')
        self.assertEqual(row['availability_precision'], 'DATE_ONLY')
        self.assertEqual(row['document_number'], '20170950')

    def test_legacy_without_issuer_signature_is_rejected(self):
        meta = self.meta(True); meta['archive_source'] = 'SITCA_ISSUER_DISCLOSURE_PDF'
        with self.assertRaises(ValueError):
            parse_notice(self.body(True, header=''), meta)

    def test_baolai_original_header_without_document_number(self):
        meta = self.meta(True)
        meta.update(title='公告寶來台灣卓越50基金實際配發金額', announcement_date='', archive_source='SITCA_LEGACY_BAOLAI_DISCLOSURE_PDF')
        text = ('寶來證券投資信託股份有限公司' + self.body(True, header='')).replace('元大台灣卓越50', '寶來台灣卓越50').replace('110年', '100年')
        row = parse_notice(text, meta)
        self.assertEqual(row['pdf_issue_date'], '2011-07-19')
        self.assertEqual(row['document_number'], '')
        self.assertFalse(row['publication_vintage_certified'])
        with self.assertRaises(ValueError):
            parse_notice(text.replace('100年', '110年'), meta)

    def test_baolai_cannot_accept_modern_or_other_fund_identity(self):
        meta = self.meta(True); meta.update(title='公告寶來台灣卓越50基金實際配發金額', archive_source='SITCA_LEGACY_BAOLAI_DISCLOSURE_PDF')
        with self.assertRaises(ValueError):
            parse_notice(self.body(True), meta)

    def test_old_yuanta_name_requires_observed_archive_and_historical_date(self):
        meta = self.meta(True)
        meta.update(title='公告元大寶來台灣卓越50基金實際配發金額', archive_source='SITCA_ISSUER_DISCLOSURE_PDF', observed_archive_listing_verified=True, announcement_date='2013-07-19')
        text = ('元大寶來證券投資信託股份有限公司元寶投信字第20130950號' + self.body(True, header='')).replace('元大台灣卓越50', '元大寶來台灣卓越50').replace('110年', '102年')
        self.assertEqual(parse_notice(text, meta)['pdf_issue_date'], '2013-07-19')
        with self.assertRaises(ValueError):
            parse_notice(text, dict(meta, observed_archive_listing_verified=False))
        with self.assertRaises(ValueError):
            parse_notice(text.replace('102年', '110年'), meta)

    def test_original_name_parenthesis_does_not_replace_current_issuer_identity(self):
        meta = self.meta(True)
        meta.update(title='公告元大台灣卓越50證券投資信託基金收益評價結果-第二階段', archive_source='SITCA_ISSUER_DISCLOSURE_PDF', observed_archive_listing_verified=True)
        text = '元大證券投資信託股份有限公司元投信字第20210950號' + self.body(True, header='').replace('中華民國', '(原名：元大寶來台灣卓越50證券投資信託基金)中華民國')
        self.assertEqual(parse_notice(text, meta)['stage'], 'FINAL')
        with self.assertRaises(ValueError):
            parse_notice(text.replace('元大證券投資信託股份有限公司', '其他證券投資信託股份有限公司'), meta)

    def test_second_stage_title_still_requires_actual_final_amount(self):
        meta = self.meta(True)
        meta.update(title='公告元大台灣卓越50基金評價结果-第二階段', observed_archive_listing_verified=True)
        with self.assertRaises(ValueError):
            parse_notice(self.body(), meta)

    def test_2012_compatibility_glyphs_without_document_number_are_bounded(self):
        meta = self.meta(True)
        meta.update(title='公告元大寶來台灣卓越50基金實際配發金額', archive_source='SITCA_ISSUER_DISCLOSURE_PDF', observed_archive_listing_verified=True, announcement_date='2012-07-19')
        text = ('元大寶來證券投資信託股份有限公司' + self.body(True, header='')).replace('元大台灣卓越50', '元大寶來台灣卓越50').replace('110年', '101年')
        text = text.replace('來', '來').replace('金', '金').replace('年', '年').replace('益', '益').replace('易', '易')
        self.assertEqual(parse_notice(text, meta)['declared_cash_amount'], '0.35')
        with self.assertRaises(ValueError):
            parse_notice(text.replace('101年', '102年'), meta)

    def test_later_final_does_not_backfill_date_only_prefix(self):
        estimated = dict(parse_notice(self.body(), self.meta()), event_id='0050:cash:2021-07-21')
        final = dict(parse_notice(self.body(True), self.meta(True)), event_id=estimated['event_id'])
        self.assertEqual(revision_snapshot([estimated, final], '2021-07-06T23:59:59+08:00'), [])
        old = revision_snapshot([estimated], '2021-07-19T23:59:59+08:00')
        self.assertEqual(revision_snapshot([estimated, final], '2021-07-19T23:59:59+08:00'), old)
        self.assertEqual(old[0]['estimated_amount'], '0.3')
        self.assertNotIn('amount', old[0])
        self.assertEqual(revision_snapshot([estimated, final], '2021-07-20T00:00:00+08:00')[0]['amount'], '0.35')


if __name__ == '__main__':
    unittest.main()
