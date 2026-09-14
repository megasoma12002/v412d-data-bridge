#!/usr/bin/env python3
"""Month-end pack data-freshness snapshot — RESEARCH / OPS only.

Collects tip/age signals for the month-end paper pack. Does not fetch data,
does not edit Soft-Frozen, does not rewrite forward/e21.

Used by ``ops_month_end_paper_pack.py`` and as a standalone:
  python3 scripts/ops_month_end_data_freshness.py
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research/ops"
OUT_JSON = OUT_DIR / "MONTH_END_DATA_FRESHNESS.json"
OUT_MD = OUT_DIR / "MONTH_END_DATA_FRESHNESS.md"

LIVE_MARKET = ROOT / "forward/e21/live_market.csv"
E22_EVENTS = ROOT / "data/dividend_events/e22_dividend_events.csv"
E22_FETCH_STATUS = ROOT / "data/dividend_events/e22_dividend_fetch_status.json"
E22_KPI = OUT_DIR / "E22_DATA_QUALITY_KPI.json"
SHADOW = OUT_DIR / "DATA_SOURCE_SHADOW_RECONCILE.json"

# Soft ops thresholds (visibility / optional fail-on-stale; not Soft-Frozen gates)
DEFAULT_MARKET_MAX_AGE_CAL_DAYS = 7
DEFAULT_E22_MAX_AGE_CAL_DAYS = 45
DEFAULT_SHADOW_MAX_AGE_CAL_DAYS = 45


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _file_mtime_utc(path: Path) -> datetime | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _parse_ymd(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _age_days(then: date | datetime | None, now: datetime) -> int | None:
    if then is None:
        return None
    if isinstance(then, datetime):
        then_d = then.astimezone(timezone.utc).date()
    else:
        then_d = then
    return (now.date() - then_d).days


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def live_market_tip(path: Path | None = None) -> dict[str, Any]:
    path = LIVE_MARKET if path is None else path
    out: dict[str, Any] = {
        "path": _rel(path) if path.exists() else str(path),
        "exists": path.exists(),
        "tip_date": None,
        "age_cal_days": None,
    }
    if not path.exists():
        return out
    # Stream only the date column for tip — avoid loading full OHLCV into memory.
    tip: str | None = None
    with path.open(newline="", encoding="utf-8") as fh:
        header = fh.readline()
        if not header:
            return out
        cols = [c.strip() for c in header.strip().split(",")]
        try:
            di = cols.index("date")
        except ValueError:
            out["error"] = "no date column"
            return out
        for line in fh:
            parts = line.rstrip("\n").split(",")
            if len(parts) > di and parts[di]:
                tip = parts[di].strip()
    out["tip_date"] = tip
    out["age_cal_days"] = _age_days(_parse_ymd(tip), _utc_now())
    return out


def e22_freshness(
    events: Path | None = None,
    fetch_status: Path | None = None,
    kpi: Path | None = None,
) -> dict[str, Any]:
    events = E22_EVENTS if events is None else events
    fetch_status = E22_FETCH_STATUS if fetch_status is None else fetch_status
    kpi = E22_KPI if kpi is None else kpi
    now = _utc_now()
    mtime = _file_mtime_utc(events)
    row: dict[str, Any] = {
        "events_path": _rel(events) if events.exists() else str(events),
        "events_exists": events.exists(),
        "events_mtime_utc": mtime.isoformat() if mtime else None,
        "events_age_cal_days": _age_days(mtime, now),
        "fetch_status_path": _rel(fetch_status) if fetch_status.exists() else str(fetch_status),
        "fetch_status_exists": fetch_status.exists(),
        "fetch_status": None,
        "kpi_ok": None,
    }
    if fetch_status.exists():
        try:
            st = json.loads(fetch_status.read_text(encoding="utf-8"))
            row["fetch_status"] = st.get("status")
            row["fetch_rows"] = st.get("rows")
        except (OSError, json.JSONDecodeError) as exc:
            row["fetch_status_error"] = str(exc)
    if kpi.exists():
        try:
            k = json.loads(kpi.read_text(encoding="utf-8"))
            row["kpi_ok"] = k.get("kpi_ok")
            row["kpi_flags"] = k.get("flags") or []
        except (OSError, json.JSONDecodeError) as exc:
            row["kpi_error"] = str(exc)
    return row


def shadow_freshness(path: Path | None = None) -> dict[str, Any]:
    path = SHADOW if path is None else path
    now = _utc_now()
    row: dict[str, Any] = {
        "path": _rel(path) if path.exists() else str(path),
        "exists": path.exists(),
        "all_ok": None,
        "generated_at_utc": None,
        "age_cal_days": None,
        "n_drift": None,
    }
    if not path.exists():
        return row
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        row["error"] = str(exc)
        return row
    gen = d.get("generated_at_utc") or d.get("generated_at")
    row["generated_at_utc"] = gen
    row["all_ok"] = d.get("all_ok")
    row["n_drift"] = d.get("n_drift")
    gen_dt: datetime | None
    try:
        gen_dt = datetime.fromisoformat(str(gen).replace("Z", "+00:00")) if gen else None
    except ValueError:
        gen_dt = None
    row["age_cal_days"] = _age_days(gen_dt, now)
    return row


def collect_freshness(
    *,
    market_max_age: int = DEFAULT_MARKET_MAX_AGE_CAL_DAYS,
    e22_max_age: int = DEFAULT_E22_MAX_AGE_CAL_DAYS,
    shadow_max_age: int = DEFAULT_SHADOW_MAX_AGE_CAL_DAYS,
) -> dict[str, Any]:
    market = live_market_tip()
    e22 = e22_freshness()
    shadow = shadow_freshness()
    warnings: list[str] = []
    stale = False

    if not market["exists"]:
        warnings.append("live_market_missing")
        stale = True
    elif market["age_cal_days"] is None:
        warnings.append("live_market_tip_unparsed")
        stale = True
    elif market["age_cal_days"] > market_max_age:
        warnings.append(
            f"live_market_tip_stale>{market_max_age}d (age={market['age_cal_days']})"
        )
        stale = True

    if not e22["events_exists"]:
        warnings.append("e22_events_missing")
        stale = True
    elif e22["events_age_cal_days"] is not None and e22["events_age_cal_days"] > e22_max_age:
        warnings.append(
            f"e22_events_mtime_stale>{e22_max_age}d (age={e22['events_age_cal_days']})"
        )
        stale = True
    if e22.get("fetch_status") not in (None, "PASS"):
        warnings.append(f"e22_fetch_status={e22.get('fetch_status')}")
        # Non-PASS is a warning; do not auto-stale pack unless missing events.
    if e22.get("kpi_ok") is False:
        warnings.append("e22_kpi_not_ok")

    if shadow["exists"]:
        if shadow.get("all_ok") is False:
            warnings.append("data_source_shadow_all_ok=false")
            stale = True
        elif (
            shadow.get("age_cal_days") is not None
            and shadow["age_cal_days"] > shadow_max_age
        ):
            warnings.append(
                f"data_source_shadow_stale>{shadow_max_age}d (age={shadow['age_cal_days']})"
            )
    else:
        warnings.append("data_source_shadow_missing")

    payload = {
        "generated_at_utc": _utc_now().isoformat(),
        "label": "MONTH_END_DATA_FRESHNESS",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "thresholds": {
            "market_max_age_cal_days": market_max_age,
            "e22_max_age_cal_days": e22_max_age,
            "shadow_max_age_cal_days": shadow_max_age,
        },
        "live_market": market,
        "e22": e22,
        "data_source_shadow": shadow,
        "warnings": warnings,
        "note": (
            "Month-end cadence = paper pack. Data re-fetch (E22 FinMind etc.) stays "
            "on-demand; this snapshot only reports tip/age. Soft-Frozen untouched."
        ),
        "remediation": {
            "stale_market": (
                "Run weekday forward job / ensure forward/e21/live_market.csv tip is current."
            ),
            "stale_e22": (
                "On-demand: workflow `v412e22-dividend-events` "
                "(pack does not auto-fetch dividends)."
            ),
            "stale_ledgers": (
                "Formal month-end: `python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers`."
            ),
            "shadow": "Re-run `python3 scripts/data_source_shadow_reconcile.py` (ops only).",
        },
    }
    # ``stale`` reserved for callers that want a pre-split signal; hard/soft split below.
    payload["_stale_hint"] = stale
    return _finalize_fresh_ok(payload)


def _finalize_fresh_ok(payload: dict[str, Any]) -> dict[str, Any]:
    """Hard: market tip + e22 events presence/age + shadow fail-if-present.

    Soft: missing shadow artifact, e22 kpi flags, shadow age, non-PASS fetch_status.
    """
    warnings = list(payload.get("warnings") or [])
    hard = [
        w
        for w in warnings
        if w.startswith("live_market_")
        or w.startswith("e22_events_")
        or w.startswith("data_source_shadow_all_ok")
    ]
    payload["fresh_ok"] = len(hard) == 0
    payload["hard_warnings"] = hard
    payload["soft_warnings"] = [w for w in warnings if w not in hard]
    payload.pop("_stale_hint", None)
    return payload


def render_md(payload: dict[str, Any]) -> str:
    m = payload["live_market"]
    e = payload["e22"]
    s = payload["data_source_shadow"]
    lines = [
        "# Month-End Data Freshness",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **RESEARCH / OPS** — Soft-Frozen unchanged; no live wire; no auto-fetch.",
        "",
        f"- Fresh OK (hard): **{payload['fresh_ok']}**",
        f"- Live market tip: **{m.get('tip_date')}** (age **{m.get('age_cal_days')}** cal days)",
        f"- E22 events mtime age: **{e.get('events_age_cal_days')}** cal days · fetch_status **{e.get('fetch_status')}** · kpi_ok **{e.get('kpi_ok')}**",
        f"- Shadow reconcile all_ok: **{s.get('all_ok')}** (age **{s.get('age_cal_days')}** cal days)",
        "",
        "## Hard warnings",
        "",
    ]
    hard = payload.get("hard_warnings") or []
    if hard:
        lines.extend(f"- {w}" for w in hard)
    else:
        lines.append("- None")
    lines += ["", "## Soft warnings", ""]
    soft = payload.get("soft_warnings") or []
    if soft:
        lines.extend(f"- {w}" for w in soft)
    else:
        lines.append("- None")
    lines += [
        "",
        "## Cadence vs fetch",
        "",
        "- **Month-end pack** = paper monitors / recon / KPI (this snapshot).",
        "- **Data re-fetch** (E22 etc.) = on-demand; not the pack default.",
        "- **Formal month-end** should use `--refresh-ledgers` (rebuild observe NAVs).",
        "",
        "See `research/ops/MONTH_END_PACK_FRESHNESS.md`.",
        "",
    ]
    return "\n".join(lines)


def write_artifacts(payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(payload) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Month-end data freshness snapshot (ops only)")
    ap.add_argument("--market-max-age-days", type=int, default=DEFAULT_MARKET_MAX_AGE_CAL_DAYS)
    ap.add_argument("--e22-max-age-days", type=int, default=DEFAULT_E22_MAX_AGE_CAL_DAYS)
    ap.add_argument("--shadow-max-age-days", type=int, default=DEFAULT_SHADOW_MAX_AGE_CAL_DAYS)
    ap.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Exit 2 when hard freshness checks fail.",
    )
    args = ap.parse_args(argv)
    payload = collect_freshness(
        market_max_age=args.market_max_age_days,
        e22_max_age=args.e22_max_age_days,
        shadow_max_age=args.shadow_max_age_days,
    )
    write_artifacts(payload)
    print(json.dumps(payload, indent=2))
    if args.fail_on_stale and not payload["fresh_ok"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
