# FIN×SAT 分歧 Episode 特徵 Stage A (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `TIP_MDD_ONLY`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9i tip-gap 時域 **`TIP_MDD_ONLY`** — 全日平均稀釋；需先標分歧再比特徵
- 0k9j／0k9k 頻域／時頻 — 確認尺度，不取代時域
- COMPOSITE **`COMP_H150_x_A20`** · SAT_RELAX **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: 先標 COMP−SAT 分歧 episode，再只在 episode 內比特徵 · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_DIV_EPISODE_STAGEA_CHARTER_2026-09-28__DONE_TIP_MDD_ONLY__NO_LIVE_WIRE`

## Why

COMP／SAT 多數時段特徵相近、報酬貼近；全日平均（含傅立葉）被相似段稀釋。  
Belief: 只在 **分歧 episode** 內對照特徵，才能看見互斥真正發作的模式。  
Risk: 門檻敏感；episode 過短；標籤與特徵同期污染。

## Mechanism（預註冊）

相對軌跡：`trail_rel_63 = ∏(1+r_COMP−r_SAT)−1` 近 63 日。

| Label | Rule（診斷用當日；切換用 lag-1） |
|---|---|
| `SAT_LEAD` | `trail_rel_63 ≤ −θ` 且連續 ≥K 日 |
| `COMP_LEAD` | `trail_rel_63 ≥ +θ` 且連續 ≥K 日 |
| `SIMILAR` | 其餘（\|trail\|&lt;θ 或過短） |

θ∈{**0.01**, **0.02**} · K=**5**（主結果報 θ=0.01；θ=0.02 敏感性）。

**Episode 內**對照特徵（預註冊表，同 0k9i 核心）：  
`crisis` · `bearcrisis` · `r0050_63` · `mdd0050_63` · `vol0050_21` · `comp_sells_21` · `zz08_bear`

另：lag-1 特徵預測「次日落入 SAT_LEAD」的 IC／命中率（只評分歧相關任務）。

Probe（≤2）：用 episode 內分離度最高的領先特徵做 lag-1 切 SAT；HIT 門同前。

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen · Exact T+1 · FUSE · COOL · SELL_a75 · live CONF α=0.10 | **KEEP** |
| COMPOSITE + SAT_RELAX observes | **KEEP OPEN** |
| 再掃 0k9i 特徵表外新欄 · 年切 | **FORBIDDEN** |
| Live wire | **forbidden** |

## Verdicts

| Verdict | Meaning |
|---|---|
| `DIV_HIT` | probe HIT |
| `DIV_FEAT_READY` | SAT_LEAD vs SIMILAR／COMP_LEAD 分離清楚 且 ≥1 領先 IC gate |
| `DIV_FEAT_WEAK` | episode 可標但分離／IC 弱 |
| `TIP_MDD_ONLY` | probe 經濟但 tip CAGR− |

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_div_episode_stagea.py
```

Register: **0k9l**
