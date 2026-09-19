#!/usr/bin/env python3
"""民股 MDD V4 A0 — sealed relative-DD episode autopsy (freeze before A1).

Charter: research/ops/PRIV_MDD_SEALED_EPISODE_V4_CHARTER.md
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e16_priv_mdd_new_mech_n1_stage_a as n1
import e16_pub_priv_coexist_mdd_stage_a as base
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/priv-mdd-sealed-episode-v4-a0"
RESEARCH = ROOT / "research/ops"
OFFENSE = n1.OFFENSE
N_EPISODES = 3
MAX_SPAN = 120
SEALED = "sealed_2023_plus"


def _nav_series(nav: pd.DataFrame) -> pd.Series:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    return d.set_index("date")["nav"].astype(float).sort_index()


def sealed_slice(nav: pd.Series) -> pd.Series:
    a, b = WINDOWS_STANDARD[SEALED]
    out = nav.copy()
    if a is not None:
        out = out[out.index >= pd.Timestamp(a)]
    if b is not None:
        out = out[out.index <= pd.Timestamp(b)]
    return out


def find_episodes(w_rel: pd.Series, n: int = N_EPISODES) -> list[dict]:
    """Deepest n relative-DD troughs with peak→trough spans (non-overlapping)."""
    peak = w_rel.cummax()
    dd = w_rel / peak - 1.0
    covered = pd.Series(False, index=w_rel.index)
    episodes = []
    work_dd = dd.copy()
    for rank in range(1, n + 1):
        work_dd = work_dd.where(~covered)
        if work_dd.dropna().empty:
            break
        trough_dt = work_dd.idxmin()
        trough_dd = float(work_dd.loc[trough_dt])
        peak_val = float(peak.loc[trough_dt])
        # last date <= trough where wealth set the running max
        pre = w_rel.loc[:trough_dt]
        peak_candidates = pre[pre >= peak_val - 1e-12]
        peak_dt = peak_candidates.index[-1]
        span_idx = w_rel.loc[peak_dt:trough_dt].index
        n_sess = int(len(span_idx))
        episodes.append(
            {
                "rank": rank,
                "peak_date": str(pd.Timestamp(peak_dt).date()),
                "trough_date": str(pd.Timestamp(trough_dt).date()),
                "dd_rel_trough": round(trough_dd, 6),
                "n_sessions": n_sess,
                "span_too_long": n_sess > MAX_SPAN,
            }
        )
        covered.loc[span_idx] = True
    return episodes


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    assert list(soft.SOFT_FROZEN_FIN_CLIP) == [0.6, 0.9]

    print("building extended market ...", flush=True)
    market = base.build_extended_market()
    dividends = load_dividends()

    print("LIVE_PUB_KD ...", flush=True)
    live = base.run_live_pub_kd(market, dividends)
    print("SF4_OFFENSE ...", flush=True)
    off_t, off_r = n1.build_sf4_pair(market, OFFENSE)
    offense = n1._sim_sf4(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra={
            "mechanism": "SF4_FROZEN",
            "priv_pol": OFFENSE["priv_pol"],
            "fin_pub_clip": [OFFENSE["pub_lo"], OFFENSE["pub_hi"]],
            "fin_priv_clip": [OFFENSE["priv_lo"], OFFENSE["priv_hi"]],
            "prior_priv_frac": OFFENSE["prior_frac"],
        },
    )

    b = sealed_slice(_nav_series(live["nav"]))
    c = sealed_slice(_nav_series(offense["nav"]))
    common = b.index.intersection(c.index)
    b, c = b.loc[common], c.loc[common]
    assert len(common) >= 60, f"sealed overlap too short: {len(common)}"
    w_rel = (c / float(c.iloc[0])) / (b / float(b.iloc[0]))
    episodes = find_episodes(w_rel, N_EPISODES)
    any_long = any(e["span_too_long"] for e in episodes)
    status = "A0_STOP_SPAN_TOO_LONG" if any_long else "A0_FROZEN_OK"
    a1_authorized = status == "A0_FROZEN_OK"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIV_MDD_SEALED_EPISODE_A0",
        "status": status,
        "a1_authorized": a1_authorized,
        "charter": "research/ops/PRIV_MDD_SEALED_EPISODE_V4_CHARTER.md",
        "baseline": "LIVE_PUB_KD",
        "challenger": "SF4_OFFENSE",
        "frozen_offense": OFFENSE["id"],
        "window": SEALED,
        "n_episodes_requested": N_EPISODES,
        "max_span_sessions": MAX_SPAN,
        "n_sealed_sessions": int(len(common)),
        "sealed_start": str(common.min().date()),
        "sealed_end": str(common.max().date()),
        "episodes": episodes,
        "live_wire": False,
        "soft_frozen_keep": True,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIV_MDD_SEALED_EPISODE_A0.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 民股 MDD V4 A0 — Sealed episode autopsy (FROZEN)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · A1 authorized: **{a1_authorized}**",
        f"Window: `{SEALED}` · `{payload['sealed_start']}` → `{payload['sealed_end']}` · n={payload['n_sealed_sessions']}",
        f"Challenger: `SF4_OFFENSE` (`{OFFENSE['id']}`) vs `LIVE_PUB_KD`",
        f"Rule: deepest {N_EPISODES} relative-DD troughs · max span **{MAX_SPAN}** sessions",
        "",
        "## Episodes (frozen)",
        "",
        "| rank | peak | trough | DD_rel | sessions | too_long |",
        "|---:|---|---|---:|---:|---|",
    ]
    for e in episodes:
        lines.append(
            f"| {e['rank']} | `{e['peak_date']}` | `{e['trough_date']}` | "
            f"{100*e['dd_rel_trough']:.2f}% | {e['n_sessions']} | "
            f"{'Y' if e['span_too_long'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen KEEP · sealed gate unchanged · no live wire.",
        "2. Episode list is **FROZEN** — do not expand after A1 starts.",
        (
            "3. A1 calendar FinPriv gate **authorized**."
            if a1_authorized
            else "3. A1 **not** authorized (span too long) — Soft-Frozen KEEP."
        ),
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sealed_episode_v4_a0.py`",
        "",
        f"Label: `PRIV_MDD_SEALED_EPISODE_A0_2026-09-19__{status}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "A0.md").write_text(md)
    RESEARCH.joinpath("PRIV_MDD_SEALED_EPISODE_A0.md").write_text(md)

    print(json.dumps({"status": status, "a1_authorized": a1_authorized, "episodes": episodes}, indent=2))
    return 0 if a1_authorized else 2


if __name__ == "__main__":
    raise SystemExit(main())
