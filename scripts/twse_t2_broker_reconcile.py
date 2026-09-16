#!/usr/bin/env python3
"""R5 — T+2 settlement estimate ↔ broker/custody reconcile pack (observe-only).

Compares ``settlement_cash_estimate.csv`` (R1–R4) against a custody / broker
statement fixture CSV. Soft-Frozen / live ``fills.csv`` / paper cash untouched.

Custody fixture schema (minimum):
  fill_id,settle_date,settlement_cash[,code,side]

Or aggregate-only:
  settle_date,settlement_cash_net
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TAIPEI = ZoneInfo("Asia/Taipei")


def _f(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def reconcile(
    estimate_rows: list[dict[str, Any]],
    custody_rows: list[dict[str, Any]],
    *,
    asof: date,
    tol: float = 1.0,
) -> dict[str, Any]:
    """Match by fill_id when present; else by settle_date net."""
    est_by_id = {
        str(r.get("fill_id") or ""): r
        for r in estimate_rows
        if str(r.get("fill_id") or "").strip()
    }
    cust_by_id = {
        str(r.get("fill_id") or ""): r
        for r in custody_rows
        if str(r.get("fill_id") or "").strip()
    }

    matched: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    missing_in_custody: list[str] = []
    missing_in_estimate: list[str] = []

    if est_by_id and cust_by_id:
        for fid, er in sorted(est_by_id.items()):
            cr = cust_by_id.get(fid)
            if cr is None:
                missing_in_custody.append(fid)
                continue
            e_cash = _f(er.get("settlement_cash"))
            c_cash = _f(cr.get("settlement_cash"))
            e_settle = str(er.get("settle_date") or "")[:10]
            c_settle = str(cr.get("settle_date") or "")[:10]
            cash_ok = (
                e_cash is not None
                and c_cash is not None
                and abs(e_cash - c_cash) <= tol
            )
            settle_ok = (not c_settle) or e_settle == c_settle
            row = {
                "fill_id": fid,
                "estimate_settle_date": e_settle,
                "custody_settle_date": c_settle,
                "estimate_settlement_cash": e_cash,
                "custody_settlement_cash": c_cash,
                "cash_delta": None
                if e_cash is None or c_cash is None
                else e_cash - c_cash,
                "ok": bool(cash_ok and settle_ok),
            }
            (matched if row["ok"] else mismatches).append(row)
        for fid in sorted(cust_by_id):
            if fid not in est_by_id:
                missing_in_estimate.append(fid)
    else:
        # Aggregate by settle_date
        def _nets(rows: list[dict[str, Any]], cash_key: str) -> dict[str, float]:
            out: dict[str, float] = {}
            for r in rows:
                d = str(r.get("settle_date") or "")[:10]
                if not d:
                    continue
                # Prefer per-fill cash; else net column
                v = _f(r.get(cash_key))
                if v is None:
                    v = _f(r.get("settlement_cash_net"))
                if v is None:
                    continue
                out[d] = out.get(d, 0.0) + v
            return out

        e_net = _nets(estimate_rows, "settlement_cash")
        c_net = _nets(custody_rows, "settlement_cash")
        days = sorted(set(e_net) | set(c_net))
        for d in days:
            ev = e_net.get(d)
            cv = c_net.get(d)
            if ev is None:
                missing_in_estimate.append(d)
                continue
            if cv is None:
                missing_in_custody.append(d)
                continue
            ok = abs(ev - cv) <= tol
            row = {
                "settle_date": d,
                "estimate_net": ev,
                "custody_net": cv,
                "cash_delta": ev - cv,
                "ok": ok,
            }
            (matched if ok else mismatches).append(row)

    settling_today_est = sum(
        float(r.get("settlement_cash") or 0)
        for r in estimate_rows
        if str(r.get("settle_date") or "")[:10] == asof.isoformat()
    )
    all_ok = (
        not mismatches
        and not missing_in_custody
        and not missing_in_estimate
        and (bool(estimate_rows) or bool(custody_rows))
    )
    # Empty both sides is vacuously ok for no-trade days
    if not estimate_rows and not custody_rows:
        all_ok = True

    return {
        "asof": asof.isoformat(),
        "tol": tol,
        "n_estimate": len(estimate_rows),
        "n_custody": len(custody_rows),
        "n_matched_ok": len(matched),
        "n_mismatches": len(mismatches),
        "missing_in_custody": missing_in_custody,
        "missing_in_estimate": missing_in_estimate,
        "settling_today_estimate_net": settling_today_est,
        "all_ok": all_ok,
        "matched": matched[:50],
        "mismatches": mismatches[:50],
        "note": (
            "observe-only reconcile pack; does not gate broker submit or "
            "mutate Soft-Frozen / fills.csv / portfolio_state"
        ),
    }


def write_pack(payload: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"t2_broker_reconcile_{payload['asof']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest = out_dir / "t2_broker_reconcile_latest.json"
    latest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--estimate",
        type=Path,
        default=ROOT / "forward" / "e21" / "settlement_cash_estimate.csv",
    )
    ap.add_argument(
        "--custody",
        type=Path,
        required=True,
        help="Broker/custody statement CSV (fixture or export)",
    )
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default Taipei today)")
    ap.add_argument("--tol", type=float, default=1.0, help="NT$ absolute cash tolerance")
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Default: estimate parent / broker_reconcile",
    )
    a = ap.parse_args()
    asof = date.fromisoformat(a.asof) if a.asof else datetime.now(tz=TAIPEI).date()
    estimate_rows = load_csv(a.estimate)
    custody_rows = load_csv(a.custody)
    pack = reconcile(estimate_rows, custody_rows, asof=asof, tol=a.tol)
    out_dir = a.out_dir or (a.estimate.parent / "broker_reconcile")
    path = write_pack(pack, out_dir)
    pack["out"] = str(path)
    print(json.dumps(pack, ensure_ascii=False, indent=2))
    return 0 if pack["all_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
