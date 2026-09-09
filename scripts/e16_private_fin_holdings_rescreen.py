#!/usr/bin/env python3
"""Private financial holdings (民營金控) paper re-screen — RESEARCH ONLY.

Soft-Frozen sleeve weights from live FINBAND (公股 R1 features).
Financial sleeve dollars re-allocated to PUB / PRIV / ALL12 member lists.
Baseline: LIVE_PUB_KD (current live intent).

Data: merge forward/e21/live_market.csv with TWSE-archive 12-stock OHLCV.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
import e50_early_stack_combined_nav as e50
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_name_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/private-fin-holdings-20260909"
RESEARCH = ROOT / "research/ops"
TW12 = Path("/tmp/tw12/artifact/v412d_12stocks_2010_2026.csv")

CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0

PUB_R1 = ["2880", "2886", "2892", "5880"]
PRIV_R3R4 = ["2884", "2885", "2890", "2891", "2881", "2882"]
BANKS_R2 = ["2801", "2834"]
ALL12 = PUB_R1 + BANKS_R2 + PRIV_R3R4
TEL = ["2412", "3045", "4904"]

KD_OPT = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}


def tip_gate(base_nav: pd.DataFrame, chal_nav: pd.DataFrame, asof: pd.Timestamp) -> dict:
    out = {}
    asof = pd.Timestamp(asof)
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"giveback_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"] / float(b["nav"].iloc[0])
        cn = c["nav"] / float(c["nav"].iloc[0])
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = None if bc is None or cc is None else (bc - cc) * 100
        gate = "PASS"
        if gb is not None and gb > TRAIL_PAUSE_PP:
            gate = "PAUSE_REVIEW"
        elif gb is not None and gb > TRAIL_ALERT_PP:
            gate = "ALERT"
        out[wname] = {
            "giveback_pp": None if gb is None else float(gb),
            "gate": gate,
            "rel_nav": float(cn.iloc[-1] / bn.iloc[-1]),
        }
    return out


def held_score(base_s, chal_s):
    mdd = mdd_delta_pp(base_s.get("max_drawdown"), chal_s.get("max_drawdown"))
    cagr = cagr_delta_pp(base_s.get("cagr"), chal_s.get("cagr"), missing_as_zero=True)
    gb = abs(float(cagr)) if cagr is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd),
        "cagr_giveback_pp": float(cagr) if cagr is not None else None,
        "score": float(mdd) - 0.5 * gb,
    }


def build_extended_market() -> pd.DataFrame:
    live = load_market()
    live["code"] = live["code"].astype(str)
    live["date"] = pd.to_datetime(live["date"])
    if not TW12.exists():
        raise SystemExit(f"missing TW12 artifact: {TW12}")
    tw = pd.read_csv(TW12, dtype={"code": str})
    tw["date"] = pd.to_datetime(tw["date"])
    # archive columns → live schema; adj_close proxy = close for research
    keep = ["date", "code", "open", "high", "low", "close", "volume"]
    tw = tw[[c for c in keep if c in tw.columns]].copy()
    tw["adj_close"] = tw["close"]
    # Prefer live rows for Soft-Frozen universe (has true adj_close).
    live_codes = set(live["code"])
    tw_extra = tw[~tw["code"].isin(live_codes)].copy()
    # Align date range to live Soft-Frozen history
    d0, d1 = live["date"].min(), live["date"].max()
    tw_extra = tw_extra[(tw_extra["date"] >= d0) & (tw_extra["date"] <= d1)]
    m = pd.concat([live, tw_extra], ignore_index=True)
    m = m.sort_values(["date", "code"]).drop_duplicates(["date", "code"], keep="last")
    return m


def run_book(
    market,
    dividends,
    target,
    regime,
    *,
    book_id: str,
    fin_codes: list[str],
    financial_alloc: str,
):
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(fin_codes)
    e50.ALL = list(fin_codes) + TEL + ["0050"]
    try:
        cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
        fin_scores = None
        fin_buy_ok = None
        if financial_alloc == FIN_PRE_EXDIV_KD:
            fin_scores = build_kd_season_tilt_scores(
                market,
                dividends,
                fin_codes,
                k_thresh=float(KD_OPT["k_thresh"]),
                season_start=KD_OPT["season_start"],
                season_end=KD_OPT["season_end"],
                pre_days=int(KD_OPT["pre_days"]),
                active_score=float(KD_OPT["active_score"]),
            )
            fin_buy_ok = build_pre_exdiv_window_buy_ok(
                cal, dividends, fin_codes, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
            )
        elif financial_alloc != FIN_EQUAL:
            fin_scores = build_name_scores(market, fin_codes)

        nav, fills, meta = e50.simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            capital=CAPITAL,
            lot_size=LOT,
            financial_alloc=financial_alloc,
            telecom_alloc=TEL_EQUAL,
            fin_name_scores=fin_scores,
            fin_buy_ok=fin_buy_ok,
        )
        assert meta.get("exact_t1_ok"), book_id
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        end_pos = meta.get("end_positions") or {}
        tip_pos = {c: float(end_pos.get(c, 0.0)) for c in fin_codes}
        return {
            "id": book_id,
            "fin_codes": list(fin_codes),
            "financial_alloc": financial_alloc,
            "n_fills": int(len(fills)),
            "windows": win,
            "nav": nav,
            "tip_fin_names": int(sum(1 for v in tip_pos.values() if abs(v) >= LOT - 1e-9)),
            "tip_positions": tip_pos,
        }
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    assert soft.FIN == PUB_R1

    print("building extended market ...", flush=True)
    market = build_extended_market()
    dividends = load_dividends()
    # Soft-Frozen features from live 公股 universe only (soft.FIN).
    print("Soft-Frozen targets ...", flush=True)
    _p, _s, target, regime = e50.e16_features(market)

    books_spec = [
        ("LIVE_PUB_KD", PUB_R1, FIN_PRE_EXDIV_KD),
        ("LIVE_PUB_EQ", PUB_R1, FIN_EQUAL),
        ("PRIV_EQ", PRIV_R3R4, FIN_EQUAL),
        ("PRIV_KD", PRIV_R3R4, FIN_PRE_EXDIV_KD),
        ("ALL12_EQ", ALL12, FIN_EQUAL),
        ("ALL12_KD", ALL12, FIN_PRE_EXDIV_KD),
    ]
    results = {}
    for i, (bid, codes, alloc) in enumerate(books_spec, 1):
        print(f"  [{i}/{len(books_spec)}] {bid} fin={codes} alloc={alloc} ...", flush=True)
        results[bid] = run_book(
            market, dividends, target, regime, book_id=bid, fin_codes=codes, financial_alloc=alloc
        )

    base = results["LIVE_PUB_KD"]
    asof = pd.to_datetime(base["nav"]["date"]).max()
    ranked = []
    for bid, row in results.items():
        if bid == "LIVE_PUB_KD":
            continue
        held = held_score(base["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"])
        tip = tip_gate(base["nav"], row["nav"], asof)
        tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
        sealed = held_score(base["windows"]["sealed_2023_plus"], row["windows"]["sealed_2023_plus"])
        ranked.append(
            {
                "id": bid,
                "financial_alloc": row["financial_alloc"],
                "n_fin_names": len(row["fin_codes"]),
                "heldout_score": held["score"],
                "mdd_improve_pp": held["mdd_improve_pp"],
                "cagr_giveback_pp": held["cagr_giveback_pp"],
                "tip_ytd": tip["ytd"]["gate"],
                "tip_1y": tip["trailing_1y"]["gate"],
                "tip_clean": tip_clean,
                "sealed_score_REPORT_ONLY": sealed["score"],
                "tip_fin_names": row["tip_fin_names"],
                "n_fills": row["n_fills"],
                "coexist": bool(tip_clean and held["score"] > 0),
            }
        )
    ranked.sort(key=lambda r: r["heldout_score"], reverse=True)
    coexist = [r for r in ranked if r["coexist"]]
    if coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["heldout_score"] > 0 for r in ranked):
        status = "STAGE_A_SCORE_POSITIVE_TIP_DIRTY"
    else:
        status = "STOP_NO_POSITIVE_HELDOUT_VS_LIVE_PUB_KD"

    # absolute snapshot
    abs_rows = {}
    for bid, row in results.items():
        a = row["windows"]
        abs_rows[bid] = {
            "full_cagr": a["full"].get("cagr"),
            "full_mdd": a["full"].get("max_drawdown"),
            "heldout_cagr": a["heldout_2019_plus"].get("cagr"),
            "heldout_mdd": a["heldout_2019_plus"].get("max_drawdown"),
        }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIVATE_FIN_HOLDINGS_RESCREEN",
        "status": status,
        "charter": "research/ops/PRIVATE_FIN_HOLDINGS_CHARTER.md",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "soft_frozen_fin_membership": PUB_R1,
        "capital": CAPITAL,
        "lot_size": LOT,
        "baseline": "LIVE_PUB_KD",
        "data_notes": [
            "Private OHLCV from TWSE-archive 12-stock build",
            "Private adj_close proxied by close",
            "Dividend events CSV lacks private names → E22 credits incomplete for PRIV/ALL12 books",
        ],
        "universes": {"PUB_R1": PUB_R1, "PRIV_R3R4": PRIV_R3R4, "ALL12": ALL12},
        "absolute": abs_rows,
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "kd_probe": KD_OPT,
    }
    # drop nav from disk json
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIVATE_FIN_HOLDINGS_RESCREEN.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    RESEARCH.joinpath("PRIVATE_FIN_HOLDINGS_CHARTER.json").write_text(
        json.dumps(
            {
                "label": "PRIVATE_FIN_HOLDINGS_CHARTER",
                "status": "STAGE_A_STOP" if status.startswith("STOP") else "ACCEPTED_RUNNING",
                "date": "2026-09-09",
                "rescreen_status": status,
                "decision_pack": "research/ops/PRIVATE_FIN_HOLDINGS_DECISION_PACK.md",
            },
            indent=2,
        )
        + "\n"
    )

    lines = [
        "# Private financial holdings (民營金控) — Stage A re-screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **{soft.SOFT_FROZEN_FIN_CLIP}** · baseline **`LIVE_PUB_KD`** · live wire **false**",
        f"Capital **{CAPITAL:,.0f}** · lot **{LOT}** · Telecom=`TEL_EQUAL`",
        "",
        "## Absolute",
        "",
        "| book | full CAGR | full MDD | heldout CAGR | heldout MDD |",
        "|---|---:|---:|---:|---:|",
    ]
    for bid in ("LIVE_PUB_KD", "LIVE_PUB_EQ", "PRIV_EQ", "PRIV_KD", "ALL12_EQ", "ALL12_KD"):
        a = abs_rows[bid]
        lines.append(
            f"| `{bid}` | {a['full_cagr']*100:.2f}% | {a['full_mdd']*100:.2f}% | "
            f"{a['heldout_cagr']*100:.2f}% | {a['heldout_mdd']*100:.2f}% |"
        )
    lines += [
        "",
        "## vs LIVE_PUB_KD (current live intent)",
        "",
        "| book | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean | coexist |",
        "|---|---:|---:|---:|---|---|---|---|",
    ]
    for r in ranked:
        lines.append(
            f"| `{r['id']}` | {r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{r['cagr_giveback_pp']:.3f} | {r['tip_ytd']} | {r['tip_1y']} | {r['tip_clean']} | {r['coexist']} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        f"- Coexist (tip-clean + held-out>0): `{payload['coexist_ids'] or 'none'}`",
        "- Soft-Frozen membership stays 公股 R1; this only rewires Financial sleeve dollars on paper.",
        "- Private dividend E22 coverage incomplete — treat PRIV/ALL12 levels as directional.",
        "- No live universe expansion from this screen.",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("PRIVATE_FIN_HOLDINGS_RESCREEN.md").write_text(md)
    print(json.dumps({"status": status, "ranked": ranked, "coexist": payload["coexist_ids"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
