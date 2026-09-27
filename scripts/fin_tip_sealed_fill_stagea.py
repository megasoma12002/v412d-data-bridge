#!/usr/bin/env python3
"""FIN tip / sealed fill quality Stage A (paper / observe).

Charter: research/ops/FIN_TIP_SEALED_FILL_STAGEA_CHARTER.md
adj_close-scaled OHLC · Soft-Frozen KEEP · no live wire.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import live_cool_c8_cutover as cool_cut
import live_dh_fuse_cutover as fuse_cut
from e16_soft_frozen_base import FIN
from e45_paper_harness import load_dividends, load_market
from live_config import KD_OPT
from live_fill_extreme_audit import (
    N_GRID,
    _clip_binding,
    _fill_px_on_panel,
    _in_kd_season,
    _ohlc_panel,
    _ohlc_panel_raw,
    _sleeve,
    _window_ext,
)
from within_sleeve_alloc import build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "forward" / "e21"
REPRO = ROOT / "repro" / "fin-tip-sealed-fill-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_TIP_SEALED_FILL_STAGEA_CHARTER"
SCREEN_ID = "FIN_TIP_SEALED_FILL_STAGEA_SCREEN"
DECISION_ID = "FIN_TIP_SEALED_FILL_STAGEA_DECISION_PACK"
BOOK_ID = "LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8"
SEALED_START = date(2023, 1, 1)
PEER_GAP_PP = 0.50
TIP_VS_SEALED_PP = 0.50
MECH_CONC = 0.70


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stats(sub: pd.DataFrame) -> dict[str, Any]:
    if sub is None or sub.empty:
        return {"n": 0}
    n5 = pd.to_numeric(sub["n5"], errors="coerce").dropna()
    n21 = pd.to_numeric(sub["n21"], errors="coerce").dropna()
    t1 = pd.to_numeric(sub["t1"], errors="coerce").dropna()
    return {
        "n": int(len(sub)),
        "n_buy": int((sub["side"] == "BUY").sum()),
        "n_sell": int((sub["side"] == "SELL").sum()),
        "mean_n5": round(float(n5.mean()), 4) if len(n5) else None,
        "median_n5": round(float(n5.median()), 4) if len(n5) else None,
        "p90_n5": round(float(n5.quantile(0.90)), 4) if len(n5) else None,
        "mean_n21": round(float(n21.mean()), 4) if len(n21) else None,
        "mean_t1": round(float(t1.mean()), 4) if len(t1) else None,
        "share_n5_le3": round(float((n5 <= 3.0).mean()), 4) if len(n5) else None,
    }


def _delta(a: dict[str, Any], b: dict[str, Any], key: str = "mean_n5") -> float | None:
    if not a or not b or a.get(key) is None or b.get(key) is None:
        return None
    return round(float(a[key]) - float(b[key]), 4)


def _mech_counts(sub: pd.DataFrame) -> dict[str, int]:
    c: Counter[str] = Counter()
    for m in sub["mechanisms"]:
        for t in m or []:
            c[t] += 1
    return dict(c.most_common())


def _annotate(
    fills: pd.DataFrame,
    *,
    market: pd.DataFrame,
    cool: pd.Series,
    dh: pd.Series | None,
    buy_ok: pd.DataFrame,
    target: pd.DataFrame | None,
    source: str,
    tip_signals: pd.DataFrame | None = None,
) -> pd.DataFrame:
    codes = sorted(fills["code"].astype(str).unique())
    panels = {c: _ohlc_panel(market, c) for c in codes}
    panels_raw = {c: _ohlc_panel_raw(market, c) for c in codes}
    sig_map = None
    if tip_signals is not None and not tip_signals.empty:
        tip_signals = tip_signals.copy()
        tip_signals["date"] = pd.to_datetime(tip_signals["date"]).dt.normalize()
        sig_map = tip_signals.set_index("date")

    rows: list[dict[str, Any]] = []
    for i, f in fills.iterrows():
        code = str(f["code"])
        side = str(f["side"]).upper()
        px_raw = float(f["fill_price"])
        sig_d = pd.Timestamp(f["signal_date"]).normalize()
        fill_d = pd.Timestamp(f["fill_date"]).normalize()
        sleeve = _sleeve(code)
        panel = panels.get(code, pd.DataFrame())
        raw_panel = panels_raw.get(code, pd.DataFrame())
        px = _fill_px_on_panel(px_raw, fill_d, raw_panel, panel)

        cool_exp = None
        if not cool.empty:
            if sig_d in cool.index and pd.notna(cool.loc[sig_d]):
                cool_exp = float(cool.loc[sig_d])
            else:
                prior = cool.index[cool.index <= sig_d]
                if len(prior):
                    cool_exp = float(cool.loc[prior[-1]])
        dh_exp = None
        if dh is not None and not dh.empty:
            if sig_d in dh.index and pd.notna(dh.loc[sig_d]):
                dh_exp = float(dh.loc[sig_d])
            else:
                prior = dh.index[dh.index <= sig_d]
                if len(prior):
                    dh_exp = float(dh.loc[prior[-1]])

        fin_w = tel_w = etf_w = None
        if sig_map is not None and sig_d in sig_map.index:
            srow = sig_map.loc[sig_d]
            if isinstance(srow, pd.DataFrame):
                srow = srow.iloc[-1]
            fin_w = float(srow["e16_financial"]) if "e16_financial" in srow.index else None
            tel_w = float(srow["e16_telecom"]) if "e16_telecom" in srow.index else None
            etf_w = float(srow["e16_0050"]) if "e16_0050" in srow.index else None
            if "dh_exposure" in srow.index and pd.notna(srow["dh_exposure"]):
                dh_exp = float(srow["dh_exposure"])
        elif target is not None and not target.empty:
            if sig_d in target.index:
                row = target.loc[sig_d]
            else:
                prior = target.index[target.index <= sig_d]
                row = target.loc[prior[-1]] if len(prior) else None
            if row is not None:
                fin_w = float(row["Financial"]) if "Financial" in row.index else None
                tel_w = float(row["Telecom"]) if "Telecom" in row.index else None
                etf_w = float(row["0050"]) if "0050" in row.index else None

        mech: list[str] = ["T1_ALWAYS"]
        t1 = None
        if not panel.empty and sig_d in panel.index:
            s_low = float(panel.loc[sig_d, "low"])
            s_high = float(panel.loc[sig_d, "high"])
            if side == "BUY" and s_low > 0:
                t1 = (px - s_low) / s_low * 100.0
            elif side == "SELL" and s_high > 0:
                t1 = (s_high - px) / s_high * 100.0
            mech.append("T1_DRAG")
        if dh_exp is not None and dh_exp < 1.0 - 1e-12:
            mech.append("DEFENSE_DH" if source == "tip" else "DEFENSE_DH_CF")
        if cool_exp is not None and cool_exp < 1.0 - 1e-12:
            mech.append("DEFENSE_COOL_CF" if source == "tip" else "DEFENSE_COOL")
        if fin_w is not None and tel_w is not None and etf_w is not None:
            mech.extend(_clip_binding(fin_w, tel_w, etf_w))
        kd_in = _in_kd_season(sig_d)
        if sleeve == "FIN":
            if not kd_in:
                mech.append("KD_OFFSEASON")
            if side == "BUY" and sig_d in buy_ok.index and code in buy_ok.columns:
                if not bool(buy_ok.loc[sig_d, code]):
                    mech.append("KD_BUY_BLOCK")

        n5 = n21 = None
        for n, key in ((5, "n5"), (21, "n21")):
            lo, hi, _ = _window_ext(panel, fill_d, n)
            if lo is None or hi is None or lo <= 0 or hi <= 0:
                continue
            if side == "BUY":
                dist = (px - lo) / lo * 100.0
            else:
                dist = (hi - px) / hi * 100.0
            if key == "n5":
                n5 = dist
            else:
                n21 = dist

        rows.append(
            {
                "source": source,
                "fill_id": f.get("fill_id", f"{fill_d.date()}-{code}-{side}-{i}"),
                "signal_date": sig_d.date().isoformat(),
                "fill_date": fill_d.date().isoformat(),
                "code": code,
                "sleeve": sleeve,
                "side": side,
                "quantity": int(f["quantity"]),
                "fill_price": px_raw,
                "fill_price_adj": round(float(px), 6),
                "ohlc_basis": "adj_close_scaled",
                "n5": None if n5 is None else round(float(n5), 4),
                "n21": None if n21 is None else round(float(n21), 4),
                "t1": None if t1 is None else round(float(t1), 4),
                "defense_cool": bool(cool_exp is not None and cool_exp < 1.0 - 1e-12),
                "defense_dh": bool(dh_exp is not None and dh_exp < 1.0 - 1e-12),
                "kd_in_season": bool(kd_in),
                "e16_financial": fin_w,
                "mechanisms": mech,
            }
        )
    return pd.DataFrame(rows)


def _sleeve_table(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for sleeve in ("FIN", "TEL", "0050", "ALL"):
        for side in ("ALL", "BUY", "SELL"):
            sub = df
            if sleeve != "ALL":
                sub = sub[sub["sleeve"] == sleeve]
            if side != "ALL":
                sub = sub[sub["side"] == side]
            if sub.empty:
                continue
            out[f"{sleeve}_{side}"] = _stats(sub)
    return out


def _fin_mech_slices(fin: pd.DataFrame) -> dict[str, Any]:
    if fin.empty:
        return {}
    out = {
        "all": _stats(fin),
        "kd_in": _stats(fin[fin["kd_in_season"]]),
        "kd_off": _stats(fin[~fin["kd_in_season"]]),
        "cool_on": _stats(fin[fin["defense_cool"]]),
        "cool_off": _stats(fin[~fin["defense_cool"]]),
        "buy": _stats(fin[fin["side"] == "BUY"]),
        "sell": _stats(fin[fin["side"] == "SELL"]),
        "by_code": {},
        "mechanism_counts": _mech_counts(fin),
    }
    clip = fin["mechanisms"].map(lambda m: "CLIP_FIN_HI" in (m or []))
    out["clip_fin_hi"] = _stats(fin[clip])
    out["not_clip_fin_hi"] = _stats(fin[~clip])
    out["delta_kd_off_minus_in_n5"] = _delta(out["kd_off"], out["kd_in"])
    out["delta_clip_minus_not_n5"] = _delta(out["clip_fin_hi"], out["not_clip_fin_hi"])
    out["delta_cool_on_minus_off_n5"] = _delta(out["cool_on"], out["cool_off"])
    for code in sorted(fin["code"].unique()):
        out["by_code"][str(code)] = _stats(fin[fin["code"] == code])
    return out


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )

    # --- tip ---
    tip_fills = pd.read_csv(STATE / "fills.csv", dtype={"code": str})
    tip_fills["signal_date"] = pd.to_datetime(tip_fills["signal_date"]).dt.normalize()
    tip_fills["fill_date"] = pd.to_datetime(tip_fills["fill_date"]).dt.normalize()
    tip_sig = (
        pd.read_csv(STATE / "signals.csv")
        if (STATE / "signals.csv").exists()
        else pd.DataFrame()
    )
    print("building cool/dh from FUSE offense (tip CF + sealed book) ...", flush=True)
    fuse_nav, _, _ = fuse_cut.build_fuse_offense_sim(market, dividends)
    cool = cool_cut.build_cool_exposure_from_offense(market, fuse_nav)
    dh = fuse_cut.build_dh_exposure_from_offense(market, fuse_nav)
    tip = _annotate(
        tip_fills,
        market=market,
        cool=cool,
        dh=dh,
        buy_ok=buy_ok,
        target=None,
        source="tip",
        tip_signals=tip_sig,
    )
    tip.to_csv(OUT / "tip_fill_detail.csv", index=False)

    # --- sealed backtest twin ---
    print("building FUSE+COOL sealed fills ...", flush=True)
    target = fuse_cut.fuse_target_for_market(market)
    cool_nav, bt_fills, _ = fuse_cut.build_fuse_offense_sim(
        market, dividends, e45_exposure=cool
    )
    del cool_nav
    bt_fills = bt_fills.copy()
    bt_fills["signal_date"] = pd.to_datetime(bt_fills["signal_date"]).dt.normalize()
    bt_fills["fill_date"] = pd.to_datetime(bt_fills["fill_date"]).dt.normalize()
    sealed_fills = bt_fills[
        bt_fills["fill_date"].dt.date >= SEALED_START
    ].reset_index(drop=True)
    sealed = _annotate(
        sealed_fills,
        market=market,
        cool=cool,
        dh=dh,
        buy_ok=buy_ok,
        target=target,
        source="sealed",
    )
    sealed.to_csv(OUT / "sealed_fill_detail.csv", index=False)

    tip_sleeves = _sleeve_table(tip)
    sealed_sleeves = _sleeve_table(sealed)
    tip_fin = _fin_mech_slices(tip[tip["sleeve"] == "FIN"])
    sealed_fin = _fin_mech_slices(sealed[sealed["sleeve"] == "FIN"])

    tip_fin_st = tip_sleeves.get("FIN_ALL") or {}
    tip_tel_st = tip_sleeves.get("TEL_ALL") or {}
    sea_fin_st = sealed_sleeves.get("FIN_ALL") or {}
    sea_tel_st = sealed_sleeves.get("TEL_ALL") or {}

    tip_peer_gap = _delta(tip_fin_st, tip_tel_st)
    sealed_peer_gap = _delta(sea_fin_st, sea_tel_st)
    tip_vs_sealed = _delta(tip_fin_st, sea_fin_st)

    tip_gap_ok = tip_peer_gap is not None and float(tip_peer_gap) >= PEER_GAP_PP
    sealed_gap_ok = (
        sealed_peer_gap is not None and float(sealed_peer_gap) >= PEER_GAP_PP
    )
    tip_unique = tip_vs_sealed is not None and float(tip_vs_sealed) >= TIP_VS_SEALED_PP

    # mechanism concentration among tip FIN fills with n5 > FIN median
    conc_note = None
    conc_hit = False
    fin_tip = tip[tip["sleeve"] == "FIN"]
    if len(fin_tip) and fin_tip["n5"].notna().any():
        med = float(fin_tip["n5"].median())
        weak = fin_tip[fin_tip["n5"] > med]
        if len(weak):
            mc = _mech_counts(weak)
            # ignore always-on T1 tags for concentration
            focus = {
                k: v
                for k, v in mc.items()
                if k not in ("T1_ALWAYS", "T1_DRAG")
            }
            if focus:
                top_tag, top_n = max(focus.items(), key=lambda x: x[1])
                share = top_n / len(weak)
                conc_note = {
                    "weak_n": int(len(weak)),
                    "median_n5": round(med, 4),
                    "top_tag": top_tag,
                    "top_n": int(top_n),
                    "share": round(float(share), 4),
                }
                conc_hit = share >= MECH_CONC

    if tip_gap_ok and sealed_gap_ok:
        verdict = "FIN_BOTH_WEAK"
    elif tip_gap_ok and tip_unique and not sealed_gap_ok:
        verdict = "FIN_TIP_SAMPLE"
    elif sealed_gap_ok and not tip_gap_ok:
        verdict = "FIN_SEALED_WEAK"
    elif tip_gap_ok and not sealed_gap_ok:
        verdict = "FIN_TIP_SAMPLE"
    else:
        verdict = "FIN_QUALITY_OK"
    if conc_hit and verdict != "FIN_QUALITY_OK":
        # annotate but keep primary structural verdict; expose flag
        pass

    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "ohlc_basis": "adj_close_scaled",
        "book_id": BOOK_ID,
        "gates": {
            "peer_gap_pp": PEER_GAP_PP,
            "tip_vs_sealed_pp": TIP_VS_SEALED_PP,
            "mech_concentration": MECH_CONC,
        },
        "gaps": {
            "tip_fin_minus_tel_n5": tip_peer_gap,
            "sealed_fin_minus_tel_n5": sealed_peer_gap,
            "tip_fin_minus_sealed_fin_n5": tip_vs_sealed,
            "tip_peer_gap_gate": bool(tip_gap_ok),
            "sealed_peer_gap_gate": bool(sealed_gap_ok),
            "tip_vs_sealed_gate": bool(tip_unique),
        },
        "tip": {
            "n_fills": int(len(tip)),
            "fill_date_min": str(tip["fill_date"].min()) if len(tip) else None,
            "fill_date_max": str(tip["fill_date"].max()) if len(tip) else None,
            "sleeves": tip_sleeves,
            "fin": tip_fin,
        },
        "sealed": {
            "n_fills": int(len(sealed)),
            "fill_date_min": str(sealed["fill_date"].min()) if len(sealed) else None,
            "fill_date_max": str(sealed["fill_date"].max()) if len(sealed) else None,
            "sleeves": sealed_sleeves,
            "fin": sealed_fin,
        },
        "weak_bucket_concentration": conc_note,
        "mech_concentrated_flag": bool(conc_hit),
        "binding": [
            "Soft-Frozen live KEEP",
            "Exact T+1 KEEP",
            "No tip rewrite",
            "No live wire from this Stage A",
        ],
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    def _row(st: dict[str, Any]) -> str:
        if not st or not st.get("n"):
            return "— | — | — | —"
        return (
            f"{st.get('n')} | {st.get('mean_n5')} | {st.get('median_n5')} | "
            f"{st.get('mean_n21')} | {st.get('mean_t1')}"
        )

    lines = [
        "# FIN tip / sealed fill quality — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **`{verdict}`** · Soft-Frozen KEEP · **no live wire** · "
        f"`ohlc_basis=adj_close_scaled` · `{BOOK_ID}`",
        "",
        "## Gaps vs gates",
        "",
        f"| gap | pp | gate ≥{PEER_GAP_PP} |",
        "|---|---:|---|",
        f"| tip FIN − tip TEL ±5d | {tip_peer_gap} | "
        f"{'Y' if tip_gap_ok else 'n'} |",
        f"| sealed FIN − sealed TEL ±5d | {sealed_peer_gap} | "
        f"{'Y' if sealed_gap_ok else 'n'} |",
        f"| tip FIN − sealed FIN ±5d | {tip_vs_sealed} | "
        f"{'Y' if tip_unique else 'n'} (unique-tip ≥{TIP_VS_SEALED_PP}) |",
        "",
        "## Tip window",
        "",
        f"Fills **{len(tip)}** · `{payload['tip']['fill_date_min']}` → "
        f"`{payload['tip']['fill_date_max']}`",
        "",
        "| sleeve_side | n | ±5 mean | ±5 med | ±21 mean | T+1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key in (
        "ALL_ALL",
        "FIN_ALL",
        "FIN_BUY",
        "FIN_SELL",
        "TEL_ALL",
        "0050_ALL",
    ):
        st = tip_sleeves.get(key) or {}
        if st.get("n"):
            lines.append(
                f"| `{key}` | {st.get('n')} | {st.get('mean_n5')} | "
                f"{st.get('median_n5')} | {st.get('mean_n21')} | {st.get('mean_t1')} |"
            )

    lines += [
        "",
        "### Tip FIN mechanism slices",
        "",
        f"KD off−in Δn5 **{tip_fin.get('delta_kd_off_minus_in_n5')}** · "
        f"CLIP−not Δn5 **{tip_fin.get('delta_clip_minus_not_n5')}** · "
        f"COOL on−off Δn5 **{tip_fin.get('delta_cool_on_minus_off_n5')}**",
        "",
        "| slice | n | ±5 mean | T+1 |",
        "|---|---:|---:|---:|",
    ]
    for k in (
        "all",
        "kd_in",
        "kd_off",
        "clip_fin_hi",
        "not_clip_fin_hi",
        "cool_on",
        "cool_off",
        "buy",
        "sell",
    ):
        st = tip_fin.get(k) or {}
        if st.get("n"):
            lines.append(
                f"| `{k}` | {st.get('n')} | {st.get('mean_n5')} | {st.get('mean_t1')} |"
            )
    lines += [
        "",
        "| mechanism | n |",
        "|---|---:|",
    ]
    for k, v in (tip_fin.get("mechanism_counts") or {}).items():
        lines.append(f"| `{k}` | {v} |")

    lines += [
        "",
        "## Sealed 2023+ (FUSE+COOL twin)",
        "",
        f"Fills **{len(sealed)}** · `{payload['sealed']['fill_date_min']}` → "
        f"`{payload['sealed']['fill_date_max']}`",
        "",
        "| sleeve_side | n | ±5 mean | ±5 med | ±21 mean | T+1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key in (
        "ALL_ALL",
        "FIN_ALL",
        "FIN_BUY",
        "FIN_SELL",
        "TEL_ALL",
        "0050_ALL",
    ):
        st = sealed_sleeves.get(key) or {}
        if st.get("n"):
            lines.append(
                f"| `{key}` | {st.get('n')} | {st.get('mean_n5')} | "
                f"{st.get('median_n5')} | {st.get('mean_n21')} | {st.get('mean_t1')} |"
            )

    lines += [
        "",
        "### Sealed FIN mechanism slices",
        "",
        f"KD off−in Δn5 **{sealed_fin.get('delta_kd_off_minus_in_n5')}** · "
        f"CLIP−not Δn5 **{sealed_fin.get('delta_clip_minus_not_n5')}** · "
        f"COOL on−off Δn5 **{sealed_fin.get('delta_cool_on_minus_off_n5')}**",
        "",
        "| slice | n | ±5 mean | T+1 |",
        "|---|---:|---:|---:|",
    ]
    for k in (
        "all",
        "kd_in",
        "kd_off",
        "clip_fin_hi",
        "not_clip_fin_hi",
        "cool_on",
        "cool_off",
        "buy",
        "sell",
    ):
        st = sealed_fin.get(k) or {}
        if st.get("n"):
            lines.append(
                f"| `{k}` | {st.get('n')} | {st.get('mean_n5')} | {st.get('mean_t1')} |"
            )

    if conc_note:
        lines += [
            "",
            "## Tip FIN weak-bucket concentration",
            "",
            f"Fills with n5 > FIN median ({conc_note['median_n5']}%): "
            f"n={conc_note['weak_n']} · top non-T1 tag `{conc_note['top_tag']}` "
            f"{conc_note['top_n']} ({conc_note['share']:.0%}) · "
            f"conc_flag={'Y' if conc_hit else 'n'}",
        ]

    lines += [
        "",
        "### Read",
        "",
        f"Verdict **`{verdict}`**: "
        + {
            "FIN_TIP_SAMPLE": "tip FIN looks weak vs TEL, but sealed does not replicate — tip-window sample.",
            "FIN_SEALED_WEAK": "sealed FIN is weak vs TEL; tip may or may not match.",
            "FIN_BOTH_WEAK": "both tip and sealed FIN ≥0.50pp worse than TEL peers.",
            "FIN_QUALITY_OK": "neither tip nor sealed peer gap clears +0.50pp.",
        }.get(verdict, ""),
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/fin_tip_sealed_fill_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": DECISION_ID,
        "generated_at_utc": _utc(),
        "status": verdict,
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "ohlc_basis": "adj_close_scaled",
        "gaps": payload["gaps"],
        "mech_concentrated_flag": bool(conc_hit),
        "weak_bucket_concentration": conc_note,
        "binding": payload["binding"],
        "next": (
            "Discussion only — FIN_TIP_SAMPLE ⇒ monitor tip, no live retune; "
            "FIN_BOTH_WEAK / FIN_SEALED_WEAK ⇒ optional follow-up Stage A on ONE lever "
            "(not Soft-Frozen batch); FIN_QUALITY_OK ⇒ close observe"
        ),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
    }
    dlines = [
        "# FIN tip / sealed fill quality — Decision Pack",
        "",
        f"Date: 2026-09-26 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false** · adj OHLC",
        "",
        f"tip FIN−TEL ±5d **{tip_peer_gap}pp** · sealed FIN−TEL **{sealed_peer_gap}pp** · "
        f"tip−sealed FIN **{tip_vs_sealed}pp**.",
        "",
        "## Binding",
        "",
    ] + [f"{i}. {b}" for i, b in enumerate(decision["binding"], 1)]
    dlines += [
        "",
        f"Next: {decision['next']}",
        "",
        f"Label: `{DECISION_ID}_2026-09-26__{verdict}`",
        "",
    ]
    for path in (OPS, REP):
        (path / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
        (path / f"{DECISION_ID}.md").write_text("\n".join(dlines) + "\n")

    (REPRO / "README.md").write_text(
        "\n".join(
            [
                "# FIN tip / sealed fill quality Stage A",
                "",
                f"Charter: `research/ops/{CHARTER_ID}.md`",
                f"Screen: `reports/{SCREEN_ID}.md`",
                "",
                "```bash",
                "PYTHONPATH=scripts python3 scripts/fin_tip_sealed_fill_stagea.py",
                "```",
                "",
            ]
        )
    )
    (REPRO / ".gitignore").write_text("**/outputs/*fill_detail*.csv\n")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "gaps": payload["gaps"],
                "tip_fin": tip_fin_st,
                "tip_tel": tip_tel_st,
                "sealed_fin": sea_fin_st,
                "sealed_tel": sea_tel_st,
                "conc": conc_note,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
