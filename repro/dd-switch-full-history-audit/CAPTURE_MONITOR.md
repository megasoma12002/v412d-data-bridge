## 最新續核抓取

issuer_capture_progress.json：COMPLETE，5/5處理，3快取、2新回應保存、0失敗，2026-10-10 01:44:32台灣時間完成。新回應為富邦股東會檔案頁與華南2013公告轉載，僅作線索，沒有升格為原始MOPS版本認證。0050 STOPPED_SOURCE_BLOCK快照保留；無背景工作正在執行。

---

## 最新缺口探測

0050原文探測：STOPPED_SOURCE_BLOCK，1/1已處理，HTTP307安全阻擋，見targeted_capture_progress.json。已停止该来源。

發行人頁面：COMPLETE，3/3保存、0失敗，見issuer_capture_progress.json。RESPONSE_SAVED_NEEDS_VALIDATION僅表示回應保存，不代表歷史日期已補件；本批人工核對沒有解除剩餘缺口。

scripts/dd_switch_targeted_capture.py保留串行、2秒間隔、15秒逾時、阻擋來源停止、連續3失敗停止及逐筆進度。沒有背景抓取正在執行。

---

## 最新續抓結果

本輪僅剩1份候選法定公告，已於2026-10-10 01:15:28台灣時間取得有效全文；COMPLETE 1/1成功，0失敗。前輪100筆監控另存 prior_capture_progress_37962101976.json。候選公告內文沒有剩餘下載，下一批必須先新增具體來源候選；沒有正在背景執行的抓取。證據完整性仍未通過，見最新REVISION_SETTLEMENT_REVIEW.md。

# 公告抓取監控

先從取消後差量包恢復最新證據，只對100份候選缺件發出請求。前5筆作試抓，全部有效才進入後續批次。每批最多10筆，單筆15秒逾時、間隔2秒；遇任何Overrun／安全阻擋立即停止，連續3筆失敗也停止。

`monitored_capture_progress.json` 包含總數、已處理、成功／失敗、最後完成時間、正在請求的公告、最近10筆結果、是否通過試抓及停止原因。每次請求開始／結束均寫入；每批完成或停止後上傳獨立的小型 `capture-monitor-probe`／`capture-monitor-batch-NN` artifact，供連接器直接讀取，不依賴手機App可否展開日誌。後續批次若被阻擋，僅保存相同停止快照，不繼續請求。

小型監控包先於完整證據上傳，因此可以查已完成批次的實際計數。批次內的即時狀態仍以job step狀態為準，不能只看in_progress認定有成功下載；按15秒逾時及連續3失敗限制，故障批次會及早停止。整個工作30分鐘硬上限。抓取成功與資料核對完備分開計數；即使停止，也執行保存資料的離線核對並上傳證據，不改正式資料、不跑策略。
