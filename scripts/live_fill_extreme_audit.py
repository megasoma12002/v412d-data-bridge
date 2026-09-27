#!/usr/bin/env python3
"""Live tip fill extreme + mechanism audit (observe only).

Charter: research/ops/LIVE_FILL_EXTREME_AUDIT_CHARTER.md
Uses forward/e21 fills + live_market; Soft-Frozen KEEP; no tip rewrite.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import e16_soft_frozen_base as soft
import live_cool_c8_cutover as cool_cut
import live_dh_fuse_cutover as fuse_cut
from e16_soft_frozen_base import FIN, TEL
from live_config import DIV_PATH, KD_OPT
from within_sleeve_alloc import build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "forward" / "e21"
REPRO = ROOT / "repro" / "live-fill-extreme-audit"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "LIVE_FILL_EXTREME_AUDIT_CHARTER"
SCREEN_ID = "LIVE_FILL_EXTREME_AUDIT_SCREEN"
DECISION_ID = "LIVE_FILL_EXTREME_AUDIT_DECISION_PACK"
N_GRID = (5, 21)
CLIP_EPS = 1e-4


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sleeve(code: str) -> str:
    c = str(code)
    if c in FIN:
        return "FIN"
    if c in TEL:
        return "TEL"
    if c == "0050":
        return "0050"
    if c in ("00631L", "00632R"):
        return "SAT"
    return "OTHER"


def _in_kd_season(dt: pd.Timestamp) -> bool:
    ss = tuple(KD_OPT["season_start"])
    se = tuple(KD_OPT["season_end"])
    md = (int(dt.month), int(dt.day))
    return ss <= md <= se


def _ohlc_panel_raw(market: pd.DataFrame, code: str) -> pd.DataFrame:
    """Raw (unadjusted) OHLC — prefer ``_ohlc_panel`` for extreme audits."""
    m = market[market["code"].astype(str) == str(code)].copy()
    m["date"] = pd.to_datetime(m["date"]).dt.normalize()
    m = m.drop_duplicates("date").sort_values("date").set_index("date")
    for col in ("open", "high", "low", "close"):
        if col not in m.columns:
            m[col] = np.nan
    if m["high"].isna().all() and "adj_close" in m.columns:
        m["high"] = m["adj_close"]
        m["low"] = m["adj_close"]
        m["close"] = m["adj_close"]
        m["open"] = m["adj_close"]
    return m[["open", "high", "low", "close"]].astype(float)


def _ohlc_panel(market: pd.DataFrame, code: str) -> pd.DataFrame:
    """Split-adjusted OHLC via ``adj_close/close`` (authoritative for extreme audits).

    Raw fills are scaled onto this plane with ``_fill_px_on_panel`` so ±N windows
    spanning corporate actions (e.g. 0050 2025-06-18 ~4:1) stay continuous.
    See ``ETF0050_BUY_FILL_STAGEA`` ``METRIC_ARTIFACT_ONLY``.
    """
    m = market[market["code"].astype(str) == str(code)].copy()
    m["date"] = pd.to_datetime(m["date"]).dt.normalize()
    m = m.drop_duplicates("date").sort_values("date").set_index("date")
    for col in ("open", "high", "low", "close", "adj_close"):
        if col not in m.columns:
            m[col] = np.nan
    close = m["close"].astype(float)
    adj = m["adj_close"].astype(float)
    if adj.notna().any() and close.notna().any():
        factor = adj / close.replace(0, np.nan)
        factor = factor.ffill().bfill().fillna(1.0)
        out = pd.DataFrame(index=m.index)
        for col in ("open", "high", "low", "close"):
            out[col] = m[col].astype(float) * factor
        out["close"] = adj.where(adj.notna(), out["close"])
        return out
    return _ohlc_panel_raw(market, code)


def _fill_px_on_panel(
    raw_px: float,
    fill_d: pd.Timestamp,
    raw_panel: pd.DataFrame,
    adj_panel: pd.DataFrame,
) -> float:
    """Map a raw fill price onto the adj OHLC plane for the fill day."""
    if fill_d in adj_panel.index and fill_d in raw_panel.index:
        raw_c = float(raw_panel.loc[fill_d, "close"])
        adj_c = float(adj_panel.loc[fill_d, "close"])
        if raw_c > 0 and np.isfinite(raw_c) and np.isfinite(adj_c):
            return float(raw_px) * (adj_c / raw_c)
    return float(raw_px)


def _window_ext(
    panel: pd.DataFrame, center: pd.Timestamp, n: int
) -> tuple[float | None, float | None, int]:
    if panel.empty:
        return None, None, 0
    idx = panel.index
    # n trading days each side via positional neighborhood
    if center not in idx:
        prior = idx[idx <= center]
        if len(prior) == 0:
            return None, None, 0
        center = prior[-1]
    loc = int(idx.get_loc(center))
    lo_i = max(0, loc - int(n))
    hi_i = min(len(idx) - 1, loc + int(n))
    sub = panel.iloc[lo_i : hi_i + 1]
    if sub.empty:
        return None, None, 0
    return float(sub["low"].min()), float(sub["high"].max()), int(len(sub))


def _clip_binding(fin_w: float, tel_w: float, etf_w: float) -> list[str]:
    tags: list[str] = []
    flo, fhi = soft.SOFT_FROZEN_FIN_LO, soft.SOFT_FROZEN_FIN_HI
    # tip period may still be prior FIN hi 0.90 before flip asof
    if fin_w <= flo + CLIP_EPS:
        tags.append("CLIP_FIN_LO")
    if fin_w >= fhi - CLIP_EPS or fin_w >= soft.SOFT_FROZEN_PRIOR_FIN_HI - CLIP_EPS:
        tags.append("CLIP_FIN_HI")
    if tel_w <= soft.SOFT_FROZEN_TEL_LO + CLIP_EPS:
        tags.append("CLIP_TEL_LO")
    if tel_w >= soft.SOFT_FROZEN_TEL_HI - CLIP_EPS:
        tags.append("CLIP_TEL_HI")
    if etf_w <= soft.SOFT_FROZEN_ETF_LO + CLIP_EPS:
        tags.append("CLIP_ETF_LO")
    if etf_w >= soft.SOFT_FROZEN_ETF_HI - CLIP_EPS:
        tags.append("CLIP_ETF_HI")
    return tags


def _agg_from_extremes(df: pd.DataFrame, n: int) -> dict[str, Any]:
    key = f"n{n}"
    dists = []
    for _, r in df.iterrows():
        e = r["extremes"] if isinstance(r["extremes"], dict) else {}
        cell = e.get(key) or {}
        if cell.get("ok"):
            dists.append(float(cell["dist_pct"]))
    if not dists:
        return {"n": 0}
    a = np.asarray(dists, dtype=float)
    return {
        "n": int(len(a)),
        "mean_dist_pct": round(float(a.mean()), 4),
        "median_dist_pct": round(float(np.median(a)), 4),
        "p90_dist_pct": round(float(np.quantile(a, 0.90)), 4),
        "share_within_1pct": round(float((a <= 1.0).mean()), 4),
        "share_within_3pct": round(float((a <= 3.0).mean()), 4),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    fills_path = STATE / "fills.csv"
    sig_path = STATE / "signals.csv"
    mkt_path = STATE / "live_market.csv"
    assert fills_path.exists(), fills_path
    assert mkt_path.exists(), mkt_path

    fills = pd.read_csv(fills_path, dtype={"code": str})
    fills["signal_date"] = pd.to_datetime(fills["signal_date"]).dt.normalize()
    fills["fill_date"] = pd.to_datetime(fills["fill_date"]).dt.normalize()
    signals = (
        pd.read_csv(sig_path)
        if sig_path.exists()
        else pd.DataFrame()
    )
    if not signals.empty:
        signals["date"] = pd.to_datetime(signals["date"]).dt.normalize()
        sig_map = signals.set_index("date")
    else:
        sig_map = pd.DataFrame()

    market = pd.read_csv(mkt_path, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"]).dt.normalize()
    dividends = (
        pd.read_csv(DIV_PATH, dtype={"code": str})
        if Path(DIV_PATH).exists()
        else pd.DataFrame()
    )

    print("building cool (reconstructed COOL_c8 twin) ...", flush=True)
    fuse_nav, _ = fuse_cut.build_fuse_offense_nav(market, dividends)
    cool = cool_cut.build_cool_exposure_from_offense(market, fuse_nav)
    cool.to_frame("cool_exposure").to_csv(OUT / "cool_c8_reconstructed.csv")

    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )

    panels = {c: _ohlc_panel(market, c) for c in sorted(fills["code"].unique())}
    panels_raw = {
        c: _ohlc_panel_raw(market, c) for c in sorted(fills["code"].unique())
    }

    rows: list[dict[str, Any]] = []
    for _, f in fills.iterrows():
        code = str(f["code"])
        side = str(f["side"]).upper()
        px_raw = float(f["fill_price"])
        sig_d = pd.Timestamp(f["signal_date"])
        fill_d = pd.Timestamp(f["fill_date"])
        sleeve = _sleeve(code)
        panel = panels.get(code, pd.DataFrame())
        raw_panel = panels_raw.get(code, pd.DataFrame())
        px = _fill_px_on_panel(px_raw, fill_d, raw_panel, panel)

        # tip defense (DH historical)
        dh_exp = None
        fin_w = tel_w = etf_w = None
        if not sig_map.empty and sig_d in sig_map.index:
            srow = sig_map.loc[sig_d]
            if isinstance(srow, pd.DataFrame):
                srow = srow.iloc[-1]
            if "dh_exposure" in srow.index and pd.notna(srow["dh_exposure"]):
                dh_exp = float(srow["dh_exposure"])
            fin_w = float(srow["e16_financial"]) if "e16_financial" in srow.index else None
            tel_w = float(srow["e16_telecom"]) if "e16_telecom" in srow.index else None
            etf_w = float(srow["e16_0050"]) if "e16_0050" in srow.index else None

        cool_exp = None
        if sig_d in cool.index and pd.notna(cool.loc[sig_d]):
            cool_exp = float(cool.loc[sig_d])
        elif len(cool.dropna()):
            prior = cool.index[cool.index <= sig_d]
            if len(prior):
                cool_exp = float(cool.loc[prior[-1]])

        mech: list[str] = ["T1_ALWAYS"]
        # T+1 drag vs signal-day extreme (adj OHLC plane)
        t1_drag_pp = None
        if not panel.empty and sig_d in panel.index:
            s_low = float(panel.loc[sig_d, "low"])
            s_high = float(panel.loc[sig_d, "high"])
            if side == "BUY" and s_low > 0:
                t1_drag_pp = (px - s_low) / s_low * 100.0
            elif side == "SELL" and s_high > 0:
                t1_drag_pp = (s_high - px) / s_high * 100.0
            mech.append("T1_DRAG")
        if dh_exp is not None and dh_exp < 1.0 - 1e-12:
            mech.append("DEFENSE_DH")
        if cool_exp is not None and cool_exp < 1.0 - 1e-12:
            mech.append("DEFENSE_COOL_CF")
        if fin_w is not None and tel_w is not None and etf_w is not None:
            for t in _clip_binding(fin_w, tel_w, etf_w):
                mech.append(t)
        if sleeve == "FIN":
            if not _in_kd_season(sig_d):
                mech.append("KD_OFFSEASON")
            if side == "BUY" and sig_d in buy_ok.index and code in buy_ok.columns:
                if not bool(buy_ok.loc[sig_d, code]):
                    mech.append("KD_BUY_BLOCK")

        ext: dict[str, Any] = {}
        for n in N_GRID:
            lo, hi, nobs = _window_ext(panel, fill_d, n)
            if lo is None or hi is None or lo <= 0 or hi <= 0:
                ext[f"n{n}"] = {"ok": False}
                continue
            if side == "BUY":
                dist = (px - lo) / lo * 100.0
                kind = "above_low_pct"
            else:
                dist = (hi - px) / hi * 100.0
                kind = "below_high_pct"
            # 0 = perfect extreme, larger = farther from ideal
            ext[f"n{n}"] = {
                "ok": True,
                "kind": kind,
                "dist_pct": round(float(dist), 4),
                "low": round(lo, 6),
                "high": round(hi, 6),
                "n_bars": nobs,
            }

        rows.append(
            {
                "fill_id": f["fill_id"],
                "signal_date": sig_d.date().isoformat(),
                "fill_date": fill_d.date().isoformat(),
                "code": code,
                "sleeve": sleeve,
                "side": side,
                "quantity": int(f["quantity"]),
                "fill_price": px_raw,
                "fill_price_adj": round(float(px), 6),
                "ohlc_basis": "adj_close_scaled",
                "t1_drag_vs_signal_ext_pct": None
                if t1_drag_pp is None
                else round(float(t1_drag_pp), 4),
                "dh_exposure": dh_exp,
                "cool_exposure_cf": None if cool_exp is None else round(float(cool_exp), 6),
                "defense_dh": bool(dh_exp is not None and dh_exp < 1.0 - 1e-12),
                "defense_cool_cf": bool(cool_exp is not None and cool_exp < 1.0 - 1e-12),
                "e16_financial": fin_w,
                "e16_telecom": tel_w,
                "e16_0050": etf_w,
                "mechanisms": mech,
                "extremes": ext,
            }
        )

    detail = pd.DataFrame(rows)
    detail.to_csv(OUT / "fill_extreme_detail.csv", index=False)
    (OUT / "fill_extreme_detail.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )

    strata = []
    for sleeve in ("FIN", "TEL", "0050", "ALL"):
        for side in ("BUY", "SELL", "ALL"):
            for def_lab in ("ALL", "DH_DEFEND", "DH_OFF", "COOL_CF_DEFEND", "COOL_CF_OFF"):
                sub = detail
                if sleeve != "ALL":
                    sub = sub[sub["sleeve"] == sleeve]
                if side != "ALL":
                    sub = sub[sub["side"] == side]
                if def_lab == "DH_DEFEND":
                    sub = sub[sub["defense_dh"].fillna(False)]
                elif def_lab == "DH_OFF":
                    sub = sub[~sub["defense_dh"].fillna(False)]
                elif def_lab == "COOL_CF_DEFEND":
                    sub = sub[sub["defense_cool_cf"].fillna(False)]
                elif def_lab == "COOL_CF_OFF":
                    sub = sub[~sub["defense_cool_cf"].fillna(False)]
                if sub.empty:
                    continue
                strata.append(
                    {
                        "sleeve": sleeve,
                        "side": side,
                        "defense": def_lab,
                        "n_fills": int(len(sub)),
                        "n5": _agg_from_extremes(sub, 5),
                        "n21": _agg_from_extremes(sub, 21),
                        "mean_t1_drag_pct": round(
                            float(
                                pd.to_numeric(
                                    sub["t1_drag_vs_signal_ext_pct"], errors="coerce"
                                ).mean()
                            ),
                            4,
                        )
                        if sub["t1_drag_vs_signal_ext_pct"].notna().any()
                        else None,
                    }
                )

    mech_counts: dict[str, int] = {}
    for r in rows:
        for m in r["mechanisms"]:
            mech_counts[m] = mech_counts.get(m, 0) + 1

    # Binding summary narrative numbers
    n = len(rows)
    n_buy = int((detail["side"] == "BUY").sum())
    n_sell = int((detail["side"] == "SELL").sum())
    core = _agg_from_extremes(detail, 5)
    core21 = _agg_from_extremes(detail, 21)

    verdict = "FILL_EXTREME_AUDIT_DONE"
    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "ohlc_basis": "adj_close_scaled",
        "n_fills": n,
        "n_buy": n_buy,
        "n_sell": n_sell,
        "fill_date_min": str(detail["fill_date"].min()),
        "fill_date_max": str(detail["fill_date"].max()),
        "codes": sorted(detail["code"].unique().tolist()),
        "overall_n5": core,
        "overall_n21": core21,
        "mean_t1_drag_pct": round(
            float(pd.to_numeric(detail["t1_drag_vs_signal_ext_pct"], errors="coerce").mean()),
            4,
        ),
        "mechanism_fill_counts": dict(sorted(mech_counts.items(), key=lambda x: -x[1])),
        "strata": strata,
        "notes": [
            "Tip fill window predates COOL live ACCEPT; DEFENSE_DH is historical tip stamp.",
            "DEFENSE_COOL_CF is reconstructed COOL_c8 on FUSE offense (current-stack twin).",
            "No rejected-order log — mechanisms tagged as binding/active on fill days.",
            "dist_pct: BUY=above local low; SELL=below local high (0=perfect extreme).",
            "OHLC basis: adj_close-scaled (fill_price_adj); raw unadjusted OHLC is not used.",
        ],
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    # Top strata table for md
    focus = [
        s
        for s in strata
        if s["defense"] in ("ALL", "DH_DEFEND", "COOL_CF_DEFEND")
        and s["side"] == "ALL"
        and s["sleeve"] in ("ALL", "FIN", "TEL", "0050")
    ]

    lines = [
        "# Live fill extreme + mechanism audit — Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **`{verdict}`** · Soft-Frozen KEEP · **no live wire** · no tip rewrite",
        "",
        f"Fills: **{n}** (BUY {n_buy} / SELL {n_sell}) · "
        f"`{payload['fill_date_min']}` → `{payload['fill_date_max']}` · codes `{payload['codes']}`",
        "",
        "## A — Distance to local extreme",
        "",
        f"Overall ±5d: mean **{core.get('mean_dist_pct')}%** · median {core.get('median_dist_pct')}% · "
        f"≤1%: {core.get('share_within_1pct')} · ≤3%: {core.get('share_within_3pct')}",
        f"Overall ±21d: mean **{core21.get('mean_dist_pct')}%** · median {core21.get('median_dist_pct')}%",
        f"Mean T+1 drag vs signal-day extreme: **{payload['mean_t1_drag_pct']}%**",
        "",
        "| sleeve | defense | n | ±5 mean% | ±5 med% | ±21 mean% | T+1 drag% |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for s in focus:
        lines.append(
            f"| {s['sleeve']} | {s['defense']} | {s['n_fills']} | "
            f"{s['n5'].get('mean_dist_pct', '')} | {s['n5'].get('median_dist_pct', '')} | "
            f"{s['n21'].get('mean_dist_pct', '')} | {s['mean_t1_drag_pct']} |"
        )

    lines += [
        "",
        "## B — Mechanism tags (count of fills where tag active)",
        "",
        "| mechanism | n_fills |",
        "|---|---:|",
    ]
    for k, v in payload["mechanism_fill_counts"].items():
        lines.append(f"| `{k}` | {v} |")

    lines += [
        "",
        "### Read",
        "",
        "1. **T1_ALWAYS / T1_DRAG** — every tip fill is Exact T+1; drag vs signal-day low/high is structural.",
        "2. **CLIP_*** — Soft-Frozen sleeve weight on a clip edge that signal day.",
        "3. **DEFENSE_DH** — historical tip defense (fill window pre-COOL live).",
        "4. **DEFENSE_COOL_CF** — same dates under reconstructed COOL_c8 (counterfactual).",
        "5. **KD_OFFSEASON** — FIN fills outside Apr15–May15 (expected for Aug–Sep tip).",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/live_fill_extreme_audit.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": DECISION_ID,
        "generated_at_utc": _utc(),
        "status": verdict,
        "verdict": verdict,
        "live_wire": False,
        "n_fills": n,
        "overall_n5_mean_dist_pct": core.get("mean_dist_pct"),
        "overall_n21_mean_dist_pct": core21.get("mean_dist_pct"),
        "mean_t1_drag_pct": payload["mean_t1_drag_pct"],
        "mechanism_fill_counts": payload["mechanism_fill_counts"],
        "binding": [
            "Soft-Frozen live KEEP — audit does not authorize clip flip",
            "Exact T+1 KEEP — drag is by design, not a defect to 'fix' by same-bar fills",
            "No tip history rewrite",
            "No live wire from this audit",
        ],
        "next": (
            "If human wants action: open a dedicated Stage A on ONE mechanism "
            "(e.g. soft-sell densify or KD season) — do not batch-retune from this audit"
        ),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
    }
    dlines = [
        "# Live fill extreme + mechanism audit — Decision Pack",
        "",
        f"Date: 2026-09-26 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        f"Tip fills **{n}** · ±5d mean distance to extreme **{core.get('mean_dist_pct')}%** · "
        f"T+1 drag mean **{payload['mean_t1_drag_pct']}%**.",
        "",
        "Primary structural driver: **Exact T+1** (all fills tagged). "
        "Aug–Sep tip sits **KD off-season** for FIN. "
        "Defense tags: use `DEFENSE_DH` for historical tip; `DEFENSE_COOL_CF` for current-stack twin.",
        "",
        "## Binding",
        "",
    ] + [f"{i}. {b}" for i, b in enumerate(decision["binding"], 1)]
    dlines += [
        "",
        f"Next: {decision['next']}",
        "",
        f"Label: `{DECISION_ID}_2026-09-26__{verdict}`",
        "",
    ]
    for path in (OPS, REP):
        (path / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
        (path / f"{DECISION_ID}.md").write_text("\n".join(dlines) + "\n")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_fills": n,
                "overall_n5": core,
                "mean_t1_drag_pct": payload["mean_t1_drag_pct"],
                "top_mechanisms": list(payload["mechanism_fill_counts"].items())[:8],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
