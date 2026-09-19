#!/usr/bin/env python3
"""民股 MDD V2 S2 — USDTWD / CBC rediscount sensor Stage A.

Charter: research/ops/PRIV_MDD_SENSOR_MECH_V2_CHARTER.md
Prior STOP: S1 breadth/FinPub–TAIEX · PRIV_MDD_SENSOR_S1_DECISION_PACK.
Fire (lag-1) → FinPriv→0050. Sealed gates unchanged.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import e16_priv_mdd_new_mech_n1_stage_a as n1
import e16_priv_mdd_new_mech_n2_stage_a as n2
import e16_pub_priv_coexist_mdd_stage_a as base
import e16_soft_frozen_base as soft
from e45_paper_harness import load_dividends

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/priv-mdd-sensor-s2-stagea"
RESEARCH = ROOT / "research/ops"
DEF_DIR = ROOT / "data/def_proxies"
OFFENSE = n1.OFFENSE
ETF_HI_CAP = float(n2.ETF_HI_CAP)

FX_Z_THRS = (1.0, 1.5)


def build_s2_sensors(cal: pd.DatetimeIndex) -> pd.DataFrame:
    """Raw (pre-lag) FX z and CBC 63d hike flag on trading calendar."""
    fx = pd.read_csv(DEF_DIR / "USDTWD_finmind.csv", parse_dates=["date"]).sort_values("date")
    mid = fx.set_index("date")["usdtwd_mid"].astype(float).reindex(cal).ffill()
    x = np.log(mid / mid.shift(1))
    mu = x.rolling(60, min_periods=20).mean()
    sd = x.rolling(60, min_periods=20).std().replace(0.0, np.nan)
    fx_z = (x - mu) / sd

    cbc = pd.read_csv(DEF_DIR / "cbc_rediscount_rate_daily.csv", parse_dates=["date"])
    rate = cbc.set_index("date")["rediscount_pct"].astype(float).reindex(cal).ffill()
    # 63d change > 0 → hike stress (ongoing elevated vs 63d ago)
    cbc_hike = (rate - rate.shift(63)) > 0.0

    return pd.DataFrame({"fx_z": fx_z, "cbc_hike": cbc_hike.astype(float)}, index=cal)


def fire_lag1(raw: pd.Series, pred) -> pd.Series:
    x = raw.shift(1)
    return pred(x).fillna(False).astype(bool)


def _run_book(market, dividends, target, regime, *, book_id: str, meta_extra: dict):
    row = n1._sim_sf4(
        market, dividends, target, regime, book_id=book_id, meta_extra=meta_extra
    )
    for k in ("s2_family", "s2_thr", "gate_on_share", "n2_sink", "etf_hi_cap", "s1_family"):
        if k in meta_extra:
            row[k] = meta_extra[k]
    return row


def _meta(mechanism: str, **extra) -> dict:
    return {
        "mechanism": mechanism,
        "priv_pol": OFFENSE["priv_pol"],
        "fin_pub_clip": [OFFENSE["pub_lo"], OFFENSE["pub_hi"]],
        "fin_priv_clip": [OFFENSE["priv_lo"], OFFENSE["priv_hi"]],
        "prior_priv_frac": OFFENSE["prior_frac"],
        **extra,
    }


def _extend_rank(row: dict, src: dict) -> dict:
    row = dict(row)
    for k in ("s2_family", "s2_thr", "gate_on_share", "n2_sink", "s1_family"):
        if k in src and src[k] is not None:
            row[k] = src[k]
    return row


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert list(soft.SOFT_FROZEN_FIN_CLIP) == [0.6, 0.9]
    assert (DEF_DIR / "USDTWD_finmind.csv").exists()
    assert (DEF_DIR / "cbc_rediscount_rate_daily.csv").exists()

    print("building extended market ...", flush=True)
    market = base.build_extended_market()
    dividends = load_dividends()

    print("baseline LIVE_PUB_KD ...", flush=True)
    live = base.run_live_pub_kd(market, dividends)
    results: dict = {"LIVE_PUB_KD": live}

    print("SF4 offense + S2 sensors ...", flush=True)
    off_t, off_r = n1.build_sf4_pair(market, OFFENSE)
    def_t, _ = n1.build_sf4_pair(market, n1.DEFENCE_CTRL)
    cal = pd.DatetimeIndex(off_t.index)
    sens = build_s2_sensors(cal)

    print("SF4_OFFENSE ...", flush=True)
    results["SF4_OFFENSE"] = _run_book(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra=_meta("SF4_FROZEN", s2_family="CONTROL"),
    )

    print("SF4_L4_08_REF ...", flush=True)
    l4_t, l4_f = n1.apply_l4_taiex_ref(off_t, def_t, market, n1.L4_REF_THR)
    results["SF4_L4_08_REF"] = _run_book(
        market,
        dividends,
        l4_t,
        off_r.reindex(l4_t.index).ffill().bfill(),
        book_id="SF4_L4_08_REF",
        meta_extra=_meta(
            "REF_TAIEX_L4_08",
            s2_family="REF_L4",
            gate_on_share=float(l4_f.mean()) if len(l4_f) else None,
        ),
    )

    print("N2_0050_LOCAL_08_REF ...", flush=True)
    priv_dd, _, _ = n1.sleeve_nav_features(market)
    flag_n2 = (priv_dd <= -0.08).fillna(False)
    n2_t, n2_f = n2.apply_n2_relocate(off_t, flag_n2, sink="0050")
    results["N2_0050_LOCAL_08_REF"] = _run_book(
        market,
        dividends,
        n2_t,
        off_r.reindex(n2_t.index).ffill().bfill(),
        book_id="N2_0050_LOCAL_08_REF",
        meta_extra=_meta(
            "REF_N2_0050_LOCAL_08",
            s2_family="REF_N2",
            n2_sink="0050",
            gate_on_share=float(n2_f.mean()) if len(n2_f) else None,
        ),
    )

    print("S1_BREADTH_45_REF ...", flush=True)
    # tip-clean closest S1 sealed among S1 books — reference only
    import e16_priv_mdd_sensor_s1_stage_a as s1

    s1_sens = s1.build_s1_sensors(market)
    flag_s1 = s1.fire_lag1(s1_sens["stress_breadth"], lambda x: x >= 0.45)
    s1_t, s1_f = n2.apply_n2_relocate(off_t, flag_s1, sink="0050")
    results["S1_BREADTH_45_REF"] = _run_book(
        market,
        dividends,
        s1_t,
        off_r.reindex(s1_t.index).ffill().bfill(),
        book_id="S1_BREADTH_45_REF",
        meta_extra=_meta(
            "REF_S1_BREADTH_45",
            s2_family="REF_S1",
            s1_family="BREADTH",
            n2_sink="0050",
            gate_on_share=float(s1_f.mean()) if len(s1_f) else None,
        ),
    )

    specs = []
    for thr in FX_Z_THRS:
        tag = f"FX_{int(round(thr * 10))}"
        specs.append(
            (
                f"S2_{tag}",
                "USDTWD_Z",
                thr,
                fire_lag1(sens["fx_z"], lambda x, t=thr: x >= t),
            )
        )
    specs.append(
        (
            "S2_CBC_HIKE",
            "CBC_HIKE",
            "d63>0",
            fire_lag1(sens["cbc_hike"], lambda x: x > 0.5),
        )
    )
    specs.append(
        (
            "S2_OR_MID",
            "OR_MID",
            "FX1.0|CBC",
            fire_lag1(sens["fx_z"], lambda x: x >= 1.0)
            | fire_lag1(sens["cbc_hike"], lambda x: x > 0.5),
        )
    )

    for bid, family, thr, flag in specs:
        print(f"{bid} ...", flush=True)
        tgt, f = n2.apply_n2_relocate(off_t, flag, sink="0050")
        results[bid] = _run_book(
            market,
            dividends,
            tgt,
            off_r.reindex(tgt.index).ffill().bfill(),
            book_id=bid,
            meta_extra=_meta(
                f"S2_{family}_TO_0050",
                s2_family=family,
                s2_thr=thr,
                n2_sink="0050",
                etf_hi_cap=ETF_HI_CAP,
                gate_on_share=float(f.mean()) if len(f) else None,
            ),
        )

    asof = pd.to_datetime(live["nav"]["date"]).max()
    ranked = []
    for bid, row in results.items():
        if bid == "LIVE_PUB_KD":
            continue
        ranked.append(_extend_rank(base.rank_row(live, row, asof), row))
    ranked.sort(key=lambda r: r["score_mdd"], reverse=True)
    s2_ranked = [r for r in ranked if str(r.get("id", "")).startswith("S2_")]
    coexist = [r for r in ranked if r["coexist"]]
    s2_coexist = [r for r in coexist if r["id"].startswith("S2_")]

    if s2_coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["gates"]["sealed_mdd"] for r in s2_ranked):
        status = "STAGE_A_SEALED_MDD_PASS_OTHER_GATES_FAIL"
    elif any(r["score_mdd"] > 0 for r in s2_ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    keep = {
        "LIVE_PUB_KD",
        "SF4_OFFENSE",
        "SF4_L4_08_REF",
        "N2_0050_LOCAL_08_REF",
        "S1_BREADTH_45_REF",
    } | {r["id"] for r in s2_coexist} | {r["id"] for r in s2_ranked[:5]}
    for bid in keep:
        if bid in results:
            results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIV_MDD_SENSOR_S2_STAGE_A",
        "status": status,
        "charter": "research/ops/PRIV_MDD_SENSOR_MECH_V2_CHARTER.md",
        "prior_s1": "research/ops/PRIV_MDD_SENSOR_S1_DECISION_PACK.md",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "etf_hi_cap": ETF_HI_CAP,
        "sink": "0050",
        "baseline": "LIVE_PUB_KD",
        "frozen_offense": OFFENSE["id"],
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "n_s2_challengers": len(s2_ranked),
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "s2_coexist_ids": [r["id"] for r in s2_coexist],
        "best": ranked[0] if ranked else None,
        "best_s2": s2_ranked[0] if s2_ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIV_MDD_SENSOR_S2_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 民股 MDD V2 S2 — USDTWD / CBC sensor Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · frozen offense **`{OFFENSE['id']}`**",
        "Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**",
        "Mechanism: lag-1 USDTWD 60d z / CBC rediscount 63d hike → FinPriv→0050",
        "",
        "## S2 coexist",
        "",
    ]
    if s2_coexist:
        for r in s2_coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD",
        "",
        "| book | family | thr | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | gate_on% | coexist |",
        "|---|---|---|---:|---:|---:|---|---|---:|---|",
    ]
    for r in ranked:
        gos = r.get("gate_on_share")
        gos_s = f"{100.0 * float(gos):.1f}" if gos is not None else "—"
        fam = r.get("s2_family")
        thr = r.get("s2_thr")
        lines.append(
            f"| `{r['id']}` | `{fam}` | `{thr}` | {r['score_mdd']:.3f} | "
            f"{r['heldout_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{'Y' if r['tip_clean'] else 'N'} | {'Y' if r['tip_mdd_ok'] else 'N'} | "
            f"{gos_s} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.",
        "2. Do not retune N1–N3 / S1 thresholds from this S2 Stage A.",
        "3. S2 coexist → Stage B; else STOP V2 sensor ladder / Soft-Frozen KEEP.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sensor_s2_stage_a.py`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("PRIV_MDD_SENSOR_S2_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "PRIV_MDD_SENSOR_S2_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "s2_coexist_ids": payload["s2_coexist_ids"],
        "best_s2": payload["best_s2"],
        "best_overall": payload["best"],
        "frozen_offense": OFFENSE["id"],
        "next": (
            "Open Stage B dual-paper observe on s2_coexist_ids"
            if s2_coexist
            else "STOP S2 / V2 sensor ladder — Soft-Frozen 公股 KEEP; sealed unchanged; new charter or human sealed-gate only"
        ),
        "charter": "research/ops/PRIV_MDD_SENSOR_MECH_V2_CHARTER.md",
        "stage_a": "research/ops/PRIV_MDD_SENSOR_S2_STAGE_A.md",
        "prior_s1": "research/ops/PRIV_MDD_SENSOR_S1_DECISION_PACK.md",
    }
    RESEARCH.joinpath("PRIV_MDD_SENSOR_S2_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# 民股 MDD V2 S2 — Decision Pack",
        "",
        f"Date: 2026-09-19 · `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Frozen offense: `{OFFENSE['id']}` · sink FinPriv→0050",
        "",
        "## Verdict",
        "",
    ]
    if s2_coexist:
        dlines += [
            "**STAGE A CANDIDATES (S2)**:",
            "",
            *[f"- `{x}`" for x in decision["s2_coexist_ids"]],
        ]
    else:
        best = decision.get("best_s2") or decision.get("best_overall") or {}
        dlines += [
            "**STOP S2** — no USDTWD/CBC sensor book cleared MDD coexist vs `LIVE_PUB_KD`.",
            "",
            f"Best S2: `{best.get('id')}` · score_mdd **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}**",
            "",
            "Binding: Soft-Frozen 公股 KEEP · V2 S1+S2 STOP · sealed gate unchanged.",
            "Next: Soft-Frozen KEEP · or human sealed-gate · or other new charter (≠ V2 retune).",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `PRIV_MDD_SENSOR_MECH_V2_CHARTER.md`",
        "- Stage A: `PRIV_MDD_SENSOR_S2_STAGE_A.md`",
        "- Prior S1: `PRIV_MDD_SENSOR_S1_DECISION_PACK.md`",
        "",
        f"Label: `PRIV_MDD_SENSOR_S2_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("PRIV_MDD_SENSOR_S2_DECISION_PACK.md").write_text("\n".join(dlines))

    print(
        json.dumps(
            {
                "status": status,
                "s2_coexist": payload["s2_coexist_ids"],
                "best_s2": payload["best_s2"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
