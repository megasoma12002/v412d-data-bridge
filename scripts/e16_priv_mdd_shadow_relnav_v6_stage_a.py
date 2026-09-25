#!/usr/bin/env python3
"""民股 MDD V6 — shadow relative-NAV continuous FinPriv damp (Stage A).

Charter: research/ops/PRIV_MDD_SHADOW_RELNAV_V6_CHARTER.md
Sensor: undamped SF4_OFFENSE vs LIVE_PUB_KD → DD_rel (lag-1).
FinPriv' = FinPriv * (1 - c * u); residual → 0050/cash/PUB blend.
δ=0.05 FROZEN. Never M1 / DH / FinPriv-sleeve DD.
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
OUT = ROOT / "repro/priv-mdd-shadow-relnav-v6-stagea"
RESEARCH = ROOT / "research/ops"
OFFENSE = n1.OFFENSE
ETF_HI_CAP = float(n2.ETF_HI_CAP)
SLEEVE_COLS = n1.SLEEVE_COLS
DELTA = 0.05  # FROZEN — not a search axis


def _nav_series(nav: pd.DataFrame) -> pd.Series:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    return d.set_index("date")["nav"].astype(float).sort_index()


def shadow_dd_rel(
    off_nav: pd.Series,
    base_nav: pd.Series,
    *,
    rolling_peak: int | None = None,
) -> pd.Series:
    """Undamped shadow relative wealth DD vs baseline."""
    common = off_nav.index.intersection(base_nav.index)
    o = off_nav.loc[common].astype(float)
    b = base_nav.loc[common].astype(float)
    w = (o / float(o.iloc[0])) / (b / float(b.iloc[0]))
    if rolling_peak is None:
        peak = w.cummax()
    else:
        peak = w.rolling(int(rolling_peak), min_periods=max(20, int(rolling_peak) // 5)).max()
    return (w / peak - 1.0).fillna(0.0)


def intensity_u(
    dd_rel: pd.Series,
    *,
    delta: float = DELTA,
    deadband: float | None = None,
) -> pd.Series:
    """u = clip(-DD_rel / δ, 0, 1); optional deadband clears shallow DD."""
    u = (-dd_rel.astype(float) / float(delta)).clip(0.0, 1.0)
    if deadband is not None:
        u = u.where(dd_rel <= -float(deadband), 0.0)
    return u.fillna(0.0)


def apply_v6_scale(
    offense: pd.DataFrame,
    u: pd.Series,
    *,
    c: float,
    sink: str,
    defence: pd.DataFrame | None = None,
    etf_hi_cap: float = ETF_HI_CAP,
) -> tuple[pd.DataFrame, pd.Series]:
    """FinPriv' = FinPriv * (1 - c * u_{lag already in u}); residual → sink."""
    common = offense.index.intersection(u.index)
    out = offense.loc[common, SLEEVE_COLS].astype(float).copy()
    # Exact T+1: caller passes lag-1 series as u
    e = (1.0 - float(c) * u.reindex(common).fillna(0.0).clip(0.0, 1.0)).clip(0.0, 1.0)
    if sink == "PUB":
        if defence is None:
            raise ValueError("PUB sink requires defence targets")
        def_a = defence.reindex(common)[SLEEVE_COLS].astype(float)
        off_a = out.to_numpy(dtype=float)
        def_b = def_a.to_numpy(dtype=float)
        e_arr = e.to_numpy(dtype=float)[:, None]
        # e=1 → full offense; e=0 → full defence (pub-only)
        blended = off_a * e_arr + def_b * (1.0 - e_arr)
        out.loc[:, SLEEVE_COLS] = blended
        return out, e

    priv = out["FinPriv"].to_numpy(dtype=float)
    new_priv = priv * e.to_numpy(dtype=float)
    residual = priv - new_priv
    out["FinPriv"] = new_priv
    if sink == "CASH":
        pass
    elif sink == "0050":
        etf = out["0050"].to_numpy(dtype=float)
        room = (float(etf_hi_cap) - etf).clip(min=0.0)
        move = np.minimum(residual, room)
        out["0050"] = etf + move
    else:
        raise ValueError(sink)
    return out, e


def _run_book(market, dividends, target, regime, *, book_id: str, meta_extra: dict):
    row = n1._sim_sf4(
        market, dividends, target, regime, book_id=book_id, meta_extra=meta_extra
    )
    for k in (
        "v6_family",
        "v6_c",
        "v6_sink",
        "v6_variant",
        "mean_exposure",
        "mean_u",
        "delta",
    ):
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
    for k in ("v6_family", "v6_c", "v6_sink", "v6_variant", "mean_exposure", "mean_u"):
        if k in src and src[k] is not None:
            row[k] = src[k]
    return row


