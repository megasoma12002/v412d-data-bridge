# FIN×SAT 互斥特徵→切換 Stage A (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `TIP_MDD_ONLY`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9e 配資混合 **`TIP_MDD_ONLY`** · 0k9f 切換 REL/DD **`TIP_MDD_ONLY`**
- COMPOSITE observe **`COMP_H150_x_A20`** · SAT_RELAX observe **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: 研究 COMP↔SAT 好／壞年互斥特徵 → 預註冊 lag-1 切換 · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_MUTEX_FEAT_STAGEA_CHARTER_2026-09-28__DONE_TIP_MDD_ONLY__NO_LIVE_WIRE`

## Why

盲測 REL/DD 切換未開 HIT。Belief: 年度勝負有可觀察特徵（regime／0050 回撤／報酬）對應互斥優勢——COMP 吃趨勢／Bull，SAT 在危機／深回撤年較不傷 tip。  
先 **診斷** 好／壞年特徵，再測 **預註冊**（非 peek-fit）lag-1 特徵切換。

Risk: 特徵分離度不足；或僅診斷無 HIT；oracle 年切有上界但不可實作。

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen · Exact T+1 · FUSE · COOL · SELL_a75 · live CONF α=0.10 | **KEEP** |
| COMPOSITE + SAT_RELAX observes | **KEEP OPEN** |
| 再開 HARD×α / COOL-HARD / blend weight / REL grid expand | **FORBIDDEN** |
| Soft×Sleeve Gate H · live wire | **FORBIDDEN** |
| Peek 後再擴特徵門檻 | **FORBIDDEN**（門檻預註冊） |

## Mechanism

1. **Year diag** — COMP vs SAT 年報酬 · winner · 對照 regime 日占比／0050 年報酬／年 MDD  
2. **Feature contrast** — COMP-win years vs SAT-win years 特徵均值差  
3. **Pre-registered switches** — 每日 lag-1 擇一 parent NAV（同 0k9f）  
4. **Oracle year**（diag only）— 當年完美選勝方 · 不可 HIT

Frozen NAV inputs（同 0k9e/0k9f）· market regime via `e16_features` · 0050 bars from market.

## Gates (HIT) — `switch` family only

1. tip YTD & 1y **CAGR↑ ≥ 0** 且 **MDD↑ ≥ 0**  
2. held CAGR↑ ≥ **+0.10pp** · held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**  
3. held CAGR↑ ≥ SAT parent held + **+0.05pp**

`diag` / `ref` / `ctrl` 不可 HIT。

## Grid (finite ≤9)

| ID | fam | rule |
|---|---|---|
| `CTRL_LIVE_A10` | ctrl | live base |
| `REF_SAT_RELAX` | ref | always SAT |
| `REF_COMP_H150_A20` | ref | always COMP |
| `SW_CRISIS_SAT` | switch | regime Crisis → SAT else COMP |
| `SW_BEARCRISIS_SAT` | switch | Bear\|Crisis → SAT else COMP |
| `SW_BULL_COMP` | switch | Bull → COMP else SAT |
| `SW_0050DD08_SAT` | switch | 0050 roll63 MDD &lt; −8% → SAT |
| `SW_0050DD12_SAT` | switch | 0050 roll63 MDD &lt; −12% → SAT |
| `SW_0050RET63NEG_SAT` | switch | 0050 trail63 ret &lt; 0 → SAT |

Diag (not in HIT grid): `ORACLE_YEAR` perfect year pick.

## Verdicts

| Verdict | Meaning |
|---|---|
| `MUTEX_HIT` | ≥1 pre-registered `switch` clears HIT |
| `TIP_CLEAN_SOFT` | tip-clean economic but fails vs SAT +0.05 |
| `TIP_MDD_ONLY` / `TIP_BLOCK` / `NO_EDGE` | as labeled |
| `DIAG_ONLY` | no switch economic/tip path; diagnosis still binding |

Even HIT → observe ballot **DRAFT only** · parents KEEP · no live.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_mutex_feat_stagea.py
```

Register: **0k9g**
