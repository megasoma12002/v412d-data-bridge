#!/usr/bin/env python3
"""民股 MDD V4 A1 — calendar FinPriv gate on frozen A0 episodes.

Charter: research/ops/PRIV_MDD_SEALED_EPISODE_V4_CHARTER.md
Requires: research/ops/PRIV_MDD_SEALED_EPISODE_A0.json with a1_authorized=true.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e16_priv_mdd_new_mech_n1_stage_a as n1
import e16_priv_mdd_new_mech_n2_stage_a as n2
import e16_pub_priv_coexist_mdd_stage_a as base
import e16_soft_frozen_base as soft
from e45_paper_harness import load_dividends

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/priv-mdd-sealed-episode-v4-a1"
RESEARCH = ROOT / "research/ops"
A0_PATH = RESEARCH / "PRIV_MDD_SEALED_EPISODE_A0.json"
OFFENSE = n1.OFFENSE
ETF_HI_CAP = float(n2.ETF_HI_CAP)


def load_a0() -> dict:
    if not A0_PATH.exists():
        raise SystemExit(f"missing A0 freeze file: {A0_PATH}")
    a0 = json.loads(A0_PATH.read_text())
    if not a0.get("a1_authorized"):
        raise SystemExit(f"A1 not authorized: status={a0.get('status')}")
    return a0


def episode_flag(index: pd.DatetimeIndex, peak: str, trough: str) -> pd.Series:
    lo, hi = pd.Timestamp(peak), pd.Timestamp(trough)
    return pd.Series((index >= lo) & (index <= hi), index=index)


def union_flag(index: pd.DatetimeIndex, episodes: list[dict]) -> pd.Series:
    f = pd.Series(False, index=index)
    for e in episodes:
        f = f | episode_flag(index, e["peak_date"], e["trough_date"])
    return f


def _run_book(market, dividends, target, regime, *, book_id: str, meta_extra: dict):
    row = n1._sim_sf4(
        market, dividends, target, regime, book_id=book_id, meta_extra=meta_extra
    )
    for k in (
        "v4_family",
        "v4_episode_rank",
        "v4_sink",
        "gate_on_share",
        "peak_date",
        "trough_date",
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
    for k in (
        "v4_family",
        "v4_episode_rank",
        "v4_sink",
        "gate_on_share",
        "peak_date",
        "trough_date",
    ):
        if k in src and src[k] is not None:
            row[k] = src[k]
    return row


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert list(soft.SOFT_FROZEN_FIN_CLIP) == [0.6, 0.9]
    a0 = load_a0()
    episodes = a0["episodes"]

    print("building extended market ...", flush=True)
    market = base.build_extended_market()
    dividends = load_dividends()

    print("baseline LIVE_PUB_KD ...", flush=True)
    live = base.run_live_pub_kd(market, dividends)
    results: dict = {"LIVE_PUB_KD": live}

    print("SF4 offense + defence ...", flush=True)
    off_t, off_r = n1.build_sf4_pair(market, OFFENSE)
    def_t, _ = n1.build_sf4_pair(market, n1.DEFENCE_CTRL)
    idx = pd.DatetimeIndex(off_t.index)

    print("SF4_OFFENSE ...", flush=True)
    results["SF4_OFFENSE"] = _run_book(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra=_meta("SF4_FROZEN", v4_family="CONTROL"),
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
            v4_family="REF_L4",
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
            v4_family="REF_N2",
            gate_on_share=float(n2_f.mean()) if len(n2_f) else None,
        ),
    )

    # Per-episode 0050 + CASH; union 0050 + CASH; one PUB contrast on deepest episode
    specs = []
    for e in episodes:
        rank = int(e["rank"])
        flag = episode_flag(idx, e["peak_date"], e["trough_date"])
        for sink in ("0050", "CASH"):
            specs.append(
                (
                    f"V4_E{rank}_{sink}",
                    "EPISODE",
                    rank,
                    sink,
                    flag,
                    e["peak_date"],
                    e["trough_date"],
                )
            )
    uflag = union_flag(idx, episodes)
    for sink in ("0050", "CASH"):
        specs.append((f"V4_UNION_{sink}", "UNION", None, sink, uflag, None, None))
    # contrast: deepest episode → pub-only path
    e1 = episodes[0]
    flag1 = episode_flag(idx, e1["peak_date"], e1["trough_date"])
    specs.append(
        (
            "V4_E1_PUB",
            "PUB_CONTRAST",
            1,
            "PUB",
            flag1,
            e1["peak_date"],
            e1["trough_date"],
        )
    )

    for bid, family, rank, sink, flag, peak, trough in specs:
        print(f"{bid} ...", flush=True)
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
                f"V4_{family}_{sink}",
                v4_family=family,
                v4_episode_rank=rank,
                v4_sink=sink,
                peak_date=peak,
                trough_date=trough,
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
    v4_ranked = [r for r in ranked if str(r.get("id", "")).startswith("V4_")]
    coexist = [r for r in ranked if r["coexist"]]
    v4_coexist = [r for r in coexist if r["id"].startswith("V4_")]

    if v4_coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["gates"]["sealed_mdd"] for r in v4_ranked):
        status = "STAGE_A_SEALED_MDD_PASS_OTHER_GATES_FAIL"
    elif any(r["score_mdd"] > 0 for r in v4_ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    keep = {
        "LIVE_PUB_KD",
        "SF4_OFFENSE",
        "SF4_L4_08_REF",
        "N2_0050_LOCAL_08_REF",
    } | {r["id"] for r in v4_coexist} | {r["id"] for r in v4_ranked[:5]}
    for bid in keep:
        if bid in results:
            results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIV_MDD_SEALED_EPISODE_V4_A1_STAGE_A",
        "status": status,
        "charter": "research/ops/PRIV_MDD_SEALED_EPISODE_V4_CHARTER.md",
        "a0": "research/ops/PRIV_MDD_SEALED_EPISODE_A0.md",
        "a0_episodes": episodes,
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "baseline": "LIVE_PUB_KD",
        "frozen_offense": OFFENSE["id"],
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "n_v4_challengers": len(v4_ranked),
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "v4_coexist_ids": [r["id"] for r in v4_coexist],
        "best": ranked[0] if ranked else None,
        "best_v4": v4_ranked[0] if v4_ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIV_MDD_SEALED_EPISODE_V4_A1_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 民股 MDD V4 A1 — calendar FinPriv gate Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · frozen offense **`{OFFENSE['id']}`**",
        "Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**",
        "Mechanism: FinPriv OFF on **frozen A0 sealed-episode calendars** only",
        "",
        "## Frozen A0 episodes",
        "",
    ]
    for e in episodes:
        lines.append(
            f"- E{e['rank']}: `{e['peak_date']}` → `{e['trough_date']}` · "
            f"{e['n_sessions']} sess · DD_rel {100*e['dd_rel_trough']:.2f}%"
        )
    lines += ["", "## V4 coexist", ""]
    if v4_coexist:
        for r in v4_coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD",
        "",
        "| book | family/sink | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | gate_on% | coexist |",
        "|---|---|---:|---:|---:|---|---|---:|---|",
    ]
    for r in ranked:
        gos = r.get("gate_on_share")
        gos_s = f"{100.0 * float(gos):.1f}" if gos is not None else "—"
        fs = f"{r.get('v4_family')}/{r.get('v4_sink')}"
        lines.append(
            f"| `{r['id']}` | `{fs}` | {r['score_mdd']:.3f} | "
            f"{r['heldout_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{'Y' if r['tip_clean'] else 'N'} | {'Y' if r['tip_mdd_ok'] else 'N'} | "
            f"{gos_s} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.",
        "2. Do not expand A0 episodes or invent live sensors from sealed peek.",
        "3. V4 coexist → Stage B; else STOP V4 · Soft-Frozen KEEP.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sealed_episode_v4_a1_stage_a.py`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("PRIV_MDD_SEALED_EPISODE_V4_A1_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "PRIV_MDD_SEALED_EPISODE_V4_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "v4_coexist_ids": payload["v4_coexist_ids"],
        "best_v4": payload["best_v4"],
        "best_overall": payload["best"],
        "frozen_offense": OFFENSE["id"],
        "a0_episodes": episodes,
        "next": (
            "Open Stage B dual-paper observe on v4_coexist_ids"
            if v4_coexist
            else "STOP V4 — calendar episode gates did not clear coexist (heldout/tip/sealed); Soft-Frozen KEEP"
        ),
        "charter": "research/ops/PRIV_MDD_SEALED_EPISODE_V4_CHARTER.md",
        "a0": "research/ops/PRIV_MDD_SEALED_EPISODE_A0.md",
        "stage_a": "research/ops/PRIV_MDD_SEALED_EPISODE_V4_A1_STAGE_A.md",
    }
    RESEARCH.joinpath("PRIV_MDD_SEALED_EPISODE_V4_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# 民股 MDD V4 — Decision Pack",
        "",
        f"Date: 2026-09-19 · `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Frozen offense: `{OFFENSE['id']}`",
        "",
        "## Verdict",
        "",
    ]
    if v4_coexist:
        dlines += [
            "**STAGE A CANDIDATES (V4)**:",
            "",
            *[f"- `{x}`" for x in decision["v4_coexist_ids"]],
        ]
    else:
        best = decision.get("best_v4") or decision.get("best_overall") or {}
        dlines += [
            "**STOP V4** — no frozen-episode calendar book cleared MDD coexist vs `LIVE_PUB_KD`.",
            "",
            f"Best V4: `{best.get('id')}` · score_mdd **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}** · "
            f"tip_clean **{best.get('tip_clean')}**",
            "",
            "Binding: Soft-Frozen 公股 KEEP · N1–N3+V2+V3+V4 STOP · sealed unchanged.",
            "Next: Soft-Frozen KEEP · human sealed-gate · or other new charter (≠ retune).",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `PRIV_MDD_SEALED_EPISODE_V4_CHARTER.md`",
        "- A0: `PRIV_MDD_SEALED_EPISODE_A0.md`",
        "- A1: `PRIV_MDD_SEALED_EPISODE_V4_A1_STAGE_A.md`",
        "",
        f"Label: `PRIV_MDD_SEALED_EPISODE_V4_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("PRIV_MDD_SEALED_EPISODE_V4_DECISION_PACK.md").write_text("\n".join(dlines))

    print(
        json.dumps(
            {
                "status": status,
                "v4_coexist": payload["v4_coexist_ids"],
                "best_v4": payload["best_v4"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
