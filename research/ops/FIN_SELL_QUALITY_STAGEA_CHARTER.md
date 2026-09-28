# FIN sell-quality Stage A — Paper Charter

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · no live wire  
Parent live: Soft-Frozen F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] + FUSE + `SELL_a75` + `COOL_c8_f50_d21` + L1=0.05  
Human intent (normalized):

```
OPEN Stage A: FIN 賣側品質過濾 · 保留已測賣側優化(SELL_a75) · MDD持平/改善 + CAGR↑ · 勝率兼顧更好 · paper only
```

Motivation: 買側品質軌暴露 Stage 評分符號問題後，改測對稱的 **賣側進場品質**——在 **保留 live `SELL_a75` soft-sell** 前提下，用硬閘少做差的 FIN SELL，能否同時抬 held CAGR、護／改善 MDD；FIN SELL 前瞻勝率為診斷加分項。

Label: `FIN_SELL_QUALITY_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## KEEP (already tested)

| Item | Status |
|---|---|
| Soft-Frozen clips + Exact T+1 | **KEEP** |
| FUSE + Soft buy assists | **KEEP** |
| Live soft-sell **`SELL_a75`** (`LIVE_FUSE_SOFT_SELL_BOOST=0.75` on `RSI6_GT80`) | **KEEP** (base scores) |
| `COOL_c8_f50_d21` | **KEEP** |
| Sell **loss-defer / 等回本** | **REJECTED — do not reopen** |

## Philosophy

| Regime | Job |
|---|---|
| **Normal rebalance sell** | Optional `fin_sell_ok` AND-gate on top of live `SELL_a75` scores |
| **COOL defense** | Live COOL exposure KEEP; optional block FIN sells while cool&lt;1 |
| **Sell win-rate** | Diagnostic: FIN SELL fill then fwd H=21 **price down** (avoided bounce); **not** tip rewrite |

Belief: skip weak / low-quality FIN sells → CAGR↑ + MDD flat/↑ (+ sell WR↑).  
Risk: starve sells → hold losers → MDD↓ / tip fail; or only sell tops and miss rotation CAGR.

## Question

On `BASE_LIVE_FUSE_COOL` (= Soft + Sleeve + **SELL_a75** + FUSE + COOL), does a finite `fin_sell_ok` overlay produce ≥1 book with:

1. held **CAGR↑** ≥ **+0.15pp** where ↑ = **chal − base** (not base−chal)  
2. held MDD near-flat (↑ ≥ **−0.25pp**) and abs MDD ≤ **15%**  
3. tip YTD / 1y MDD improve ≥ **0**  
4. FIN SELL win-rate (H=21, fwd ret **&lt; 0**) improve ≥ **+1.0pp** vs control (HIT bar; soft if short)

## Metric sign (binding)

- `cagr_delta_pp(base, chal)` in helpers = **BASE − CHAL** (giveback).  
- Stage A **must** report `held_cagr_lift_pp = −cagr_delta_pp(...)` and gate on **lift**.  
- Do **not** repeat buy-quality Stage A labeling bug (printing giveback as CAGR↑).

## Non-actions

- Soft-Frozen clip / Exact T+1 / tip rewrite  
- Re-open sell loss-defer / FIFO accounting rewrite  
- Lower or remove live `SELL_a75` amplitude (KEEP; NEG control only if labeled)  
- Live wire / broker / COOL retune  
- Buy-quality observe promote from this charter  

## Grid (finite)

| ID | `fin_sell_ok` overlay |
|---|---|
| `CTRL_BASE` | none (live SELL_a75 scores only) |
| `S_RSI6_GT80` | hard AND `RSI6_GT80` |
| `S_RSI14_GT70` | hard AND `RSI14_GT70` |
| `S_K9_GT70` | hard AND `K9_GT70` |
| `S_K9_GT80` | hard AND `K9_GT80` |
| `S_ABOVE_MA60` | hard AND `ABOVE_MA60` |
| `S_ABOVE_MA20` | hard AND `ABOVE_MA20` |
| `S_NOT_BELOW_MA120` | hard AND NOT `BELOW_MA120` |
| `S_NOT_BELOW_MA60` | hard AND NOT `BELOW_MA60` |
| `S_RET5_POS` | hard AND RET5 &gt; 0 |
| `S_RET10_POS` | hard AND RET10 &gt; 0 |
| `S_COOL1_ONLY` | hard AND cool≈1 |
| `S_BELOW_MA120_NEG` | hard AND `BELOW_MA120` (**NEG** control) |

## Verdict ladder

| Label | Meaning |
|---|---|
| `SELL_QUALITY_HIT` | ≥1 challenger clears **all** gates (incl. sell win-rate) |
| `CAGR_SOFT` / `WIN_SOFT` | CAGR+MDD+tip clear; win-rate short → `WIN_SOFT` |
| `CAGR_SOFT` | MDD+tip clear; CAGR short |
| `MDD_BLOCK` / `TIP_BLOCK` | structural fail |
| `NO_EDGE` | no legal challenger clears economic gates |

## Run

```bash
PYTHONPATH=scripts python3 scripts/fin_sell_quality_stagea.py
```

Artifacts: `research/ops/FIN_SELL_QUALITY_STAGEA_*` · `repro/fin-sell-quality-stagea/`
