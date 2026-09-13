#!/usr/bin/env python3
"""E45 defend→handoff Stage A paper screen (charter #219; no stitch reopen).

Finite grid only: dd ∈ {6%,8%,10%} × vol_z ∈ {1.0,1.5}.
Offense book = paper LIVE_STACK twin (Soft-Frozen + KD_OPT + TEL_EQUAL).
Defense actuator (frozen) = SHRINK e45_exposure to (1−0.50) while in defense.
No live wire · no E45 stitch reopen · no observe OPEN from this screen alone.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from soft_assist_helpers import LIVE_KD
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "e45-defend-handoff-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "E45_DEFEND_HANDOFF_PAPER_CHARTER"
SCREEN_ID = "E45_DEFEND_HANDOFF_STAGEA_SCREEN"
ARTIFACT = "research/ops/E45_DEFEND_HANDOFF_STAGEA_SCREEN.md"

DD_GRID = (0.06, 0.08, 0.10)
VOL_Z_GRID = (1.0, 1.5)
COOLDOWN = 5
RECOVER_FRAC = 0.97
MAX_DEF_SESSIONS = 42
HANDOFF_RACE_DAYS = 21
SHRINK = 0.50
GIVEBACK_CAP_PP = 2.0
HELDOUT = "heldout_2019_plus"
REPORT_WINDOWS = (
    "full",
    "oof_2011_2018",
    "validation_2019_2022",
    "sealed_2023_plus",
    "heldout_2019_plus",
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _close_panel(market: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    m = market[market["code"].isin(codes)].copy()
    m["date"] = pd.to_datetime(m["date"])
    return m.pivot(index="date", columns="code", values="close").sort_index().ffill()


def _vol_z(s: pd.Series) -> pd.Series:
    r = np.log(s.astype(float)).diff()
    vol = r.rolling(21, min_periods=15).std()
    mu = vol.rolling(63, min_periods=40).mean()
    sd = vol.rolling(63, min_periods=40).std()
    return ((vol - mu) / sd.replace(0.0, np.nan)).fillna(0.0)


def _mdd63(s: pd.Series) -> pd.Series:
    roll = s.astype(float).rolling(63, min_periods=40).max()
    return (s.astype(float) / roll - 1.0).fillna(0.0)


def _nav_series(nav: pd.DataFrame) -> pd.Series:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    return d.set_index("date")["nav"].astype(float).sort_index()


def _risk_features(market: pd.DataFrame, base_nav: pd.Series) -> dict[str, pd.Series]:
    fin = _close_panel(market, list(FIN)).mean(axis=1)
    etf = _close_panel(market, ["0050"])["0050"]
    idx = fin.index.intersection(base_nav.index).intersection(etf.index)
    nav = base_nav.reindex(idx).ffill()
    etf = etf.reindex(idx).ffill()
    fin = fin.reindex(idx).ffill()
    return {
        "book_mdd63": _mdd63(nav),
        "fin_vol_z": _vol_z(fin),
        "proxy_mdd63": _mdd63(etf),
        "proxy_ret": etf.pct_change().fillna(0.0),
        "off_ret": nav.pct_change().fillna(0.0),
        "off_nav": nav,
    }


def _build_exposure(
    dates: pd.DatetimeIndex,
    feat: dict[str, pd.Series],
    dd: float,
    vz: float,
) -> pd.Series:
    """Causal defend path on offense-book features (Exact T+1; no peek).

    X3 (handoff race): offense trailing 21d return > 0050 proxy 21d → force exit
    (offense won race vs market; hand capital back). Documented freeze for Stage A.
    """
    out = pd.Series(1.0, index=dates, dtype=float)
    defense = False
    cool = 0
    off_nav = feat["off_nav"].reindex(dates).ffill()
    peak = float(off_nav.iloc[0])
    def_sessions = 0

    book_mdd = feat["book_mdd63"].reindex(dates).fillna(0.0)
    fin_z = feat["fin_vol_z"].reindex(dates).fillna(0.0)
    proxy_mdd = feat["proxy_mdd63"].reindex(dates).fillna(0.0)
    off_ret = feat["off_ret"].reindex(dates).fillna(0.0)
    proxy_ret = feat["proxy_ret"].reindex(dates).fillna(0.0)

    for i, _dt in enumerate(dates):
        v = float(off_nav.iloc[i])
        if cool > 0:
            cool -= 1
            out.iloc[i] = 1.0
            continue

        if not defense:
            peak = max(peak, v)
            t1 = float(book_mdd.iloc[i]) <= -float(dd)
            t2 = float(fin_z.iloc[i]) >= float(vz) or float(proxy_mdd.iloc[i]) <= -0.10
            if t1 and t2:
                defense = True
                peak = v
                def_sessions = 0
        else:
            def_sessions += 1
            # X2: reset dwell clock on fresh T1 breach
            if float(book_mdd.iloc[i]) <= -float(dd):
                def_sessions = 0

            recovered = v >= float(peak) * RECOVER_FRAC
            timed = def_sessions >= MAX_DEF_SESSIONS

            race = False
            if i >= HANDOFF_RACE_DAYS and def_sessions >= HANDOFF_RACE_DAYS:
                sl = slice(i - HANDOFF_RACE_DAYS + 1, i + 1)
                off_trail = float((1.0 + off_ret.iloc[sl]).prod() - 1.0)
                px_trail = float((1.0 + proxy_ret.iloc[sl]).prod() - 1.0)
                if off_trail > px_trail:
                    race = True

            if recovered or timed or race:
                defense = False
                cool = COOLDOWN
                out.iloc[i] = 1.0
                continue

        out.iloc[i] = (1.0 - SHRINK) if defense else 1.0
    return out


def _run_book(
    market: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    dividends: pd.DataFrame,
    *,
    scores: pd.DataFrame,
    buy_ok: pd.DataFrame,
    exposure: pd.Series | None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
    )
    if exposure is not None:
        kwargs["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kwargs)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return {"nav": nav, "n_fills": int(len(fills)), "meta": meta}


def _pack_windows(nav: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, (a, b) in WINDOWS_STANDARD.items():
        st = window_stats(nav, a, b)
        out[k] = {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None
            if st.get("max_drawdown") is None
            else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
    return out


def _tip_windows(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {
                "mdd_improve_pp": None,
                "cagr_giveback_pp": None,
                "gate": "INSUFFICIENT",
            }
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = cagr_delta_pp(bc, cc)
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "gate": "PASS",
        }
    return out


def _held_delta(base_w: dict[str, Any], chal_w: dict[str, Any], key: str) -> dict[str, Any] | None:
    b, c = base_w.get(key), chal_w.get(key)
    if not b or not c or b.get("cagr") is None or c.get("cagr") is None:
        return None
    gb = cagr_delta_pp(b.get("cagr"), c.get("cagr"))
    return {
        "mdd_improve_pp": round(
            float(mdd_delta_pp(b.get("max_drawdown"), c.get("max_drawdown"))), 4
        ),
        "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
        "base_cagr": b["cagr"],
        "chal_cagr": c["cagr"],
        "base_mdd": b["max_drawdown"],
        "chal_mdd": c["max_drawdown"],
    }


def _verdict(rows: list[dict[str, Any]]) -> tuple[str, str | None, dict[str, Any]]:
    shaped: list[dict[str, Any]] = []
    mdd_only: list[dict[str, Any]] = []
    for r in rows:
        h = r.get("heldout_delta") or {}
        tip = r.get("tip") or {}
        tips_ok = all(
            (tip.get(w) or {}).get("mdd_improve_pp") is not None
            and float((tip.get(w) or {}).get("mdd_improve_pp")) >= 0.0
            for w in ("ytd", "trailing_1y")
        )
        md = h.get("mdd_improve_pp")
        gb = h.get("cagr_giveback_pp")
        if md is None or gb is None:
            continue
        # promote-shaped: MDD improves, giveback ≤ cap, tip MDD not worse
        if float(md) > 0.0 and float(gb) <= GIVEBACK_CAP_PP and tips_ok:
            shaped.append(r)
        elif float(md) > 0.0:
            mdd_only.append(r)
    if shaped:
        best = max(
            shaped,
            key=lambda x: (
                float(x["heldout_delta"]["mdd_improve_pp"]),
                -float(x["heldout_delta"]["cagr_giveback_pp"]),
            ),
        )
        return (
            "HANDOFF_PROMOTE_SHAPED",
            best["variant_id"],
            {
                "held_mdd_improve_pp": best["heldout_delta"]["mdd_improve_pp"],
                "held_cagr_giveback_pp": best["heldout_delta"]["cagr_giveback_pp"],
                "n_shaped": len(shaped),
            },
        )
    if mdd_only:
        best = max(mdd_only, key=lambda x: float(x["heldout_delta"]["mdd_improve_pp"]))
        return (
            "MDD_HELP_CAGR_FAIL",
            best["variant_id"],
            {
                "held_mdd_improve_pp": best["heldout_delta"]["mdd_improve_pp"],
                "held_cagr_giveback_pp": best["heldout_delta"]["cagr_giveback_pp"],
                "n_mdd_help": len(mdd_only),
            },
        )
    return "NO_LIFT", None, {"n_rows": len(rows)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    import e21_forward_pipeline as e21

    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}]={LIVE_KD[k]!r} != e21.KD_OPT[{k}]={e21.KD_OPT[k]!r}")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse Stage A while LIVE_E45_STITCH is True")

    print("[1/3] loading + baseline LIVE_STACK twin …", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())

    scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )

    base = _run_book(
        market, target, regime, dividends, scores=scores, buy_ok=buy_ok, exposure=None
    )
    base["nav"].to_csv(OUT / "nav_BASE_LIVE_STACK.csv", index=False)
    base_windows = _pack_windows(base["nav"])
    base_nav_s = _nav_series(base["nav"])
    feat = _risk_features(market, base_nav_s)
    dates = pd.DatetimeIndex(base_nav_s.index)

    rows: list[dict[str, Any]] = []
    n = len(DD_GRID) * len(VOL_Z_GRID)
    i = 0
    print(f"[2/3] grid n={n} …", flush=True)
    for dd in DD_GRID:
        for vz in VOL_Z_GRID:
            i += 1
            vid = f"DH_dd{int(dd * 100):02d}_vz{str(vz).replace('.', 'p')}"
            print(f"  [{i}/{n}] {vid}", flush=True)
            exp = _build_exposure(dates, feat, dd, vz)
            frac_def = float((exp < 0.999).mean())
            chal = _run_book(
                market,
                target,
                regime,
                dividends,
                scores=scores,
                buy_ok=buy_ok,
                exposure=exp,
            )
            chal["nav"].to_csv(OUT / f"nav_{vid}.csv", index=False)
            exp.rename("e45_exposure").to_frame().to_csv(OUT / f"exposure_{vid}.csv")
            chal_windows = _pack_windows(chal["nav"])
            tip = _tip_windows(base["nav"], chal["nav"])
            held = _held_delta(base_windows, chal_windows, HELDOUT)
            sealed = _held_delta(base_windows, chal_windows, "sealed_2023_plus")
            rows.append(
                {
                    "variant_id": vid,
                    "dd_threshold": dd,
                    "vol_z_threshold": vz,
                    "frac_days_defense": round(frac_def, 6),
                    "exact_t1_ok": bool(chal["meta"].get("exact_t1_ok")),
                    "n_fills": chal["n_fills"],
                    "mean_e45_exposure": chal["meta"].get("mean_e45_exposure"),
                    "windows": {k: chal_windows.get(k) for k in REPORT_WINDOWS if k in chal_windows},
                    "heldout_delta": held,
                    "sealed_delta": sealed,
                    "tip": tip,
                }
            )

    verdict, best_id, detail = _verdict(rows)
    best = next((r for r in rows if r["variant_id"] == best_id), None)

    payload = {
        "schema_version": "e45_defend_handoff_stagea_screen_v1",
        "screen_id": SCREEN_ID,
        "charter_id": CHARTER_ID,
        "generated_at_utc": _utc(),
        "status": "DONE",
        "mode": "PAPER_ONLY",
        "live_wire": False,
        "stitch_reopen": False,
        "observe_open": False,
        "gates": {
            "exact_t1_ok": True,
            "apply_e22": True,
            "apply_stock_div": True,
            "financial_alloc": FIN_PRE_EXDIV_KD,
            "telecom_alloc": TEL_EQUAL,
            "fin_name_scores": "KD_OPT via LIVE_KD",
            "soft_frozen_fin_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
            "board_lot": int(BOARD_LOT),
            "initial_capital": float(DEFAULT_CAPITAL),
            "e45_actuator": f"SHRINK exposure to {1.0 - SHRINK} in defense",
            "offense_book": "paper LIVE_STACK twin (Soft-Frozen + pre-exdiv KD + TEL_EQUAL)",
            "giveback_cap_pp_heldout": GIVEBACK_CAP_PP,
            "x3_rule": "offense_21d_ret > 0050_proxy_21d_ret → force exit (handoff race)",
        },
        "base_windows": {k: base_windows.get(k) for k in REPORT_WINDOWS if k in base_windows},
        "grid": {"dd": list(DD_GRID), "vol_z": list(VOL_Z_GRID), "n": n},
        "rows": rows,
        "verdict": verdict,
        "best_variant_id": best_id,
        "verdict_detail": detail,
        "best_row": best,
        "non_actions": [
            "No Soft-Frozen / Soft / Sleeve / FUSE / E45 live wire",
            "No E45 stitch reopen / no undo DROP_E45_A05",
            "No observe OPEN from this Stage A alone",
            "Even HANDOFF_PROMOTE_SHAPED stays research until separate ballot",
        ],
    }
    (OUT / "stagea_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OPS / "E45_DEFEND_HANDOFF_STAGEA_SCREEN.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# E45 defend→handoff — Stage A screen",
        "",
        f"- screen_id: `{SCREEN_ID}`",
        f"- charter: `{CHARTER_ID}`",
        f"- generated_at_utc: `{payload['generated_at_utc']}`",
        "- status: **DONE** | mode: PAPER_ONLY | live_wire: false | stitch_reopen: false | observe_open: false",
        "",
        "## Verdict",
        "",
        f"- **`{verdict}`**",
        f"- best_variant_id: `{best_id}`",
        f"- detail: `{json.dumps(detail, ensure_ascii=False)}`",
        "",
        "## Held-out / tip deltas vs BASE_LIVE_STACK",
        "",
        "| variant | frac_def | held MDD↑ pp | held giveback pp | tip ytd MDD↑ | tip 1y MDD↑ |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        h = r.get("heldout_delta") or {}
        tip = r.get("tip") or {}
        lines.append(
            f"| `{r['variant_id']}` | {r['frac_days_defense']:.3f} | "
            f"{h.get('mdd_improve_pp')} | {h.get('cagr_giveback_pp')} | "
            f"{(tip.get('ytd') or {}).get('mdd_improve_pp')} | "
            f"{(tip.get('trailing_1y') or {}).get('mdd_improve_pp')} |"
        )
    lines += [
        "",
        "## Base windows (offense book)",
        "",
        "```json",
        json.dumps(payload["base_windows"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Non-actions",
        "",
    ]
    lines += [f"- {x}" for x in payload["non_actions"]]
    lines += [
        "",
        f"Artifact: `{ARTIFACT}`",
        f"Repro: `repro/e45-defend-handoff-stagea/`",
        "",
    ]
    text = "\n".join(lines)
    (REP / "E45_DEFEND_HANDOFF_STAGEA_SCREEN.md").write_text(text, encoding="utf-8")
    (OPS / "E45_DEFEND_HANDOFF_STAGEA_SCREEN.md").write_text(text, encoding="utf-8")

    print(f"[3/3] verdict={verdict} best={best_id}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
