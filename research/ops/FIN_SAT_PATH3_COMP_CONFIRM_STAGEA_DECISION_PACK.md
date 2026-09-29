# FIN_SAT_PATH3_COMP_CONFIRM_STAGEA_DECISION_PACK

Date: 2026-09-29 · Verdict: **`COMP_CONFIRM_NO_EDGE`**
Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · cutover **BLOCKED** · no live

## Answer

Paper 探 COMP 進場 confirm／SAT 最短停留，**修不了 2022，也沒有優於 raw P3 的 HIT**。

| Book | held↑ | tipY↑ | tipClean | shaped | y2022% | vs BASE |
|---|---:|---:|---|---|---:|---:|
| `P3_T0_STATE` | 3.48 | 2.73 | True | True | 5.75 | **−0.75** |
| `COMP_CONFIRM_D1`（≡P3） | 3.48 | 2.73 | True | True | 5.75 | −0.75 |
| `COMP_CONFIRM_D2+` | ↓ | tip− | False | False | 更差 | ≤−0.93 |
| `SAT_MINSTAY_5` | 3.05 | 0.76 | True | True | 5.73 | −0.77 |
| `SAT_MINSTAY_21`（最佳2022） | 2.60 | −0.46 | False | False | 5.76 | **−0.74** |
| Combos D2/D3×S10/21 | tip− | — | False | False | 更差 | ≤−0.76 |

- Confirm D≥2：傷 tip（YTD 轉負），2022 更差  
- Min-stay：最多把 2022 從 −0.75 修到 **−0.74**（無效），長停留還傷 tip  
- `COMP_CONFIRM_D1` ≡ raw P3（一天 confirm = 原規則）

## Implication

1. **COMP enter confirm / SAT min-stay ladder exhausted** for the 2022 −0.75pp gap.  
2. Path3 observe **KEEP OPEN**（不關）— 全樣本仍 HIT 形狀。  
3. fill/emit flags **KEEP OFF** · Soft-Frozen／Exact T+1／CONF α **KEEP** · cutover **BLOCKED**.  
4. 若再追 2022：不要再加 confirm/minstay 網格；需另類特徵（例如 COMP 進場的外生 confirm），或接受 1/15 年殘差。

Screen: `FIN_SAT_PATH3_COMP_CONFIRM_STAGEA_SCREEN.md` · Charter: `FIN_SAT_PATH3_COMP_CONFIRM_STAGEA_CHARTER.md` · Register **0k9y**

Label: `FIN_SAT_PATH3_COMP_CONFIRM_STAGEA_DECISION_PACK_2026-09-29__COMP_CONFIRM_NO_EDGE__NO_LIVE`
