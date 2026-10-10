import unittest
import pandas as pd
from dd_switch_pit_features import features_at, schedule_snapshot


class PointInTimeFeatureTests(unittest.TestCase):
    def setUp(self):
        self.cal = pd.bdate_range('2026-05-01', '2026-06-30')
        self.market = pd.DataFrame([dict(date=d, code='2880', high=20., low=10., close=10.1) for d in self.cal])
        self.row = dict(event_id='allocation-A', code='2880', leg='cash',
                        reported_at='2026-05-01T10:00:00+08:00', ex_date='2026-06-15')
        self.params = dict(k_thresh=25., season_start=(5,15), season_end=(6,10), pre_days=10, active_score=1.5)

    def result(self, versions=None, market=None, cutoff='2026-05-20T13:30:00+08:00'):
        return features_at(self.market if market is None else market,
                           [self.row] if versions is None else versions, self.cal, ['2880'], cutoff, self.params)

    def test_future_quotes_and_versions_cannot_change_prior_decision(self):
        changed = self.market.copy(); changed.loc[changed.date > '2026-05-20', ['high','low','close']] = 9999.
        future = dict(self.row, reported_at='2026-05-21T10:00:00+08:00', ex_date='2026-05-25')
        self.assertEqual(self.result(), self.result([self.row, future], changed))

    def test_known_future_ex_date_keeps_season_signal(self):
        self.assertEqual(self.result()['kd']['2880'], 1.5)

    def test_unpublished_event_does_not_activate_signal(self):
        self.assertEqual(self.result([dict(self.row, reported_at='2026-05-21T10:00:00+08:00')])['kd']['2880'], 0.)

    def test_pre_ex_mask_uses_calendar_without_future_prices(self):
        self.assertFalse(self.result(cutoff='2026-06-05T13:30:00+08:00')['buy_ok']['2880'])

    def test_revision_changes_only_after_its_clock(self):
        revised = dict(self.row, reported_at='2026-06-05T14:00:00+08:00', ex_date='2026-06-30')
        self.assertFalse(self.result([self.row,revised], cutoff='2026-06-05T13:30:00+08:00')['buy_ok']['2880'])
        self.assertTrue(self.result([self.row,revised], cutoff='2026-06-05T14:00:00+08:00')['buy_ok']['2880'])

    def test_unknown_clock_excluded_naive_clock_rejected(self):
        self.assertEqual(self.result([dict(self.row,reported_at='')])['missing_clocks_excluded'], 1)
        with self.assertRaises(ValueError): self.result([dict(self.row,reported_at='2026-05-01')])

    def test_same_clock_conflict_rejected(self):
        with self.assertRaises(ValueError): self.result([self.row,dict(self.row,ex_date='2026-06-30')])

    def test_withdrawal_does_not_retain_old_schedule(self):
        revised = dict(self.row, reported_at='2026-05-19T10:00:00+08:00', ex_date='')
        self.assertEqual(self.result([self.row,revised])['known_schedules'], 0)

    def test_missing_session_not_silently_shifted(self):
        with self.assertRaises(ValueError): self.result([dict(self.row,ex_date='2026-06-14')])

    def test_intraday_and_missing_current_quote_rejected(self):
        with self.assertRaises(ValueError): self.result(cutoff='2026-05-20T12:00:00+08:00')
        with self.assertRaises(ValueError): self.result(market=self.market[self.market.date != '2026-05-20'])
