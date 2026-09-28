# FIN×SAT 配資混合 Stage A — COMPOSITE × SAT_RELAX (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `TIP_MDD_ONLY`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- COMPOSITE observe **`COMP_H150_x_A20`** · held／sealed 強 · tip MDD↑ · tip CAGR PAUSE
- SAT_RELAX observe **`SAT_A20_RELAX`** · tip CAGR 乾淨 · held 升幅較小

Human intent (normalized):

```
OPEN Stage A: 配資混合 COMPOSITE × SAT_RELAX · tip-clean + held lift · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_BLEND_STAGEA_CHARTER_2026-09-28__DONE_TIP_MDD_ONLY__NO_LIVE_WIRE`

## Why

Mechanism fuse（HARD×densify）無法同時保留兩邊優點。  
改測 **紙上配資混合**：每日報酬加權  
`r = w·r_COMP + (1−w)·r_SAT`（daily rebalance proxy）。

Belief: 中間權重可在 tip CAGR≥0 下，抬高 held 超過純 SAT。  
Risk: 可行域空（tip-clean 時 held 仍貼 SAT）；或僅平均、無 HIT。

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen · Exact T+1 · FUSE · COOL · SELL_a75 · live CONF α=0.10 | **KEEP** |
| COMPOSITE + SAT_RELAX observes | **KEEP OPEN** |
| 再開 HARD×α / COOL-HARD / season tip-repair | **FORBIDDEN** |
| Soft×Sleeve Gate H | **FORBIDDEN** |
| Live wire / 改 live 配資 | **forbidden** |

## Mechanism

| Input NAV (frozen SSOT) | Path |
|---|---|
| Live base | `repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv` |
| COMPOSITE | `…/comp_h150_x_a20_daily_nav.csv` |
| SAT_RELAX | `repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv` |

Blend: daily simple-return mix · `w = weight on COMPOSITE` · no new fills／no new overlays.

## Gates (HIT) — `blend` family

1. tip YTD & 1y **CAGR↑ ≥ 0**  
2. tip YTD & 1y **MDD↑ ≥ 0**  
3. held CAGR↑ ≥ **+0.10pp**  
4. held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**  
5. held CAGR↑ ≥ SAT parent held + **+0.05pp**（必須比純 SAT 多一點 held）

## Grid (finite ≤9)

| ID | fam | w_COMP |
|---|---|---:|
| `CTRL_LIVE_A10` | ctrl | —（base） |
| `REF_SAT_RELAX` | ref | 0.00 |
| `REF_COMP_H150_A20` | ref | 1.00 |
| `BLEND_C25` | blend | 0.25 |
| `BLEND_C35` | blend | 0.35 |
| `BLEND_C40` | blend | 0.40 |
| `BLEND_C50` | blend | 0.50 |
| `BLEND_C65` | blend | 0.65 |
| `BLEND_C75` | blend | 0.75 |

## Verdicts

| Verdict | Meaning |
|---|---|
| `BLEND_HIT` | ≥1 `blend` clears all HIT gates |
| `TIP_CLEAN_SOFT` | tip-clean + held≥0.10 but fails +0.05 vs SAT |
| `TIP_MDD_ONLY` / `TIP_BLOCK` / `NO_EDGE` | as labeled |

Even HIT → observe ballot **DRAFT only** · 不自動取代兩條 parent observe · no live.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_blend_stagea.py
```

Register: **0k9e**
