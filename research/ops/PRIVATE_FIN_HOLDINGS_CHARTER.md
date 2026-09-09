# Private Financial Holdings (民營金控) — Research Charter

Date: 2026-09-09  
Status: **CHARTER ACCEPTED → Stage A STOP** — human **「直接開 charter 並開跑」** · pack `PRIVATE_FIN_HOLDINGS_DECISION_PACK.md`  
Class: **A. Research / EXPERIMENTAL**  
Soft-Frozen live: **KEEP FINBAND [0.60, 0.90]** (公股 R1 sleeve membership unchanged)  
Live FIN within-sleeve: **KD_OPT KEEP** (公股)  
Live Telecom: **TEL_EQUAL KEEP**  
Capital **500M** · lot **1000** · Exact T+1 · books **`E22_v2s_tw`** where events exist

**Passing ≠ Soft-Frozen flip ≠ live universe expansion.**

---

## Problem

Early V4.11–V4.12-D / E30 research treated **民營金融** as a separate path from **公股金控** Soft-Frozen core.  
Formal router Validation passed but Blind/Final **lost to 12-stock equal-weight** → not deployed.  
That work used **EQUAL-style** within-router / equal-weight controls under older cost/execution assumptions.

Now live Soft-Frozen Financial is **公股四檔 + KD_OPT** (not EQUAL), capital/lot/E22 differ.  
Human asks to **re-open paper research** on 民營金控 under the current stack.

## Universes (frozen labels)

| Label | Codes | Note |
|---|---|---|
| **PUB_R1** (live Soft-Frozen FIN) | 2880 華南 · 2886 兆豐 · 2892 第一 · 5880 合庫 | 公股金控 |
| **PRIV_R3R4** (民營金控 focus) | 2884 玉山 · 2885 元大 · 2890 永豐 · 2891 中信 · 2881 富邦 · 2882 國泰 | R3+R4 |
| **ALL12** | PUB_R1 + 2801 彰銀 · 2834 臺企 + PRIV_R3R4 | Historical 12-stock control set |

## In scope (paper)

1. Keep Soft-Frozen **sleeve weights** from live FINBAND SSOT (Financial / Telecom / 0050).  
2. Re-allocate **only the Financial sleeve dollars** to PUB / PRIV / ALL12 member lists.  
3. Within-Financial policies: **EQUAL** and **PRE_EXDIV_KD** (live KD_OPT season params as first probe).  
4. Compare vs **`LIVE_PUB_KD`** baseline (Soft-Frozen + PUB_R1 KD_OPT + TEL_EQUAL).  
5. Metrics: held-out score vs baseline · tip YTD/1y gates · sealed report-only.

## Out of scope / WON’T

- Soft-Frozen clip / membership live edit  
- Live `e21` universe expansion without dedicated cutover ACCEPT  
- Re-tuning V4.12-D formal router Blind/Final (frozen generation)  
- Inventing replacement for retired E45 MDD narrative  

## Known data limits (updated 2026-09-09 fill)

- Private-name OHLCV from official-derived TWSE archives (`v412d_build_12stocks`).  
- Private `adj_close`: **filled** → `data/market/private_fin_adjusted.csv` (FinMind factors).  
- Private dividend events: **filled** → merged into `e22_dividend_events.csv` (+ Yahoo payment dates). See `PRIVATE_FIN_DIV_ADJ_FILL.md`.  
- Live Soft-Frozen membership still 公股 R1 only (no e21 expand).

## Stage plan

```
A  Charter ACCEPT + paper screen @ 500M     ← DONE → STOP
A′ Div/adj data fill + re-screen            ← DONE → still STOP
B  If tip-clean + held-out>0 → dual-paper observe ballot
C  Live universe / sleeve cutover ONLY after dedicated ACCEPT
```

## Artifacts

- `scripts/e16_private_fin_holdings_rescreen.py`
- `scripts/e22_fill_private_fin_div_adj.py`
- `research/ops/PRIVATE_FIN_HOLDINGS_CHARTER.md` (this file)
- `research/ops/PRIVATE_FIN_DIV_ADJ_FILL.md`
- `research/ops/PRIVATE_FIN_HOLDINGS_RESCREEN.{md,json}`
- `repro/private-fin-holdings-20260909/`

## Label

`PRIVATE_FIN_HOLDINGS_CHARTER_2026-09-09__PAPER_ONLY__SOFT_FROZEN_PUB_KEEP`
