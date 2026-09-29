#!/usr/bin/env python3
"""FIN×SAT Path3 live Exact T+0 mechanism Stage A (paper).

MOC fractional proxies vs oracle same-bar vs Exact T+1 open fill.
Charter: research/ops/FIN_SAT_PATH3_LIVE_T0_MECH_STAGEA_CHARTER.md
Soft-Frozen KEEP · Path3 observe KEEP · no live · no fill-core edit.
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
REPRO = ROOT / "repro" / "fin-sat-path3-live-t0-mech-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_LIVE_T0_MECH_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_LIVE_T0_MECH_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_LIVE_T0_MECH_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

THETA = 0.01
CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0
VS_SAT_HELD_EXTRA_PP = 0.05
MOC_FRACS = (0.25, 0.50, 0.75)

# Binding Exact T+1 guards (inventory; not executed here)
T1_GUARDS = [
    {
        "id": "paper_open_fill",
        "path": "scripts/live_fill_core.py::PaperOpenFillPort",
        "rule": "fill prior pending at today's open",
    },
    {
        "id": "pending_signal_lt_latest",
        "path": "scripts/live_fill_core.py::_iter_pending",
        "rule": "signal_date < latest only (blocks same-bar pending)",
    },
    {
        "id": "exact_t1_stats",
        "path": "scripts/live_fill_core.py::_exact_t1_stats",
        "rule": "fill_date <= signal_date counts as same_bar",
    },
    {
        "id": "pipeline_raise",
        "path": "scripts/e21_forward_pipeline.py",
        "rule": "raises if exact_t1_ok is False",
    },
    {
        "id": "qc_exact_t1",
        "path": "scripts/e21_qc.py",
        "rule": "qc_status.exact_t1_ok fail-closed",
    },
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)[["date", "nav"]].assign(
        nav=lambda x: x["nav"].astype(float)
    )


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
            out[wname] = {"mdd_improve_pp": None, "cagr_lift_pp": None, "gate": "INSUFFICIENT"}
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
            "gate": "PASS",
        }
    return out


def _trail_from_rel(rel: np.ndarray, n: int = 63) -> np.ndarray:
    """Causal trailing product; NaN until warmup."""
    out = np.full(len(rel), np.nan, dtype=float)
    for i in range(n - 1, len(rel)):
        window = rel[i - n + 1 : i + 1]
        out[i] = float(np.prod(1.0 + window) - 1.0)
    return out


def _sat_lead(trail: float | np.floating, theta: float = THETA) -> float:
    if trail != trail:  # NaN
        return 0.0
    return 1.0 if float(trail) <= -theta else 0.0


def _nav_from_r(dates: np.ndarray, r: np.ndarray, nav0: float) -> pd.DataFrame:
    nav = (1.0 + r).cumprod() * float(nav0)
    return pd.DataFrame({"date": dates, "nav": nav})


def blend_oracle(rc: np.ndarray, rs: np.ndarray, rel: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Same-bar: trail includes day t; weight applies to full day t (non-causal)."""
    trail = _trail_from_rel(rel)
    w = np.array([_sat_lead(t) for t in trail], dtype=float)
    r = (1.0 - w) * rc + w * rs
    return r, w


