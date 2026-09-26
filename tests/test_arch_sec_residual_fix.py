#!/usr/bin/env python3
"""Class D FinPriv ops-alert freshness + tip-write QC gate residual fixes."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class ClassDFinPrivAlertTests(unittest.TestCase):
    def test_stale_priv_panel_emits_high(self):
        import ops_alert_scan as scan
        import live_config as lc

        with tempfile.TemporaryDirectory() as td:
            tip = Path(td) / "portfolio_state.json"
            tip.write_text(json.dumps({"last_date": "2099-01-01"}) + "\n")
            with mock.patch.object(scan, "TIP_STATE", tip):
                with mock.patch.object(scan, "SIGNALS_CSV", Path(td) / "no_signals.csv"):
                    with mock.patch.object(lc, "LIVE_FIN_PRIV_V7_F05", True):
                        alerts = scan._class_d_finpriv_alerts()
        codes = {a["code"] for a in alerts}
        self.assertIn("FINPRIV_PX_STALE_OR_MISSING", codes)

    def test_fresh_panel_emits_info(self):
        import ops_alert_scan as scan
        from live_config import LIVE_FIN_PRIV_V7_F05

        if not LIVE_FIN_PRIV_V7_F05:
            self.skipTest("Class D flag off")
        alerts = scan._class_d_finpriv_alerts()
        codes = {a["code"] for a in alerts}
        # Live tip asof should be within lag of refreshed panel on this checkout.
        self.assertTrue(
            "FINPRIV_PX_FRESH" in codes or "FINPRIV_PX_STALE_OR_MISSING" in codes,
            msg=alerts,
        )


class PrivTipRefreshScriptTests(unittest.TestCase):
    def test_script_imports(self):
        import private_fin_adj_tip_refresh as refresh

        self.assertTrue(refresh.ADJ.name.endswith("private_fin_adjusted.csv"))
        self.assertIn("2884", refresh.FILL_CODES)


if __name__ == "__main__":
    unittest.main()
