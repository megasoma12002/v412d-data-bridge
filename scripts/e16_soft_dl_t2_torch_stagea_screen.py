#!/usr/bin/env python3
"""Stage A paper: Soft-assist DL T2 torch TCN / tiny LSTM (CPU).

Charter: research/ops/SOFT_DL_T2_TORCH_STAGEA_CHARTER.md

Opens TCN/LSTM after numpy T2 toehold (RULE_PROMOTE_ONLY_NO_T2_LIFT).
No live wire / no Soft×Sleeve fuse / Soft∥Sleeve OPEN unchanged.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_dl_t2_seq_stagea_screen as base

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/soft-dl-t2-torch-stagea"
OPS = ROOT / "research/ops"
DEVICE = torch.device("cpu")
SEED = 42
EPOCHS = 25
BATCH = 512
LR = 1e-2
MIN_TRAIN = int(getattr(base, "MIN_TRAIN_ROWS", 800))

SOFT_BASE = base.SOFT_BASE
OBSERVE_ID = base.OBSERVE_CHAL_ID
RULE_SELL = base.RULE_SELL_A05


class CausalTCN(nn.Module):
    """Shallow causal Conv1d over length-L log-return sequences."""

    def __init__(self, seq_len: int, channels: int = 8, kernel: int = 3):
        super().__init__()
        self.seq_len = int(seq_len)
        self.kernel = int(kernel)
        self.pad = self.kernel - 1
        self.conv = nn.Conv1d(1, channels, kernel_size=self.kernel, padding=self.pad)
        self.head = nn.Linear(channels, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.conv(x.unsqueeze(1))
        if self.pad:
            h = h[..., : -self.pad]
        h = torch.tanh(h).mean(dim=-1)
        return self.head(h).squeeze(-1)


class TinyLSTM(nn.Module):
    def __init__(self, hidden: int = 8):
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=hidden, num_layers=1, batch_first=True)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x.unsqueeze(-1))
        return self.head(out[:, -1, :]).squeeze(-1)


def _fit_torch(model: nn.Module, X: np.ndarray, y: np.ndarray, w: np.ndarray, *, seed: int) -> nn.Module:
    torch.manual_seed(int(seed))
    model = model.to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-3)
    xt = torch.tensor(X, dtype=torch.float32, device=DEVICE)
    yt = torch.tensor(y, dtype=torch.float32, device=DEVICE)
    wt = torch.tensor(w, dtype=torch.float32, device=DEVICE)
    n = xt.shape[0]
    model.train()
    for _ in range(EPOCHS):
        perm = torch.randperm(n, device=DEVICE)
        for s0 in range(0, n, BATCH):
            b = perm[s0 : s0 + BATCH]
            pred = model(xt[b])
            err = (pred - yt[b]) * wt[b]
            loss = err.pow(2).sum() / wt[b].sum().clamp_min(1.0)
            opt.zero_grad()
            loss.backward()
            opt.step()
    model.eval()
    return model


def _predict(model: nn.Module, X: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        xt = torch.tensor(X, dtype=torch.float32, device=DEVICE)
        return model(xt).cpu().numpy().ravel()


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-z))


def walk_forward_torch(
    dates,
    codes,
    seq: np.ndarray,
    fwd: np.ndarray,
    *,
    kind: str,
    alpha: float,
    seed_off: int,
) -> pd.DataFrame:
    boost = np.zeros((len(dates), len(codes)), dtype=np.float64)
    years = np.array([int(d.year) for d in dates])
    L = int(seq.shape[-1])
    for y in sorted(set(years.tolist())):
        train = years < y
        apply = years == y
        if not apply.any():
            continue
        pack = base._pack_flat(seq, fwd, train)
        if pack is None:
            continue
        Xt, yt, w = pack
        if Xt.shape[0] < MIN_TRAIN:
            continue
        if kind == "tcn":
            model: nn.Module = CausalTCN(seq_len=L, channels=8, kernel=3)
        elif kind == "lstm":
            model = TinyLSTM(hidden=8)
        else:
            raise ValueError(kind)
        model = _fit_torch(model, Xt, yt, w, seed=SEED + seed_off + y)
        for ti in np.where(apply)[0]:
            Xti = seq[ti].astype(np.float64)
            ok = np.isfinite(Xti).all(axis=1)
            score = np.zeros(len(codes), dtype=np.float64)
            if ok.any():
                score[ok] = _predict(model, Xti[ok])
            mu = float(np.nanmean(score))
            sd = float(np.nanstd(score) + 1e-6)
            boost[ti, :] = float(alpha) * _sigmoid((score - mu) / sd)
    return pd.DataFrame(boost, index=dates, columns=codes)


def main() -> int:
    print(
        f"torch {torch.__version__} cuda={torch.cuda.is_available()} device={DEVICE}",
        flush=True,
    )
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    soft = base.soft
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    import e21_forward_pipeline as e21

    LIVE_KD = base.LIVE_KD
    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse screen while LIVE_E45_STITCH is True")

    print("loading ...", flush=True)
    market = base.load_market()
    dividends = base.load_dividends()
    _p, _s, target, regime = base.e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = base.build_low_high_catalog(market, cal, list(base.FIN))

    kd_scores = base.build_kd_season_tilt_scores(
        market,
        dividends,
        list(base.FIN),
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    kd_ok = base.build_pre_exdiv_window_buy_ok(
        cal, dividends, list(base.FIN), pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    observe_buy = base.build_observe_buy_scores(kd_scores, lows)
    sell_a10 = base.soft_sell_panel(highs[base.SELL_HIGH_ID], boost=base.SOFT_BOOST)
    sell_a05 = base.soft_sell_panel(highs[base.SELL_HIGH_ID], boost=0.5)

    print("building T2 causal log-return sequences ...", flush=True)
    dates = pd.DatetimeIndex(kd_scores.index)
    codes = list(base.FIN)
    fwd = base.build_fwd_returns(market, codes, dates)
    seq10 = base.build_logret_seq(market, codes, dates, L=10)
    seq20 = base.build_logret_seq(market, codes, dates, L=20)

    print("  walk-forward TORCH TCN10 ...", flush=True)
    buy_tcn10 = walk_forward_torch(dates, codes, seq10, fwd, kind="tcn", alpha=0.5, seed_off=0)
    print("  walk-forward TORCH LSTM10 ...", flush=True)
    buy_lstm10 = walk_forward_torch(dates, codes, seq10, fwd, kind="lstm", alpha=0.5, seed_off=100)
    print("  walk-forward TORCH TCN20 ...", flush=True)
    buy_tcn20 = walk_forward_torch(dates, codes, seq20, fwd, kind="tcn", alpha=0.5, seed_off=200)
    buy_tcn10_a025 = buy_tcn10 * 0.5

    def align(df: pd.DataFrame) -> pd.DataFrame:
        return df.reindex(index=kd_scores.index, columns=kd_scores.columns).fillna(0.0)

    buy_tcn10 = align(buy_tcn10)
    buy_lstm10 = align(buy_lstm10)
    buy_tcn20 = align(buy_tcn20)
    buy_tcn10_a025 = align(buy_tcn10_a025)

    jobs = [
        (SOFT_BASE, "base", None, None),
        (OBSERVE_ID, "observe", observe_buy, sell_a10),
        (RULE_SELL, "rule_sell_ref", observe_buy, sell_a05),
        ("DL_T2_TORCH_TCN10_a05", "t2_torch_tcn10", kd_scores.astype(float) + buy_tcn10, sell_a10),
        ("DL_T2_TORCH_LSTM10_a05", "t2_torch_lstm10", kd_scores.astype(float) + buy_lstm10, sell_a10),
        ("DL_T2_TORCH_TCN20_a05", "t2_torch_tcn20", kd_scores.astype(float) + buy_tcn20, sell_a10),
        ("DL_T2_TORCH_TCN10_a025", "t2_torch_tcn10", kd_scores.astype(float) + buy_tcn10_a025, sell_a10),
        (
            "DL_T2_TORCH_LSTM10_a05__SELL_a05",
            "t2_torch_lstm10_sell_a05",
            kd_scores.astype(float) + buy_lstm10,
            sell_a05,
        ),
    ]

    print(f"Stage A books: {len(jobs)} (torch T2 TCN/LSTM CPU)", flush=True)
    rows = []
    nav_base = win_base = asof = None
    for i, (book_id, track, scores, sell) in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] {book_id}", flush=True)
        sc = kd_scores if scores is None else scores
        res = base.run_kd(market, target, regime, dividends, scores=sc, buy_ok=kd_ok, sell_scores=sell)
        win = {w: base.window_stats(res["nav"], a, b) for w, (a, b) in base.WINDOWS_STANDARD.items()}
        if book_id == SOFT_BASE:
            nav_base = res["nav"]
            win_base = win
            asof = pd.to_datetime(res["nav"]["date"]).max()
            tip = base.tip_gate(nav_base, nav_base, asof)
            held = {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "score": 0.0}
        else:
            tip = base.tip_gate(nav_base, res["nav"], asof)
            held = base.held_score(win_base["heldout_2019_plus"], win["heldout_2019_plus"])
        rows.append(
            base.book_row(
                book_id=book_id,
                track=track,
                tip=tip,
                held=held,
                win=win,
                n_fills=res["n_fills"],
                extra={
                    "is_observe_ref": book_id == OBSERVE_ID,
                    "is_rule_sell_ref": book_id == RULE_SELL,
                    "is_dl": track.startswith("t2_torch"),
                    "torch_used": True,
                },
            )
        )

    observe = next(r for r in rows if r["id"] == OBSERVE_ID)
    rule_sell = next(r for r in rows if r["id"] == RULE_SELL)
    ranked = sorted(
        rows,
        key=lambda r: (
            1 if r.get("promote_shaped") else 0,
            1 if r.get("coexist") else 0,
            r["heldout_score"],
        ),
        reverse=True,
    )
    beat_live = [r for r in ranked if r["id"] != SOFT_BASE and r.get("coexist") and r["heldout_score"] > 0]
    beat_observe = [
        r
        for r in ranked
        if r["id"] not in (SOFT_BASE, OBSERVE_ID)
        and r.get("tip_clean")
        and r["heldout_score"] > observe["heldout_score"]
    ]
    promote_vs_observe = [
        r
        for r in ranked
        if r["id"] not in (SOFT_BASE, OBSERVE_ID)
        and r.get("promote_shaped")
        and r["heldout_score"] > observe["heldout_score"]
    ]
    dl_promote = [r for r in promote_vs_observe if r.get("is_dl")]
    dl_scores = [r["heldout_score"] for r in ranked if r.get("is_dl")]
    rule_still_best = rule_sell["heldout_score"] >= (max(dl_scores) if dl_scores else -9.0)

    if dl_promote:
        verdict = "T2_TORCH_PROMOTE_SHAPED_BEATS_OBSERVE"
    elif promote_vs_observe and not dl_promote:
        verdict = "RULE_PROMOTE_ONLY_NO_T2_TORCH_LIFT"
    elif beat_live:
        verdict = "BEATS_LIVE_NO_OBSERVE_LIFT"
    else:
        verdict = "NO_LIFT"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_DL_T2_TORCH_STAGEA_SCREEN",
        "charter": "research/ops/SOFT_DL_T2_TORCH_STAGEA_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "soft_x_sleeve_fuse": False,
        "observe_swap": False,
        "torch_used": True,
        "torch_version": torch.__version__,
        "cuda": bool(torch.cuda.is_available()),
        "asof": str(pd.Timestamp(asof).date()),
        "verdict": verdict,
        "observe_id": OBSERVE_ID,
        "observe_heldout_score": observe["heldout_score"],
        "rule_sell_a05_heldout_score": rule_sell["heldout_score"],
        "rule_sell_still_best_vs_dl": bool(rule_still_best),
        "n_books": len(rows),
        "n_beat_live": len(beat_live),
        "n_beat_observe": len(beat_observe),
        "n_promote_shaped_beats_observe": len(promote_vs_observe),
        "n_dl_promote_shaped_beats_observe": len(dl_promote),
        "beat_live_ids": [r["id"] for r in beat_live],
        "beat_observe_ids": [r["id"] for r in beat_observe],
        "promote_shaped_ids": [r["id"] for r in promote_vs_observe],
        "dl_promote_shaped_ids": [r["id"] for r in dl_promote],
        "books": ranked,
        "non_actions": [
            "No live Soft-assist / Soft-Frozen / KD / TEL / E45 wire",
            "No Soft-assist or Sleeve observe swap from this screen",
            "No Soft×Sleeve auto-combo",
            "No same-MLP binary Soft-buy deepen",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    blob = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "soft_dl_t2_torch_stagea_screen.json").write_text(blob, encoding="utf-8")
    (OPS / "SOFT_DL_T2_TORCH_STAGEA_SCREEN.json").write_text(blob, encoding="utf-8")

    def pct(x):
        return "—" if x is None else f"{100 * float(x):.2f}%"

    def line(r):
        return (
            f"| `{r['id']}` | {r['track']} | {r['tip_ytd']} | {r['tip_1y']} | "
            f"{'Y' if r['tip_mdd_clean'] else 'N'} | {'Y' if r['promote_shaped'] else 'N'} | "
            f"{r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{pct(r.get('heldout_cagr'))} | {pct(r.get('heldout_mdd'))} | "
            f"{pct(r.get('sealed_cagr'))} | {pct(r.get('sealed_mdd'))} |"
        )

    lines = [
        "# Soft-Assist DL T2 Torch Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Verdict: **`{verdict}`** · books **{payload['n_books']}** · torch **{torch.__version__}** (cuda={torch.cuda.is_available()})",
        "Live wire: **false** · Soft×Sleeve fuse: **forbidden** · observe swap: **false**",
        "",
        "## Question",
        "",
        "Do torch causal TCN / tiny LSTM Soft buy boosts promote-shaped-beat Soft observe "
        "after the numpy T2 toehold showed no lift?",
        "",
        "## Summary",
        "",
        f"- Observe `{OBSERVE_ID}` held **{observe['heldout_score']:.3f}** · tip_mdd_clean **{observe['tip_mdd_clean']}**",
        f"- Rule `SELL_a05` held **{rule_sell['heldout_score']:.3f}** · tip_mdd_clean **{rule_sell['tip_mdd_clean']}** · still_best_vs_dl **{rule_still_best}**",
        f"- Beat live: **{len(beat_live)}** → `{[r['id'] for r in beat_live]}`",
        f"- Promote-shaped > observe: **{len(promote_vs_observe)}** → `{[r['id'] for r in promote_vs_observe]}`",
        f"- **DL torch T2** promote-shaped > observe: **{len(dl_promote)}** → `{[r['id'] for r in dl_promote]}`",
        "",
        "## Books",
        "",
        "| ID | Track | Tip YTD | Tip 1y | Tip MDD clean | Promote-shaped | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD |",
        "|---|---|---|---|:---:|:---:|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(line(r) for r in ranked)
    lines += [
        "",
        "## Reading",
        "",
        "- Features: causal past L∈{10,20} daily log-return sequences.",
        "- Models: torch causal TCN (ch8/k3) · tiny LSTM (h8) on CPU.",
        "- Parent numpy T2 screen remains the no-torch toehold; this charter is torch-only.",
        "- Soft∥Sleeve OPEN ballots stay independent; this screen never fuses or wires live.",
        "",
        "## Non-actions",
        "",
    ]
    lines.extend(f"- {x}" for x in payload["non_actions"])
    lines += ["", "## Label", "", f"`SOFT_DL_T2_TORCH_STAGEA_SCREEN_{payload['asof']}__{verdict}`", ""]
    md = "\n".join(lines)
    (OUT / "reports" / "SOFT_DL_T2_TORCH_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")
    (OPS / "SOFT_DL_T2_TORCH_STAGEA_SCREEN.md").write_text(md, encoding="utf-8")

    zh = "\n".join(
        [
            "# Soft-Assist DL T2 Torch Stage A 篩選",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"判決：**`{verdict}`** · torch **{torch.__version__}**",
            "",
            f"- Observe held **{observe['heldout_score']:.3f}**",
            f"- 規則 SELL_a05 held **{rule_sell['heldout_score']:.3f}** · 仍優於 DL **{rule_still_best}**",
            f"- DL torch T2 promote>observe **{len(dl_promote)}** → `{[r['id'] for r in dl_promote]}`",
            "",
            "詳表見英文稿。本 Stage A 為 torch CPU TCN／tiny LSTM（接在 numpy T2 toehold 之後）。",
            "",
            "## 非動作",
            "",
            "- 不接 live · 不換 Soft／Sleeve observe · 不融合 · 不再加深同一套 binary Soft-buy MLP",
            "",
            f"`SOFT_DL_T2_TORCH_STAGEA_SCREEN_{payload['asof']}__{verdict}`",
            "",
        ]
    )
    (OPS / "SOFT_DL_T2_TORCH_STAGEA_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    for path, open_tok, done_tok in (
        (
            OPS / "SOFT_DL_T2_TORCH_STAGEA_CHARTER.md",
            "**PAPER STAGE A OPEN**",
            f"**PAPER STAGE A DONE** · verdict **`{verdict}`**",
        ),
        (
            OPS / "SOFT_DL_T2_TORCH_STAGEA_CHARTER.zh-TW.md",
            "**PAPER STAGE A OPEN**",
            f"**PAPER STAGE A DONE** · 判決 **`{verdict}`**",
        ),
    ):
        if path.exists():
            t = path.read_text().replace(open_tok, done_tok)
            t = t.replace(
                "`SOFT_DL_T2_TORCH_STAGEA_CHARTER_2026-09-12__PAPER_OPEN`",
                f"`SOFT_DL_T2_TORCH_STAGEA_CHARTER_2026-09-12__{verdict}`",
            )
            path.write_text(t)
    cj = OPS / "SOFT_DL_T2_TORCH_STAGEA_CHARTER.json"
    if cj.exists():
        cjd = json.loads(cj.read_text())
        cjd["status"] = "PAPER_DONE"
        cjd["verdict"] = verdict
        cjd["label"] = f"SOFT_DL_T2_TORCH_STAGEA_CHARTER_2026-09-12__{verdict}"
        cj.write_text(json.dumps(cjd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    marker = "Soft-assist DL T2 torch Stage A"
    if reg.exists() and marker not in reg.read_text():
        row = (
            f"| {marker} | **PAPER DONE / {verdict}** (2026-09-12) | "
            f"torch CPU TCN/LSTM causal logret L10/L20 · "
            f"DL promote>observe **{len(dl_promote)}** · rule SELL_a05 still_best_vs_dl **{rule_still_best}** · "
            f"no live / no fuse / Soft∥Sleeve OPEN unchanged · `SOFT_DL_T2_TORCH_STAGEA_SCREEN.md` |\n"
        )
        lines_r = reg.read_text().splitlines(True)
        out_r = []
        done = False
        for l in lines_r:
            out_r.append(l)
            if not done and (
                "Soft-assist DL T2 seq Stage A" in l
                or "Soft-assist DL 4-track Stage A" in l
                or "Soft-assist dual-paper observe" in l
            ):
                out_r.append(row)
                done = True
        if done:
            reg.write_text("".join(out_r))

    print(
        json.dumps(
            {
                "verdict": verdict,
                "dl_promote": [r["id"] for r in dl_promote],
                "promote_vs_observe": [r["id"] for r in promote_vs_observe],
                "rule_sell_held": rule_sell["heldout_score"],
                "observe_held": observe["heldout_score"],
                "rule_still_best_vs_dl": rule_still_best,
                "torch_used": True,
                "torch_version": torch.__version__,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
