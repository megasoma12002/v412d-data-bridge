#!/usr/bin/env python3
"""Live-baseline synthetic leverage combination trial (DIAGNOSE ONLY).

Applies candidate leverage schedules to Soft-Frozen + KD_OPT + TEL_EQUAL
BASE daily returns and reports CAGR / MDD by window.

IMPORTANT
---------
- Synthetic overlay only: r_L = e_t * r_BASE.
- Does **not** model borrow, margin calls, forced liquidations, or fee amplification.
- Executable L>1 is out of scope (e45_exposure clips to [0,1]; cash Exact T+1).
- Not promote-eligible. No live wire.

Combination modes
-----------------
1. equal_weight — equal capital across selected books
   → r = mean_i(e_i) * r_BASE
2. product — multiply selected exposure schedules daywise
   → r = prod_i(e_i) * r_BASE

Examples
--------
  python3 scripts/e16_live_leverage_combo_trial.py
  python3 scripts/e16_live_leverage_combo_trial.py --pick L150 L200 --mode equal_weight
  python3 scripts/e16_live_leverage_combo_trial.py --pick L125 DDGATE_15_07 --mode product
"""
from __future__ import annotations

import argparse
import itertools
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
from e45_paper_harness import WINDOWS_STANDARD, window_stats  # noqa: E402
from research_metric_helpers import utility_score  # noqa: E402

DEFAULT_NAV = ROOT / "repro/kelly-exposure-stagea/outputs/nav_BASE_LIVE_STACK.csv"
OUT_DIR = ROOT / "repro/live-leverage-combo-trial/outputs"
REPORT_MD = ROOT / "research/ops/LIVE_LEVERAGE_COMBO_TRIAL.md"
REPORT_JSON = ROOT / "research/ops/LIVE_LEVERAGE_COMBO_TRIAL.json"

CANDIDATE_IDS = (
    "L100",
    "L125",
    "L150",
    "L175",
    "L200",
    "REGIME_B15_X08",
    "REGIME_B20_X07",
    "DDGATE_15_07",
)


