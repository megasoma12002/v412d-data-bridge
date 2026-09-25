#!/usr/bin/env python3
"""Unit tests for E22 dividend fetch: payment-date preserve + FinMind retry."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import urllib.error

from v412e22_fetch_dividend_events import (
    FinMindQuotaError,
    apply_prior_payment_dates,
    fetch,
    load_prior_payment_maps,
)


class FakeResp:
    def __init__(self, payload):
        self._buf = io.BytesIO(json.dumps(payload).encode())

    def __enter__(self):
        return self._buf

    def __exit__(self, *args):
        return False


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://api.finmindtrade.com/api/v4/data",
        code,
        "err",
        hdrs=None,
        fp=io.BytesIO(b""),
    )


class PaymentDatePreserveTests(unittest.TestCase):
    def test_load_and_apply_preserves_blank_finmind_pay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "e22_dividend_events.csv"
            path.write_text(
                "code,cash_ex_date,cash_payment_date,cash_dividend,"
                "stock_ex_date,stock_payment_date,stock_dividend\n"
                "2880,2010-08-12,2010-09-03,1.0,,,0\n"
                "2412,2011-07-21,,0.5,2011-07-21,2011-09-01,1.0\n",
                encoding="utf-8",
            )
            cash, stock = load_prior_payment_maps(path)
            self.assertEqual(cash[("2880", "2010-08-12")], "2010-09-03")
            self.assertEqual(stock[("2412", "2011-07-21")], "2011-09-01")

            rows = [
                {
                    "code": "2880",
                    "cash_ex_date": "2010-08-12",
                    "cash_payment_date": "",
                    "stock_ex_date": "",
                    "stock_payment_date": "",
                },
                {
                    "code": "2412",
                    "cash_ex_date": "2011-07-21",
                    "cash_payment_date": "2011-08-15",
                    "stock_ex_date": "2011-07-21",
                    "stock_payment_date": "",
                },
            ]
            stats = apply_prior_payment_dates(rows, cash, stock)
            self.assertEqual(rows[0]["cash_payment_date"], "2010-09-03")
            self.assertEqual(rows[1]["cash_payment_date"], "2011-08-15")
            self.assertEqual(rows[1]["stock_payment_date"], "2011-09-01")
            self.assertEqual(stats["preserved_cash_payment_dates"], 1)
            self.assertEqual(stats["preserved_stock_payment_dates"], 1)

    def test_no_invent_without_prior_key(self):
        rows = [
            {
                "code": "2880",
                "cash_ex_date": "2099-01-01",
                "cash_payment_date": "",
                "stock_ex_date": "",
                "stock_payment_date": "",
            }
        ]
        apply_prior_payment_dates(rows, {("2880", "2010-08-12"): "2010-09-03"}, {})
        self.assertEqual(rows[0]["cash_payment_date"], "")


class FinMindRetryTests(unittest.TestCase):
    def test_retries_then_succeeds_on_transient(self):
        payloads = [_http_error(500), {"status": 200, "data": [{"year": "2010"}]}]

        def fake_urlopen(req, timeout=120):  # noqa: ARG001
            item = payloads.pop(0)
            if isinstance(item, BaseException):
                raise item
            return FakeResp(item)

        with mock.patch(
            "v412e22_fetch_dividend_events.urllib.request.urlopen", fake_urlopen
        ):
            with mock.patch(
                "v412e22_fetch_dividend_events.time.sleep", return_value=None
            ):
                data = fetch("2880", retries=3)
        self.assertEqual(data, [{"year": "2010"}])

    def test_402_exhausted_raises_quota_error(self):
        def always_402(req, timeout=120):  # noqa: ARG001
            raise _http_error(402)

        with mock.patch(
            "v412e22_fetch_dividend_events.urllib.request.urlopen", always_402
        ):
            with mock.patch(
                "v412e22_fetch_dividend_events.time.sleep", return_value=None
            ):
                with self.assertRaises(FinMindQuotaError):
                    fetch("2880", retries=5)


if __name__ == "__main__":
    unittest.main()
