# FIN×SAT Path3 live Exact T+0 mechanism Stage A (paper)

Date: 2026-09-29  
Status: **Stage A DONE — `ORACLE_ONLY`** · Soft-Frozen **KEEP** · global Exact T+1 **KEEP**（僅研究 carve-out）· Path3 observe **KEEP** · live CONF α=0.10 **KEEP** · no live wire  
Parents: 0k9r Path3 observe · 0k9s `T0_SAMEBAR_ONLY`（hybrid tip不过）· carve `T0_CARVE_FIN_SAT_SWITCH`

Human intent (normalized):

```
OPEN Stage A: research live Exact T+0 mechanism for Path3 COMP↔SAT switch carve-out · Soft-Frozen KEEP · paper only
```

## Why

0k9s：若 live 只做「决策 T+0 + fill 仍 T+1」→ tipY↑ **−8.49**。  
Observe `P3_T0_STATE` same-bar 才 HIT。要逼近该上界，必须研究 **live same-session fill** 机制（窄 carve-out），不是再扩 hybrid。

## Live binding（现状）

| Guard | Location | Effect |
|---|---|---|
| Paper fill = prior pending @ **today open** | `live_fill_core.PaperOpenFillPort` | structural T+1 |
| Pending only if `signal_date < latest` | `live_fill_core._iter_pending` | blocks same-bar |
| `fill_date <= signal_date` → `same_bar_fills` | `_exact_t1_stats` | QC fail-closed |
| Pipeline raises on `exact_t1_ok=False` | `e21_forward_pipeline` | live hard stop |
| QC `exact_t1_ok` | `e21_qc` | smoke CRITICAL |

→ 现役 live **禁止** same-bar fill；carve-out 上 live 需 **具名例外**（非全局关 Exact T+1）。

## Mechanism options（finite）

| ID | Causal? | Definition |
|---|---|---|
| `ORACLE_SAMEBAR` | ❌ | `P3_T0_STATE`：全日 trail 含当日 → 全日收益（observe 上界） |
| `T1_OPEN` | ✅ | hybrid / `R_SAT_LEAD_L1`：close 决策 → 次日 open（已证 tip−） |
| `MOC_F25` / `MOC_F50` / `MOC_F75` | ✅ 近似 | 日 frac `f` 用 `w_prev`；观察 `f·rel` 更新 `SAT_LEAD`；余下 `(1−f)` 用 `w_new`（MOC 代理） |
| `MOC_F0` | ✅ | ≡ `T1_OPEN`（全日 `w_prev`） |

`MOC_Ff` 近似「盘中看见一部分相对收益后再切，尾盘吃剩余」。无 OHLC 时用线性 frac proxy。

## Gates / rank

同 0k9q HIT 形：tip-clean + held CAGR↑≥+0.10 + vsSAT+0.05 + MDD near-flat/band。  
`ORACLE_SAMEBAR` 标 `sf_ok=false`；MOC／T1 标 `sf_ok=true`（因果）。

## Verdicts

`LIVE_T0_MOC_HIT` / `LIVE_T0_MOC_SOFT` / `LIVE_T0_BLOCK` / `ORACLE_ONLY`

## Non-goals

- Soft-Frozen clip flip · 全局关 Exact T+1 · live wire · broker SendOrder  
- 不关闭 Path3 observe  
- 不在本 Stage A 改 `live_fill_core`（只出机制结论与下一票）

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_path3_live_t0_mech_stagea.py
```

Register: **0k9t**
