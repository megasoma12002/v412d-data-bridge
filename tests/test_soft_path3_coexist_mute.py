#!/usr/bin/env python3
"""Guards for Soft↔Path3 flip-day coexistence mute (0kaa)."""
from __future__ import annotations

import unittest

from live_config import (
    LIVE,
    LIVE_SOFT_PATH3_COEXIST_MUTE,
    LIVE_SOFT_PATH3_COEXIST_MUTE_POLICY,
)
from live_soft_path3_coexist_mute import (
    DEFAULT_POLICY,
    MECHANISM_ID,
    POLICY_MUTE_SOFT_FIN_TEL,
    POLICY_MUTE_SOFT_ON_FLIP_META,
    apply_coexist_mute,
    filter_soft_orders,
    should_mute,
)


def _soft_rows():
    return [
        {"order_id": "2026-06-12-2880-BUY", "code": "2880", "side": "BUY", "qty": 1000},
        {"order_id": "2026-06-12-2412-SELL", "code": "2412", "side": "SELL", "qty": 1000},
        {"order_id": "2026-06-12-0050-BUY", "code": "0050", "side": "BUY", "qty": 2000},
        {
            "order_id": "2026-06-12-00631L-BUY",
            "code": "00631L",
            "side": "BUY",
            "qty": 1000,
        },
    ]


class MuteFlagDefaults(unittest.TestCase):
    def test_flag_on_after_accept(self) -> None:
        self.assertTrue(LIVE.live_soft_path3_coexist_mute)
        self.assertTrue(LIVE_SOFT_PATH3_COEXIST_MUTE)
        self.assertEqual(LIVE_SOFT_PATH3_COEXIST_MUTE_POLICY, POLICY_MUTE_SOFT_FIN_TEL)
        self.assertIn("ACCEPT Soft↔Path3 coexist mute", LIVE.live_soft_path3_coexist_mute_ballot)


class ShouldMute(unittest.TestCase):
    def test_requires_flag_emit_flip_and_deltas(self) -> None:
        self.assertFalse(
            should_mute(mute_enabled=False, emit_enabled=True, flip=True, n_path3_delta_names=3)
        )
        self.assertFalse(
            should_mute(mute_enabled=True, emit_enabled=False, flip=True, n_path3_delta_names=3)
        )
        self.assertFalse(
            should_mute(mute_enabled=True, emit_enabled=True, flip=False, n_path3_delta_names=3)
        )
        self.assertFalse(
            should_mute(mute_enabled=True, emit_enabled=True, flip=True, n_path3_delta_names=0)
        )
        self.assertTrue(
            should_mute(mute_enabled=True, emit_enabled=True, flip=True, n_path3_delta_names=3)
        )

    def test_flip_meta_policy_mutes_without_deltas(self) -> None:
        self.assertTrue(
            should_mute(
                mute_enabled=True,
                emit_enabled=True,
                flip=True,
                n_path3_delta_names=0,
                policy=POLICY_MUTE_SOFT_ON_FLIP_META,
            )
        )


class FilterSoftOrders(unittest.TestCase):
    def test_mute_fin_tel_keeps_0050_and_satellite(self) -> None:
        kept, muted, meta = filter_soft_orders(_soft_rows(), policy=DEFAULT_POLICY, apply=True)
        self.assertEqual(meta["mechanism_id"], MECHANISM_ID)
        self.assertEqual(meta["n_muted"], 2)
        self.assertEqual({r["code"] for r in muted}, {"2880", "2412"})
        self.assertEqual({r["code"] for r in kept}, {"0050", "00631L"})

    def test_never_drops_path3_tagged(self) -> None:
        rows = _soft_rows() + [
            {
                "order_id": "2026-06-12-2880-SELL-P3T0",
                "code": "2880",
                "side": "SELL",
                "qty": 1000,
                "path3_switch": True,
            }
        ]
        kept, muted, _meta = filter_soft_orders(rows, apply=True)
        self.assertTrue(any(r.get("path3_switch") for r in kept))
        self.assertEqual(sum(1 for r in muted if r["code"] == "2880"), 1)

    def test_apply_false_keeps_all(self) -> None:
        kept, muted, meta = filter_soft_orders(_soft_rows(), apply=False)
        self.assertEqual(len(kept), 4)
        self.assertEqual(muted, [])
        self.assertFalse(meta["applied"])


class ApplyPipelineHelper(unittest.TestCase):
    def test_pipeline_mute_on_flip_with_deltas(self) -> None:
        kept, meta = apply_coexist_mute(
            _soft_rows(),
            mute_enabled=True,
            emit_enabled=True,
            flip=True,
            path3_delta_shares={"2880": -1000.0, "2412": 1000.0},
            policy=POLICY_MUTE_SOFT_FIN_TEL,
        )
        self.assertTrue(meta["should_mute"])
        self.assertTrue(meta["applied"])
        self.assertEqual(meta["n_muted"], 2)
        self.assertEqual({r["code"] for r in kept}, {"0050", "00631L"})

    def test_flag_off_no_mute(self) -> None:
        kept, meta = apply_coexist_mute(
            _soft_rows(),
            mute_enabled=False,
            emit_enabled=True,
            flip=True,
            path3_delta_shares={"2880": -1000.0},
        )
        self.assertFalse(meta["should_mute"])
        self.assertEqual(len(kept), 4)


if __name__ == "__main__":
    unittest.main()
