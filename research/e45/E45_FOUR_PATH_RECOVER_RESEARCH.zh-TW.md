# E45 四條路回收長期分數 — 研究摘要（中文）

日期：2026-09-08  
狀態：**研究完成 — 未改 observe lock**  
全文：`research/ops/E45_FOUR_PATH_RECOVER_RESEARCH.md`  
決策包：`E45_FOUR_PATH_RECOVER_DECISION_PACK.md`

Soft-Frozen **KEEP** · stitch **FORBIDDEN** · 無 live wire

## 數字錨點

| 書 | tip | held-out |
|---|---|---:|
| 無閘門 C35（現行 lock） | PAUSE / ALERT | **+1.81** |
| Soft_A | **PASS / PASS** | **+0.83** |
| Hard Bear+Crisis | **PASS / PASS** | +0.72 |

## 四條路結果

| 路 | 結論 |
|---|---|
| **1 Soft_A retarget** | tip 乾淨下最佳；草稿 ballot 已備，需人類 ACCEPT 才換 lock |
| **2 雙軌監控** | 無閘門看長期分數 + Soft_A 看 tip；設計草稿，未 OPEN |
| **3 新機制** | 強度分位 / cheap-protect / M3：**沒有** tip 乾淨且勝過 Soft_A 的書 |
| **4 接受取捨** | tip 綁定時，接受 held-out ~0.8 是合理預設 |

## 建議疊加（非擇一）

1. tip 衛生用 Soft_A（或 HARD）  
2. 長期分數誠實度用無閘門雙軌  
3. 研究前進繼續 M1–M3（離開 C35×regime soft-mult）  
4. tip 綁定則正式接受 Path4 取捨  

INTEN_Q80 held-out +0.89 略高於 Soft_A，但 tip 仍髒 — tip 綁定時不合格。
