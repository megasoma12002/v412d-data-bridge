#!/usr/bin/env python3
"""Path-3 (T+0 counterfactual) full/held/sealed + yearly vs CTRL_LIVE_A10 base."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "fin-sat-t1-lag-path-compare-stagea" / "outputs"
REP = ROOT / "repro" / "fin-sat-t1-lag-path-compare-stagea" / "reports"
OPS = ROOT / "research" / "ops"

REPORT_ID = "FIN_SAT_T1_LAG_PATH3_VS_BASE"
BASE_NAV = OUT / "nav_CTRL_LIVE_A10.csv"
FALLBACK_BASE = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
BOOKS = {
    "P3_T0_STATE": OUT / "nav_P3_T0_STATE.csv",
    "P3_T0_ENTER_M1": OUT / "nav_P3_T0_ENTER_M1.csv",
}
WINDOW_ORDER = (
    "full",
    "oof_2011_2018",
    "validation_2019_2022",
    "heldout_2019_plus",
    "sealed_2023_plus",
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)[["date", "nav"]].assign(
        nav=lambda x: x["nav"].astype(float)
    )


def _pct(x: float | None, *, mul100: bool = True) -> str:
    if x is None:
        return "—"
    v = float(x) * 100.0 if mul100 else float(x)
    return f"{v:.2f}%"


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
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


def _deltas(chal_w: dict[str, Any], base_w: dict[str, Any]) -> dict[str, Any]:
    d: dict[str, Any] = {}
    for k in WINDOWS_STANDARD:
        b = base_w[k]
        c = chal_w[k]
        d[k] = {
            "cagr_lift_pp": None
            if b["cagr"] is None or c["cagr"] is None
            else round(float(cagr_lift_pp(b["cagr"], c["cagr"])), 4),
            "mdd_improve_pp": None
            if b["max_drawdown"] is None or c["max_drawdown"] is None
            else round(float(mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])), 4),
            "chal_cagr": c["cagr"],
            "base_cagr": b["cagr"],
            "chal_mdd": c["max_drawdown"],
            "base_mdd": b["max_drawdown"],
            "n_days": c["n_days"],
        }
    return d


def _yearly(base: pd.DataFrame, chal: pd.DataFrame, label: str) -> list[dict[str, Any]]:
    m = base.rename(columns={"nav": "nav_b"}).merge(chal.rename(columns={"nav": "nav_c"}), on="date")
    m["year"] = m["date"].dt.year
    rows: list[dict[str, Any]] = []
    for y, g in m.groupby("year"):
        if len(g) < 20:
            continue
        bn = g["nav_b"].astype(float) / float(g["nav_b"].iloc[0])
        cn = g["nav_c"].astype(float) / float(g["nav_c"].iloc[0])
        br = float(bn.iloc[-1] - 1.0)
        cr = float(cn.iloc[-1] - 1.0)
        bm = float((bn / bn.cummax() - 1.0).min())
        cm = float((cn / cn.cummax() - 1.0).min())
        rows.append(
            {
                "year": int(y),
                "n_days": int(len(g)),
                "book": label,
                "base_ret_pct": round(br * 100.0, 2),
                "chal_ret_pct": round(cr * 100.0, 2),
                "ret_lift_pp": round((cr - br) * 100.0, 2),
                "base_mdd_pct": round(bm * 100.0, 2),
                "chal_mdd_pct": round(cm * 100.0, 2),
                "mdd_improve_pp": round((abs(bm) - abs(cm)) * 100.0, 2),
                "winner_vs_base": "P3" if cr > br else ("BASE" if br > cr else "TIE"),
            }
        )
    return rows


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    base = _load(BASE_NAV if BASE_NAV.exists() else FALLBACK_BASE)
    base_w = _pack(base)
    generated = _utc()
    payload: dict[str, Any] = {
        "label": f"{REPORT_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "base": "CTRL_LIVE_A10",
        "soft_frozen_exact_t_plus_1_keep": True,
        "counterfactual_only": True,
        "live_wire": False,
        "windows": {},
        "yearly": {},
        "summary": {},
        "register": "0k9q",
    }

    md = [
        f"# {REPORT_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        "Status: **T+0 counterfactual diagnostics** · Soft-Frozen Exact T+1 **KEEP** · not observe · not live",
        "",
        "Base: `CTRL_LIVE_A10`",
        "Books: `P3_T0_STATE`（同日 SAT_LEAD→SAT）· `P3_T0_ENTER_M1`（enter 早 1 日 oracle）",
        "",
        "Parent compare: `FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK.md` · register **0k9q**",
        "",
    ]

    for bid, path in BOOKS.items():
        nav = _load(path)
        d = _deltas(_pack(nav), base_w)
        yrs = _yearly(base, nav, bid)
        payload["windows"][bid] = d
        payload["yearly"][bid] = yrs
        nw = sum(1 for r in yrs if r["winner_vs_base"] == "P3")
        nb = sum(1 for r in yrs if r["winner_vs_base"] == "BASE")
        payload["summary"][bid] = {
            "full": d["full"],
            "heldout_2019_plus": d["heldout_2019_plus"],
            "sealed_2023_plus": d["sealed_2023_plus"],
            "years_beat_base": nw,
            "years_lose_base": nb,
            "n_years": len(yrs),
            "mean_ret_lift_pp": round(float(np.mean([r["ret_lift_pp"] for r in yrs])), 2) if yrs else None,
            "p3_win_years": [r["year"] for r in yrs if r["winner_vs_base"] == "P3"],
            "base_win_years": [r["year"] for r in yrs if r["winner_vs_base"] == "BASE"],
        }

        md += [
            f"## `{bid}` vs base — full / held / sealed",
            "",
            "| window | base CAGR | P3 CAGR | CAGR↑ pp | base MDD | P3 MDD | MDD↑ pp | n |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for w in WINDOW_ORDER:
            x = d[w]
            md.append(
                f"| `{w}` | {_pct(x['base_cagr'])} | {_pct(x['chal_cagr'])} | {x['cagr_lift_pp']} | "
                f"{_pct(x['base_mdd'])} | {_pct(x['chal_mdd'])} | {x['mdd_improve_pp']} | {x['n_days']} |"
            )
        md += [
            "",
            f"Year score vs base: **{nw}–{nb}** (P3–BASE) · mean ret lift **{payload['summary'][bid]['mean_ret_lift_pp']}** pp",
            "",
            f"### `{bid}` yearly",
            "",
            "| year | base ret% | P3 ret% | Δpp | base MDD% | P3 MDD% | MDD↑pp | winner |",
            "|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
        for r in yrs:
            md.append(
                f"| {r['year']} | {r['base_ret_pct']} | {r['chal_ret_pct']} | {r['ret_lift_pp']} | "
                f"{r['base_mdd_pct']} | {r['chal_mdd_pct']} | {r['mdd_improve_pp']} | {r['winner_vs_base']} |"
            )
        md += ["", f"P3-win years: {payload['summary'][bid]['p3_win_years']}", ""]
        pd.DataFrame(yrs).to_csv(OUT / f"yearly_{bid}_vs_base.csv", index=False)

    # head-to-head STATE vs ENTER_M1 on held/sealed
    s = payload["summary"]["P3_T0_STATE"]
    e = payload["summary"]["P3_T0_ENTER_M1"]
    md += [
        "## Head-to-head (both vs same base)",
        "",
        "| book | full CAGR↑ | held CAGR↑ | sealed CAGR↑ | held MDD↑ | sealed MDD↑ | year W–L |",
        "|---|---:|---:|---:|---:|---:|---|",
        f"| `P3_T0_STATE` | {s['full']['cagr_lift_pp']} | {s['heldout_2019_plus']['cagr_lift_pp']} | "
        f"{s['sealed_2023_plus']['cagr_lift_pp']} | {s['heldout_2019_plus']['mdd_improve_pp']} | "
        f"{s['sealed_2023_plus']['mdd_improve_pp']} | {s['years_beat_base']}–{s['years_lose_base']} |",
        f"| `P3_T0_ENTER_M1` | {e['full']['cagr_lift_pp']} | {e['heldout_2019_plus']['cagr_lift_pp']} | "
        f"{e['sealed_2023_plus']['cagr_lift_pp']} | {e['heldout_2019_plus']['mdd_improve_pp']} | "
        f"{e['sealed_2023_plus']['mdd_improve_pp']} | {e['years_beat_base']}–{e['years_lose_base']} |",
        "",
        "## Reading",
        "",
        "- 兩條路徑三都是 **Exact T+0 反事實**（Soft-Frozen Exact T+1 KEEP 下不可直接上）。",
        "- 相對 live base：full／held／sealed CAGR 與逐年勝率見上表。",
        "- `P3_T0_STATE` 通常 ≥ `P3_T0_ENTER_M1`（同日狀態上界優於僅早 1 日）。",
        "",
        f"Label: `{REPORT_ID}_2026-09-28__COUNTERFACTUAL__NO_LIVE`",
        "",
    ]

    body = "\n".join(md)
    write_ops_and_repro_pointer(OPS / f"{REPORT_ID}.md", REP / f"{REPORT_ID}.md", body)
    write_ops_and_repro_pointer(
        OPS / f"{REPORT_ID}.json",
        REP / f"{REPORT_ID}.json",
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    )
    (OUT / "path3_vs_base.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # append pointer into path-compare decision pack if present
    dec = OPS / "FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK.md"
    if dec.exists():
        txt = dec.read_text(encoding="utf-8")
        pointer = (
            "\n## Path-3 detail vs base\n\n"
            f"Full／held／sealed／逐年：`{REPORT_ID}.md`\n"
        )
        if REPORT_ID not in txt:
            txt = txt.replace(
                f"Label: `FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK_2026-09-28__T0_ONLY_EDGE__NO_LIVE`",
                pointer
                + f"\nLabel: `FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK_2026-09-28__T0_ONLY_EDGE__NO_LIVE`",
            )
            dec.write_text(txt, encoding="utf-8")
            write_ops_and_repro_pointer(
                OPS / "FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK.md",
                REP / "FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK.md",
                dec.read_text(encoding="utf-8"),
            )

    print(
        json.dumps(
            {
                "report": REPORT_ID,
                "P3_T0_STATE": payload["summary"]["P3_T0_STATE"],
                "P3_T0_ENTER_M1": payload["summary"]["P3_T0_ENTER_M1"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
