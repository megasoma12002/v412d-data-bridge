# 原 DD_SWITCH：歷史重現與接續開關驗證

**結論：忠實接續原研究來源鏈，2026-09-30 至 10-08 的七個交易日均保持 Path3 active，沒有觸發 FIN／TEL 全部轉現金。** 日常 WITHIN_SLEEVE 再配置仍會改變持股；active 不等於每一檔股數不變。

## 截至 9/29 的重現

從真正的上游建構器重跑 COMP／SAT 持股帳、BASE、Path3，再依原算法重建 Soft-core ALWAYS_WITHIN、TRAIL42 CASH、TRAIL 及 DD_SWITCH。沒有只重跑複製封存 NAV 的 monitor。

|核對項|結果|
|---|---|
|COMP／SAT 兩個底層持股帳|各 3,365 個持倉日逐日逐標的股數差異均為 0|
|BASE／Path3|各 3,366 個 NAV 日相對誤差最大 2.23e-16|
|兩個 Soft-core、TRAIL／DD_SWITCH|各 3,360 個 NAV 日；最大相對誤差 6.67e-15|
|原 production CSV 開關 want_trail／trail_on／active|共同歷史判斷差異各 0 次|

Git 建構來源：live-stack `5449f76b3a3feba434f40e0c5e10483e32c00b44`；upper-layer `97933be85192e8d0ef89695be0c292342bba694d`；COMP／SAT ledgers `f73c1ba1f48d77b4728ce510da97ae8a0885038e`。

不同研究層的輸入不是同一版本：live-stack 建構分支上的 COMP／SAT 與 observe signal 原本只到 9/24，upper-layer 則使用更新到 9/29 的輸入；母 NAV 本身到 9/29。核對時依各層真正的建構版本恢復，不能把不同層的輸入版本混成一份。observe signal CSV 沒有 book 欄位，必須依原 loader 從 sat_lead 補出 COMP／SAT；直接缺省成 COMP 會重建錯誤。已加回歸測試。

## 忠實接續到 10/8

原始輸入歷史保持原樣，只附加 9/29 以後現有 live_market 與已保存的官方 00631L 新日線。先接續 COMP／SAT 母帳，再生成新日期的選擇訊號與持股配置；BASE、Path3、Soft-core、TRAIL、DD_SWITCH 隨同接續。六條 NAV 與底層兩個持股帳的 9/29 以前前綴再次通過核對，沒有回填母 NAV 或強制保持 active。

|日期|premium42|門檻|選擇|Path3|
|---|---:|---:|---|---|
|09-29|+0.2546%|-1.0000%|TRAIL|ON|
|09-30|+0.1412%|-1.0000%|TRAIL|ON|
|10-01|+0.2448%|-1.0000%|TRAIL|ON|
|10-02|+0.2446%|-1.0000%|TRAIL|ON|
|10-05|+0.1631%|-1.0000%|TRAIL|ON|
|10-06|+0.1063%|-1.0000%|TRAIL|ON|
|10-07|+0.1680%|-1.0000%|TRAIL|ON|
|10-08|+0.1598%|-1.0000%|TRAIL|ON|

這些開關由重建後的 CSV 輸入交給 production 的 `want_trail_series`、`trail42_on_series`、`path3_active_series` 獨立核對。極小浮點差可能影響 DD 完全相等時的分支，因此核對以實際 CSV 消費方式為準；歷史開關與原封存資料完全一致。

這比先前「強制 Path3 active」消融多一層證據：忠實更新的原模型本身就在此視窗維持 ON。R1 在 10/1 退場不能作為原 DD_SWITCH 更新後的行為。這不代表約 925 萬元差距已全數恢復到可成交帳本。

## 已驗證與尚未驗證

已驗證的是原研究來源鏈、歷史數值與接續後的控制行為。BASE／P3、COMP／SAT 有獨立模擬的持股與現金帳；TRAIL／DD 仍保留原報酬拼接與同日 DD 選擇，並非一個共同出資的完整成交帳。為了忠實重現，原日曆缺日、企業行動及其他舊假設沒有在這次偷偷改掉。

下一步應以這套來源鏈產生完整 T+1 forward 重播，核對退場後資金預算與再進場規則，另列日期／拆股／股利修正版本的收益損失，最後才驗證真實 T+0。此結果不證明原長期研究收益可實盤取得，也不構成部署資格。沒有正式 runtime 發布、live 歷史覆寫、部署或券商操作。

## 檔案與重跑

`summary.json`：核心結論與程式 hash；`prefix_parity.json`／`extension_parity.json`／`parent_parity.json`：輸入 SHA256、建構版本與核對；`gate_decisions_0929_1008.csv`：門檻日期明細；`controls_all_dates.csv`：全歷史控制；`all_mother_navs.csv`：七條母 NAV；`book_BASE.csv`／`book_P3.csv`：完整現金、應收股利及股權估值。近期兩個模擬母帳的逐筆成交／持股另附，不是原 forward 成交紀錄。

```bash
# 如 clone 是 shallow，先取得必要建構 commit
# 隔離輸出目錄必須不存在；下列 suffix 可自行更名。
python scripts/dd_switch_original_parents.py --out repro/original-parents-new --asof 2026-10-08 --append-tip
python scripts/dd_switch_original_reproduction.py --out repro/original-prefix-new --input-ref 5449f76b3a3feba434f40e0c5e10483e32c00b44
python scripts/dd_switch_original_reproduction.py --out repro/original-extension-new --input-ref 5449f76b3a3feba434f40e0c5e10483e32c00b44 --asof 2026-10-08 --extended-parents repro/original-parents-new
python scripts/dd_switch_original_audit.py --source repro/original-extension-new --prefix repro/original-prefix-new --parents repro/original-parents-new --out repro/original-audit-new
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_dd_switch_*.py'
```

41 個相關 unittest 通過；父持股帳、六条研究 NAV、production 開關與新日期前綴核對均通過。封存輸入可由上列 Git commit 還原；新日期輸入與官方價格檔的 hash 記於來源核對 JSON，重跑應使用相同輸入。