# (book_id, c, sink, deadband, rolling_peak, variant)
V6_SPECS = [
    ("V6_C50_0050", 0.50, "0050", None, None, "BASE"),
    ("V6_C75_0050", 0.75, "0050", None, None, "BASE"),
    ("V6_C100_0050", 1.00, "0050", None, None, "BASE"),
    ("V6_C50_CASH", 0.50, "CASH", None, None, "BASE"),
    ("V6_C100_CASH", 1.00, "CASH", None, None, "BASE"),
    ("V6_C100_0050_DB01", 1.00, "0050", 0.01, None, "DB01"),
    ("V6_C100_0050_ROLL252", 1.00, "0050", None, 252, "ROLL252"),
    ("V6_C100_PUB", 1.00, "PUB", None, None, "PUB"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert list(soft.SOFT_FROZEN_FIN_CLIP) == [0.6, 0.8]
    assert abs(DELTA - 0.05) < 1e-12

    print("building extended market ...", flush=True)
    market = base.build_extended_market()
    dividends = load_dividends()

    print("baseline LIVE_PUB_KD ...", flush=True)
    live = base.run_live_pub_kd(market, dividends)
    results: dict = {"LIVE_PUB_KD": live}

    print("SF4 offense + defence ...", flush=True)
    off_t, off_r = n1.build_sf4_pair(market, OFFENSE)
    def_t, _ = n1.build_sf4_pair(market, n1.DEFENCE_CTRL)

    print("SF4_OFFENSE (undamped shadow) ...", flush=True)
    offense = _run_book(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra=_meta("SF4_FROZEN", v6_family="CONTROL"),
    )
    results["SF4_OFFENSE"] = offense

    # Shadow sensor from undamped NAVs only — never damped challenger
    off_nav = _nav_series(offense["nav"])
    base_nav = _nav_series(live["nav"])
    dd_exp = shadow_dd_rel(off_nav, base_nav, rolling_peak=None)
    dd_roll = shadow_dd_rel(off_nav, base_nav, rolling_peak=252)

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
            v6_family="REF_L4",
            mean_exposure=1.0 - float(l4_f.mean()) if len(l4_f) else None,
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
            v6_family="REF_N2",
            mean_exposure=1.0 - float(n2_f.mean()) if len(n2_f) else None,
        ),
    )

    for bid, c, sink, deadband, roll, variant in V6_SPECS:
        print(f"{bid} ...", flush=True)
        dd = dd_roll if roll else dd_exp
        u_raw = intensity_u(dd, delta=DELTA, deadband=deadband)
        u_lag = u_raw.shift(1).fillna(0.0)  # Exact T+1
        tgt, e = apply_v6_scale(
            off_t, u_lag, c=c, sink=sink, defence=def_t if sink == "PUB" else None
        )
        results[bid] = _run_book(
            market,
            dividends,
            tgt,
            off_r.reindex(tgt.index).ffill().bfill(),
            book_id=bid,
            meta_extra=_meta(
                f"V6_SHADOW_{variant}_{sink}_C{int(round(c*100))}",
                v6_family="SHADOW_RELNAV",
                v6_c=c,
                v6_sink=sink,
                v6_variant=variant,
                delta=DELTA,
                mean_exposure=float(e.mean()) if len(e) else None,
                mean_u=float(u_lag.reindex(e.index).mean()) if len(e) else None,
            ),
        )

    asof = pd.to_datetime(live["nav"]["date"]).max()
    ranked = []
    for bid, row in results.items():
        if bid == "LIVE_PUB_KD":
            continue
        ranked.append(_extend_rank(base.rank_row(live, row, asof), row))
    ranked.sort(key=lambda r: r["score_mdd"], reverse=True)
    v6_ranked = [r for r in ranked if str(r.get("id", "")).startswith("V6_")]
    coexist = [r for r in ranked if r["coexist"]]
    v6_coexist = [r for r in coexist if r["id"].startswith("V6_")]

    if v6_coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["gates"]["sealed_mdd"] for r in v6_ranked):
        status = "STAGE_A_SEALED_MDD_PASS_OTHER_GATES_FAIL"
    elif any(r["score_mdd"] > 0 for r in v6_ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    keep = {
        "LIVE_PUB_KD",
        "SF4_OFFENSE",
        "SF4_L4_08_REF",
        "N2_0050_LOCAL_08_REF",
    } | {r["id"] for r in v6_coexist} | {r["id"] for r in v6_ranked[:5]}
    for bid in keep:
        if bid in results:
            results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIV_MDD_SHADOW_RELNAV_V6_STAGE_A",
        "status": status,
        "charter": "research/ops/PRIV_MDD_SHADOW_RELNAV_V6_CHARTER.md",
        "sensor": "undamped_shadow_DD_rel_SF4_OFFENSE_vs_LIVE_PUB_KD",
        "delta": DELTA,
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "baseline": "LIVE_PUB_KD",
        "frozen_offense": OFFENSE["id"],
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "n_v6_challengers": len(v6_ranked),
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "v6_coexist_ids": [r["id"] for r in v6_coexist],
        "best": ranked[0] if ranked else None,
        "best_v6": v6_ranked[0] if v6_ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIV_MDD_SHADOW_RELNAV_V6_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 民股 MDD V6 — shadow relative-NAV FinPriv damp Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · frozen offense **`{OFFENSE['id']}`**",
        "Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**",
        f"Sensor: undamped shadow `DD_rel(SF4_OFFENSE vs LIVE_PUB)` · δ=**{DELTA}** frozen · lag-1",
        "Actuator: `FinPriv' = FinPriv · (1 − c · u)` · residual → 0050/cash/PUB",
        "",
        "## V6 coexist",
        "",
    ]
    if v6_coexist:
        for r in v6_coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD",
        "",
        "| book | c/sink/var | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | mean_u | coexist |",
        "|---|---|---:|---:|---:|---|---|---:|---|",
    ]
    for r in ranked:
        if str(r.get("id", "")).startswith("V6_"):
            cs = f"{r.get('v6_c')}/{r.get('v6_sink')}/{r.get('v6_variant')}"
            mu = r.get("mean_u")
            mu_s = f"{float(mu):.3f}" if mu is not None else "—"
        else:
            cs = str(r.get("v6_family") or "—")
            mu_s = "—"
        lines.append(
            f"| `{r['id']}` | `{cs}` | {r['score_mdd']:.3f} | "
            f"{r['heldout_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{'Y' if r['tip_clean'] else 'N'} | {'Y' if r['tip_mdd_ok'] else 'N'} | "
            f"{mu_s} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.",
        "2. Do not retune δ / N1–V5 / SF4 clips / sealed from this Stage A.",
        "3. V6 coexist → Stage B; else STOP V6 · Soft-Frozen KEEP.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_shadow_relnav_v6_stage_a.py`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("PRIV_MDD_SHADOW_RELNAV_V6_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "PRIV_MDD_SHADOW_RELNAV_V6_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "v6_coexist_ids": payload["v6_coexist_ids"],
        "best_v6": payload["best_v6"],
        "best_overall": payload["best"],
        "frozen_offense": OFFENSE["id"],
        "delta": DELTA,
        "next": (
            "Open Stage B dual-paper observe on v6_coexist_ids"
            if v6_coexist
            else "STOP V6 — shadow relative-NAV damp did not clear MDD coexist; Soft-Frozen KEEP; sealed-gate or other new charter"
        ),
        "charter": "research/ops/PRIV_MDD_SHADOW_RELNAV_V6_CHARTER.md",
        "stage_a": "research/ops/PRIV_MDD_SHADOW_RELNAV_V6_STAGE_A.md",
    }
    RESEARCH.joinpath("PRIV_MDD_SHADOW_RELNAV_V6_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# 民股 MDD V6 — Decision Pack",
        "",
        f"Date: 2026-09-19 · `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Frozen offense: `{OFFENSE['id']}` · δ=`{DELTA}` · sensor shadow `DD_rel`",
        "",
        "## Verdict",
        "",
    ]
    if v6_coexist:
        dlines += [
            "**STAGE A CANDIDATES (V6)**:",
            "",
            *[f"- `{x}`" for x in decision["v6_coexist_ids"]],
        ]
    else:
        best = decision.get("best_v6") or decision.get("best_overall") or {}
        dlines += [
            "**STOP V6** — no shadow-relnav book cleared MDD coexist vs `LIVE_PUB_KD`.",
            "",
            f"Best V6: `{best.get('id')}` · score_mdd **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}** · "
            f"tip_clean **{best.get('tip_clean')}**",
            "",
            "Binding: Soft-Frozen 公股 KEEP · N1–N5+V6 STOP · sealed unchanged.",
            "Next: Soft-Frozen KEEP · human sealed-gate · or other new charter (≠ retune).",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `PRIV_MDD_SHADOW_RELNAV_V6_CHARTER.md`",
        "- Stage A: `PRIV_MDD_SHADOW_RELNAV_V6_STAGE_A.md`",
        "",
        f"Label: `PRIV_MDD_SHADOW_RELNAV_V6_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("PRIV_MDD_SHADOW_RELNAV_V6_DECISION_PACK.md").write_text(
        "\n".join(dlines)
    )

    print(
        json.dumps(
            {
                "status": status,
                "v6_coexist": payload["v6_coexist_ids"],
                "best_v6": payload["best_v6"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
