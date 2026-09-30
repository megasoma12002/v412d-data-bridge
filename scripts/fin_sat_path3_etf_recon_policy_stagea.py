#!/usr/bin/env python3
"""Path3 0050 ETF recon policy Stage A (0kae) — paper only.

Parent 0kad: 0050 COMP≠SAT material · keep_0050=False no-op under freeze-sleeve-$.
Design + flip-day probe of ETF policies; Soft KEEP · broker false · cutover BLOCKED.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, load_or_build_signal
from live_path3_t0_weight_engine import sleeve_notional
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from path3_comp_sat_daily_share_ssot import load_book_shares, shares_asof
from tw_share_lots import BOARD_LOT, board_lots

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-etf-recon-policy-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_ETF_RECON_POLICY_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_ETF_RECON_POLICY_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_ETF_RECON_POLICY_STAGEA_DECISION_PACK"
REGISTER = "0kae"

ETF = "0050"
SOFT_CORE = list(FIN) + list(TEL) + [ETF]
COMP_SCHED = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/schedule_comp_h150_x_a20.csv"
SAT_SCHED = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/schedule_sat_a20_relax.csv"
STATE = ROOT / "forward/e21/portfolio_state.json"
MARKET = ROOT / "forward/e21/live_market.csv"

POLICIES = ("KEEP", "SCHEDULE_W", "LEDGER_SOFT_RATIO")


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_live() -> tuple[dict[str, float], dict[str, float], str]:
    ps = json.loads(STATE.read_text(encoding="utf-8"))
    pos = {str(k): float(v) for k, v in (ps.get("positions") or {}).items()}
    asof = str(ps.get("last_date") or "")
    m = pd.read_csv(MARKET, dtype={"code": str})
    m["date"] = pd.to_datetime(m["date"])
    day = m[m["date"] == pd.Timestamp(asof)]
    if day.empty:
        day = m[m["date"] == m["date"].max()]
        asof = str(pd.Timestamp(day["date"].iloc[0]).date())
    prices = {
        str(r.code): float(r.close)
        for r in day.itertuples()
        if str(r.code) != "TAIEX" and float(r.close) > 0
    }
    return pos, prices, asof


def _schedules() -> tuple[pd.DataFrame, dict[str, Any]]:
    c = pd.read_csv(COMP_SCHED, parse_dates=["date"]).sort_values("date")
    s = pd.read_csv(SAT_SCHED, parse_dates=["date"]).sort_values("date")
    m = c.merge(s, on="date", suffixes=("_c", "_s"))
    id_stats = {}
    for col in ["Financial", "Telecom", "0050", "DEF"]:
        d = (m[f"{col}_c"] - m[f"{col}_s"]).abs()
        id_stats[col] = {
            "max_abs": float(d.max()),
            "pct_days_differ": float((d > 1e-12).mean()),
        }
    return c.set_index("date"), {
        "comp_sat_schedule_identical": all(v["max_abs"] == 0.0 for v in id_stats.values()),
        "per_col": id_stats,
    }


def etf_target_shares(
    *,
    policy: str,
    live_pos: Mapping[str, float],
    prices: Mapping[str, float],
    ledger_shares: Mapping[str, float],
    schedule_etf_w: float | None,
) -> tuple[float, dict[str, Any]]:
    """Return target 0050 shares under policy (Soft core $ frozen unless noted)."""
    p = {str(k): float(v) for k, v in live_pos.items() if abs(float(v)) > 1e-12}
    px = {str(k): float(v) for k, v in prices.items() if float(v) > 0}
    live_etf = float(p.get(ETF, 0.0))
    meta: dict[str, Any] = {"policy": policy, "live_etf_shares": live_etf}

    if policy == "KEEP":
        meta["reason"] = "keep_live"
        return live_etf, meta

    soft_dol = sleeve_notional(SOFT_CORE, p, px)
    meta["live_soft_core_notional"] = round(soft_dol, 2)
    if soft_dol <= 1e-9 or ETF not in px:
        meta["reason"] = "no_soft_core_or_px"
        return live_etf, meta

    if policy == "SCHEDULE_W":
        w = float(schedule_etf_w or 0.0)
        meta["schedule_etf_w"] = w
        if w <= 0:
            meta["reason"] = "schedule_w_nonpos"
            return live_etf, meta
        tgt = float(board_lots(soft_dol * w / float(px[ETF])))
        meta["reason"] = "schedule_w_on_live_soft_core"
        return tgt, meta

    if policy == "LEDGER_SOFT_RATIO":
        # Paper Soft-core dollar weight of 0050 → apply to live Soft-core $.
        led = {str(k): float(v) for k, v in ledger_shares.items()}
        paper_dol = 0.0
        paper_etf = 0.0
        for c in SOFT_CORE:
            if c not in led or c not in px:
                continue
            dol = float(led[c]) * float(px[c])
            paper_dol += dol
            if c == ETF:
                paper_etf = dol
        if paper_dol <= 1e-9:
            meta["reason"] = "paper_soft_core_empty"
            return live_etf, meta
        w = paper_etf / paper_dol
        meta["paper_etf_w_in_soft_core"] = round(w, 6)
        meta["paper_soft_core_notional_at_live_px"] = round(paper_dol, 2)
        tgt = float(board_lots(soft_dol * w / float(px[ETF])))
        meta["reason"] = "ledger_soft_ratio_on_live_soft_core"
        return tgt, meta

    raise ValueError(policy)


def _delta_etf(live: float, tgt: float) -> float | None:
    d = float(tgt) - float(live)
    if abs(d) < float(BOARD_LOT) - 1e-9:
        return None
    return d


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    comp = load_book_shares(BOOK_COMP)
    sat = load_book_shares(BOOK_SAT)
    sched, sched_meta = _schedules()
    sig = load_or_build_signal()
    sig["date"] = pd.to_datetime(sig["date"])
    pos, prices, state_asof = _load_live()

    flips = sig[sig["flip"].astype(bool)].copy()
    dates = comp.index.intersection(sat.index)
    flip_rows = []
    for _, row in flips.iterrows():
        dt = pd.Timestamp(row["date"]).normalize()
        if dt not in dates:
            continue
        book = str(row["book"])
        panel = sat if book == BOOK_SAT else comp
        led = {
            str(c): float(panel.loc[dt, c])
            for c in panel.columns
            if abs(float(panel.loc[dt, c])) > 1e-12
        }
        sw = None
        if dt in sched.index:
            sw = float(sched.loc[dt, ETF])
        elif len(sched.index[sched.index <= dt]):
            sw = float(sched.loc[sched.index[sched.index <= dt][-1], ETF])

        # Use live tip pos/prices as proxy capital (Stage A fidelity), ledger asof=flip.
        entry: dict[str, Any] = {
            "date": str(dt.date()),
            "book": book,
            "book_prev": str(row.get("book_prev") or ""),
        }
        for pol in POLICIES:
            tgt, meta = etf_target_shares(
                policy=pol,
                live_pos=pos,
                prices=prices,
                ledger_shares=led,
                schedule_etf_w=sw,
            )
            dlt = _delta_etf(float(pos.get(ETF, 0.0)), tgt)
            entry[pol] = {
                "target_shares": round(tgt, 1),
                "delta_shares": None if dlt is None else round(dlt, 1),
                "traded": dlt is not None,
                "meta": meta,
            }
        flip_rows.append(entry)

    # Aggregate
    summary = {}
    for pol in POLICIES:
        traded = [r for r in flip_rows if r[pol]["traded"]]
        deltas = [float(r[pol]["delta_shares"]) for r in traded]
        summary[pol] = {
            "n_flips": len(flip_rows),
            "n_traded_0050": len(traded),
            "pct_flips_trade_0050": round(len(traded) / len(flip_rows), 6) if flip_rows else 0.0,
            "median_abs_delta_when_traded": round(float(np.median(np.abs(deltas))), 1)
            if deltas
            else 0.0,
            "max_abs_delta": round(float(np.max(np.abs(deltas))), 1) if deltas else 0.0,
        }

    # Last flip each way detail
    legs = []
    for direction, book in (("COMP→SAT", BOOK_SAT), ("SAT→COMP", BOOK_COMP)):
        sub = [r for r in flip_rows if r["book"] == book]
        if not sub:
            continue
        legs.append({"label": direction, **sub[-1]})

    # Champion rule: SCHEDULE_W dead if schedules identical; LEDGER must beat KEEP on trade rate.
    if sched_meta["comp_sat_schedule_identical"]:
        schedule_status = "RULED_OUT_IDENTICAL_COMP_SAT"
    else:
        schedule_status = "OPEN"
    ledger_beats = summary["LEDGER_SOFT_RATIO"]["n_traded_0050"] > summary["KEEP"]["n_traded_0050"]
    if schedule_status.startswith("RULED_OUT") and ledger_beats:
        verdict = "ETF_POLICY_LEDGER_RATIO_HIT"
    elif schedule_status.startswith("RULED_OUT") and summary["LEDGER_SOFT_RATIO"]["n_traded_0050"] == 0:
        verdict = "ETF_POLICY_NO_EDGE_KEEP"
    elif not schedule_status.startswith("RULED_OUT") and ledger_beats:
        verdict = "ETF_POLICY_CANDIDATES_OPEN"
    else:
        verdict = "ETF_POLICY_KEEP_DEFAULT"

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parent": "0kad",
        "state_asof": state_asof,
        "ledger_panel_end": str(pd.Timestamp(comp.index.max()).date()),
        "n_flip_rows": len(flip_rows),
        "schedule_meta": sched_meta,
        "schedule_status": schedule_status,
        "policy_summary": summary,
        "legs_last": legs,
        "verdict": verdict,
        "live_0050_shares": float(pos.get(ETF, 0.0)),
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    (OUT / "flip_etf_policy_rows.json").write_text(
        json.dumps(flip_rows, indent=2) + "\n", encoding="utf-8"
    )

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage A — Path3 0050 ETF recon policy** · Soft **KEEP** · broker **false** · "
            "cutover **BLOCKED** · no live",
            "Parent: 0kad `ETF_DIVERGES__SATELLITE_OVERLAY_BLOCK`",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Which paper policy can make Path3 move Soft `0050` when COMP≠SAT, given "
            "`keep_0050=False` freeze-sleeve-$ is a no-op?",
            "",
            "## Candidates",
            "",
            "| ID | Rule |",
            "|---|---|",
            "| `KEEP` | status quo — never touch 0050 |",
            "| `SCHEDULE_W` | paper Soft schedule `0050` weight × live Soft-core $ |",
            "| `LEDGER_SOFT_RATIO` | paper ledger $ weight 0050/(FIN+TEL+0050) × live Soft-core $ |",
            "",
            "## Method",
            "",
            "- Prove COMP vs SAT sleeve schedules identical or not",
            "- On each Path3 flip: compute 0050 target/delta under each policy (live tip capital proxy)",
            "- Champion = material flip-day 0050 trades + book-sensitive (not schedule-identical dead)",
            "",
            "## Non-goals",
            "",
            "- Live wire · mute expand · cutover ACCEPT · broker · satellite 00631L",
            "- Full NAV paper dual (Stage B after policy HIT)",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__0050_POLICY__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parent": "0kad",
                "policies": list(POLICIES),
                "soft_keep": True,
                "broker": False,
                "cutover_blocked": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · flips={len(flip_rows)} · ledger_end=`{screen['ledger_panel_end']}` · "
            f"live=`{state_asof}`",
            "",
            f"## Schedule COMP vs SAT: **{schedule_status}**",
            "",
            f"- identical={sched_meta['comp_sat_schedule_identical']}",
            "",
            "## Policy summary (flip days, live tip capital proxy)",
            "",
            "| Policy | % flips trade 0050 | n traded | median |Δ| | max |Δ| |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for pol in POLICIES:
        s = summary[pol]
        screen_md += (
            f"\n| `{pol}` | {100*s['pct_flips_trade_0050']:.1f}% | {s['n_traded_0050']} | "
            f"{s['median_abs_delta_when_traded']:.0f} | {s['max_abs_delta']:.0f} |"
        )
    screen_md += "\n\n## Last flip legs\n\n"
    for leg in legs:
        screen_md += f"- **{leg['label']}** @{leg['date']} book=`{leg['book']}`\n"
        for pol in POLICIES:
            d = leg[pol]["delta_shares"]
            screen_md += f"  - `{pol}` Δ0050={d}\n"
    screen_md += (
        f"\nRepro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_recon_policy_stagea.py`\n\n"
        f"Label: `{SCREEN_ID}_{generated[:10]}__{verdict}`\n"
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = []
    if verdict == "ETF_POLICY_LEDGER_RATIO_HIT":
        next_steps.append(
            "Stage B paper dual NAV: Path3 flip+FIN∪TEL ledger KEEP-0050 vs +LEDGER_SOFT_RATIO "
            "(tipY/held/sealed + 0050 turnover) — Soft KEEP / no live"
        )
    next_steps.append("Do not live-wire ETF policy until paper dual HIT")
    next_steps.append("0kac PAPER_WITHIN_HIT remains primary roadmap")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "parent": "0kad",
        "champion_policy": "LEDGER_SOFT_RATIO"
        if verdict == "ETF_POLICY_LEDGER_RATIO_HIT"
        else ("KEEP" if "KEEP" in verdict else None),
        "schedule_status": schedule_status,
        "policy_summary": summary,
        "soft_keep": True,
        "broker": False,
        "cutover_blocked": True,
        "live_wire": False,
        "next": next_steps,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parent: **0kad**",
            "",
            "## Finding",
            "",
            f"- COMP/SAT Soft **schedules are identical** → `SCHEDULE_W` **cannot** be Path3-book-sensitive.",
            f"- `KEEP` trades 0050 on **{summary['KEEP']['n_traded_0050']}** / {summary['KEEP']['n_flips']} flips.",
            f"- `LEDGER_SOFT_RATIO` trades 0050 on **{summary['LEDGER_SOFT_RATIO']['n_traded_0050']}** / "
            f"{summary['LEDGER_SOFT_RATIO']['n_flips']} flips "
            f"(median |Δ| {summary['LEDGER_SOFT_RATIO']['median_abs_delta_when_traded']:.0f}).",
            "",
            "## Disposition",
            "",
            f"- Champion paper policy: **`{decision['champion_policy']}`**"
            if decision["champion_policy"]
            else "- No champion — keep default",
            "- Full NAV dual = Stage B (not this pack).",
            "",
            "## Next",
            "",
            *[f"{i+1}. {s}" for i, s in enumerate(next_steps)],
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "schedule_identical": sched_meta["comp_sat_schedule_identical"],
                "ledger_trades": summary["LEDGER_SOFT_RATIO"]["n_traded_0050"],
                "keep_trades": summary["KEEP"]["n_traded_0050"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
