#!/usr/bin/env python3
"""民股 MDD V5 — DH defend-window FSM gates FinPriv only (Stage A).

Charter: research/ops/PRIV_MDD_DH_PRIV_WINDOW_V5_CHARTER.md
Enter: frozen DH_dd06_vz1p0 on offense-book features (not FinPriv-local DD).
While DEFEND: FinPriv → 0050/cash/PUB; FinPub/TEL unchanged.
≠ SF4_DH whole-book shrink · ≠ N1–V4 retune.
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
import e45_defend_handoff_helpers as dh
from e45_paper_harness import load_dividends
from e50_early_stack_combined_nav import FIN as FIN_PUB_CODES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/priv-mdd-dh-priv-window-v5-stagea"
RESEARCH = ROOT / "research/ops"
OFFENSE = n1.OFFENSE
ETF_HI_CAP = float(n2.ETF_HI_CAP)

# Frozen DH_dd06_vz1p0 enter
DD_THR = float(dh.DD_THRESHOLD)  # 0.06
VOL_Z_THR = float(dh.VOL_Z_THRESHOLD)  # 1.0
COOLDOWN = 5
PROXY_MDD_THR = -0.10
HANDOFF_RACE_DAYS = 21
SHRINK = float(dh.SHRINK)  # 0.50 for SF4_DH_REF only

FIN_PUB = list(FIN_PUB_CODES)  # Soft-Frozen 公股 FIN — matches frozen DH recipe


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


def risk_features(market: pd.DataFrame, off_nav: pd.Series) -> dict[str, pd.Series]:
    fin = _close_panel(market, FIN_PUB).mean(axis=1)
    etf = _close_panel(market, ["0050"])["0050"]
    idx = fin.index.intersection(off_nav.index).intersection(etf.index)
    nav = off_nav.reindex(idx).ffill()
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


def build_defend_flag(
    dates: pd.DatetimeIndex,
    feat: dict[str, pd.Series],
    *,
    recover_frac: float = 0.97,
    max_def_sessions: int = 42,
    require_t2: bool = True,
    dd: float = DD_THR,
    vz: float = VOL_Z_THR,
) -> pd.Series:
    """Causal DH FSM → boolean DEFEND (Exact T+1; no peek)."""
    out = pd.Series(False, index=dates)
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
            continue

        if not defense:
            peak = max(peak, v)
            t1 = float(book_mdd.iloc[i]) <= -float(dd)
            t2 = float(fin_z.iloc[i]) >= float(vz) or float(proxy_mdd.iloc[i]) <= PROXY_MDD_THR
            if t1 and (t2 if require_t2 else True):
                defense = True
                peak = v
                def_sessions = 0
        else:
            def_sessions += 1
            if float(book_mdd.iloc[i]) <= -float(dd):
                def_sessions = 0

            recovered = v >= float(peak) * float(recover_frac)
            timed = def_sessions >= int(max_def_sessions)

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
                continue

        out.iloc[i] = bool(defense)
    return out


def apply_whole_book_shrink(
    offense: pd.DataFrame,
    flag: pd.Series,
    *,
    shrink: float = SHRINK,
) -> tuple[pd.DataFrame, pd.Series]:
    """SF4_DH_REF contrast: scale all sleeves by (1−shrink) while DEFEND (cash residual).

    e45_exposure is unsupported with FinPub/FinPriv 4-sleeve targets — weight-scale instead.
    """
    common = offense.index.intersection(flag.index)
    f = flag.reindex(common).fillna(False).astype(bool)
    out = offense.loc[common, n1.SLEEVE_COLS].astype(float).copy()
    if f.any():
        out.loc[f] = out.loc[f] * (1.0 - float(shrink))
    return out, f


def _run_book(market, dividends, target, regime, *, book_id: str, meta_extra: dict):
    row = n1._sim_sf4(
        market, dividends, target, regime, book_id=book_id, meta_extra=meta_extra
    )
    for k in ("v5_family", "v5_sink", "v5_exit", "gate_on_share", "require_t2"):
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
    for k in ("v5_family", "v5_sink", "v5_exit", "gate_on_share", "require_t2"):
        if k in src and src[k] is not None:
            row[k] = src[k]
    return row


# Stage A specs: (book_id, sink, recover, max_sess, require_t2, exit_label)
V5_SPECS = [
    ("V5_DH_0050_XDEF", "0050", 0.97, 42, True, "XDEF"),
    ("V5_DH_CASH_XDEF", "CASH", 0.97, 42, True, "XDEF"),
    ("V5_DH_0050_XLONG", "0050", 0.97, 63, True, "XLONG"),
    ("V5_DH_0050_XTIGHT", "0050", 0.99, 21, True, "XTIGHT"),
    ("V5_DH_0050_XLOOSE", "0050", 0.95, 42, True, "XLOOSE"),
    ("V5_DH_PUB_XDEF", "PUB", 0.97, 42, True, "XDEF"),
    ("V5_DH_0050_NOT2", "0050", 0.97, 42, False, "XDEF_NOT2"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert list(soft.SOFT_FROZEN_FIN_CLIP) == [0.6, 0.8]
    assert abs(DD_THR - 0.06) < 1e-12
    assert abs(VOL_Z_THR - 1.0) < 1e-12

    print("building extended market ...", flush=True)
    market = base.build_extended_market()
    dividends = load_dividends()

    print("baseline LIVE_PUB_KD ...", flush=True)
    live = base.run_live_pub_kd(market, dividends)
    results: dict = {"LIVE_PUB_KD": live}

    print("SF4 offense + defence targets ...", flush=True)
    off_t, off_r = n1.build_sf4_pair(market, OFFENSE)
    def_t, _ = n1.build_sf4_pair(market, n1.DEFENCE_CTRL)

    print("SF4_OFFENSE ...", flush=True)
    offense = _run_book(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra=_meta("SF4_FROZEN", v5_family="CONTROL"),
    )
    results["SF4_OFFENSE"] = offense

    print("DH features from SF4_OFFENSE NAV ...", flush=True)
    off_nav = _nav_series(offense["nav"])
    feat = risk_features(market, off_nav)
    idx = pd.DatetimeIndex(off_t.index).intersection(feat["off_nav"].index)

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
            v5_family="REF_L4",
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
            v5_family="REF_N2",
            gate_on_share=float(n2_f.mean()) if len(n2_f) else None,
        ),
    )

    # SF4_DH_REF — whole-book shrink contrast (report only)
    print("SF4_DH_REF ...", flush=True)
    flag_xdef = build_defend_flag(idx, feat, recover_frac=0.97, max_def_sessions=42, require_t2=True)
    flag_xdef = flag_xdef.reindex(off_t.index).fillna(False)
    dh_t, dh_f = apply_whole_book_shrink(off_t, flag_xdef)
    results["SF4_DH_REF"] = _run_book(
        market,
        dividends,
        dh_t,
        off_r.reindex(dh_t.index).ffill().bfill(),
        book_id="SF4_DH_REF",
        meta_extra=_meta(
            "REF_SF4_DH_WHOLE_BOOK",
            v5_family="REF_DH_SHRINK",
            v5_sink="SHRINK",
            v5_exit="XDEF",
            gate_on_share=float(dh_f.mean()) if len(dh_f) else None,
        ),
    )

    for bid, sink, recover, max_sess, req_t2, exit_lab in V5_SPECS:
        print(f"{bid} ...", flush=True)
        flag = build_defend_flag(
            idx,
            feat,
            recover_frac=recover,
            max_def_sessions=max_sess,
            require_t2=req_t2,
        )
        flag = flag.reindex(off_t.index).fillna(False)
        if sink == "PUB":
            tgt, f = n1.apply_priv_off_path(off_t, def_t, flag)
        else:
            tgt, f = n2.apply_n2_relocate(off_t, flag, sink=sink)
        results[bid] = _run_book(
            market,
            dividends,
            tgt,
            off_r.reindex(tgt.index).ffill().bfill(),
            book_id=bid,
            meta_extra=_meta(
                f"V5_DH_{sink}_{exit_lab}",
                v5_family="DH_PRIV_WINDOW",
                v5_sink=sink,
                v5_exit=exit_lab,
                require_t2=req_t2,
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
    v5_ranked = [r for r in ranked if str(r.get("id", "")).startswith("V5_")]
    coexist = [r for r in ranked if r["coexist"]]
    v5_coexist = [r for r in coexist if r["id"].startswith("V5_")]

    if v5_coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["gates"]["sealed_mdd"] for r in v5_ranked):
        status = "STAGE_A_SEALED_MDD_PASS_OTHER_GATES_FAIL"
    elif any(r["score_mdd"] > 0 for r in v5_ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    keep = {
        "LIVE_PUB_KD",
        "SF4_OFFENSE",
        "SF4_L4_08_REF",
        "N2_0050_LOCAL_08_REF",
        "SF4_DH_REF",
    } | {r["id"] for r in v5_coexist} | {r["id"] for r in v5_ranked[:5]}
    for bid in keep:
        if bid in results:
            results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIV_MDD_DH_PRIV_WINDOW_V5_STAGE_A",
        "status": status,
        "charter": "research/ops/PRIV_MDD_DH_PRIV_WINDOW_V5_CHARTER.md",
        "enter_recipe": dh.CHAL_ID,
        "dd_threshold": DD_THR,
        "vol_z_threshold": VOL_Z_THR,
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "baseline": "LIVE_PUB_KD",
        "frozen_offense": OFFENSE["id"],
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "n_v5_challengers": len(v5_ranked),
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "v5_coexist_ids": [r["id"] for r in v5_coexist],
        "best": ranked[0] if ranked else None,
        "best_v5": v5_ranked[0] if v5_ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIV_MDD_DH_PRIV_WINDOW_V5_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 民股 MDD V5 — DH FinPriv window Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · frozen offense **`{OFFENSE['id']}`**",
        "Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**",
        f"Enter: frozen `{dh.CHAL_ID}` (dd={DD_THR}, vol_z={VOL_Z_THR}) on offense-book features",
        "Actuator: while DEFEND → FinPriv relocate only (≠ whole-book shrink)",
        "",
        "## V5 coexist",
        "",
    ]
    if v5_coexist:
        for r in v5_coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD",
        "",
        "| book | sink/exit | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | gate_on% | coexist |",
        "|---|---|---:|---:|---:|---|---|---:|---|",
    ]
    for r in ranked:
        gos = r.get("gate_on_share")
        gos_s = f"{100.0 * float(gos):.1f}" if gos is not None else "—"
        se = f"{r.get('v5_sink')}/{r.get('v5_exit')}"
        lines.append(
            f"| `{r['id']}` | `{se}` | {r['score_mdd']:.3f} | "
            f"{r['heldout_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{'Y' if r['tip_clean'] else 'N'} | {'Y' if r['tip_mdd_ok'] else 'N'} | "
            f"{gos_s} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.",
        "2. Do not retune DH enter / N1–V4 / SF4 clips from this Stage A.",
        "3. V5 coexist → Stage B; else STOP V5 · Soft-Frozen KEEP.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_dh_priv_window_v5_stage_a.py`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("PRIV_MDD_DH_PRIV_WINDOW_V5_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "PRIV_MDD_DH_PRIV_WINDOW_V5_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "v5_coexist_ids": payload["v5_coexist_ids"],
        "best_v5": payload["best_v5"],
        "best_overall": payload["best"],
        "frozen_offense": OFFENSE["id"],
        "enter_recipe": dh.CHAL_ID,
        "next": (
            "Open Stage B dual-paper observe on v5_coexist_ids"
            if v5_coexist
            else "STOP V5 — DH FinPriv window did not clear MDD coexist; Soft-Frozen KEEP; sealed-gate or other new charter"
        ),
        "charter": "research/ops/PRIV_MDD_DH_PRIV_WINDOW_V5_CHARTER.md",
        "stage_a": "research/ops/PRIV_MDD_DH_PRIV_WINDOW_V5_STAGE_A.md",
    }
    RESEARCH.joinpath("PRIV_MDD_DH_PRIV_WINDOW_V5_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# 民股 MDD V5 — Decision Pack",
        "",
        f"Date: 2026-09-19 · `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Frozen offense: `{OFFENSE['id']}` · enter `{dh.CHAL_ID}`",
        "",
        "## Verdict",
        "",
    ]
    if v5_coexist:
        dlines += [
            "**STAGE A CANDIDATES (V5)**:",
            "",
            *[f"- `{x}`" for x in decision["v5_coexist_ids"]],
        ]
    else:
        best = decision.get("best_v5") or decision.get("best_overall") or {}
        dlines += [
            "**STOP V5** — no DH FinPriv-window book cleared MDD coexist vs `LIVE_PUB_KD`.",
            "",
            f"Best V5: `{best.get('id')}` · score_mdd **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}** · "
            f"tip_clean **{best.get('tip_clean')}**",
            "",
            "Binding: Soft-Frozen 公股 KEEP · N1–N3+V2+V3+V4+V5 STOP · sealed unchanged.",
            "Next: Soft-Frozen KEEP · human sealed-gate · or other new charter (≠ retune).",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `PRIV_MDD_DH_PRIV_WINDOW_V5_CHARTER.md`",
        "- Stage A: `PRIV_MDD_DH_PRIV_WINDOW_V5_STAGE_A.md`",
        "- DH: `E45_DEFEND_HANDOFF_PAPER_CHARTER.md`",
        "",
        f"Label: `PRIV_MDD_DH_PRIV_WINDOW_V5_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("PRIV_MDD_DH_PRIV_WINDOW_V5_DECISION_PACK.md").write_text(
        "\n".join(dlines)
    )

    print(
        json.dumps(
            {
                "status": status,
                "v5_coexist": payload["v5_coexist_ids"],
                "best_v5": payload["best_v5"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
