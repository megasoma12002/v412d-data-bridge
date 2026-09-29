#!/usr/bin/env python3
"""FIN×SAT Path3 wrong-stay census Stage A (paper).

Multi-year count of Path3 站錯 episodes under SAT_LEAD θ, reusing the 0k9x
definition exactly: contiguous COMP/SAT episode is wrong when held book ≠
episode-best(COMP,SAT) on episode cum-returns.

Compare observe θ=0.01 vs paper challenger θ=0.005 (0ka3/0ka4). Soft-Frozen
KEEP · Path3 observe θ=0.01 KEEP · fill/emit OFF · no live.

Register: 0ka5
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
REPRO = ROOT / "repro" / "fin-sat-path3-wrong-stay-census-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_WRONG_STAY_CENSUS_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_WRONG_STAY_CENSUS_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_WRONG_STAY_CENSUS_STAGEA_DECISION_PACK"
REGISTER = "0ka5"

BASE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

# Pre-registered (no expand after peek)
THETAS = (0.01, 0.005)
SEVERE_GAP_PP = -0.5
SEVERE_MIN_DAYS = 10
MOD_GAP_PP = -0.1
MOD_VS_BEST_PP = -0.3
THETA_CUT_FRAC = 0.70  # 0.005 severe ≤ 70% of 0.01 → "cuts"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)[["date", "nav"]].assign(
        nav=lambda x: x["nav"].astype(float)
    )


def _trail(r: pd.Series, n: int) -> pd.Series:
    return (1.0 + r).rolling(n, min_periods=n).apply(lambda x: float(np.prod(x) - 1.0), raw=True)


def _ret_mdd(r: pd.Series) -> tuple[float, float]:
    nav = (1.0 + r.fillna(0.0)).cumprod()
    ret = float(nav.iloc[-1] / nav.iloc[0] - 1.0) * 100.0
    mdd = float((nav / nav.cummax() - 1.0).min()) * 100.0
    return round(ret, 2), round(mdd, 2)


def _severity(e: dict[str, Any]) -> str | None:
    if not e["wrong"]:
        return None
    gap = float(e["p3_vs_base_pp"])
    vs_best = float(e["p3_vs_best_pp"])
    n = int(e["n_days"])
    if gap <= SEVERE_GAP_PP and n >= SEVERE_MIN_DAYS:
        return "SEVERE"
    if gap <= MOD_GAP_PP or vs_best <= MOD_VS_BEST_PP:
        return "MODERATE"
    return "MILD"


def _episodes(m: pd.DataFrame) -> list[dict[str, Any]]:
    """0k9x definition; year-clipped panel (boundary restarts episode)."""
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
            side = None
            if wrong:
                side = "COMP_WRONG" if book == "COMP" else "SAT_WRONG"
            e: dict[str, Any] = {
                "ep": len(rows) + 1,
                "start": str(g.iloc[0]["date"].date()),
                "end": str(g.iloc[-1]["date"].date()),
                "year": int(g.iloc[0]["date"].year),
                "n_days": int(len(g)),
                "book": book,
                "best_book": best_book,
                "wrong": bool(wrong),
                "wrong_side": side,
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
            e["severity"] = _severity(e)
            rows.append(e)
            start = i
    return rows


def _year_panel(m_full: pd.DataFrame, year: int) -> pd.DataFrame:
    return m_full[m_full["date"].dt.year == year].reset_index(drop=True)


def _summarize_year(year: int, m_y: pd.DataFrame, eps: list[dict[str, Any]]) -> dict[str, Any]:
    wrong = [e for e in eps if e["wrong"]]
    severe = [e for e in wrong if e["severity"] == "SEVERE"]
    moderate = [e for e in wrong if e["severity"] == "MODERATE"]
    mild = [e for e in wrong if e["severity"] == "MILD"]
    comp_w = [e for e in wrong if e["wrong_side"] == "COMP_WRONG"]
    sat_w = [e for e in wrong if e["wrong_side"] == "SAT_WRONG"]
    rb, _ = _ret_mdd(m_y["r_b"])
    rp, _ = _ret_mdd(m_y["r_p"])
    gap = round(rp - rb, 2)
    neg_drag = round(sum(min(0.0, float(e["p3_vs_base_pp"])) for e in wrong), 2)
    sev_drag = round(sum(min(0.0, float(e["p3_vs_base_pp"])) for e in severe), 2)
    longest = max((e["n_days"] for e in wrong), default=0)
    longest_sev = max((e["n_days"] for e in severe), default=0)
    flips = int(m_y["flip"].sum()) if len(m_y) else 0
    return {
        "year": year,
        "n_days": int(len(m_y)),
        "n_flips": flips,
        "n_episodes": len(eps),
        "n_wrong": len(wrong),
        "n_comp_wrong": len(comp_w),
        "n_sat_wrong": len(sat_w),
        "n_severe": len(severe),
        "n_moderate": len(moderate),
        "n_mild": len(mild),
        "n_severe_comp": len([e for e in severe if e["wrong_side"] == "COMP_WRONG"]),
        "n_severe_sat": len([e for e in severe if e["wrong_side"] == "SAT_WRONG"]),
        "year_p3_vs_base_pp": gap,
        "wrong_neg_drag_pp": neg_drag,
        "severe_neg_drag_pp": sev_drag,
        "longest_wrong_days": int(longest),
        "longest_severe_days": int(longest_sev),
        "pct_sat": round(float((m_y["w_sat"] > 0.5).mean()) * 100, 2) if len(m_y) else 0.0,
        "year_loss": bool(gap < 0),
    }


def _build_panel(base: pd.DataFrame, comp: pd.DataFrame, sat: pd.DataFrame, theta: float) -> pd.DataFrame:
    m = (
        base.rename(columns={"nav": "nav_b"})
        .merge(comp.rename(columns={"nav": "nav_c"}), on="date")
        .merge(sat.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    m["r_b"] = m["nav_b"].pct_change().fillna(0.0)
    m["r_c"] = m["nav_c"].pct_change().fillna(0.0)
    m["r_s"] = m["nav_s"].pct_change().fillna(0.0)
    rel = m["r_c"] - m["r_s"]
    m["trail_rel_63"] = _trail(rel, 63)
    m["sat_lead"] = (m["trail_rel_63"] <= -float(theta)).fillna(False)
    m["w_sat"] = m["sat_lead"].astype(float)
    m["book"] = np.where(m["w_sat"] > 0.5, "SAT", "COMP")
    m["r_p"] = (1.0 - m["w_sat"]) * m["r_c"] + m["w_sat"] * m["r_s"]
    m["flip"] = m["w_sat"].diff().abs().fillna(0.0) > 1e-12
    m["theta"] = float(theta)
    return m


def _census_theta(m_full: pd.DataFrame, theta: float) -> dict[str, Any]:
    years = sorted(int(y) for y in m_full["date"].dt.year.unique())
    all_eps: list[dict[str, Any]] = []
    year_rows: list[dict[str, Any]] = []
    for y in years:
        m_y = _year_panel(m_full, y)
        if len(m_y) < 20:
            continue
        eps = _episodes(m_y)
        for e in eps:
            e["theta"] = float(theta)
            all_eps.append(e)
        year_rows.append(_summarize_year(y, m_y, eps))

    wrong = [e for e in all_eps if e["wrong"]]
    severe = [e for e in wrong if e["severity"] == "SEVERE"]
    years_severe = sorted({e["year"] for e in severe})
    years_severe_comp = sorted({e["year"] for e in severe if e["wrong_side"] == "COMP_WRONG"})
    years_loss = [r for r in year_rows if r["year_loss"]]
    total_sev_drag = round(sum(min(0.0, float(e["p3_vs_base_pp"])) for e in severe), 2)
    drag_2022 = round(
        sum(min(0.0, float(e["p3_vs_base_pp"])) for e in severe if e["year"] == 2022), 2
    )
    share_2022 = None if total_sev_drag >= -1e-12 else round(abs(drag_2022) / abs(total_sev_drag), 3)

    return {
        "theta": float(theta),
        "n_years": len(year_rows),
        "n_episodes": len(all_eps),
        "n_wrong": len(wrong),
        "n_comp_wrong": len([e for e in wrong if e["wrong_side"] == "COMP_WRONG"]),
        "n_sat_wrong": len([e for e in wrong if e["wrong_side"] == "SAT_WRONG"]),
        "n_severe": len(severe),
        "n_moderate": len([e for e in wrong if e["severity"] == "MODERATE"]),
        "n_mild": len([e for e in wrong if e["severity"] == "MILD"]),
        "n_severe_comp": len([e for e in severe if e["wrong_side"] == "COMP_WRONG"]),
        "n_severe_sat": len([e for e in severe if e["wrong_side"] == "SAT_WRONG"]),
        "years_with_severe": years_severe,
        "years_with_severe_comp": years_severe_comp,
        "n_years_with_severe": len(years_severe),
        "n_years_with_severe_comp": len(years_severe_comp),
        "n_years_loss": len(years_loss),
        "years_loss": [r["year"] for r in years_loss],
        "severe_neg_drag_pp": total_sev_drag,
        "severe_neg_drag_2022_pp": drag_2022,
        "severe_drag_share_2022": share_2022,
        "years": year_rows,
        "episodes": all_eps,
        "severe_episodes": severe,
    }


def _verdict(c01: dict[str, Any], c005: dict[str, Any]) -> str:
    """Pre-registered verdict ladder (structure first, then θ sensitivity)."""
    n_sev_y = int(c01["n_years_with_severe_comp"])
    share = c01.get("severe_drag_share_2022")
    sev01 = int(c01["n_severe"])
    sev005 = int(c005["n_severe"])
    theta_cuts = sev01 > 0 and sev005 <= THETA_CUT_FRAC * sev01

    if n_sev_y >= 3:
        base = "WRONG_STAY_RECURRENT"
    elif n_sev_y == 1 and c01["years_with_severe_comp"] == [2022]:
        base = "WRONG_STAY_2022_UNIQUE"
    elif n_sev_y >= 1 and share is not None and share >= 0.50:
        base = "WRONG_STAY_2022_DOMINANT"
    elif n_sev_y >= 1:
        base = "WRONG_STAY_SPARSE"
    elif int(c01["n_wrong"]) > 0:
        base = "WRONG_STAY_MILD_ONLY"
    else:
        base = "WRONG_STAY_NONE"

    if theta_cuts and base not in ("WRONG_STAY_NONE", "WRONG_STAY_MILD_ONLY"):
        return f"{base}__THETA_CUTS"
    if sev01 > 0 and not theta_cuts and base not in ("WRONG_STAY_NONE", "WRONG_STAY_MILD_ONLY"):
        return f"{base}__THETA_INSENSITIVE"
    return base


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    base = _load(BASE_NAV)
    comp = _load(COMP_NAV)
    sat = _load(SAT_NAV)

    censuses: dict[str, Any] = {}
    for th in THETAS:
        m = _build_panel(base, comp, sat, th)
        m.to_csv(OUT / f"daily_theta_{th:g}.csv", index=False)
        censuses[f"{th:g}"] = _census_theta(m, th)

    c01 = censuses["0.01"]
    c005 = censuses["0.005"]
    verdict = _verdict(c01, c005)

    # Persist episode + year tables
    for key, c in censuses.items():
        pd.DataFrame(c["episodes"]).to_csv(OUT / f"episodes_theta_{key}.csv", index=False)
        pd.DataFrame(c["years"]).to_csv(OUT / f"years_theta_{key}.csv", index=False)
        pd.DataFrame(c["severe_episodes"]).to_csv(OUT / f"severe_theta_{key}.csv", index=False)

    # Slim books for JSON (drop full episode lists from nested; keep paths)
    books_slim = {}
    for key, c in censuses.items():
        slim = {k: v for k, v in c.items() if k not in ("episodes", "severe_episodes")}
        slim["severe_episodes"] = c["severe_episodes"]  # keep severe full (small)
        books_slim[key] = slim

    delta = {
        "d_n_wrong": int(c005["n_wrong"]) - int(c01["n_wrong"]),
        "d_n_severe": int(c005["n_severe"]) - int(c01["n_severe"]),
        "d_n_severe_comp": int(c005["n_severe_comp"]) - int(c01["n_severe_comp"]),
        "d_n_years_with_severe_comp": int(c005["n_years_with_severe_comp"])
        - int(c01["n_years_with_severe_comp"]),
        "d_severe_neg_drag_pp": round(
            float(c005["severe_neg_drag_pp"]) - float(c01["severe_neg_drag_pp"]), 2
        ),
    }

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            "Status: **Stage A — Path3 wrong-stay census** · Soft-Frozen **KEEP** · Path3 observe θ=0.01 **KEEP** · "
            "fill/emit **OFF** · no live",
            "Parents: 0k9x `COMP_STAY_MISS` · 0k9v yearly 14–1 · θ paper challenger 0.005 (0ka3/0ka4)",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "各曆年 Path3 **站錯**（held ≠ episode-best COMP/SAT）次數與嚴重度如何分布？"
            "2022 是否唯一 SEVERE COMP_WRONG 年？θ=0.005 是否減少站錯？",
            "",
            "## Method (pre-registered)",
            "",
            "- Reuse **0k9x** episode definition (year-clipped contiguous book runs)",
            "- Wrong when `book != argmax(episode COMP ret, SAT ret)`",
            f"- Severity: **SEVERE** = wrong ∧ P3−BASE≤{SEVERE_GAP_PP} ∧ days≥{SEVERE_MIN_DAYS}; "
            f"**MODERATE** = wrong ∧ (P3−BASE≤{MOD_GAP_PP} ∨ P3−best≤{MOD_VS_BEST_PP}); else **MILD**",
            f"- θ grid: `{list(THETAS)}` (observe 0.01 · challenger 0.005)",
            "- No live / Soft-Frozen KEEP / fill/emit OFF / no severity expand after peek",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__WRONG_STAY_CENSUS__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "thetas": list(THETAS),
                "severity": {
                    "severe_gap_pp": SEVERE_GAP_PP,
                    "severe_min_days": SEVERE_MIN_DAYS,
                    "mod_gap_pp": MOD_GAP_PP,
                    "mod_vs_best_pp": MOD_VS_BEST_PP,
                },
                "soft_frozen_keep": True,
                "path3_observe_keep": True,
                "fill_emit_flags": False,
                "live_wire": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "verdict": verdict,
        "register": REGISTER,
        "thetas": list(THETAS),
        "census": books_slim,
        "delta_005_minus_01": delta,
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "fill_emit_flags": False,
        "live_wire": False,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    md = [
        f"# {SCREEN_ID}",
        "",
        f"Date: 2026-09-29 · `{generated}` · Verdict **`{verdict}`**",
        "Parent 0k9x definition · θ=0.01 observe · θ=0.005 paper · fill/emit OFF · no live",
        "",
        "## Totals",
        "",
        "| θ | wrong | COMP_W | SAT_W | SEVERE | sev_COMP | years_sev_COMP | sev_drag | 2022 share |",
        "|---:|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    for key in ("0.01", "0.005"):
        c = censuses[key]
        md.append(
            f"| {key} | {c['n_wrong']} | {c['n_comp_wrong']} | {c['n_sat_wrong']} | {c['n_severe']} | "
            f"{c['n_severe_comp']} | {c['years_with_severe_comp']} | {c['severe_neg_drag_pp']} | "
            f"{c['severe_drag_share_2022']} |"
        )
    md += [
        "",
        f"Δ(0.005−0.01): wrong {delta['d_n_wrong']} · severe {delta['d_n_severe']} · "
        f"sev_COMP {delta['d_n_severe_comp']} · years_sev_COMP {delta['d_n_years_with_severe_comp']} · "
        f"sev_drag {delta['d_severe_neg_drag_pp']}",
        "",
        "## By year (θ=0.01 observe)",
        "",
        "| year | wrong | COMP_W | SEV | SEV_C | flips | P3−BASE | wrong_drag | long_sev |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in c01["years"]:
        md.append(
            f"| {r['year']} | {r['n_wrong']} | {r['n_comp_wrong']} | {r['n_severe']} | "
            f"{r['n_severe_comp']} | {r['n_flips']} | {r['year_p3_vs_base_pp']} | "
            f"{r['wrong_neg_drag_pp']} | {r['longest_severe_days']} |"
        )
    md += [
        "",
        "## SEVERE episodes (θ=0.01)",
        "",
        "| year | start | end | n | book | best | P3−BASE | P3−best |",
        "|---:|---|---|---:|---|---|---:|---:|",
    ]
    for e in c01["severe_episodes"]:
        md.append(
            f"| {e['year']} | {e['start']} | {e['end']} | {e['n_days']} | {e['book']} | "
            f"{e['best_book']} | {e['p3_vs_base_pp']} | {e['p3_vs_best_pp']} |"
        )
    md += ["", "Repro: `repro/fin-sat-path3-wrong-stay-census-stagea/`", ""]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    # Decision pack
    top_years = sorted(c01["years"], key=lambda r: r["n_severe_comp"], reverse=True)[:5]
    dec = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe θ=0.01 **KEEP** · fill/emit **OFF** · no live",
            f"Register: **{REGISTER}** · Parents: 0k9x / 0k9v / θ-challenger 0.005",
            "",
            "## Answer",
            "",
            f"θ=0.01: wrong **{c01['n_wrong']}** · COMP_WRONG **{c01['n_comp_wrong']}** · "
            f"SEVERE **{c01['n_severe']}** (COMP **{c01['n_severe_comp']}**) · "
            f"years with SEVERE COMP_WRONG **{c01['years_with_severe_comp']}** · "
            f"sev_drag **{c01['severe_neg_drag_pp']}** · 2022 share **{c01['severe_drag_share_2022']}**.",
            f"θ=0.005: wrong **{c005['n_wrong']}** · SEVERE **{c005['n_severe']}** "
            f"(COMP **{c005['n_severe_comp']}**) · years **{c005['years_with_severe_comp']}** · "
            f"Δsevere **{delta['d_n_severe']}**.",
            f"Year-loss years (P3−BASE<0) θ=0.01: **{c01['years_loss']}**.",
            "Top SEVERE-COMP years: "
            + ", ".join(
                f"{r['year']}(sev_c={r['n_severe_comp']}, gap={r['year_p3_vs_base_pp']})"
                for r in top_years
                if r["n_severe_comp"] > 0
            ),
            "",
            "## Implication",
            "",
            "- `WRONG_STAY_2022_UNIQUE`：嚴重症僅 2022 → 不全局改偵測；局部殘差票。",
            "- `WRONG_STAY_2022_DOMINANT`／`RECURRENT`：多年度 SEVERE → 機制/θ/confirm 仍可研究，但 observe θ=0.01 KEEP 至 ballot。",
            "- `*__THETA_CUTS`：θ=0.005 明顯砍 SEVERE → 與 0ka3 tip HIT 同向，可併入 observe retune DRAFT。",
            "- `*__THETA_INSENSITIVE`：θ 不治站錯根因（呼應 0ka3 2022 不敏感）。",
            "- Soft-Frozen KEEP · fill/emit OFF · cutover BLOCKED · no live。",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md`",
            "",
            f"Label: `{DECISION_ID}_2026-09-29__{verdict}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", dec, kind="decision pack")
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(
            {
                "label": f"{DECISION_ID}_2026-09-29__{verdict}__NO_LIVE",
                "verdict": verdict,
                "register": REGISTER,
                "census": books_slim,
                "delta_005_minus_01": delta,
                "soft_frozen_keep": True,
                "path3_observe_keep": True,
                "fill_emit_flags": False,
                "live_wire": False,
                "cutover": "BLOCKED",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "theta_0.01": {
                    k: c01[k]
                    for k in (
                        "n_wrong",
                        "n_comp_wrong",
                        "n_severe",
                        "n_severe_comp",
                        "years_with_severe_comp",
                        "severe_neg_drag_pp",
                        "severe_drag_share_2022",
                        "years_loss",
                    )
                },
                "theta_0.005": {
                    k: c005[k]
                    for k in (
                        "n_wrong",
                        "n_severe",
                        "n_severe_comp",
                        "years_with_severe_comp",
                        "severe_neg_drag_pp",
                    )
                },
                "delta": delta,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
