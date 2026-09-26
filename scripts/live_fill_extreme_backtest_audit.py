#!/usr/bin/env python3
"""Backtest fill extreme + mechanism audit on live FUSE+COOL twin (observe only).

Charter: research/ops/LIVE_FILL_EXTREME_AUDIT_CHARTER.md
Full-history paper fills from simulate_core (FUSE offense → COOL_c8 stacked).
Soft-Frozen KEEP; no live wire; no tip rewrite.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import live_cool_c8_cutover as cool_cut
import live_dh_fuse_cutover as fuse_cut
from e16_soft_frozen_base import FIN
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market
from live_config import KD_OPT
from live_fill_extreme_audit import (
    N_GRID,
    _agg_from_extremes,
    _clip_binding,
    _in_kd_season,
    _ohlc_panel,
    _sleeve,
    _window_ext,
)
from within_sleeve_alloc import build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "live-fill-extreme-audit"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "LIVE_FILL_EXTREME_AUDIT_CHARTER"
SCREEN_ID = "LIVE_FILL_EXTREME_BACKTEST_SCREEN"
DECISION_ID = "LIVE_FILL_EXTREME_BACKTEST_DECISION_PACK"
BOOK_ID = "LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lookup_exp(exp: pd.Series, sig_d: pd.Timestamp) -> float | None:
    if exp.empty:
        return None
    if sig_d in exp.index and pd.notna(exp.loc[sig_d]):
        return float(exp.loc[sig_d])
    prior = exp.index[exp.index <= sig_d]
    if len(prior) and pd.notna(exp.loc[prior[-1]]):
        return float(exp.loc[prior[-1]])
    return None


def _lookup_sleeve(
    target: pd.DataFrame, sig_d: pd.Timestamp
) -> tuple[float | None, float | None, float | None]:
    if target.empty:
        return None, None, None
    row = None
    if sig_d in target.index:
        row = target.loc[sig_d]
    else:
        prior = target.index[target.index <= sig_d]
        if len(prior):
            row = target.loc[prior[-1]]
    if row is None:
        return None, None, None
    return (
        float(row["Financial"]) if "Financial" in row.index else None,
        float(row["Telecom"]) if "Telecom" in row.index else None,
        float(row["0050"]) if "0050" in row.index else None,
    )


def _window_mask(fill_dates: pd.Series, a: date | None, b: date | None) -> pd.Series:
    d = pd.to_datetime(fill_dates).dt.date
    ok = pd.Series(True, index=fill_dates.index)
    if a is not None:
        ok &= d >= a
    if b is not None:
        ok &= d <= b
    return ok


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()

    print("building FUSE offense (SELL_a75) ...", flush=True)
    fuse_nav, _fills_off, fuse_meta = fuse_cut.build_fuse_offense_sim(market, dividends)
    print(f"  offense fills={fuse_meta['n_fills']}", flush=True)

    print("building COOL_c8 from offense ...", flush=True)
    cool = cool_cut.build_cool_exposure_from_offense(market, fuse_nav)
    cool.to_frame("cool_exposure").to_csv(OUT / "backtest_cool_c8_from_fuse.csv")
    dh = fuse_cut.build_dh_exposure_from_offense(market, fuse_nav)
    dh.to_frame("dh_exposure").to_csv(OUT / "backtest_dh_from_fuse.csv")

    print("building FUSE+COOL live-twin fills ...", flush=True)
    cool_nav, fills, cool_meta = fuse_cut.build_fuse_offense_sim(
        market, dividends, e45_exposure=cool
    )
    cool_nav.to_csv(OUT / "backtest_fuse_cool_nav.csv", index=False)
    fills = fills.copy()
    fills["signal_date"] = pd.to_datetime(fills["signal_date"]).dt.normalize()
    fills["fill_date"] = pd.to_datetime(fills["fill_date"]).dt.normalize()
    fills.to_csv(OUT / "backtest_fuse_cool_fills.csv", index=False)
    print(f"  twin fills={len(fills)}", flush=True)

    target = fuse_cut.fuse_target_for_market(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )
    panels = {c: _ohlc_panel(market, c) for c in sorted(fills["code"].astype(str).unique())}

    rows: list[dict[str, Any]] = []
    for i, f in fills.iterrows():
        code = str(f["code"])
        side = str(f["side"]).upper()
        px = float(f["fill_price"])
        sig_d = pd.Timestamp(f["signal_date"])
        fill_d = pd.Timestamp(f["fill_date"])
        sleeve = _sleeve(code)
        panel = panels.get(code, pd.DataFrame())

        cool_exp = _lookup_exp(cool, sig_d)
        dh_exp = _lookup_exp(dh, sig_d)
        fin_w, tel_w, etf_w = _lookup_sleeve(target, sig_d)

        mech: list[str] = ["T1_ALWAYS"]
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
            mech.append("DEFENSE_DH_CF")
        if cool_exp is not None and cool_exp < 1.0 - 1e-12:
            mech.append("DEFENSE_COOL")
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
                "fill_id": f"{fill_d.date().isoformat()}-{code}-{side}-{i}",
                "signal_date": sig_d.date().isoformat(),
                "fill_date": fill_d.date().isoformat(),
                "code": code,
                "sleeve": sleeve,
                "side": side,
                "quantity": int(f["quantity"]),
                "fill_price": px,
                "t1_drag_vs_signal_ext_pct": None
                if t1_drag_pp is None
                else round(float(t1_drag_pp), 4),
                "dh_exposure_cf": None if dh_exp is None else round(float(dh_exp), 6),
                "cool_exposure": None if cool_exp is None else round(float(cool_exp), 6),
                "defense_dh_cf": bool(dh_exp is not None and dh_exp < 1.0 - 1e-12),
                "defense_cool": bool(cool_exp is not None and cool_exp < 1.0 - 1e-12),
                "e16_financial": fin_w,
                "e16_telecom": tel_w,
                "e16_0050": etf_w,
                "mechanisms": mech,
                "extremes": ext,
            }
        )

    detail = pd.DataFrame(rows)
    detail.to_csv(OUT / "backtest_fill_extreme_detail.csv", index=False)
    # Skip full-row JSON (multi-MB); screen/decision packs carry aggregates.

    def _agg(df: pd.DataFrame, n: int) -> dict[str, Any]:
        return _agg_from_extremes(df, n)

    strata: list[dict[str, Any]] = []
    for sleeve in ("FIN", "TEL", "0050", "ALL"):
        for side in ("BUY", "SELL", "ALL"):
            for def_lab in ("ALL", "COOL_DEFEND", "COOL_OFF", "DH_CF_DEFEND", "DH_CF_OFF"):
                sub = detail
                if sleeve != "ALL":
                    sub = sub[sub["sleeve"] == sleeve]
                if side != "ALL":
                    sub = sub[sub["side"] == side]
                if def_lab == "COOL_DEFEND":
                    sub = sub[sub["defense_cool"].fillna(False)]
                elif def_lab == "COOL_OFF":
                    sub = sub[~sub["defense_cool"].fillna(False)]
                elif def_lab == "DH_CF_DEFEND":
                    sub = sub[sub["defense_dh_cf"].fillna(False)]
                elif def_lab == "DH_CF_OFF":
                    sub = sub[~sub["defense_dh_cf"].fillna(False)]
                if sub.empty:
                    continue
                strata.append(
                    {
                        "sleeve": sleeve,
                        "side": side,
                        "defense": def_lab,
                        "n_fills": int(len(sub)),
                        "n5": _agg(sub, 5),
                        "n21": _agg(sub, 21),
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

    windows: dict[str, Any] = {}
    for wname, (a, b) in WINDOWS_STANDARD.items():
        mask = _window_mask(detail["fill_date"], a, b)
        sub = detail[mask]
        if sub.empty:
            windows[wname] = {"n_fills": 0}
            continue
        windows[wname] = {
            "n_fills": int(len(sub)),
            "n_buy": int((sub["side"] == "BUY").sum()),
            "n_sell": int((sub["side"] == "SELL").sum()),
            "overall_n5": _agg(sub, 5),
            "overall_n21": _agg(sub, 21),
            "mean_t1_drag_pct": round(
                float(
                    pd.to_numeric(sub["t1_drag_vs_signal_ext_pct"], errors="coerce").mean()
                ),
                4,
            )
            if sub["t1_drag_vs_signal_ext_pct"].notna().any()
            else None,
            "cool_defend_share": round(float(sub["defense_cool"].fillna(False).mean()), 4),
        }

    mech_counts: dict[str, int] = {}
    for r in rows:
        for m in r["mechanisms"]:
            mech_counts[m] = mech_counts.get(m, 0) + 1

    n = len(rows)
    n_buy = int((detail["side"] == "BUY").sum())
    n_sell = int((detail["side"] == "SELL").sum())
    core = _agg(detail, 5)
    core21 = _agg(detail, 21)
    cool_frac = float((cool < 1.0 - 1e-12).mean()) if len(cool) else 0.0

    verdict = "FILL_EXTREME_BACKTEST_DONE"
    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "book_id": BOOK_ID,
        "fuse_meta": {k: fuse_meta[k] for k in (
            "fuse_id", "soft_id", "soft_sell_boost", "sleeve_id", "n_fills", "e22_books_version"
        )},
        "cool_meta": {
            "n_fills": int(cool_meta["n_fills"]),
            "cool_defense_frac_days": round(cool_frac, 4),
        },
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
        "windows": windows,
        "strata": strata,
        "notes": [
            "Fills from simulate_core FUSE+COOL live twin (SELL_a75 + COOL_c8 e45_exposure).",
            "DEFENSE_COOL is on-book (exposure applied in sim); DEFENSE_DH_CF is counterfactual DH.",
            "Clip tags from Soft-Frozen champion target on signal_date (pre-defense).",
            "dist_pct: BUY=above local low; SELL=below local high (0=perfect extreme).",
        ],
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    focus = [
        s
        for s in strata
        if s["defense"] in ("ALL", "COOL_DEFEND", "COOL_OFF")
        and s["side"] == "ALL"
        and s["sleeve"] in ("ALL", "FIN", "TEL", "0050")
    ]

    lines = [
        "# Backtest fill extreme + mechanism audit — Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **`{verdict}`** · Soft-Frozen KEEP · **no live wire** · book `{BOOK_ID}`",
        "",
        f"Fills: **{n}** (BUY {n_buy} / SELL {n_sell}) · "
        f"`{payload['fill_date_min']}` → `{payload['fill_date_max']}` · codes `{payload['codes']}`",
        f"COOL defense day-frac: **{cool_frac:.2%}**",
        "",
        "## A — Distance to local extreme (full history)",
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
        "## Windows",
        "",
        "| window | n | ±5 mean% | ±21 mean% | T+1 drag% | cool_defend_share |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for wname, w in windows.items():
        if not w.get("n_fills"):
            continue
        lines.append(
            f"| `{wname}` | {w['n_fills']} | "
            f"{(w.get('overall_n5') or {}).get('mean_dist_pct', '')} | "
            f"{(w.get('overall_n21') or {}).get('mean_dist_pct', '')} | "
            f"{w.get('mean_t1_drag_pct')} | {w.get('cool_defend_share')} |"
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
        "1. **T1_ALWAYS / T1_DRAG** — Exact T+1 open fills (by design).",
        "2. **DEFENSE_COOL** — on-book COOL_c8 shrink day (live twin).",
        "3. **DEFENSE_DH_CF** — same signal dates under historical DH rule (counterfactual).",
        "4. **CLIP_*** — Soft-Frozen champion sleeve weight on a clip edge that signal day.",
        "5. **KD_OFFSEASON / KD_BUY_BLOCK** — FIN KD season / pre-exdiv buy gate.",
        "",
        "Compare tip audit (`LIVE_FILL_EXTREME_AUDIT_SCREEN`) for short live tip window.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/live_fill_extreme_backtest_audit.py`",
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
        "book_id": BOOK_ID,
        "n_fills": n,
        "overall_n5_mean_dist_pct": core.get("mean_dist_pct"),
        "overall_n21_mean_dist_pct": core21.get("mean_dist_pct"),
        "mean_t1_drag_pct": payload["mean_t1_drag_pct"],
        "cool_defense_frac_days": round(cool_frac, 4),
        "windows": {
            k: {
                "n_fills": v.get("n_fills"),
                "n5_mean": (v.get("overall_n5") or {}).get("mean_dist_pct"),
                "t1_drag": v.get("mean_t1_drag_pct"),
                "cool_defend_share": v.get("cool_defend_share"),
            }
            for k, v in windows.items()
            if v.get("n_fills")
        },
        "mechanism_fill_counts": payload["mechanism_fill_counts"],
        "binding": [
            "Soft-Frozen live KEEP — audit does not authorize clip flip",
            "Exact T+1 KEEP — drag is by design",
            "No tip history rewrite",
            "No live wire from this backtest audit",
        ],
        "next": (
            "If human wants action: open a dedicated Stage A on ONE mechanism "
            "(e.g. soft-sell densify or KD season) — do not batch-retune from this audit"
        ),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "tip_screen": "research/ops/LIVE_FILL_EXTREME_AUDIT_SCREEN.md",
    }
    dlines = [
        "# Backtest fill extreme + mechanism audit — Decision Pack",
        "",
        f"Date: 2026-09-26 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false** · `{BOOK_ID}`",
        "",
        f"Paper twin fills **{n}** · ±5d mean distance to extreme **{core.get('mean_dist_pct')}%** · "
        f"T+1 drag mean **{payload['mean_t1_drag_pct']}%** · "
        f"COOL defend day-frac **{cool_frac:.2%}**.",
        "",
        "Primary structural driver remains **Exact T+1**. "
        "COOL on-book defense days are now visible across full history "
        "(unlike the short tip window which had full exposure).",
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
                "cool_defense_frac_days": round(cool_frac, 4),
                "windows": {
                    k: v.get("overall_n5", {}).get("mean_dist_pct")
                    for k, v in windows.items()
                    if v.get("n_fills")
                },
                "top_mechanisms": list(payload["mechanism_fill_counts"].items())[:10],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
