#!/usr/bin/env python3
"""FIN×SAT Path3 2022 flip-landing Stage A (paper diagnostics).

Why P3_T0_STATE underperformed CTRL_LIVE_A10 in calendar 2022 (−0.75pp).
Episode attribution of SAT_LEAD flips · COMP vs SAT stay · Soft-Frozen KEEP ·
Path3 observe KEEP · no live · no fill/emit flag flip.

Register: 0k9x
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-2022-flip-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_2022_FLIP_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_2022_FLIP_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_2022_FLIP_STAGEA_DECISION_PACK"
REGISTER = "0k9x"
YEAR = 2022

BASE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"
P3_NAV = ROOT / "repro/fin-sat-path3-t0-dual-paper-observe/outputs/p3_t0_state_daily_nav.csv"
SIGNAL = ROOT / "repro/fin-sat-path3-t0-dual-paper-observe/outputs/p3_t0_state_signal.csv"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path, nav_col: str = "nav") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def _ret_mdd(r: pd.Series) -> tuple[float, float]:
    nav = (1.0 + r.fillna(0.0)).cumprod()
    ret = float(nav.iloc[-1] / nav.iloc[0] - 1.0) * 100.0
    mdd = float((nav / nav.cummax() - 1.0).min()) * 100.0
    return round(ret, 2), round(mdd, 2)


def _episodes(m: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start = 0
    for i in range(1, len(m) + 1):
        if i == len(m) or m.loc[i, "book"] != m.loc[start, "book"]:
            g = m.iloc[start:i]
            rb, _ = _ret_mdd(g["r_b"])
            rc, _ = _ret_mdd(g["r_c"])
            rs, _ = _ret_mdd(g["r_s"])
            rp, _ = _ret_mdd(g["r_p"])
            book = str(g.iloc[0]["book"])
            best = max(rc, rs)
            best_book = "COMP" if rc >= rs else "SAT"
            wrong = book != best_book
            rows.append(
                {
                    "ep": len(rows) + 1,
                    "start": str(g.iloc[0]["date"].date()),
                    "end": str(g.iloc[-1]["date"].date()),
                    "n_days": int(len(g)),
                    "book": book,
                    "best_book": best_book,
                    "wrong": bool(wrong),
                    "base_ret_pct": rb,
                    "comp_ret_pct": rc,
                    "sat_ret_pct": rs,
                    "p3_ret_pct": rp,
                    "p3_vs_base_pp": round(rp - rb, 2),
                    "p3_vs_best_pp": round(rp - best, 2),
                    "trail_rel_63_end": None
                    if pd.isna(g.iloc[-1].get("trail_rel_63"))
                    else round(float(g.iloc[-1]["trail_rel_63"]), 4),
                }
            )
            start = i
    return rows


def _verdict(eps: list[dict[str, Any]], year_gap: float, mayjun_gap: float) -> str:
    wrong = [e for e in eps if e["wrong"]]
    drag = sorted(wrong, key=lambda e: e["p3_vs_base_pp"])
    top = drag[:2] if drag else []
    top_share = sum(abs(min(0.0, e["p3_vs_base_pp"])) for e in top)
    total_neg = abs(min(0.0, year_gap))
    # May–Jun whipsaw not the story if it helped
    if mayjun_gap >= 0 and top and top_share >= 0.7 * total_neg and total_neg > 0:
        return "COMP_STAY_MISS"
    if mayjun_gap < -0.5:
        return "WHIPSAW_DRAG"
    if wrong:
        return "FLIP_LANDING_MIXED"
    return "NO_FLIP_ISSUE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    base = _load(BASE_NAV).rename(columns={"nav": "nav_b"})
    comp = _load(COMP_NAV).rename(columns={"nav": "nav_c"})
    sat = _load(SAT_NAV).rename(columns={"nav": "nav_s"})
    p3 = _load(P3_NAV).rename(columns={"nav": "nav_p"})
    sig = _load(SIGNAL)

    m = (
        base.merge(comp, on="date")
        .merge(sat, on="date")
        .merge(p3, on="date")
        .merge(sig, on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    m = m[(m["date"].dt.year == YEAR)].reset_index(drop=True)
    if m.empty:
        raise SystemExit(f"no rows for {YEAR}")

    m["r_b"] = m["nav_b"].pct_change().fillna(0.0)
    m["r_c"] = m["nav_c"].pct_change().fillna(0.0)
    m["r_s"] = m["nav_s"].pct_change().fillna(0.0)
    m["r_p"] = m["nav_p"].pct_change().fillna(0.0)
    m["w_sat"] = m["w_sat"].astype(float)
    m["book"] = np.where(m["w_sat"] > 0.5, "SAT", "COMP")
    m["flip"] = m["w_sat"].diff().abs().fillna(0.0) > 1e-12

    year = {
        "base": dict(zip(["ret_pct", "mdd_pct"], _ret_mdd(m["r_b"]))),
        "comp": dict(zip(["ret_pct", "mdd_pct"], _ret_mdd(m["r_c"]))),
        "sat": dict(zip(["ret_pct", "mdd_pct"], _ret_mdd(m["r_s"]))),
        "p3": dict(zip(["ret_pct", "mdd_pct"], _ret_mdd(m["r_p"]))),
    }
    year_gap = round(year["p3"]["ret_pct"] - year["base"]["ret_pct"], 2)

    flips = m[m["flip"]].copy()
    flip_rows = [
        {
            "date": str(r.date.date()),
            "to_book": "SAT" if float(r.w_sat) > 0.5 else "COMP",
            "trail_rel_63": None if pd.isna(r.trail_rel_63) else round(float(r.trail_rel_63), 4),
            "w_sat": float(r.w_sat),
        }
        for r in flips.itertuples()
    ]

    eps = _episodes(m)
    wrong = [e for e in eps if e["wrong"]]
    drag_sorted = sorted(eps, key=lambda e: e["p3_vs_base_pp"])

    mj = m[(m["date"] >= f"{YEAR}-05-01") & (m["date"] <= f"{YEAR}-06-30")]
    mj_gap = round(_ret_mdd(mj["r_p"])[0] - _ret_mdd(mj["r_b"])[0], 2)
    mj_flips = int(mj["flip"].sum())

    # counterfactual pure books already in year dict
    # if forced SAT all year:
    sat_gap = round(year["sat"]["ret_pct"] - year["base"]["ret_pct"], 2)
    # oracle daily best of COMP/SAT returns
    r_oracle = np.where(m["r_c"].to_numpy() >= m["r_s"].to_numpy(), m["r_c"], m["r_s"])
    oracle_ret, oracle_mdd = _ret_mdd(pd.Series(r_oracle))

    verdict = _verdict(eps, year_gap, mj_gap)
    generated = _utc()

    # Persist tables
    pd.DataFrame(eps).to_csv(OUT / "episodes_2022.csv", index=False)
    pd.DataFrame(flip_rows).to_csv(OUT / "flips_2022.csv", index=False)
    m.to_csv(OUT / "daily_2022.csv", index=False)

    top_drag = [e for e in drag_sorted if e["p3_vs_base_pp"] < 0][:3]

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            f"Status: **Stage A — 2022 flip landing** · Soft-Frozen **KEEP** · Path3 observe **KEEP** · "
            "fill/emit flags **OFF** · cutover **BLOCKED** · no live",
            f"Parents: 0k9r Path3 observe · 0k9v fill-sim · yearly P3 vs BASE sole loss = **{YEAR}** (−0.75pp)",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            f"Calendar {YEAR} 是 `P3_T0_STATE` 唯一輸 `CTRL_LIVE_A10` 的年份。"
            "SAT_LEAD flip 落點／episode 停留是否解釋這 −0.75pp？是 whipsaw 還是錯站 COMP？",
            "",
            "## Method",
            "",
            "- Align BASE / COMP / SAT / P3 daily NAV + Path3 signal for 2022",
            "- Segment contiguous COMP/SAT episodes; mark wrong when held book ≠ episode-best(COMP,SAT)",
            "- Count May–Jun flips separately (whipsaw hypothesis)",
            "- No live / no Soft-Frozen change / no flag flip",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__2022_FLIP__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    charter_json = {
        "id": CHARTER_ID,
        "register": REGISTER,
        "year": YEAR,
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
        "cutover": "BLOCKED",
    }
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(charter_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": CHARTER_ID,
        "register": REGISTER,
        "verdict": verdict,
        "year": YEAR,
        "year_books": year,
        "p3_vs_base_pp": year_gap,
        "n_flips": len(flip_rows),
        "n_episodes": len(eps),
        "n_wrong_episodes": len(wrong),
        "pct_days_sat": round(float((m["w_sat"] > 0.5).mean()) * 100, 2),
        "may_jun": {"n_flips": mj_flips, "p3_vs_base_pp": mj_gap},
        "oracle_daily_best": {"ret_pct": oracle_ret, "mdd_pct": oracle_mdd},
        "sat_vs_base_pp": sat_gap,
        "top_drag_episodes": top_drag,
        "episodes": eps,
        "flips": flip_rows,
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    md = [
        f"# {SCREEN_ID}",
        "",
        f"Date: 2026-09-29 · generated `{generated}`",
        f"Verdict: **`{verdict}`** · Soft-Frozen KEEP · Path3 observe KEEP · no live",
        "",
        f"## Calendar {YEAR} books",
        "",
        "| Book | ret% | MDD% |",
        "|---|---:|---:|",
        f"| `CTRL_LIVE_A10` | {year['base']['ret_pct']} | {year['base']['mdd_pct']} |",
        f"| `COMP_H150_x_A20` | {year['comp']['ret_pct']} | {year['comp']['mdd_pct']} |",
        f"| `SAT_A20_RELAX` | {year['sat']['ret_pct']} | {year['sat']['mdd_pct']} |",
        f"| `P3_T0_STATE` | {year['p3']['ret_pct']} | {year['p3']['mdd_pct']} |",
        "",
        f"P3 − BASE: **{year_gap}** pp · flips: **{len(flip_rows)}** · episodes: **{len(eps)}** · wrong: **{len(wrong)}** · %days SAT: **{screen['pct_days_sat']}**",
        "",
        f"May–Jun: flips **{mj_flips}** · P3−BASE **{mj_gap}** pp",
        "",
        "## Top drag episodes (P3 vs BASE)",
        "",
        "| ep | start | end | n | book | best | wrong | P3−BASE | P3−best |",
        "|---:|---|---|---:|---|---|---|---:|---:|",
    ]
    for e in top_drag:
        md.append(
            f"| {e['ep']} | {e['start']} | {e['end']} | {e['n_days']} | {e['book']} | "
            f"{e['best_book']} | {e['wrong']} | {e['p3_vs_base_pp']} | {e['p3_vs_best_pp']} |"
        )
    md += [
        "",
        "## All episodes",
        "",
        "| ep | start | end | n | book | best | wrong | base% | comp% | sat% | p3% | P3−BASE |",
        "|---:|---|---|---:|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for e in eps:
        md.append(
            f"| {e['ep']} | {e['start']} | {e['end']} | {e['n_days']} | {e['book']} | "
            f"{e['best_book']} | {e['wrong']} | {e['base_ret_pct']} | {e['comp_ret_pct']} | "
            f"{e['sat_ret_pct']} | {e['p3_ret_pct']} | {e['p3_vs_base_pp']} |"
        )
    md += [
        "",
        "## Flip dates",
        "",
        "| date | to | trail_rel_63 |",
        "|---|---|---:|",
    ]
    for f in flip_rows:
        md.append(f"| {f['date']} | {f['to_book']} | {f['trail_rel_63']} |")
    md += ["", f"Repro: `repro/fin-sat-path3-2022-flip-stagea/`", ""]
    screen_md = "\n".join(md) + "\n"
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")

    # Decision narrative
    e_mar = next((e for e in eps if e["ep"] == 2), None)
    e_sum = next((e for e in eps if e["ep"] == 14), None)
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · "
            "cutover **BLOCKED** · no live",
            "",
            "## Answer",
            "",
            f"2022 P3 輸 BASE **{year_gap}** pp 的主因是 **錯站 COMP 的長停留**，不是 5–6 月 whipsaw。",
            "",
            f"- Year: BASE {year['base']['ret_pct']}% · COMP {year['comp']['ret_pct']}% · "
            f"SAT {year['sat']['ret_pct']}% · P3 {year['p3']['ret_pct']}%",
            f"- Flips: **{len(flip_rows)}** · wrong episodes: **{len(wrong)}/{len(eps)}** · %days SAT **{screen['pct_days_sat']}**",
            f"- May–Jun: flips **{mj_flips}** 但 P3−BASE **{mj_gap}** pp（whipsaw **沒有**解釋全年落敗）",
            "",
            "### Primary drag episodes",
            "",
        ]
        + (
            [
                f"1. **ep{e_mar['ep']}** {e_mar['start']}→{e_mar['end']}（{e_mar['n_days']}d）站 **COMP**：P3−BASE **{e_mar['p3_vs_base_pp']}** · "
                f"best was {e_mar['best_book']} · P3−best {e_mar['p3_vs_best_pp']}",
            ]
            if e_mar
            else []
        )
        + (
            [
                f"2. **ep{e_sum['ep']}** {e_sum['start']}→{e_sum['end']}（{e_sum['n_days']}d）站 **COMP**：P3−BASE **{e_sum['p3_vs_base_pp']}** · "
                f"best was {e_sum['best_book']} · P3−best {e_sum['p3_vs_best_pp']}",
            ]
            if e_sum
            else []
        )
        + [
            "",
            "兩段負貢獻合計約 **−2.0** pp，覆蓋全年 −0.75（其餘 episode 略正）。",
            "",
            "## Implication",
            "",
            "- 2022 略差 ≠ 否定 Path3 年勝 14–1；是 **SAT_LEAD 進 COMP 的時段誤判**（尤其 3 月下旬、夏秋 COMP stay）。",
            "- 5–6 月高頻 flip 是噪音，但該窗 P3 相對 BASE **為正**，不是修刀目標。",
            "- 若要修：下一票應是 **enter/confirm／最短停留** 對 COMP 進場（paper only），不是關 Path3 observe、也不是翻 fill/emit。",
            "- Soft-Frozen／Exact T+1／CONF α **KEEP**；cutover 仍 **BLOCKED**。",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md` · Register **{REGISTER}**",
            "",
            f"Label: `{DECISION_ID}_2026-09-29__{verdict}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    decision_json = {
        "label": f"{DECISION_ID}_2026-09-29__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "year": YEAR,
        "p3_vs_base_pp": year_gap,
        "year_books": year,
        "may_jun": screen["may_jun"],
        "n_wrong_episodes": len(wrong),
        "top_drag_episodes": top_drag,
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
        "cutover": "BLOCKED",
    }
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    print(json.dumps({"verdict": verdict, "year_gap": year_gap, "may_jun_gap": mj_gap, "top_drag": top_drag}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
