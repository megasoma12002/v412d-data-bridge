#!/usr/bin/env python3
"""FIN×SAT Path3 full / held / sealed window pack Stage A (paper).

Side-by-side WINDOWS_STANDARD (full · heldout_2019_plus · sealed_2023_plus)
plus tip YTD/1y for:
  BASE = CTRL_LIVE_A10
  P3_θ0.01 = observe P3_T0_STATE
  P3_θ0.005 = paper challenger (0ka3/0ka4)
  COMP / SAT pure books (context)

Soft-Frozen KEEP · Path3 observe θ=0.01 KEEP · fill/emit OFF · no live
Register: 0ka6
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-window-pack-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_WINDOW_PACK_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_WINDOW_PACK_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_WINDOW_PACK_STAGEA_DECISION_PACK"
REGISTER = "0ka6"

BASE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"
P3_01_NAV = ROOT / "repro/fin-sat-path3-t0-dual-paper-observe/outputs/p3_t0_state_daily_nav.csv"

WIN_KEYS = ("full", "heldout_2019_plus", "sealed_2023_plus")
SEALED_MDD_FLOOR_PP = -0.25  # ACCEPTABLE band from 0k9r sealed disposition
TIP_CAGR_MIN = 0.0
TIP_MDD_MIN = 0.0


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


def _blend(comp: pd.DataFrame, sat: pd.DataFrame, theta: float) -> pd.DataFrame:
    rc = comp["nav"].pct_change().fillna(0.0)
    rs = sat["nav"].pct_change().fillna(0.0)
    trail = _trail(rc - rs, 63)
    w = (trail <= -float(theta)).fillna(False).astype(float).to_numpy()
    r = (1.0 - w) * rc.to_numpy() + w * rs.to_numpy()
    nav = (1.0 + r).cumprod() * float(comp["nav"].iloc[0])
    return pd.DataFrame({"date": comp["date"].to_numpy(), "nav": nav})


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


def _tip(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"mdd_improve_pp": None, "cagr_lift_pp": None}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        lift = cagr_lift_pp(bc, cc)
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_lift_pp": None if lift is None else round(float(lift), 4),
        }
    return out


def _book_row(book_id: str, base: pd.DataFrame, nav: pd.DataFrame, *, note: str) -> dict[str, Any]:
    wins = _pack(nav)
    tip = _tip(base, nav)
    abs_rows = {}
    lifts = {}
    base_w = _pack(base)
    for k in WIN_KEYS:
        bw = base_w.get(k) or {}
        cw = wins.get(k) or {}
        abs_rows[k] = {
            "cagr": cw.get("cagr"),
            "max_drawdown": cw.get("max_drawdown"),
            "n_days": cw.get("n_days"),
            "base_cagr": bw.get("cagr"),
            "base_max_drawdown": bw.get("max_drawdown"),
        }
        lifts[k] = {
            "cagr_lift_pp": None
            if bw.get("cagr") is None or cw.get("cagr") is None
            else round(float(cagr_lift_pp(bw["cagr"], cw["cagr"])), 4),
            "mdd_pp": None
            if bw.get("max_drawdown") is None or cw.get("max_drawdown") is None
            else round(float(mdd_delta_pp(bw["max_drawdown"], cw["max_drawdown"])), 4),
        }
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    tip_1 = (tip.get("trailing_1y") or {}).get("cagr_lift_pp")
    tip_ym = (tip.get("ytd") or {}).get("mdd_improve_pp")
    tip_1m = (tip.get("trailing_1y") or {}).get("mdd_improve_pp")
    tip_clean = (
        tip_y is not None
        and tip_1 is not None
        and tip_ym is not None
        and tip_1m is not None
        and tip_y >= TIP_CAGR_MIN
        and tip_1 >= TIP_CAGR_MIN
        and tip_ym >= TIP_MDD_MIN
        and tip_1m >= TIP_MDD_MIN
    )
    sealed_mdd = (lifts.get("sealed_2023_plus") or {}).get("mdd_pp")
    sealed_ok = sealed_mdd is None or float(sealed_mdd) >= SEALED_MDD_FLOOR_PP
    all_cagr_pos = all(
        (lifts[k].get("cagr_lift_pp") or -999) > 0 for k in WIN_KEYS
    )
    return {
        "id": book_id,
        "note": note,
        "windows": abs_rows,
        "lifts_vs_base": lifts,
        "tip": tip,
        "tip_clean": bool(tip_clean),
        "sealed_mdd_ok": bool(sealed_ok),
        "all_window_cagr_pos": bool(all_cagr_pos),
        "n_days_full": int((wins.get("full") or {}).get("n_days") or 0),
    }


def _verdict(books: dict[str, dict[str, Any]]) -> str:
    p01 = books["P3_THETA_0.01"]
    p005 = books["P3_THETA_0.005"]
    # Uniform Path3 edge across full/held/sealed?
    if p01["all_window_cagr_pos"] and p01["sealed_mdd_ok"] and p01["tip_clean"]:
        # Does 0.005 dominate 0.01 on all three CAGR lifts?
        dom = True
        for k in WIN_KEYS:
            a = (p005["lifts_vs_base"][k].get("cagr_lift_pp") or -999)
            b = (p01["lifts_vs_base"][k].get("cagr_lift_pp") or -999)
            if a + 0.05 < b:  # allow tiny sealed noise
                dom = False
                break
        held_better = (p005["lifts_vs_base"]["heldout_2019_plus"].get("cagr_lift_pp") or 0) > (
            p01["lifts_vs_base"]["heldout_2019_plus"].get("cagr_lift_pp") or 0
        ) + 0.10
        sealed_flat = abs(
            (p005["lifts_vs_base"]["sealed_2023_plus"].get("cagr_lift_pp") or 0)
            - (p01["lifts_vs_base"]["sealed_2023_plus"].get("cagr_lift_pp") or 0)
        ) <= 0.10
        if dom and held_better and sealed_flat:
            return "WINDOW_UNIFORM__THETA005_HELD_EDGE"
        if p01["sealed_mdd_ok"]:
            return "WINDOW_UNIFORM__SEALED_MDD_OK"
        return "WINDOW_UNIFORM"
    if p01["all_window_cagr_pos"] and not p01["sealed_mdd_ok"]:
        return "WINDOW_CAGR_OK__SEALED_MDD_TAX"
    return "WINDOW_MIXED"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    base = _load(BASE_NAV)
    comp = _load(COMP_NAV)
    sat = _load(SAT_NAV)
    dates = sorted(set(base["date"]) & set(comp["date"]) & set(sat["date"]))
    base = base[base["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat = sat[sat["date"].isin(dates)].reset_index(drop=True)

    p3_01 = _load(P3_01_NAV)
    p3_01 = p3_01[p3_01["date"].isin(dates)].reset_index(drop=True)
    # Rebuild θ=0.005 on aligned panel (SSOT; matches 0ka3/0ka4)
    p3_005 = _blend(comp, sat, 0.005)
    # Sanity: rebuild θ=0.01 should track observe P3 closely
    p3_01_rebuild = _blend(comp, sat, 0.01)

    for name, nav in (
        ("BASE_CTRL_LIVE_A10", base),
        ("COMP_H150_x_A20", comp),
        ("SAT_A20_RELAX", sat),
        ("P3_THETA_0.01", p3_01),
        ("P3_THETA_0.01_rebuild", p3_01_rebuild),
        ("P3_THETA_0.005", p3_005),
    ):
        nav.to_csv(OUT / f"nav_{name}.csv", index=False)

    books = {
        "BASE_CTRL_LIVE_A10": _book_row("BASE_CTRL_LIVE_A10", base, base, note="parent Exact T+1 CTRL"),
        "COMP_H150_x_A20": _book_row("COMP_H150_x_A20", base, comp, note="pure COMP"),
        "SAT_A20_RELAX": _book_row("SAT_A20_RELAX", base, sat, note="pure SAT"),
        "P3_THETA_0.01": _book_row(
            "P3_THETA_0.01", base, p3_01, note="Path3 observe θ=0.01 (P3_T0_STATE)"
        ),
        "P3_THETA_0.005": _book_row(
            "P3_THETA_0.005", base, p3_005, note="paper challenger θ=0.005 (0ka3/0ka4)"
        ),
    }
    rebuild = _book_row("P3_THETA_0.01_rebuild", base, p3_01_rebuild, note="rebuild check")
    # rebuild vs observe held gap
    rebuild_gap = {
        k: round(
            float((rebuild["lifts_vs_base"][k].get("cagr_lift_pp") or 0))
            - float((books["P3_THETA_0.01"]["lifts_vs_base"][k].get("cagr_lift_pp") or 0)),
            4,
        )
        for k in WIN_KEYS
    }

    d005 = {
        k: {
            "d_cagr_lift_pp": round(
                float((books["P3_THETA_0.005"]["lifts_vs_base"][k].get("cagr_lift_pp") or 0))
                - float((books["P3_THETA_0.01"]["lifts_vs_base"][k].get("cagr_lift_pp") or 0)),
                4,
            ),
            "d_mdd_pp": round(
                float((books["P3_THETA_0.005"]["lifts_vs_base"][k].get("mdd_pp") or 0))
                - float((books["P3_THETA_0.01"]["lifts_vs_base"][k].get("mdd_pp") or 0)),
                4,
            ),
        }
        for k in WIN_KEYS
    }

    verdict = _verdict(books)
    generated = _utc()

    # flat CSV
    flat = []
    for bid, b in books.items():
        for k in WIN_KEYS:
            flat.append(
                {
                    "book": bid,
                    "window": k,
                    "cagr": b["windows"][k]["cagr"],
                    "max_drawdown": b["windows"][k]["max_drawdown"],
                    "cagr_lift_pp": b["lifts_vs_base"][k]["cagr_lift_pp"],
                    "mdd_pp": b["lifts_vs_base"][k]["mdd_pp"],
                    "n_days": b["windows"][k]["n_days"],
                }
            )
    pd.DataFrame(flat).to_csv(OUT / "window_pack.csv", index=False)

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            "Status: **Stage A — Path3 full/held/sealed window pack** · Soft-Frozen **KEEP** · "
            "Path3 observe θ=0.01 **KEEP** · fill/emit **OFF** · no live",
            "Parents: 0k9r observe · 0k9v fill-sim · 0ka3/0ka4 θ · 0ka5 wrong-stay census",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "`P3_T0_STATE`（θ=0.01）與 paper θ=0.005 在 **full / held / sealed** 相對 `CTRL_LIVE_A10` "
            "的 CAGR／MDD 差異為何？sealed MDD 稅是否仍在 ACCEPTABLE 帶？",
            "",
            "## Method",
            "",
            "- `WINDOWS_STANDARD`: full · heldout_2019_plus · sealed_2023_plus",
            "- Books: BASE · COMP · SAT · P3 θ=0.01 (observe NAV) · P3 θ=0.005 (rebuild)",
            "- Tip YTD / trailing_1y for tip-clean context",
            "- No live / Soft-Frozen KEEP / fill/emit OFF",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__WINDOW_PACK__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "windows": list(WIN_KEYS),
                "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
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
        "books": books,
        "delta_005_minus_01": d005,
        "rebuild_01_gap_vs_observe": rebuild_gap,
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "fill_emit_flags": False,
        "live_wire": False,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    def _pct(x: float | None) -> str:
        if x is None:
            return "—"
        return f"{100.0 * float(x):.2f}%"

    def _pp(x: float | None) -> str:
        if x is None:
            return "—"
        return f"{float(x):+.2f}"

    md = [
        f"# {SCREEN_ID}",
        "",
        f"Date: 2026-09-29 · `{generated}` · Verdict **`{verdict}`**",
        "",
        "## Absolute CAGR / MDD",
        "",
        "| book | full CAGR | full MDD | held CAGR | held MDD | sealed CAGR | sealed MDD |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for bid in ("BASE_CTRL_LIVE_A10", "COMP_H150_x_A20", "SAT_A20_RELAX", "P3_THETA_0.01", "P3_THETA_0.005"):
        b = books[bid]
        md.append(
            "| `{bid}` | {fc} | {fm} | {hc} | {hm} | {sc} | {sm} |".format(
                bid=bid,
                fc=_pct(b["windows"]["full"]["cagr"]),
                fm=_pct(b["windows"]["full"]["max_drawdown"]),
                hc=_pct(b["windows"]["heldout_2019_plus"]["cagr"]),
                hm=_pct(b["windows"]["heldout_2019_plus"]["max_drawdown"]),
                sc=_pct(b["windows"]["sealed_2023_plus"]["cagr"]),
                sm=_pct(b["windows"]["sealed_2023_plus"]["max_drawdown"]),
            )
        )
    md += [
        "",
        "## Lift vs BASE (pp)",
        "",
        "| book | full CAGR↑ | full MDD↑ | held CAGR↑ | held MDD↑ | sealed CAGR↑ | sealed MDD↑ | tipY↑ | tip1y↑ | tipClean |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for bid in ("COMP_H150_x_A20", "SAT_A20_RELAX", "P3_THETA_0.01", "P3_THETA_0.005"):
        b = books[bid]
        L = b["lifts_vs_base"]
        md.append(
            "| `{bid}` | {a} | {b_} | {c} | {d} | {e} | {f} | {ty} | {t1} | {tc} |".format(
                bid=bid,
                a=_pp(L["full"]["cagr_lift_pp"]),
                b_=_pp(L["full"]["mdd_pp"]),
                c=_pp(L["heldout_2019_plus"]["cagr_lift_pp"]),
                d=_pp(L["heldout_2019_plus"]["mdd_pp"]),
                e=_pp(L["sealed_2023_plus"]["cagr_lift_pp"]),
                f=_pp(L["sealed_2023_plus"]["mdd_pp"]),
                ty=_pp((b["tip"].get("ytd") or {}).get("cagr_lift_pp")),
                t1=_pp((b["tip"].get("trailing_1y") or {}).get("cagr_lift_pp")),
                tc=b["tip_clean"],
            )
        )
    md += [
        "",
        "## Δ θ=0.005 − θ=0.01",
        "",
        "| window | Δ CAGR↑ | Δ MDD↑ |",
        "|---|---:|---:|",
    ]
    for k in WIN_KEYS:
        md.append(f"| {k} | {_pp(d005[k]['d_cagr_lift_pp'])} | {_pp(d005[k]['d_mdd_pp'])} |")
    md += [
        "",
        f"Rebuild θ=0.01 vs observe gap (CAGR↑): `{rebuild_gap}`",
        "",
        "Repro: `repro/fin-sat-path3-window-pack-stagea/`",
        "",
    ]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    p01 = books["P3_THETA_0.01"]
    p005 = books["P3_THETA_0.005"]
    dec = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe θ=0.01 **KEEP** · fill/emit **OFF** · no live",
            f"Register: **{REGISTER}** · Parents: 0k9r / 0k9v / 0ka3–0ka5",
            "",
            "## Answer",
            "",
            "Path3 θ=0.01 vs BASE:",
            f"- **full**: CAGR↑ **{_pp(p01['lifts_vs_base']['full']['cagr_lift_pp'])}** · "
            f"MDD↑ {_pp(p01['lifts_vs_base']['full']['mdd_pp'])}",
            f"- **held**: CAGR↑ **{_pp(p01['lifts_vs_base']['heldout_2019_plus']['cagr_lift_pp'])}** · "
            f"MDD↑ {_pp(p01['lifts_vs_base']['heldout_2019_plus']['mdd_pp'])}",
            f"- **sealed**: CAGR↑ **{_pp(p01['lifts_vs_base']['sealed_2023_plus']['cagr_lift_pp'])}** · "
            f"MDD↑ {_pp(p01['lifts_vs_base']['sealed_2023_plus']['mdd_pp'])} "
            f"(floor {SEALED_MDD_FLOOR_PP} → sealed_mdd_ok={p01['sealed_mdd_ok']})",
            f"- tipY↑ {_pp((p01['tip'].get('ytd') or {}).get('cagr_lift_pp'))} · "
            f"tip1y↑ {_pp((p01['tip'].get('trailing_1y') or {}).get('cagr_lift_pp'))} · "
            f"tipClean={p01['tip_clean']}",
            "",
            "θ=0.005 vs θ=0.01 (Δ CAGR↑): "
            + ", ".join(f"{k} {_pp(d005[k]['d_cagr_lift_pp'])}" for k in WIN_KEYS)
            + ".",
            "",
            "## Implication",
            "",
            "- `WINDOW_UNIFORM*`：三窗 CAGR 全正、sealed MDD 稅可接受 → Path3 edge 非 tip-only。",
            "- `WINDOW_UNIFORM__THETA005_HELD_EDGE`：0.005 在 held/full 優、sealed 近似 → 呼應 0ka3 HIT，observe retune 仍需 ballot。",
            "- Soft-Frozen KEEP · observe θ=0.01 KEEP · fill/emit OFF · cutover BLOCKED · no live。",
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
                "books": books,
                "delta_005_minus_01": d005,
                "rebuild_01_gap_vs_observe": rebuild_gap,
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
                "p3_01_lifts": p01["lifts_vs_base"],
                "p3_005_lifts": p005["lifts_vs_base"],
                "delta_005_minus_01": d005,
                "tip_01": p01["tip"],
                "tip_005": p005["tip"],
                "rebuild_gap": rebuild_gap,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
