# FIN_SAT_DIV_RULE_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T14:09:59Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_DIV_RULE_STAGEA_CHARTER.md`
Screen: `FIN_SAT_DIV_RULE_STAGEA_SCREEN.md`
Parents: 0k9l/0k9i · register **0k9m**

## Verdict

**`TIP_MDD_ONLY`**

Best economic tipMDD rule: `R_DIV_ONLY` · held↑ 1.2962 · tipCAGR↑ -8.4925 · %SAT 24.13

## Reading

6 預註冊 switch 全過 economic+tipMDD，**無一 tip-clean**（tipYTD CAGR 全 −6～−12）。

**精煉：**
1. **規則層仍修不了 tip CAGR** — enter/confirm/exit（HOT∧CONF、DIV∧CONF hold、crisis hold、HOT→DIV）與單狀態 `DIV_ONLY` 同一失敗模式：held 可贏 live／甚至贏 SAT（`R_DIV_ONLY` held↑+1.30 vs SAT +0.33），但 tip 窗仍吃 COMP HARD 拖累。
2. **確認＋退出未優於單純 DIV** — `R_ENTER_EXIT` flips=459 過頻、held 最弱；`R_DIV_CONF_HOLD`／`R_HOT_THEN_DIV` held↑≈+1.0 仍 tipCAGR−；crisis-only 最保守（%SAT 15.9）也 tipCAGR−11.6。
3. **相對純 SAT**：純 SAT tip-clean 但 held MDD 不過；規則書用部分時間 SAT 保住 held MDD／CAGR，卻把 tip 鎖在 COMP 側虧損——與 0k9e–0k9l 同一 tip／held 互斥。
4. **Binding 缺口轉移**：特徵／episode／規則三層 paper 皆 `TIP_MDD_ONLY`。下一輪若再開，應換機制族（非 COMP↔SAT 日切），或接受 tip-clean 需接近純 SAT 並另找 held MDD 修補——**不擴本規則格**。

## Rule books

- `R_DIV_ONLY` · %SAT=24.13 flips=153 · held↑ 1.2962 tipCAGR↑ -8.4925 · tipClean=False econ=True vsSAT=True
- `R_HOT_AND_CONF` · %SAT=22.35 flips=131 · held↑ 0.5427 tipCAGR↑ -12.3694 · tipClean=False econ=True vsSAT=True
- `R_ENTER_EXIT` · %SAT=20.15 flips=459 · held↑ 0.4219 tipCAGR↑ -10.6946 · tipClean=False econ=True vsSAT=True
- `R_DIV_CONF_HOLD` · %SAT=26.84 flips=31 · held↑ 1.0982 tipCAGR↑ -9.671 · tipClean=False econ=True vsSAT=True
- `R_CRISIS_HOLD21` · %SAT=15.9 flips=24 · held↑ 0.4709 tipCAGR↑ -11.6459 · tipClean=False econ=True vsSAT=True
- `R_HOT_THEN_DIV` · %SAT=28.29 flips=37 · held↑ 0.9767 tipCAGR↑ -6.2022 · tipClean=False econ=True vsSAT=True

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. Do not expand feature table or rule grid after peek
4. Rule-layer COMP↔SAT day-switch ladder exhausted for tip-clean · no observe · no live

Label: `FIN_SAT_DIV_RULE_STAGEA_DECISION_PACK_2026-09-28__TIP_MDD_ONLY__NO_LIVE`
