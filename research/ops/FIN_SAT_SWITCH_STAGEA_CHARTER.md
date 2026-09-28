# FIN×SAT 切換機制 Stage A — COMPOSITE ↔ SAT_RELAX (paper)

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9e 配資混合 **`TIP_MDD_ONLY`** — continuous `w` blend 可行域空（任一 COMP 權重 tip CAGR−）
- COMPOSITE observe **`COMP_H150_x_A20`** · SAT_RELAX observe **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: 切換機制 COMPOSITE ↔ SAT_RELAX · lag-1 signal · tip-clean + held lift · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_SWITCH_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why

配資混合證明 **同時持有** 兩邊會把 COMP tip CAGR 拖入混合物。  
Belief: **擇時擇一**（每日 100% COMP 或 100% SAT）可用 lag-1 相對績效／回撤訊號，在 tip 區間躲進 SAT、其餘吃 COMP held。  
Risk: 訊號過慢仍吃 tip 拖累；過快抖動傷 MDD；或僅貼近純 SAT／純 COMP。

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen · Exact T+1 · FUSE · COOL · SELL_a75 · live CONF α=0.10 | **KEEP** |
| COMPOSITE + SAT_RELAX observes | **KEEP OPEN** |
| 再開 HARD×α / COOL-HARD / season tip-repair / blend weight grid | **FORBIDDEN** |
| Soft×Sleeve Gate H | **FORBIDDEN** |
| Live wire / 改 live 切換 | **forbidden** |

## Mechanism

Frozen parent NAVs（同 0k9e）· **no new fills／overlays**.

每日報酬：
`r_t = r_SAT,t` if `signal_{t-1}=SAT` else `r_COMP,t`  
（lag-1 · causal）

Signals (finite):

| Family | Rule |
|---|---|
| `REL_L` COMP-def | trailing L-day return：COMP < SAT → next day SAT；else COMP |
| `REL_L` SAT-def | inverse default |
| `DD_L` COMP-def | rolling L-day max DD：COMP worse than SAT → next day SAT |
| `REL_L` + hold H | same REL + min hold H days after each flip |

## Gates (HIT) — `switch` family

1. tip YTD & 1y **CAGR↑ ≥ 0**  
2. tip YTD & 1y **MDD↑ ≥ 0**  
3. held CAGR↑ ≥ **+0.10pp**  
4. held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**  
5. held CAGR↑ ≥ SAT parent held + **+0.05pp**

## Grid (finite ≤9)

| ID | fam | rule |
|---|---|---|
| `CTRL_LIVE_A10` | ctrl | live base |
| `REF_SAT_RELAX` | ref | always SAT |
| `REF_COMP_H150_A20` | ref | always COMP |
| `SW_REL21_CDEF` | switch | REL L=21 · COMP default |
| `SW_REL63_CDEF` | switch | REL L=63 · COMP default |
| `SW_REL126_CDEF` | switch | REL L=126 · COMP default |
| `SW_REL63_SDEF` | switch | REL L=63 · SAT default |
| `SW_DD63_CDEF` | switch | DD L=63 · COMP default |
| `SW_REL63_H21` | switch | REL L=63 · COMP default · min-hold 21 |

## Verdicts

| Verdict | Meaning |
|---|---|
| `SWITCH_HIT` | ≥1 `switch` clears all HIT gates |
| `TIP_CLEAN_SOFT` | tip-clean + held≥0.10 but fails +0.05 vs SAT |
| `TIP_MDD_ONLY` / `TIP_BLOCK` / `NO_EDGE` | as labeled |

Even HIT → observe ballot **DRAFT only** · parents KEEP · no live.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_switch_stagea.py
```

Register: **0k9f**
