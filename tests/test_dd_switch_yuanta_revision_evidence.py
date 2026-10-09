import unittest
from dd_switch_yuanta_revision_evidence import parse_notice
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
