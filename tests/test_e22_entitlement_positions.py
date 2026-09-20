#!/usr/bin/env python3
"""Entitlement snapshot: open fills on ex must not change cash/stock credits."""
from __future__ import annotations

import unittest

import e22_dividend_accounting as formal
import e22_v3_sandbox_books as sandbox
from e22_books_apply import apply_books_for_date


class EntitlementPositionsFormalTests(unittest.TestCase):
    def test_buy_on_ex_cash_uses_entitlement_not_post_fill(self) -> None:
        ev = formal.DivEvent(
            code="2880",
            kind="cash",
            ex_date="2026-07-13",
            amount=1.5,
            payment_date="2026-08-07",
        )
        ent = {"2880": 1000.0}
        post_fill = {"2880": 2000.0}  # bought 1000 at open on ex
        pos, cash, res = formal.apply_dividends_for_date(
            "2026-07-13",
            post_fill,
            0.0,
            [ev],
            version=formal.E22_V2S_TW,
            entitlement_positions=ent,
        )
        self.assertAlmostEqual(cash, 1500.0)  # 1000 * 1.5, not 2000
        self.assertEqual(pos["2880"], 2000.0)  # post-fill preserved
        self.assertAlmostEqual(res.details[0]["shares"], 1000.0)

    def test_sell_on_ex_cash_still_uses_entitlement(self) -> None:
        ev = formal.DivEvent(
            code="2880",
            kind="cash",
            ex_date="2026-07-13",
            amount=2.0,
            payment_date="2026-08-07",
        )
        ent = {"2880": 1000.0}
        post_fill = {"2880": 0.0}  # sold all at open on ex
        _, cash, res = formal.apply_dividends_for_date(
            "2026-07-13",
            post_fill,
            0.0,
            [ev],
            version=formal.E22_V2S_TW,
            entitlement_positions=ent,
        )
        self.assertAlmostEqual(cash, 2000.0)
        self.assertAlmostEqual(res.details[0]["shares"], 1000.0)

    def test_stock_floor_cil_applies_delta_to_post_fill_pos(self) -> None:
        # 10% stock div (1 元/股 → factor 1.1): entitlement 1000 → +100 whole shares
        ev = formal.DivEvent(
            code="2880",
            kind="stock",
            ex_date="2026-07-13",
            amount=1.0,
            payment_date="2026-08-07",
        )
        ent = {"2880": 1000.0}
        post_fill = {"2880": 1500.0}  # bought 500 on ex
        pos, cash, res = formal.apply_dividends_for_date(
            "2026-07-13",
            post_fill,
            0.0,
            [ev],
            version=formal.E22_V2S_TW,
            entitlement_positions=ent,
        )
        self.assertAlmostEqual(res.stock_shares_added, 100.0)
        self.assertAlmostEqual(pos["2880"], 1600.0)  # 1500 + 100, not replace with 1100
        self.assertEqual(cash, 0.0)


class EntitlementPositionsSandboxTests(unittest.TestCase):
    def test_recv_pay_buy_on_ex_uses_entitlement(self) -> None:
        ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-13",
            amount=1.0,
            payment_date="2026-08-07",
        )
        ent = {"2891": 1000.0}
        post = {"2891": 3000.0}
        _, cash, recv, res = sandbox.apply_sandbox_for_date(
            "2026-07-13",
            post,
            0.0,
            {},
            [ev],
            version=sandbox.E22_V3_RECV_PAY,
            entitlement_positions=ent,
        )
        self.assertEqual(cash, 0.0)
        self.assertAlmostEqual(sum(recv.values()), 1000.0)
        self.assertAlmostEqual(res.details[0]["gross_credit"], 1000.0)

    def test_books_router_passes_entitlement(self) -> None:
        ev = formal.DivEvent(
            code="2880",
            kind="cash",
            ex_date="2026-07-13",
            amount=1.0,
            payment_date="2026-08-07",
        )
        pos, cash, _recv, res = apply_books_for_date(
            "2026-07-13",
            {"2880": 5000.0},
            0.0,
            [ev],
            version=formal.E22_V2S_TW,
            entitlement_positions={"2880": 1000.0},
        )
        self.assertAlmostEqual(cash, 1000.0)
        self.assertEqual(pos["2880"], 5000.0)
        self.assertAlmostEqual(res.cash_credit, 1000.0)


class BlankPaymentDateFailClosed(unittest.TestCase):
    def test_recv_family_blank_payment_raises(self) -> None:
        ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-13",
            amount=1.0,
            payment_date="",
        )
        with self.assertRaises(ValueError) as ctx:
            sandbox.apply_sandbox_for_date(
                "2026-07-13",
                {"2891": 1000.0},
                0.0,
                {},
                [ev],
                version=sandbox.E22_V3_RECV_PAY,
            )
        self.assertIn("blank payment_date", str(ctx.exception))
        self.assertIn("2891", str(ctx.exception))

    def test_preserved_cash_on_ex_allows_blank_payment(self) -> None:
        ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-13",
            amount=1.0,
            payment_date="",
        )
        _, cash, res = formal.apply_dividends_for_date(
            "2026-07-13",
            {"2891": 1000.0},
            0.0,
            [ev],
            version=formal.E22_V2S_TW,
        )
        self.assertAlmostEqual(cash, 1000.0)
        self.assertAlmostEqual(res.cash_credit, 1000.0)


class EffdelayStockPathManifest(unittest.TestCase):
    def test_effdelay_stock_path_is_tw_effex(self) -> None:
        m = sandbox.version_manifest(sandbox.E22_V3_RECV_PAY_EFFDELAY)
        self.assertEqual(m["stock_path"], formal.E22_V2S_TW_EFFEX)
        m2 = sandbox.version_manifest(sandbox.E22_V3_RECV_PAY)
        self.assertEqual(m2["stock_path"], sandbox.STOCK_BASE_VERSION)


if __name__ == "__main__":
    unittest.main()
