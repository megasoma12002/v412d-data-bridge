#!/usr/bin/env python3
"""Pre–real API broker 防呆: live_write_gate, ack↔pending, circuit, budget."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from broker_safety import (
    DEFAULT_CIRCUIT_FAIL_THRESHOLD,
    ProcessLock,
    already_broker_deduped,
    already_submitted,
    broker_dedupe_key,
    build_submit_intents,
    client_order_id_for,
    confirm_and_reserve_broker_submit,
    confirm_before_broker_submit,
    live_write_gate,
    load_circuit,
    reset_circuit,
    trip_circuit,
    validate_ack_against_pending,
)
from live_config import LIVE
from live_execution import BrokerPreflightFillPort
from live_ledger import fees_tax_for, make_order_id
from tw_share_lots import BOARD_LOT


def _open_probe(_d: date) -> SimpleNamespace:
    return SimpleNamespace(
        status="OPEN",
        broker_submit_allowed=True,
        is_session=True,
        notes=["open"],
    )


def _seed_pending(sdir: Path, *, oid: str = "o1", code: str = "0050") -> None:
    pd.DataFrame(
        [
            {
                "order_id": oid,
                "signal_date": "2026-07-10",
                "code": code,
                "side": "BUY",
                "quantity": BOARD_LOT,
            }
        ]
    ).to_csv(sdir / "orders.csv", index=False)


def _write_ack(
    sdir: Path,
    *,
    asof: str = "2026-07-13",
    order_id: str = "o1",
    code: str = "0050",
    side: str = "BUY",
    quantity: int = BOARD_LOT,
    fill_price: float = 100.0,
    ops_confirmed: bool = True,
    extra_acks: list[dict] | None = None,
) -> None:
    ack_dir = sdir / "broker_acks"
    ack_dir.mkdir(parents=True, exist_ok=True)
    acks = [
        {
            "order_id": order_id,
            "code": code,
            "side": side,
            "quantity": quantity,
            "fill_price": fill_price,
            "signal_date": "2026-07-10",
            "ops_confirmed": ops_confirmed,
        }
    ]
    if extra_acks:
        acks.extend(extra_acks)
    (ack_dir / f"{asof}.json").write_text(
        json.dumps({"acks": acks}) + "\n",
        encoding="utf-8",
    )




def _write_accept_ballot(sdir: Path, *, accepted: bool = True) -> None:
    (sdir / "broker_live_write_accept.json").write_text(
        json.dumps({"accepted": accepted}) + "\n", encoding="utf-8"
    )

class LiveWriteGateTests(unittest.TestCase):
    def test_default_live_config_accepts_flag(self) -> None:
        # ACCEPT 2026-09-19 broker live-write — flag True; env+ballot still required.
        self.assertTrue(LIVE.broker_live_write_accepted)

    def test_gate_requires_accept_and_env(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            g = live_write_gate(
                config_accepted=False, state_dir=sdir, env_write_live=True
            )
            self.assertFalse(g.allowed)
            self.assertTrue(any("broker_live_write_accepted" in r for r in g.reasons))

            g2 = live_write_gate(
                config_accepted=True, state_dir=sdir, env_write_live=False
            )
            self.assertFalse(g2.allowed)
            self.assertTrue(any("E21_BROKER_WRITE_LIVE" in r for r in g2.reasons))

            g3 = live_write_gate(
                config_accepted=True, state_dir=sdir, env_write_live=True
            )
            self.assertFalse(g3.allowed)
            self.assertTrue(any("broker_live_write_accept" in r for r in g3.reasons))
            _write_accept_ballot(sdir, accepted=True)
            g4 = live_write_gate(
                config_accepted=True, state_dir=sdir, env_write_live=True
            )
            self.assertTrue(g4.allowed)

    def test_ballot_reject_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            (sdir / "broker_live_write_accept.json").write_text(
                json.dumps({"accepted": False}) + "\n", encoding="utf-8"
            )
            g = live_write_gate(
                config_accepted=True, state_dir=sdir, env_write_live=True
            )
            self.assertFalse(g.allowed)


class AckValidationTests(unittest.TestCase):
    def test_orphan_ack_rejected(self) -> None:
        pending = {"o1": SimpleNamespace(code="0050", side="BUY", quantity=BOARD_LOT)}
        v = validate_ack_against_pending(
            {"order_id": "orphan", "code": "0050", "side": "BUY", "quantity": BOARD_LOT},
            pending,
            asof=date(2026, 7, 13),
            open_prices={"0050": 100.0},
            slip=0.0,
            fees_tax_fn=fees_tax_for,
        )
        self.assertFalse(v.ok)
        self.assertIn("ack_not_in_pending", str(v.reject_reason))

    def test_code_mismatch_rejected(self) -> None:
        pending = {"o1": SimpleNamespace(code="0050", side="BUY", quantity=BOARD_LOT)}
        v = validate_ack_against_pending(
            {"order_id": "o1", "code": "2330", "side": "BUY", "quantity": BOARD_LOT},
            pending,
            asof=date(2026, 7, 13),
            open_prices={"0050": 100.0, "2330": 500.0},
            slip=0.0,
            fees_tax_fn=fees_tax_for,
        )
        self.assertFalse(v.ok)
        self.assertIn("code_mismatch", str(v.reject_reason))

    def test_match_builds_fill_with_client_order_id(self) -> None:
        pending = {
            "o1": SimpleNamespace(
                code="0050", side="BUY", quantity=BOARD_LOT, signal_date="2026-07-10"
            )
        }
        asof = date(2026, 7, 13)
        v = validate_ack_against_pending(
            {
                "order_id": "o1",
                "code": "0050",
                "side": "BUY",
                "quantity": BOARD_LOT,
                "fill_price": 100.0,
            },
            pending,
            asof=asof,
            open_prices={"0050": 100.0},
            slip=0.0,
            fees_tax_fn=fees_tax_for,
        )
        self.assertTrue(v.ok)
        assert v.fill is not None
        self.assertEqual(v.client_order_id, client_order_id_for("o1", asof=asof))
        self.assertEqual(v.fill["client_order_id"], v.client_order_id)
        self.assertIn("fees_tax", v.fill)


class CircuitAndIntentTests(unittest.TestCase):
    def test_circuit_opens_after_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            for i in range(DEFAULT_CIRCUIT_FAIL_THRESHOLD):
                c = trip_circuit(sdir, f"reject_{i}")
            self.assertTrue(c.open)
            self.assertTrue(load_circuit(sdir).open)
            reset_circuit(sdir)
            self.assertFalse(load_circuit(sdir).open)

    def test_submit_intents_skeleton(self) -> None:
        intents = build_submit_intents(
            [{"order_id": "o1", "code": "0050", "side": "BUY", "quantity": BOARD_LOT}],
            asof=date(2026, 7, 13),
        )
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].status, "INTENT_ONLY")
        self.assertIn("No broker API", intents[0].to_dict()["note"])


class BrokerPortSafetyTests(unittest.TestCase):
    def test_env_alone_cannot_live_write(self) -> None:
        """E21_BROKER_WRITE_LIVE=1 without LiveConfig ACCEPT stays shadow."""
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            _seed_pending(sdir)
            _write_ack(sdir)
            port = BrokerPreflightFillPort(
                probe_fn=_open_probe,
                write_live=True,  # env-equivalent override
                config_accepted=False,  # Soft-Frozen KEEP
            )
            pos, cash, fills, _, ok = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertEqual(len(fills), 0)  # gate denied → no pipeline fills
            self.assertEqual(pos, {})
            self.assertEqual(cash, 1_000_000.0)
            self.assertFalse((sdir / "fills.csv").exists())
            shadow = json.loads(
                (sdir / "broker_preflight" / "fills_2026-07-13.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(shadow["n_fills"], 1)
            allow = json.loads(
                (sdir / "broker_preflight" / "allow_2026-07-13.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(allow["live_write_gate_allowed"])
            self.assertFalse(allow["live_fills_written"])
            self.assertTrue(ok)

    def test_orphan_ack_no_fill_trips_circuit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            _seed_pending(sdir, oid="o1")
            _write_ack(sdir, order_id="not-pending")
            port = BrokerPreflightFillPort(
                probe_fn=_open_probe, write_live=False, config_accepted=False
            )
            _, _, fills, _, _ = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertEqual(fills, [])
            allow = json.loads(
                (sdir / "broker_preflight" / "allow_2026-07-13.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(any("ack_not_in_pending" in r for r in allow["ack_rejects"]))
            self.assertEqual(load_circuit(sdir).fail_count, 1)

    def test_mismatch_ack_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            _seed_pending(sdir, code="0050")
            _write_ack(sdir, code="2330")
            port = BrokerPreflightFillPort(
                probe_fn=_open_probe, write_live=False, config_accepted=False
            )
            _, _, fills, _, _ = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0, "2330": 500.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertEqual(fills, [])

    def test_accept_plus_env_writes_live_once(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            _seed_pending(sdir)
            _write_ack(sdir)
            _write_accept_ballot(sdir)
            port = BrokerPreflightFillPort(
                probe_fn=_open_probe,
                write_live=True,
                config_accepted=True,
            )
            pos, cash, fills, _, ok = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertEqual(len(fills), 1)
            self.assertTrue((sdir / "fills.csv").exists())
            self.assertEqual(pos.get("0050"), float(BOARD_LOT))
            self.assertLess(cash, 1_000_000.0)
            self.assertTrue(ok)
            coid = client_order_id_for("o1", asof=date(2026, 7, 13))
            self.assertTrue(already_submitted(sdir, coid))

            # Idempotent second pass — no duplicate fill rows.
            pos2, cash2, _, _, _ = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos=dict(pos),
                cash=float(cash),
            )
            rows = (sdir / "fills.csv").read_text(encoding="utf-8").strip().splitlines()
            # header + 1 data row
            self.assertEqual(len(rows), 2)
            self.assertEqual(pos2, pos)
            self.assertEqual(cash2, cash)

    def test_circuit_blocks_further_work(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            for i in range(DEFAULT_CIRCUIT_FAIL_THRESHOLD):
                trip_circuit(sdir, f"x{i}")
            _seed_pending(sdir)
            _write_ack(sdir)
            _write_accept_ballot(sdir)
            port = BrokerPreflightFillPort(
                probe_fn=_open_probe, write_live=True, config_accepted=True
            )
            pos, cash, fills, _, _ = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertEqual(fills, [])
            self.assertFalse((sdir / "fills.csv").exists())
            self.assertTrue(
                (sdir / "broker_preflight" / "block_2026-07-13.json").exists()
            )

    def test_submit_intents_written_on_open(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            _seed_pending(sdir)
            port = BrokerPreflightFillPort(
                probe_fn=_open_probe, write_live=False, config_accepted=False
            )
            port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            path = sdir / "broker_preflight" / "submit_intents_2026-07-13.json"
            self.assertTrue(path.exists())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(payload["api_wired"])
            self.assertEqual(payload["n"], 1)
            self.assertEqual(payload["intents"][0]["status"], "INTENT_ONLY")
            self.assertTrue(payload["intents"][0]["require_confirm_before_submit"])
            self.assertIn("broker_dedupe_key", payload["intents"][0])


class StableOrderIdTests(unittest.TestCase):
    def test_make_order_id_stable_and_bit_identical(self) -> None:
        a = make_order_id(signal_date=date(2026, 7, 13), code="0050", side="buy")
        b = make_order_id(signal_date="2026-07-13", code="0050", side="BUY")
        self.assertEqual(a, b)
        self.assertEqual(a, "2026-07-13-0050-BUY")

    def test_regenerating_same_content_same_client_order_id(self) -> None:
        oid = make_order_id(signal_date=date(2026, 7, 10), code="2330", side="SELL")
        asof = date(2026, 7, 13)
        c1 = client_order_id_for(oid, asof=asof)
        c2 = client_order_id_for(
            make_order_id(signal_date=date(2026, 7, 10), code="2330", side="SELL"),
            asof=asof,
        )
        self.assertEqual(c1, c2)


class ProcessLockAndConfirmTests(unittest.TestCase):
    def test_process_lock_exclusive_nonblocking(self) -> None:
        import multiprocessing as mp
        import time

        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            ready = mp.Event()
            release = mp.Event()
            result: mp.Queue = mp.Queue()

            def holder() -> None:
                with ProcessLock(sdir, blocking=True):
                    ready.set()
                    release.wait(timeout=5)

            def contender() -> None:
                ready.wait(timeout=5)
                try:
                    with ProcessLock(sdir, blocking=False):
                        result.put("acquired")
                except BlockingIOError:
                    result.put("blocked")

            p1 = mp.Process(target=holder)
            p2 = mp.Process(target=contender)
            p1.start()
            p2.start()
            p2.join(timeout=5)
            release.set()
            p1.join(timeout=5)
            self.assertEqual(result.get(timeout=2), "blocked")
            self.assertEqual(p2.exitcode, 0)
            self.assertEqual(p1.exitcode, 0)

    def test_confirm_requires_explicit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            r = confirm_before_broker_submit(
                state_dir=sdir,
                client_order_id="o1@2026-07-13",
                code="0050",
                side="BUY",
                quantity=BOARD_LOT,
                asof=date(2026, 7, 13),
                confirmed=False,
                config_accepted=True,
                env_write_live=True,
            )
            self.assertFalse(r.allowed)
            self.assertTrue(any("confirmed=False" in x for x in r.reasons))

    def test_confirm_and_reserve_dedupes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            _write_accept_ballot(sdir)
            with ProcessLock(sdir):
                r1 = confirm_and_reserve_broker_submit(
                    state_dir=sdir,
                    client_order_id="o1@2026-07-13",
                    code="0050",
                    side="BUY",
                    quantity=BOARD_LOT,
                    asof=date(2026, 7, 13),
                    confirmed=True,
                    config_accepted=True,
                    env_write_live=True,
                )
                self.assertTrue(r1.allowed)
                self.assertTrue(already_broker_deduped(sdir, r1.dedupe_key or ""))
                r2 = confirm_and_reserve_broker_submit(
                    state_dir=sdir,
                    client_order_id="o1@2026-07-13",
                    code="0050",
                    side="BUY",
                    quantity=BOARD_LOT,
                    asof=date(2026, 7, 13),
                    confirmed=True,
                    config_accepted=True,
                    env_write_live=True,
                )
                self.assertFalse(r2.allowed)
                self.assertTrue(any("broker_dedupe_hit" in x for x in r2.reasons))

    def test_dedupe_key_includes_qty(self) -> None:
        a = broker_dedupe_key(
            client_order_id="x", code="0050", side="BUY", quantity=1000
        )
        b = broker_dedupe_key(
            client_order_id="x", code="0050", side="BUY", quantity=2000
        )
        self.assertNotEqual(a, b)

    def test_live_write_reserves_dedupe(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            _seed_pending(sdir)
            _write_ack(sdir)
            _write_accept_ballot(sdir)
            port = BrokerPreflightFillPort(
                probe_fn=_open_probe, write_live=True, config_accepted=True
            )
            port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            coid = client_order_id_for("o1", asof=date(2026, 7, 13))
            dkey = broker_dedupe_key(
                client_order_id=coid, code="0050", side="BUY", quantity=BOARD_LOT
            )
            self.assertTrue(already_broker_deduped(sdir, dkey))


class BrokerLiveAffordAndConfirmTests(unittest.TestCase):
    def test_insufficient_cash_skips_live_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            _seed_pending(sdir)
            _write_ack(sdir, fill_price=100.0)
            _write_accept_ballot(sdir)
            port = BrokerPreflightFillPort(
                probe_fn=_open_probe, write_live=True, config_accepted=True
            )
            pos, cash, fills, _, ok = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000.0,  # far below 1000*100 + fee
            )
            self.assertEqual(len(fills), 1)  # shadow fill present
            self.assertEqual(pos, {})
            self.assertEqual(cash, 1_000.0)
            self.assertFalse((sdir / "fills.csv").exists())
            allow = json.loads(
                (sdir / "broker_preflight" / "allow_2026-07-13.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(
                any("insufficient_cash" in s for s in allow.get("live_skips", []))
            )
            self.assertTrue(ok)

    def test_missing_ops_confirmed_blocks_live_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            _seed_pending(sdir)
            _write_ack(sdir, ops_confirmed=False)
            _write_accept_ballot(sdir)
            port = BrokerPreflightFillPort(
                probe_fn=_open_probe, write_live=True, config_accepted=True
            )
            pos, cash, fills, _, _ = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertEqual(len(fills), 1)
            self.assertEqual(pos, {})
            self.assertEqual(cash, 1_000_000.0)
            self.assertFalse((sdir / "fills.csv").exists())
            allow = json.loads(
                (sdir / "broker_preflight" / "allow_2026-07-13.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(
                any("confirm_denied" in s for s in allow.get("live_skips", []))
            )

    def test_orphan_plus_valid_ack_blocks_all_live_writes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            _seed_pending(sdir, oid="o1")
            _write_ack(
                sdir,
                order_id="o1",
                extra_acks=[
                    {
                        "order_id": "orphan-x",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": BOARD_LOT,
                        "fill_price": 100.0,
                        "ops_confirmed": True,
                    }
                ],
            )
            _write_accept_ballot(sdir)
            port = BrokerPreflightFillPort(
                probe_fn=_open_probe, write_live=True, config_accepted=True
            )
            pos, cash, fills, _, _ = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertEqual(len(fills), 0)  # unresolved block → no pipeline fills
            self.assertEqual(pos, {})
            self.assertEqual(cash, 1_000_000.0)
            self.assertFalse((sdir / "fills.csv").exists())
            shadow = json.loads(
                (sdir / "broker_preflight" / "fills_2026-07-13.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertGreaterEqual(shadow["n_fills"], 1)
            allow = json.loads(
                (sdir / "broker_preflight" / "allow_2026-07-13.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(allow.get("reason"), "unresolved_orders_present")
            self.assertFalse(allow.get("live_fills_written"))


class LandmineBrokerLiveAccept(unittest.TestCase):
    def test_live_config_broker_live_write_accepted_true(self) -> None:
        cfg = Path("scripts/live_config.py").read_text(encoding="utf-8")
        self.assertIn("broker_live_write_accepted: bool = True", cfg)


if __name__ == "__main__":
    unittest.main()
