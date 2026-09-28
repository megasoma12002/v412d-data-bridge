# FIN×SAT Exact T+1 lag 處理路徑比較 Stage A (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `T0_ONLY_EDGE`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP**（路徑 3 標為政策反事實）· `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9n/0k9o/0k9p **`TIP_LAG_BLOCK` / `FFT_LAG_NO_EDGE`** — lag 不可解；處理改路徑
- COMPOSITE **`COMP_H150_x_A20`** · SAT_RELAX **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: 回測比較 Exact T+1 lag 四條處理路徑哪個較優 · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_CHARTER_2026-09-28__DONE_T0_ONLY_EDGE__NO_LIVE_WIRE`

## Paths（預註冊）

| ID | path | 定義 | Soft-Frozen 相容 |
|---|---|---|---|
| `P1_STOP_LIVE` | 1 停切換 | 維持 live（無 COMP↔SAT 切） | ✅ |
| `P1_STOP_COMP` | 1 停切換 | 固定 COMPOSITE | ✅ |
| `P2_SAT_PURE` | 2 tip≈SAT | 固定 SAT_RELAX | ✅（held MDD 另案） |
| `P3_T0_STATE` | 3 放寬 T+0 | 同日 `SAT_LEAD`→SAT | ❌ 反事實（需改 Exact T+1） |
| `P3_T0_ENTER_M1` | 3 放寬 | 早 1 日 oracle enter | ❌ 反事實 |
| `P4_BLEND_TRAIL` | 4 換機制 | `w_SAT=clip(−trail_l1/θ,0,1)` 日配資 | ✅ Exact T+1 |
| `P4_SCALE50_L1` | 4 換機制 | `SAT_LEAD_l1`→50/50 else COMP | ✅ |
| `R_SAT_LEAD_L1` | 對照 | 二元 lag-1 切（已知 tip−） | ✅ |

另：`CTRL_LIVE_A10` / `REF_SAT` / `REF_COMP` 與上重疊者只列一次。

## Gates / rank

- **HIT 形狀**（僅標 `sf_ok` 路徑可爭 champion）：tip-clean + held CAGR↑≥+0.10 + vsSAT+0.05 + held MDD near-flat/band  
- **Score**（全路徑）：`1.5*tip_cagr_pp_clip + tip_mdd_ok + held_cagr_pp + 0.5*held_mdd_pp`（pp 已裁剪）  
- Soft-Frozen 下 champion 只從 `sf_ok=true` 選

## Verdicts

`PATH_HIT` / `PATH_SOFT` / `PATH_TRADEOFF` / `NO_SF_EDGE` / `T0_ONLY_EDGE`

- **PATH_TRADEOFF**: tip 最優與 held 最優分屬不同路徑  
- **T0_ONLY_EDGE**: 僅反事實 T+0 達 HIT 形狀

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_t1_lag_path_compare_stagea.py
```

Register: **0k9q**
