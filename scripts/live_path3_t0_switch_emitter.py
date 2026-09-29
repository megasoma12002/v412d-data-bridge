#!/usr/bin/env python3
"""Path3 COMP↔SAT switch order emitter — PREP (flag OFF).

Builds ``carve_out_id=T0_CARVE_FIN_SAT_SWITCH`` tagged Soft-Frozen order rows
for Exact T+0 same-bar fill allowlist (0k9u). Soft-Frozen Exact T+1 KEEP
elsewhere · Path3 observe KEEP · cutover BLOCKED · no broker write.

Emit stays **OFF** until dedicated ACCEPT flips
``LIVE.live_t0_carve_fin_sat_switch_emit``. Full COMP/SAT sleeve weight engines
are **not** wired here — ``maybe_emit_switch_orders`` fail-closes without an
explicit ``delta_shares`` plan (cutover / Stage-B scope).
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from t0_carve_fin_sat_switch import (
    CARVE_OUT_ID,
    MECHANISM,
    ORDER_TAG_COL,
    tag_order,
)
from tw_share_lots import BOARD_LOT, board_lots

ROOT = Path(__file__).resolve().parents[1]
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"
SIGNAL_CSV = ROOT / "repro/fin-sat-path3-t0-dual-paper-observe/outputs/p3_t0_state_signal.csv"

THETA = 0.01
BOOK_COMP = "COMP_H150_x_A20"
BOOK_SAT = "SAT_A20_RELAX"

# Human ACCEPT line to enable live Path3 tagged switch emission (not yet executed).
ACCEPT_EMIT_LINE = (
    "ACCEPT Live Path3 switch emitter: T0_CARVE_FIN_SAT_SWITCH tagged orders "
    "(P3_T0_STATE · Soft-Frozen Exact T+1 KEEP elsewhere · cutover still BLOCKED)"
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_emit_authorized() -> bool:
    """True only after ACCEPT flips LiveConfig emit flag (default False)."""
    try:
        from live_config import LIVE

        return bool(getattr(LIVE, "live_t0_carve_fin_sat_switch_emit", False))
    except Exception:
        return False


def make_path3_switch_order_id(*, signal_date: Any, code: str, side: str) -> str:
    """Stable Path3 switch ``order_id`` — distinct from Soft-Frozen day keys.

    Soft-Frozen uses ``{date}-{code}-{side}``; Path3 appends ``-P3T0`` so
    same-day sleeve + switch do not collide under append-immutable first-wins.
    """
    if hasattr(signal_date, "isoformat"):
        d = str(signal_date.isoformat())[:10]
    else:
        d = str(signal_date).strip()[:10]
    return f"{d}-{str(code).strip()}-{str(side).strip().upper()}-P3T0"


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)[["date", "nav"]].assign(
        nav=lambda x: x["nav"].astype(float)
    )


def _trail(r: pd.Series, n: int = 63) -> pd.Series:
    return (1.0 + r).rolling(n, min_periods=n).apply(lambda x: float(np.prod(x) - 1.0), raw=True)


def build_sat_lead_signal(
    comp: pd.DataFrame | None = None,
    sat: pd.DataFrame | None = None,
    *,
    theta: float = THETA,
) -> pd.DataFrame:
    """Causal trail_rel_63 → SAT_LEAD (same rule as P3_T0_STATE observe)."""
    if comp is None:
        comp = _load_nav(COMP_NAV)
    if sat is None:
        sat = _load_nav(SAT_NAV)
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    rc = m["nav_c"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    rel = rc - rs
    trail = _trail(rel, 63)
    sat_lead = (trail <= -float(theta)).fillna(False).astype(bool)
    w = sat_lead.astype(float)
    prev = w.shift(1).fillna(0.0)
    flip = (w - prev).abs() > 1e-12
    book = np.where(sat_lead.to_numpy(), BOOK_SAT, BOOK_COMP)
    return pd.DataFrame(
        {
            "date": m["date"].to_numpy(),
            "trail_rel_63": trail.to_numpy(),
            "sat_lead": sat_lead.to_numpy(),
            "w_sat": w.to_numpy(),
            "flip": flip.to_numpy(),
            "book": book,
            "book_prev": np.where(prev.to_numpy() > 0.5, BOOK_SAT, BOOK_COMP),
        }
    )


def load_or_build_signal(*, prefer_observe_csv: bool = True) -> pd.DataFrame:
    """Prefer dual-paper observe signal CSV; else rebuild from COMP/SAT NAV."""
    if prefer_observe_csv and SIGNAL_CSV.exists():
        sig = pd.read_csv(SIGNAL_CSV)
        sig["date"] = pd.to_datetime(sig["date"])
        if "sat_lead" not in sig.columns and "w_sat" in sig.columns:
            sig["sat_lead"] = sig["w_sat"].astype(float) > 0.5
        if "w_sat" not in sig.columns and "sat_lead" in sig.columns:
            sig["w_sat"] = sig["sat_lead"].astype(float)
        if "flip" not in sig.columns:
            w = sig["w_sat"].astype(float)
            sig["flip"] = (w - w.shift(1).fillna(0.0)).abs() > 1e-12
        if "book" not in sig.columns:
            lead = sig["sat_lead"].astype(bool)
            sig["book"] = np.where(lead, BOOK_SAT, BOOK_COMP)
        if "book_prev" not in sig.columns:
            prev = sig["w_sat"].astype(float).shift(1).fillna(0.0)
            sig["book_prev"] = np.where(prev > 0.5, BOOK_SAT, BOOK_COMP)
        return sig.sort_values("date").reset_index(drop=True)
    return build_sat_lead_signal()


def switch_meta_for_asof(asof: pd.Timestamp | str, signal: pd.DataFrame | None = None) -> dict[str, Any]:
    """Path3 switch meta on ``asof`` (flip / book / SAT_LEAD)."""
    asof = pd.Timestamp(asof).normalize()
    sig = load_or_build_signal() if signal is None else signal
    sub = sig[pd.to_datetime(sig["date"]) <= asof]
    if sub.empty:
        return {
            "asof": asof.date().isoformat(),
            "ok": False,
            "reason": "no_signal_asof",
            "flip": False,
            "carve_out_id": CARVE_OUT_ID,
            "mechanism": MECHANISM,
        }
    row = sub.iloc[-1]
    flip = bool(row.get("flip", False))
    sat_lead = bool(row.get("sat_lead", False))
    return {
        "asof": asof.date().isoformat(),
        "ok": True,
        "flip": flip,
        "sat_lead": sat_lead,
        "w_sat": float(row.get("w_sat", 0.0) or 0.0),
        "book": str(row.get("book") or (BOOK_SAT if sat_lead else BOOK_COMP)),
        "book_prev": str(row.get("book_prev") or BOOK_COMP),
        "trail_rel_63": None
        if pd.isna(row.get("trail_rel_63"))
        else float(row.get("trail_rel_63")),
        "carve_out_id": CARVE_OUT_ID,
        "mechanism": MECHANISM,
        "theta": THETA,
    }


def build_tagged_switch_order_rows(
    *,
    signal_date: date | str,
    delta_shares: Mapping[str, float] | Sequence[tuple[str, float]],
    prices: Mapping[str, float],
    make_order_id: Callable[..., str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Board-lot tagged Path3 switch orders from signed share deltas.

    Positive delta → BUY; negative → SELL. Rows always carry ``carve_out_id``.
    """
    oid_fn = make_order_id or make_path3_switch_order_id
    if hasattr(signal_date, "isoformat"):
        sig_d = signal_date  # date
        sig_iso = signal_date.isoformat()[:10]
    else:
        sig_iso = str(signal_date).strip()[:10]
        sig_d = date.fromisoformat(sig_iso)

    if isinstance(delta_shares, Mapping):
        items = list(delta_shares.items())
    else:
        items = [(str(c), float(q)) for c, q in delta_shares]

    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for code, raw_delta in items:
        code = str(code).strip()
        delta = float(raw_delta)
        if abs(delta) < 1e-9:
            continue
        px = float(prices.get(code) or 0.0)
        if px <= 0:
            skipped.append({"code": code, "reason": "missing_px", "delta": delta})
            continue
        qty = board_lots(abs(delta))
        if qty < BOARD_LOT:
            skipped.append({"code": code, "reason": "below_lot", "delta": delta})
            continue
        side = "BUY" if delta > 0 else "SELL"
        raw = {
            "order_id": oid_fn(signal_date=sig_d, code=code, side=side),
            "signal_date": sig_iso,
            "code": code,
            "side": side,
            "quantity": int(qty),
            "reference_close": px,
            "path3_switch": True,
            "path3_book_pair": f"{BOOK_COMP}|{BOOK_SAT}",
        }
        rows.append(tag_order(raw))

    rows.sort(key=lambda o: (0 if o["side"] == "SELL" else 1, o["code"]))
    meta = {
        "carve_out_id": CARVE_OUT_ID,
        "mechanism": MECHANISM,
        "n_orders": len(rows),
        "n_skipped": len(skipped),
        "skipped": skipped,
        "signal_date": sig_iso,
    }
    return rows, meta


