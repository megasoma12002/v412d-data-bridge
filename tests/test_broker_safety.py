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
    already_submitted,
    build_submit_intents,
    client_order_id_for,
    live_write_gate,
    load_circuit,
    reset_circuit,
    trip_circuit,
    validate_ack_against_pending,
)
from live_config import LIVE
from live_execution import BrokerPreflightFillPort
from live_ledger import fees_tax_for
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
) -> None:
    ack_dir = sdir / "broker_acks"
    ack_dir.mkdir(parents=True, exist_ok=True)
    (ack_dir / f"{asof}.json").write_text(
        json.dumps(
            {
                "acks": [
                    {
                        "order_id": order_id,
                        "code": code,
                        "side": side,
                        "quantity": quantity,
                        "fill_price": fill_price,
                        "signal_date": "2026-07-10",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )


class LiveWriteGateTests(unittest.TestCase):
    def test_default_live_config_rejects(self) -> None:
        self.assertFalse(LIVE.broker_live_write_accepted)

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
            self.assertTrue(g3.allowed)

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
            self.assertEqual(len(fills), 1)
            self.assertEqual(pos, {})
            self.assertEqual(cash, 1_000_000.0)
            self.assertFalse((sdir / "fills.csv").exists())
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


class LandmineBrokerLiveAccept(unittest.TestCase):
    def test_live_config_keeps_broker_live_write_false(self) -> None:
        cfg = Path("scripts/live_config.py").read_text(encoding="utf-8")
        self.assertIn("broker_live_write_accepted: bool = False", cfg)


if __name__ == "__main__":
    unittest.main()
