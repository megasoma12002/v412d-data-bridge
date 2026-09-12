# 外部借鑑筆記 — Soft-assist ∥ Sleeve-tilt ∥ 月結 promote

日期：2026-09-11  
狀態：**僅參考 · 不上 live · 不自動 combo**  
對照：`SOFT_ASSIST_OBSERVE_POSTURE.md` · `SLEEVE_LAYER_TILT_OBSERVE_POSTURE.md` · `MONTH_END_PROMOTE_GATE_CHECKLIST.md` · `SOFT_SLEEVE_OBSERVE_OVERLAP.md`

## 五條

1. **Paper→下一階段是 ops**（NexusFi / Quant Memo / qlrk / Oyamori）  
   → 對齊閘門 A–I（凍結 ID、tip 乾淨、heldout>0、alerts、cutover 仍 BLOCKED）。單月綠燈 ≠ promote；paper 數字 ≠ live claim。

2. **Soft 訊號：告知交易，不單獨開第二本 live 帳**（AQR *To Trade or Not to Trade*）  
   → Soft-assist = 在 `KD_OPT` 上改 **within-FIN name soft**；live KD HOLD；軟加分／OR，不重開硬 AND。

3. **戰術 tilt 要過分散門檻**（AQR *Tactical Tilts* / *Tactical Views*）  
   → Sleeve-tilt 只動 router 袖套權重；低相關時「拼在一起」代價更大。Gate **H** 禁止月結提 Soft×Sleeve combo。

4. **「合得來」≠ 自動合成一本書**（Allocate Smartly）  
   → Overlap 欄（corr／same-sign／both−／joint DD）只進月結 log。Seed heldout corr≈−0.025 → 繼續 **獨立 observe**；高／低 overlap 都不開 combo。

5. **先戴 Architect 帽再談 fuse**（Robot Wealth *Edge Alchemy*）  
   → 雙軌 OPERATING 是刻意分開致動器。路徑：月結 A–I → `READY_FOR_DEDICATED_ACCEPT_BALLOT` → 人類 ACCEPT → cutover PR。Combo 要新 charter。

## 不做

PTT 存股文當治理依據；corr>0.7 自動砍軌；從本頁上 live／joint ACCEPT；重開已 STOP 的 Stage A。

## 操作

`python3 scripts/ops_month_end_paper_pack.py` → 填月結 checklist → 看 overlap → 預設 `KEEP_OBSERVE`。

英文全文：`EXTERNAL_BORROW_NOTES.md`
