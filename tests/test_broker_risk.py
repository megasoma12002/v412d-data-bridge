#!/usr/bin/env python3
"""Tests for broker_risk: state machine, risk, rate limit, recovery."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from broker_risk import (
    OrderState,
    RiskConfig,
    check_rate_limit,
    circuit_access,
    list_alerts,
    load_order_states,
    load_unresolved,
    pre_submit_full_gate,
    pre_submit_risk_check,
    record_rate_limit_write,
    resolve_unresolved_order,
    run_startup_reconcile,
    set_panic,
    transition_order,
)
from broker_safety import (
    DEFAULT_CIRCUIT_FAIL_THRESHOLD,
    allow_circuit_write,
    load_circuit,
    record_circuit_success,
    trip_circuit,
)
from tw_share_lots import BOARD_LOT


class StateMachineTests(unittest.TestCase):
    def test_pending_to_filled_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            asof = date(2026, 7, 13)
            transition_order(
                sdir,
                client_order_id="o1@2026-07-13",
                order_id="o1",
                code="0050",
                side="BUY",
                quantity=BOARD_LOT,
                asof=asof,
                new_state=OrderState.PENDING,
            )
            transition_order(
                sdir,
                client_order_id="o1@2026-07-13",
                order_id="o1",
                code="0050",
                side="BUY",
                quantity=BOARD_LOT,
                asof=asof,
                new_state=OrderState.SUBMITTED,
            )
            transition_order(
                sdir,
                client_order_id="o1@2026-07-13",
                order_id="o1",
                code="0050",
                side="BUY",
                quantity=BOARD_LOT,
                asof=asof,
                new_state=OrderState.FILLED,
                filled_qty=BOARD_LOT,
            )
            st = load_order_states(sdir)["o1@2026-07-13"]
            self.assertEqual(st.state, OrderState.FILLED.value)

    def test_illegal_transition_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            asof = date(2026, 7, 13)
            transition_order(
                sdir,
                client_order_id="o1@d",
                order_id="o1",
                code="0050",
                side="BUY",
                quantity=BOARD_LOT,
                asof=asof,
                new_state=OrderState.FILLED,
                force=True,
            )
            with self.assertRaises(ValueError):
                transition_order(
                    sdir,
                    client_order_id="o1@d",
                    order_id="o1",
                    code="0050",
                    side="BUY",
                    quantity=BOARD_LOT,
                    asof=asof,
                    new_state=OrderState.PENDING,
                )


class RiskAndRateTests(unittest.TestCase):
    def test_panic_and_blacklist(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            set_panic(sdir, True, reason="test")
            r = pre_submit_risk_check(
                sdir, code="0050", side="BUY", quantity=BOARD_LOT, price=100.0
            )
            self.assertFalse(r.allowed)
            self.assertTrue(any("panic" in x for x in r.reasons))
            set_panic(sdir, False)
            cfg = RiskConfig(blacklist=["2330"], max_qty_shares=BOARD_LOT)
            cfg.save(sdir)
            r2 = pre_submit_risk_check(
                sdir, code="2330", side="BUY", quantity=BOARD_LOT, price=500.0
            )
            self.assertFalse(r2.allowed)
            self.assertTrue(any("blacklist" in x for x in r2.reasons))

    def test_qty_and_notional_caps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            RiskConfig(max_qty_shares=BOARD_LOT, max_notional=50_000.0).save(sdir)
            r = pre_submit_risk_check(
                sdir, code="0050", side="BUY", quantity=2 * BOARD_LOT, price=100.0
            )
            self.assertFalse(r.allowed)
            r2 = pre_submit_risk_check(
                sdir, code="0050", side="BUY", quantity=BOARD_LOT, price=100.0
            )
            # 1000*100=100000 > 50000
            self.assertFalse(r2.allowed)

    def test_rate_limit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            RiskConfig(max_writes_per_minute=2).save(sdir)
            record_rate_limit_write(sdir, client_order_id="a")
            record_rate_limit_write(sdir, client_order_id="b")
            r = check_rate_limit(sdir)
            self.assertFalse(r.allowed)


class RecoveryAndCircuitTests(unittest.TestCase):
    def test_reconcile_and_manual_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            asof = date(2026, 7, 13)
            transition_order(
                sdir,
                client_order_id="o1@d",
                order_id="o1",
                code="0050",
                side="BUY",
                quantity=BOARD_LOT,
                asof=asof,
                new_state=OrderState.SUBMITTED,
            )
            payload = run_startup_reconcile(sdir, asof=asof)
            self.assertEqual(payload["n_unresolved"], 1)
            gate = pre_submit_full_gate(
                sdir, code="0050", side="BUY", quantity=BOARD_LOT, price=100.0
            )
            self.assertFalse(gate.allowed)
            self.assertTrue(any("unresolved" in x for x in gate.reasons))
            resolve_unresolved_order(
                sdir, "o1@d", final_state=OrderState.CANCELLED, asof=asof
            )
            self.assertEqual(load_unresolved(sdir).get("n_unresolved"), 0)
            gate2 = pre_submit_full_gate(
                sdir, code="0050", side="BUY", quantity=BOARD_LOT, price=100.0
            )
            self.assertTrue(gate2.allowed)

    def test_circuit_blocks_writes_allows_reads(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            for i in range(DEFAULT_CIRCUIT_FAIL_THRESHOLD):
                trip_circuit(sdir, f"x{i}")
            access = circuit_access(sdir)
            self.assertFalse(access.writes_allowed)
            self.assertTrue(access.reads_allowed)

    def test_half_open_probe_after_cooldown_then_success(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            for i in range(DEFAULT_CIRCUIT_FAIL_THRESHOLD):
                trip_circuit(sdir, f"x{i}")
            c = load_circuit(sdir)
            self.assertEqual(c.mode, "open")
            # Pretend cooldown already elapsed
            c.opened_at = "2020-01-01T00:00:00+00:00"
            from broker_safety import save_circuit

            save_circuit(sdir, c)
            ok, c2 = allow_circuit_write(sdir)
            self.assertTrue(ok)
            self.assertEqual(c2.mode, "half_open")
            access = circuit_access(sdir)
            self.assertTrue(access.writes_allowed)
            record_circuit_success(sdir)
            c3 = load_circuit(sdir)
            self.assertEqual(c3.mode, "closed")
            self.assertFalse(c3.open)

    def test_stale_past_trade_date_tagged(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            transition_order(
                sdir,
                client_order_id="o1@old",
                order_id="o1",
                code="0050",
                side="BUY",
                quantity=BOARD_LOT,
                asof=date(2026, 7, 10),
                new_state=OrderState.SUBMITTED,
            )
            payload = run_startup_reconcile(sdir, asof=date(2026, 7, 13))
            self.assertEqual(payload["n_unresolved"], 1)
            self.assertEqual(payload["n_stale"], 1)
            self.assertTrue(payload["unresolved"][0].get("stale"))

    def test_alerts_logged(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            set_panic(sdir, True, reason="unit")
            alerts = list_alerts(sdir)
            self.assertTrue(any(a.get("kind") == "panic_on" for a in alerts))


class LandmineOpsStatusConflict(unittest.TestCase):
    def test_ops_status_has_no_conflict_markers(self) -> None:
        text = Path("research/ops/OPS_STATUS.md").read_text(encoding="utf-8")
        self.assertNotIn("<<<<<<<", text)
        self.assertNotIn(">>>>>>>", text)


if __name__ == "__main__":
    unittest.main()