def maybe_emit_switch_orders(
    *,
    asof: pd.Timestamp | str,
    prices: Mapping[str, float],
    delta_shares: Mapping[str, float] | Sequence[tuple[str, float]] | None = None,
    authorized: bool | None = None,
    signal: pd.DataFrame | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Pipeline entry: emit tagged switch orders only when authorized + flip + deltas.

    Fail-closed defaults:
    - emit flag OFF → empty
    - no flip → empty
    - ``delta_shares`` missing → empty (``weight_engine_not_wired``)
    """
    auth = is_emit_authorized() if authorized is None else bool(authorized)
    meta: dict[str, Any] = {
        "enabled": auth,
        "carve_out_id": CARVE_OUT_ID,
        "mechanism": MECHANISM,
        "n_orders": 0,
    }
    if not auth:
        meta["reason"] = "emit_flag_off"
        return [], meta

    sw = switch_meta_for_asof(asof, signal=signal)
    meta["switch"] = sw
    if not sw.get("ok"):
        meta["reason"] = sw.get("reason") or "signal_unavailable"
        return [], meta
    if not sw.get("flip"):
        meta["reason"] = "no_flip"
        return [], meta
    if delta_shares is None:
        meta["reason"] = "weight_engine_not_wired"
        meta["note"] = (
            "PREP: pass explicit delta_shares when COMP↔SAT sleeve engines are wired; "
            "do not invent Path3 quantities from Soft-Frozen alone"
        )
        return [], meta

    asof_ts = pd.Timestamp(asof).normalize()
    rows, build_meta = build_tagged_switch_order_rows(
        signal_date=asof_ts.date(),
        delta_shares=delta_shares,
        prices=prices,
    )
    meta.update(build_meta)
    meta["reason"] = "emitted" if rows else "empty_after_lot_filter"
    return rows, meta


def propose_switch_ledger(
    signal: pd.DataFrame | None = None,
    *,
    out_path: Path | None = None,
) -> pd.DataFrame:
    """Shadow ledger of historical Path3 flips (intent only — no live quantities)."""
    sig = load_or_build_signal() if signal is None else signal.copy()
    flips = sig[sig["flip"].astype(bool)].copy()
    if flips.empty:
        out = pd.DataFrame(
            columns=[
                "date",
                "book_prev",
                "book",
                "sat_lead",
                "w_sat",
                "trail_rel_63",
                "carve_out_id",
                "mechanism",
                "status",
            ]
        )
    else:
        out = pd.DataFrame(
            {
                "date": pd.to_datetime(flips["date"]).dt.strftime("%Y-%m-%d"),
                "book_prev": flips["book_prev"].astype(str).to_numpy(),
                "book": flips["book"].astype(str).to_numpy(),
                "sat_lead": flips["sat_lead"].astype(bool).to_numpy(),
                "w_sat": flips["w_sat"].astype(float).to_numpy(),
                "trail_rel_63": flips["trail_rel_63"].to_numpy(),
                "carve_out_id": CARVE_OUT_ID,
                "mechanism": MECHANISM,
                "status": "PROPOSED_SHADOW_NO_LIVE_QTY",
            }
        )
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(out_path, index=False)
    return out


def main() -> int:
    """Write shadow proposed-switch ledger under repro (no live / no broker)."""
    out_dir = ROOT / "repro" / "fin-sat-path3-t0-emitter-prep" / "outputs"
    rep = ROOT / "repro" / "fin-sat-path3-t0-emitter-prep" / "reports"
    ops = ROOT / "research" / "ops"
    for d in (out_dir, rep, ops):
        d.mkdir(parents=True, exist_ok=True)

    sig = load_or_build_signal()
    sig.to_csv(out_dir / "p3_t0_emitter_signal.csv", index=False)
    ledger = propose_switch_ledger(sig, out_path=out_dir / "path3_t0_proposed_switches.csv")
    generated = _utc()
    summary = {
        "label": f"LIVE_PATH3_T0_SWITCH_EMITTER_PREP_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "status": "PREP_OPERATING",
        "emit_flag": is_emit_authorized(),
        "fill_flag_note": "separate LIVE.live_t0_carve_fin_sat_switch_fill (0k9u)",
        "carve_out_id": CARVE_OUT_ID,
        "mechanism": MECHANISM,
        "n_signal_days": int(len(sig)),
        "n_proposed_flips": int(len(ledger)),
        "pct_days_sat": round(float(sig["w_sat"].mean()) * 100, 2) if len(sig) else 0.0,
        "accept_emit_line": ACCEPT_EMIT_LINE,
        "live_wire": False,
        "cutover": "BLOCKED",
        "weight_engine": "not_wired",
    }
    (out_dir / "emitter_prep_summary.json").write_text(
        __import__("json").dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(__import__("json").dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