def _load_base(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    if "nav" not in df.columns:
        raise SystemExit(f"missing nav column in {path}")
    df["ret"] = df["nav"].pct_change().fillna(0.0)
    if "regime" not in df.columns:
        df["regime"] = "Unknown"
    peak = df["nav"].cummax()
    dd = df["nav"] / peak - 1.0
    df["base_dd_lag1"] = dd.shift(1).fillna(0.0)
    return df


def _exposure_schedule(cid: str, base: pd.DataFrame) -> pd.Series:
    idx = base.index
    regime = base["regime"].astype(str).str.lower()
    is_bull = regime.str.contains("bull")

    if cid == "L100":
        e = pd.Series(1.00, index=idx)
    elif cid == "L125":
        e = pd.Series(1.25, index=idx)
    elif cid == "L150":
        e = pd.Series(1.50, index=idx)
    elif cid == "L175":
        e = pd.Series(1.75, index=idx)
    elif cid == "L200":
        e = pd.Series(2.00, index=idx)
    elif cid == "REGIME_B15_X08":
        e = pd.Series(np.where(is_bull, 1.50, 0.80), index=idx, dtype=float)
    elif cid == "REGIME_B20_X07":
        e = pd.Series(np.where(is_bull, 2.00, 0.70), index=idx, dtype=float)
    elif cid == "DDGATE_15_07":
        e = pd.Series(
            np.where(base["base_dd_lag1"].to_numpy() <= -0.10, 0.70, 1.50),
            index=idx,
            dtype=float,
        )
    else:
        raise SystemExit(f"unknown candidate id: {cid}")
    return e.astype(float)


def _combine_exposures(schedules: list[pd.Series], mode: str) -> pd.Series:
    mat = pd.concat(schedules, axis=1)
    if mode == "equal_weight":
        return mat.mean(axis=1)
    if mode == "product":
        return mat.prod(axis=1)
    raise SystemExit(f"unknown mode: {mode}")


def _nav_from_levered_returns(
    dates: pd.Series, ret_base: pd.Series, exposure: pd.Series
) -> pd.DataFrame:
    r = exposure.to_numpy(dtype=float) * ret_base.to_numpy(dtype=float)
    r = np.maximum(r, -0.999)  # ruin floor for table stability
    nav = np.cumprod(1.0 + r)
    nav = nav / nav[0]
    return pd.DataFrame({"date": dates, "nav": nav})


def _pack_row(
    book_id: str,
    picks: tuple[str, ...],
    mode: str,
    exposure: pd.Series,
    nav: pd.DataFrame,
    base_nav: pd.DataFrame,
) -> dict:
    row: dict = {
        "book_id": book_id,
        "picks": list(picks),
        "n_picks": len(picks),
        "mode": mode,
        "mean_exposure": float(exposure.mean()),
        "min_exposure": float(exposure.min()),
        "max_exposure": float(exposure.max()),
        "fidelity": "SYNTHETIC_RETURN_OVERLAY_DIAGNOSE_ONLY",
        "executable_l_gt_1": False,
    }
    for wname, (start, end) in WINDOWS_STANDARD.items():
        st = window_stats(nav, start, end)
        bt = window_stats(base_nav, start, end)
        cagr = st.get("cagr")
        mdd = st.get("max_drawdown")
        bc = bt.get("cagr")
        bm = bt.get("max_drawdown")
        row[f"{wname}_cagr"] = cagr
        row[f"{wname}_mdd"] = mdd
        row[f"{wname}_util"] = utility_score(cagr, mdd, lam=0.5)
        row[f"{wname}_cagr_vs_base_pp"] = (
            None if cagr is None or bc is None else (float(cagr) - float(bc)) * 100.0
        )
        row[f"{wname}_mdd_improve_pp"] = (
            None
            if mdd is None or bm is None
            else (abs(float(bm)) - abs(float(mdd))) * 100.0
        )
        row[f"{wname}_n_days"] = st.get("n_days")
    return row


def _fmt_pct(x: float | None, digits: int = 2) -> str:
    if x is None:
        return "n/a"
    return f"{100.0 * float(x):.{digits}f}%"


def _fmt_pp(x: float | None, digits: int = 2) -> str:
    if x is None:
        return "n/a"
    return f"{float(x):+.{digits}f}pp"


def _default_jobs() -> list[tuple[str, tuple[str, ...], str]]:
    out: list[tuple[str, tuple[str, ...], str]] = []
    for cid in CANDIDATE_IDS:
        out.append((f"SINGLE__{cid}", (cid,), "equal_weight"))
    for combo in (
        ("L125", "L150"),
        ("L150", "L200"),
        ("L125", "L150", "L175"),
        ("L100", "L200"),
        ("L125", "L175", "L200"),
        ("L100", "L150", "L200"),
    ):
        out.append((f"EQ__{'_'.join(combo)}", combo, "equal_weight"))
    for combo in (
        ("L125", "REGIME_B15_X08"),
        ("L150", "DDGATE_15_07"),
        ("L125", "DDGATE_15_07"),
        ("REGIME_B15_X08", "DDGATE_15_07"),
        ("L125", "REGIME_B15_X08", "DDGATE_15_07"),
    ):
        out.append((f"PROD__{'_'.join(combo)}", combo, "product"))
    return out


def _md_table(rows: list[dict], window: str) -> str:
    lines = [
        f"| book | picks | mode | mean e | {window} CAGR | {window} MDD | vs BASE CAGR | MDD improve | util |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            "| `{book}` | {picks} | {mode} | {me:.2f} | {cagr} | {mdd} | {dc} | {dm} | {u} |".format(
                book=r["book_id"],
                picks="+".join(r["picks"]),
                mode=r["mode"],
                me=r["mean_exposure"],
                cagr=_fmt_pct(r.get(f"{window}_cagr")),
                mdd=_fmt_pct(r.get(f"{window}_mdd")),
                dc=_fmt_pp(r.get(f"{window}_cagr_vs_base_pp")),
                dm=_fmt_pp(r.get(f"{window}_mdd_improve_pp")),
                u=_fmt_pct(r.get(f"{window}_util")),
            )
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nav", type=Path, default=DEFAULT_NAV)
    ap.add_argument(
        "--pick",
        nargs="+",
        default=None,
        help=f"Candidate ids to combine. Available: {', '.join(CANDIDATE_IDS)}",
    )
    ap.add_argument(
        "--mode",
        choices=("equal_weight", "product"),
        default="equal_weight",
        help="How to combine multiple --pick ids (ignored for default menu).",
    )
    ap.add_argument(
        "--all-pairs-eq",
        action="store_true",
        help="Also emit all equal-weight pairs among constant L* candidates.",
    )
    args = ap.parse_args()

    base = _load_base(args.nav)
    base_nav = base[["date", "nav"]].copy()
    base_nav["nav"] = base_nav["nav"] / float(base_nav["nav"].iloc[0])

    if args.pick:
        picks = tuple(args.pick)
        for p in picks:
            if p not in CANDIDATE_IDS:
                raise SystemExit(f"unknown pick {p}; choose from {CANDIDATE_IDS}")
        jobs = [(f"CUSTOM__{'_'.join(picks)}__{args.mode}", picks, args.mode)]
    else:
        jobs = _default_jobs()
        if args.all_pairs_eq:
            consts = [c for c in CANDIDATE_IDS if c.startswith("L")]
            for a, b in itertools.combinations(consts, 2):
                book = f"EQ__{a}_{b}"
                if not any(j[0] == book for j in jobs):
                    jobs.append((book, (a, b), "equal_weight"))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for book_id, picks, mode in jobs:
        schedules = [_exposure_schedule(p, base) for p in picks]
        exposure = _combine_exposures(schedules, mode)
        nav = _nav_from_levered_returns(base["date"], base["ret"], exposure)
        nav.to_csv(OUT_DIR / f"nav_{book_id}.csv", index=False)
        rows.append(_pack_row(book_id, picks, mode, exposure, nav, base_nav))

    rows_sorted = sorted(
        rows,
        key=lambda r: (
            -(r.get("heldout_2019_plus_util") or -9.0),
            abs(r.get("heldout_2019_plus_mdd") or 9.0),
        ),
    )

    tip_end = pd.to_datetime(base["date"]).dt.date.max()
    tip_start_ytd = date(tip_end.year, 1, 1)
    tip_start_1y = date(tip_end.year - 1, tip_end.month, tip_end.day)

    tip_rows = []
    for book_id, _picks, _mode in jobs:
        nav = pd.read_csv(OUT_DIR / f"nav_{book_id}.csv")
        nav["date"] = pd.to_datetime(nav["date"])
        ytd = window_stats(nav, tip_start_ytd, tip_end)
        t1y = window_stats(nav, tip_start_1y, tip_end)
        by = window_stats(base_nav, tip_start_ytd, tip_end)
        b1 = window_stats(base_nav, tip_start_1y, tip_end)
        tip_rows.append(
            {
                "book_id": book_id,
                "ytd_cagr": ytd.get("cagr"),
                "ytd_mdd": ytd.get("max_drawdown"),
                "ytd_cagr_vs_base_pp": None
                if ytd.get("cagr") is None or by.get("cagr") is None
                else (float(ytd["cagr"]) - float(by["cagr"])) * 100.0,
                "t1y_cagr": t1y.get("cagr"),
                "t1y_mdd": t1y.get("max_drawdown"),
                "t1y_cagr_vs_base_pp": None
                if t1y.get("cagr") is None or b1.get("cagr") is None
                else (float(t1y["cagr"]) - float(b1["cagr"])) * 100.0,
            }
        )

    payload = {
        "label": "LIVE_LEVERAGE_COMBO_TRIAL",
        "status": "DIAGNOSE_ONLY",
        "fidelity": "SYNTHETIC_RETURN_OVERLAY",
        "base_nav": str(args.nav.relative_to(ROOT)),
        "live_stack": "Soft-Frozen FIN[0.60,0.90] + KD_OPT + TEL_EQUAL; E45 OFF",
        "candidate_ids": list(CANDIDATE_IDS),
        "combination_modes": {
            "equal_weight": "r = mean(e_i) * r_BASE",
            "product": "r = prod(e_i) * r_BASE",
        },
        "non_actions": [
            "No live wire",
            "No Soft-Frozen flip",
            "No claim of executable L>1",
            "No promote from this trial alone",
        ],
        "asof": str(tip_end),
        "n_books": len(rows_sorted),
        "books": rows_sorted,
        "tip": tip_rows,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    singles = [r for r in rows_sorted if r["n_picks"] == 1]
    multis = [r for r in rows_sorted if r["n_picks"] > 1]
    lines = [
        "# Live Baseline — Leverage Combination Trial (DIAGNOSE ONLY)",
        "",
        f"Date: 2026-09-13 · asof tip `{tip_end}`  ",
        "Status: **DIAGNOSE ONLY** · synthetic `r_L = e_t · r_BASE`  ",
        "Base: Soft-Frozen + `KD_OPT` + `TEL_EQUAL` · "
        f"`{args.nav.relative_to(ROOT)}`  ",
        "",
        "## Fidelity / non-actions",
        "",
        "- **Not** a margin/borrow simulator; L>1 is **not executable** in current Exact T+1 cash engine.",
        "- `e45_exposure` clips to `[0,1]` — do not pass L>1 expecting gearing.",
        "- No live wire · no Soft-Frozen flip · no promote from this table alone.",
        "",
        "## Candidate menu (pick 1..N)",
        "",
        "| id | meaning |",
        "|---|---|",
        "| `L100` | constant 1.00× (Live BASE) |",
        "| `L125` / `L150` / `L175` / `L200` | constant 1.25× / 1.50× / 1.75× / 2.00× |",
        "| `REGIME_B15_X08` | Bull 1.50× · else 0.80× |",
        "| `REGIME_B20_X07` | Bull 2.00× · else 0.70× |",
        "| `DDGATE_15_07` | BASE lagged DD ≤ −10% → 0.70× · else 1.50× |",
        "",
        "### Combine rules",
        "",
        "- **equal_weight**: capital split across selected books → effective e = mean(e_i).",
        "- **product**: daywise product of selected schedules → e = ∏ e_i.",
        "",
        "```bash",
        "python3 scripts/e16_live_leverage_combo_trial.py --pick L150 L200 --mode equal_weight",
        "python3 scripts/e16_live_leverage_combo_trial.py --pick L125 DDGATE_15_07 --mode product",
        "```",
        "",
        "## Single-candidate grid (heldout sort)",
        "",
        _md_table(singles, "heldout_2019_plus"),
        "",
        "### Full-sample",
        "",
        _md_table(singles, "full"),
        "",
        "### Sealed 2023+",
        "",
        _md_table(singles, "sealed_2023_plus"),
        "",
        "## Multi-candidate combinations",
        "",
        _md_table(multis, "heldout_2019_plus"),
        "",
        "### Multi — sealed 2023+",
        "",
        _md_table(multis, "sealed_2023_plus"),
        "",
        "## Tip hygiene (YTD / trailing ~1y CAGR vs BASE)",
        "",
        "| book | YTD CAGR | YTD vs BASE | 1y CAGR | 1y vs BASE | YTD MDD | 1y MDD |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for t in tip_rows:
        lines.append(
            "| `{b}` | {yc} | {yd} | {tc} | {td} | {ym} | {tm} |".format(
                b=t["book_id"],
                yc=_fmt_pct(t["ytd_cagr"]),
                yd=_fmt_pp(t["ytd_cagr_vs_base_pp"]),
                tc=_fmt_pct(t["t1y_cagr"]),
                td=_fmt_pp(t["t1y_cagr_vs_base_pp"]),
                ym=_fmt_pct(t["ytd_mdd"]),
                tm=_fmt_pct(t["t1y_mdd"]),
            )
        )
    lines += [
        "",
        "## Reading guide",
        "",
        "- **CAGR rises roughly with mean e**; **|MDD| also scales** under constant L "
        "(near-linear on the synthetic overlay).",
        "- Regime / DD-gate schedules trade some bull CAGR for shallower stress — "
        "inspect sealed + tip giveback before any charter talk.",
        "- Equal-weight of `L100+L200` ≈ `L150` on this overlay (by construction).",
        "",
        "## Label",
        "",
        "`LIVE_LEVERAGE_COMBO_TRIAL_2026-09-13__SYNTHETIC__NO_LIVE_WIRE`",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("=== LIVE leverage combo trial (SYNTHETIC / DIAGNOSE ONLY) ===")
    print(f"base: {args.nav}")
    print(f"books: {len(rows_sorted)} → {REPORT_MD.relative_to(ROOT)}")
    print()
    print(f"{'book':48s} {'held CAGR':>10s} {'held MDD':>10s} {'mean_e':>7s} {'util':>8s}")
    for r in rows_sorted[:15]:
        print(
            f"{r['book_id'][:48]:48s} "
            f"{_fmt_pct(r.get('heldout_2019_plus_cagr')):>10s} "
            f"{_fmt_pct(r.get('heldout_2019_plus_mdd')):>10s} "
            f"{r['mean_exposure']:7.2f} "
            f"{_fmt_pct(r.get('heldout_2019_plus_util')):>8s}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
