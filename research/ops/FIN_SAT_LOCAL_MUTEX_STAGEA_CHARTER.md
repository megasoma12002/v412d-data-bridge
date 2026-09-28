# FIN×SAT 局部互斥 Stage A (paper)

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9m 分歧切換規則 **`TIP_MDD_ONLY`** — enter/confirm/exit 全 tipCAGR− · rule-layer day-switch exhausted
- 0k9l Episode — SAT_LEAD vs SIMILAR 互斥；SIMILAR~54%
- COMPOSITE **`COMP_H150_x_A20`** · SAT_RELAX **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: tip/held 互斥是不是「局部」——損害與獲利是否落在不同時段 · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_LOCAL_MUTEX_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why

0k9e–0k9m 全樣本／規則層都像「全局 tip↔held 互斥」。  
Belief: tip HARD 拖累與 held COMP 優勢落在 **不同時段／episode**（局部互斥）；若成立，上界應可同時 tip-clean+held，binding 轉成 **因果／lag** 而非結構不可能。  
Risk: 其實同日衝突（全局）；或上界也 tip/held 互斥。

## Diagnosis（預註冊）

θ=0.01 · `trail_rel_63` · tip=trailing 1y · pre-tip = heldout\tip

| 指標 | 含義 |
|---|---|
| `P(SAT_LEAD\|tip)` vs `P(SAT_LEAD\|pre)` | tip 是否局部偏向 SAT_LEAD |
| `P(COMP_LEAD\|tip)` vs `P(COMP_LEAD\|pre)` | held 優勢是否在 tip 外 |
| `sum_rel` by state × window | tip 損害／held 獲利歸因 |
| `P(drag\|tip)` vs `P(drag\|pre)` | tip-drag 濃度 |
| `local_mutex_score` | ΔP(SAT_LEAD tip−pre) + ΔP(COMP_LEAD pre−tip) |

## Books（≤2 UB + ≤4 causal）

| ID | fam | 規則 |
|---|---|---|
| `CTRL_LIVE_A10` | ctrl | live |
| `REF_SAT_RELAX` | ref | always SAT |
| `REF_COMP_H150_A20` | ref | always COMP |
| `UB_TIPWIN_SAT` | ub | tip 日曆 → SAT else COMP（**非因果**） |
| `UB_STATE_SD` | ub | 同日 `SAT_LEAD` → SAT（trail 含當日 · **軟前瞻**） |
| `R_SAT_LEAD_L1` | switch | lag-1 SAT_LEAD |
| `R_DRAG_L1` | switch | lag-1 `trail_rel_63 < 0`（更早進） |
| `R_TIPLIKE_L1` | switch | lag-1 SAT_LEAD ∧ 近 63d drag 密度≥0.5 |
| `R_PRE_COMP_TIP_SAT_L1` | switch | lag-1：pre-tip 代理（非 tip 密度）→COMP；tip-like→SAT |

## Gates (HIT)

`switch` only · tip-clean + held CAGR↑≥+0.10 + vs SAT +0.05。  
UB 不計 HIT；只標 `ub_shaped`（同門檻形狀）。

## Verdicts

`LOCAL_MUTEX_HIT` / `LOCAL_MUTEX_SIGNAL` / `TIP_LAG_BLOCK` / `GLOBAL_CONFLICT` / `TIP_MDD_ONLY` / `NO_EDGE`

- **LOCAL_MUTEX_SIGNAL**: 診斷局部成立 · UB 形狀可同時 tip+held · causal 未 HIT  
- **TIP_LAG_BLOCK**: SIGNAL + UB tip-clean/held 但所有 causal tipCAGR−（lag 綁定）  
- **GLOBAL_CONFLICT**: tip 與 held 要在重疊日選相反書

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_local_mutex_stagea.py
```

Register: **0k9n**