def blend_t1_open(rc: np.ndarray, rs: np.ndarray, rel: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Exact T+1: weight from prior close trail; earn full day t."""
    trail = _trail_from_rel(rel)
    w_dec = np.array([_sat_lead(t) for t in trail], dtype=float)
    w = np.roll(w_dec, 1)
    w[0] = 0.0
    r = (1.0 - w) * rc + w * rs
    return r, w


def blend_moc_frac(
    rc: np.ndarray, rs: np.ndarray, rel: np.ndarray, frac: float
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """MOC proxy: earn frac with w_prev; observe frac*rel; earn (1-frac) with w_new."""
    n = len(rc)
    r = np.zeros(n, dtype=float)
    w_end = np.zeros(n, dtype=float)
    flips = 0
    # maintain rolling window of completed daily rel for trail base
    # For day i: trail_prev from rel[0:i] (through i-1); after partial, trail uses
    # rel[0:i-1] + frac*rel[i] as last element of 63-window.
    for i in range(n):
        # w_prev from trail through i-1
        if i == 0:
            w_prev = 0.0
            trail_prev = np.nan
        else:
            trail_prev = _trail_from_rel(rel[:i])[-1]
            w_prev = _sat_lead(trail_prev)
        # partial update
        if i == 0:
            # no history: stay flat first frac then decide on frac*rel alone (degenerate)
            partial_rel_series = np.array([frac * rel[i]], dtype=float)
            trail_mid = float(partial_rel_series[0]) if True else np.nan
            # with <63 bars, trail_from_rel returns nan until warmup — use running product of available
            w_new = _sat_lead(trail_mid) if i + 1 >= 63 else w_prev
            if i + 1 < 63:
                # warmup: keep w_prev until full window possible with partial
                hist = np.concatenate([rel[:i], np.array([frac * rel[i]])]) if i > 0 else np.array([frac * rel[i]])
                if len(hist) >= 63:
                    trail_mid = float(np.prod(1.0 + hist[-63:]) - 1.0)
                    w_new = _sat_lead(trail_mid)
                else:
                    w_new = w_prev
        else:
            hist = np.concatenate([rel[:i], np.array([frac * float(rel[i])])])
            if len(hist) >= 63:
                trail_mid = float(np.prod(1.0 + hist[-63:]) - 1.0)
                w_new = _sat_lead(trail_mid)
            else:
                w_new = w_prev
        r[i] = frac * ((1.0 - w_prev) * rc[i] + w_prev * rs[i]) + (1.0 - frac) * (
            (1.0 - w_new) * rc[i] + w_new * rs[i]
        )
        w_end[i] = w_new
        if abs(w_new - w_prev) > 1e-12:
            flips += 1
    meta = {"n_intraday_flips": flips, "frac": frac}
    return r, w_end, meta


def _eval(
    base_w: dict[str, Any],
    chal_w: dict[str, Any],
    tip: dict[str, Any],
    *,
    fam: str,
    sat_held_cagr: float | None,
    sf_ok: bool,
) -> dict[str, Any]:
    held_b = base_w.get("heldout_2019_plus") or {}
    held_c = chal_w.get("heldout_2019_plus") or {}
    cagr_pp = cagr_lift_pp(held_b.get("cagr"), held_c.get("cagr"))
    mdd_pp = mdd_delta_pp(held_b.get("max_drawdown"), held_c.get("max_drawdown"))
    abs_mdd = held_c.get("max_drawdown")
    tip_ytd_mdd = (tip.get("ytd") or {}).get("mdd_improve_pp")
    tip_1y_mdd = (tip.get("trailing_1y") or {}).get("mdd_improve_pp")
    tip_ytd_cagr = (tip.get("ytd") or {}).get("cagr_lift_pp")
    tip_1y_cagr = (tip.get("trailing_1y") or {}).get("cagr_lift_pp")
    tip_mdd_ok = (
        tip_ytd_mdd is not None
        and tip_1y_mdd is not None
        and float(tip_ytd_mdd) >= TIP_MDD_MIN_PP
        and float(tip_1y_mdd) >= TIP_MDD_MIN_PP
    )
    tip_cagr_ok = (
        tip_ytd_cagr is not None
        and tip_1y_cagr is not None
        and float(tip_ytd_cagr) >= TIP_CAGR_MIN_PP
        and float(tip_1y_cagr) >= TIP_CAGR_MIN_PP
    )
    cagr_ok = cagr_pp is not None and float(cagr_pp) >= CAGR_FLOOR_PP
    mdd_ok = mdd_pp is not None and float(mdd_pp) >= HELD_MDD_MIN_PP
    band_ok = abs_mdd is not None and abs(float(abs_mdd)) <= HELD_ABS_MDD_MAX
    vs_sat_ok = (
        cagr_pp is not None
        and sat_held_cagr is not None
        and float(cagr_pp) >= float(sat_held_cagr) + VS_SAT_HELD_EXTRA_PP
    )
    tip_clean = bool(tip_mdd_ok and tip_cagr_ok)
    economic = bool(cagr_ok and mdd_ok and band_ok and tip_mdd_ok)
    shaped = bool(tip_clean and economic and vs_sat_ok)
    tip_cagr_s = 0.0 if tip_ytd_cagr is None else float(np.clip(tip_ytd_cagr, -5.0, 5.0))
    held_s = 0.0 if cagr_pp is None else float(np.clip(cagr_pp, -2.0, 5.0))
    mdd_s = 0.0 if mdd_pp is None else float(np.clip(mdd_pp, -1.0, 1.0))
    score = round(1.5 * tip_cagr_s + (1.0 if tip_mdd_ok else 0.0) + held_s + 0.5 * mdd_s, 4)
    return {
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_cagr_pp": tip_ytd_cagr,
        "tip_1y_cagr_pp": tip_1y_cagr,
        "tip_ytd_mdd_pp": tip_ytd_mdd,
        "tip_1y_mdd_pp": tip_1y_mdd,
        "family": fam,
        "sf_ok": sf_ok,
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_mdd": bool(tip_mdd_ok),
            "tip_cagr": bool(tip_cagr_ok),
            "tip_clean": tip_clean,
            "economic": economic,
            "vs_sat_held": bool(vs_sat_ok),
            "shaped": shaped,
        },
        "score": score,
        "hit": bool(sf_ok and shaped),
        "oracle_shaped": bool((not sf_ok) and shaped),
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    moc = [r for r in rows if r["id"].startswith("MOC_F") and r["eval"]["sf_ok"]]
    oracle = next((r for r in rows if r["id"] == "ORACLE_SAMEBAR"), None)
    if any(r["eval"]["hit"] for r in moc):
        return "LIVE_T0_MOC_HIT"
    tip_ok = [r for r in moc if r["eval"]["gates"]["tip_clean"] and r["eval"]["gates"]["economic"]]
    if tip_ok:
        return "LIVE_T0_MOC_SOFT"
    if oracle and oracle["eval"]["oracle_shaped"] and not any(r["eval"]["gates"]["tip_clean"] for r in moc):
        return "ORACLE_ONLY"
    return "LIVE_T0_BLOCK"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    live = _load(LIVE_NAV)
    comp = _load(COMP_NAV)
    sat = _load(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat = sat[sat["date"].isin(dates)].reset_index(drop=True)

    rc = comp["nav"].pct_change().fillna(0.0).to_numpy()
    rs = sat["nav"].pct_change().fillna(0.0).to_numpy()
    rel = rc - rs
    dates_np = comp["date"].to_numpy()
    nav0 = float(comp["nav"].iloc[0])

    base_w = _pack(live)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (_pack(sat).get("heldout_2019_plus") or {}).get("cagr"),
    )

    books: list[dict[str, Any]] = []

    def add(bid: str, fam: str, sf_ok: bool, r: np.ndarray, w: np.ndarray, note: str, extra: dict | None = None) -> None:
        nav = _nav_from_r(dates_np, r, nav0)
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
            if bid == BASE_ID
            else _tip(live, nav)
        )
        ev = _eval(base_w, _pack(nav), tip, fam=fam, sat_held_cagr=sat_held, sf_ok=sf_ok)
        meta = {
            "note": note,
            "pct_days_sat": round(float(np.mean(w)) * 100, 2),
            "mean_w_sat": round(float(np.mean(w)), 4),
        }
        if extra:
            meta.update(extra)
        books.append({"id": bid, "fam": fam, "meta": meta, "eval": ev, "tip": tip})
        print(json.dumps({"book": bid, "sf_ok": sf_ok, "eval": ev}, ensure_ascii=False), flush=True)

    # CTRL
    add(BASE_ID, "ctrl", True, live["nav"].pct_change().fillna(0.0).to_numpy(), np.zeros(len(live)), "live base")

    r_o, w_o = blend_oracle(rc, rs, rel)
    add("ORACLE_SAMEBAR", "oracle", False, r_o, w_o, "P3_T0_STATE same-bar upper bound")

    r_t1, w_t1 = blend_t1_open(rc, rs, rel)
    add("T1_OPEN", "t1", True, r_t1, w_t1, "Exact T+1 open fill ≡ hybrid 0k9s")

    for f in MOC_FRACS:
        print(f"MOC_F{int(f*100)} ...", flush=True)
        r_m, w_m, meta_m = blend_moc_frac(rc, rs, rel, f)
        add(
            f"MOC_F{int(f * 100)}",
            "moc",
            True,
            r_m,
            w_m,
            f"MOC proxy frac={f}: prev w for f, new w for 1-f",
            meta_m,
        )

    r_sat = rs.copy()
    add("P2_SAT_PURE", "path", True, r_sat, np.ones(len(rs)), "always SAT tip line")

    verdict = _verdict(books)
    generated = _utc()
    oracle = next(r for r in books if r["id"] == "ORACLE_SAMEBAR")
    t1 = next(r for r in books if r["id"] == "T1_OPEN")
    moc_rows = [r for r in books if r["id"].startswith("MOC_F")]
    best_moc = max(moc_rows, key=lambda r: float(r["eval"]["score"])) if moc_rows else None

    screen = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": CHARTER_ID,
        "register": "0k9t",
        "verdict": verdict,
        "theta": THETA,
        "t1_guards": T1_GUARDS,
        "rows": books,
        "best_moc": None if best_moc is None else {"id": best_moc["id"], "eval": best_moc["eval"]},
        "oracle": oracle["eval"],
        "t1_open": t1["eval"],
        "soft_frozen_keep": True,
        "global_exact_t1_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
        "code_change_this_stage": False,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md = [
        f"# {SCREEN_ID}",
        "",
        f"Date: 2026-09-29 · `{generated}` · Verdict: **`{verdict}`**",
        "Soft-Frozen KEEP · global Exact T+1 KEEP · Path3 observe KEEP · no live",
        "",
        "## Live Exact T+1 guards (binding)",
        "",
    ]
    for g in T1_GUARDS:
        md.append(f"- `{g['id']}` — `{g['path']}`: {g['rule']}")
    md += [
        "",
        "## Head-to-head",
        "",
        "| Book | sf_ok | held↑ | MDD↑ | tipY↑ | tip1y↑ | tipClean | shaped | score |",
        "|---|---|---:|---:|---:|---:|---|---|---:|",
    ]
    for r in books:
        e = r["eval"]
        md.append(
            f"| `{r['id']}` | {e['sf_ok']} | {e['held_cagr_lift_pp']} | {e['held_mdd_pp']} | "
            f"{e['tip_ytd_cagr_pp']} | {e['tip_1y_cagr_pp']} | {e['gates']['tip_clean']} | "
            f"{e['gates']['shaped']} | {e['score']} |"
        )
    md += ["", f"Best MOC: `{best_moc['id'] if best_moc else None}`", "", "Repro: `repro/fin-sat-path3-live-t0-mech-stagea/`", ""]
    screen_md = "\n".join(md) + "\n"
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    bm = best_moc["eval"] if best_moc else {}
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · global Exact T+1 **KEEP** · Path3 observe **KEEP** · cutover **BLOCKED** · no live · no fill-core edit",
            "",
            "## Answer",
            "",
            "Live 路径要吃到 Path3 tip，必须研究 **same-session fill carve-out**；",
            "仅 T+1 open（0k9s hybrid）不够。",
            "",
            f"- Oracle same-bar: tipY↑ **{oracle['eval']['tip_ytd_cagr_pp']}** · held↑ {oracle['eval']['held_cagr_lift_pp']}",
            f"- T1 open: tipY↑ **{t1['eval']['tip_ytd_cagr_pp']}** · tipClean={t1['eval']['gates']['tip_clean']}",
            f"- Best MOC `{best_moc['id'] if best_moc else 'n/a'}`: tipY↑ **{bm.get('tip_ytd_cagr_pp')}** · held↑ {bm.get('held_cagr_lift_pp')} · tipClean={bm.get('gates', {}).get('tip_clean')}",
            "",
            "## Live mechanism implication",
            "",
            "1. 现役 `PaperOpenFillPort` / `_iter_pending` / QC **禁止** same-bar；carve-out 需具名例外（`T0_CARVE_FIN_SAT_SWITCH` only）。",
            "2. MOC／盘中代理是下一研究实现方向（非整盘关 Exact T+1）。",
            "3. Path3 observe 继续当 **上界**；勿把 observe 当 live fill 预期。",
            "4. Soft-Frozen / CONF α / 全局 T+1 **KEEP**；本 Stage A **不改** live 代码。",
            "",
            "## Next（需人裁）",
            "",
            "- 若要推进：开 live fill carve-out 设计票（paper MOC port / same-bar allowlist）· 仍 BLOCKED 至 ACCEPT",
            "- 或 DEFER：维持 observe-only，不碰 fill 时钟",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md` · Register **0k9t**",
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
        "register": "0k9t",
        "best_moc": None if best_moc is None else {"id": best_moc["id"], "eval": best_moc["eval"]},
        "oracle": oracle["eval"],
        "t1_open": t1["eval"],
        "t1_guards": T1_GUARDS,
        "soft_frozen_keep": True,
        "global_exact_t1_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
        "code_change_this_stage": False,
        "cutover_blocked": True,
    }
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    charter_md = (OPS / f"{CHARTER_ID}.md").read_text(encoding="utf-8")
    (OPS / f"{CHARTER_ID}.md").write_text(
        charter_md.replace("Status: **Stage A OPEN**", f"Status: **Stage A DONE — `{verdict}`**", 1),
        encoding="utf-8",
    )
    cj = json.loads((OPS / f"{CHARTER_ID}.json").read_text(encoding="utf-8"))
    cj["status"] = "STAGE_A_DONE"
    cj["verdict"] = verdict
    (OPS / f"{CHARTER_ID}.json").write_text(json.dumps(cj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict, "best_moc": best_moc["id"] if best_moc else None}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
