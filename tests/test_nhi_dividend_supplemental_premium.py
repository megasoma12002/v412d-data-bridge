#!/usr/bin/env python3
"""NHI dividend supplemental premium helper — unit tests."""
from __future__ import annotations

import unittest

from nhi_dividend_supplemental_premium import (
    NHI_DIVIDEND_THRESHOLD_TWD,
    NHI_SUPPLEMENTAL_RATE,
    nhi_dividend_premium,
)


class NhiDividendPremiumTests(unittest.TestCase):
    def test_below_threshold_no_premium(self) -> None:
        r = nhi_dividend_premium(19_999.0)
        self.assertFalse(r.applies)
        self.assertEqual(r.premium_twd, 0.0)
        self.assertEqual(r.net_cash_twd, 19_999.0)

    def test_at_threshold_full_base(self) -> None:
        r = nhi_dividend_premium(20_000.0)
        self.assertTrue(r.applies)
        self.assertAlmostEqual(r.premium_twd, 20_000.0 * NHI_SUPPLEMENTAL_RATE)
        self.assertAlmostEqual(r.net_cash_twd, 20_000.0 - r.premium_twd)
        self.assertEqual(r.threshold_twd, NHI_DIVIDEND_THRESHOLD_TWD)

    def test_cap_at_ten_million(self) -> None:
        r = nhi_dividend_premium(10_000_001.0)
        self.assertTrue(r.applies)
        self.assertEqual(r.taxable_base_twd, 10_000_000.0)
        self.assertAlmostEqual(r.premium_twd, 10_000_000.0 * NHI_SUPPLEMENTAL_RATE)

    def test_negative_rejected(self) -> None:
        with self.assertRaises(ValueError):
            nhi_dividend_premium(-1.0)


if __name__ == "__main__":
    unittest.main()
