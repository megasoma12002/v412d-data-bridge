## GitHub 傳輸與重現

GitHub連接器登入有效；本地HTTPS git缺憑證，改由連接器上傳Git物件。23.6MB resumed證據ZIP依原始bytes拆成3段，先執行 `python scripts/dd_switch_restore_resumed_delivery_archive.py` 再解壓；每段及完整ZIP SHA256均核對，原ZIP雜湊534ac270024c5e2662dbcf568bd394b08a3de6985d9284dacf44bca9afeab71f不變。此前「未上傳」記錄是當時狀態，最終同步狀態以PR最新說明為準。

---

## 2026-10-10 接續：股務代理與中信金公開說明書

本輪5份來源完整下載並核對原始／壓縮SHA256；新增解除缺口0。華南永昌官方公司清單確認2880（統編70826764）及公司詳細頁連結，詳細頁僅列114／115年歷史；目前一週記事與公告未提供目標2010–2013年一般交付原文。不推論舊公告從未存在。頁面115/8/28是現金股利日期，不能當股票交付證據。

中信金公開說明書完整9,576,160 bytes、848頁、PDF EOF有效，刊印日102/2/1；PDF第53頁（印刷44頁）資本沿革列101年4月現增7,150,000仟元，已視覺核對，但不是明確一般普通股交付日期。全文抽取檢查的上市日期僅公司原上市日，不能解除2012／2013現增交付缺口；文字檢索也不證明所有舊原文不存在。

重現：先依既有順序恢复快取至resumed_delivery_capture_delta.zip，再解壓followup_delivery_capture_delta.zip，執行 `PYTHONPATH=scripts python scripts/dd_switch_followup_delivery_review.py`。本輪5/5原文hash核對成功；整體3497組來源回應、6組請求及9份canonical輸入hash核對通過；3個抓取佇列均COMPLETE，沒有背景工作。

仍餘股票交付6、現增普通股交付9、股份階段2及全歷史認證阻塞9；類別重疊。`backtest_ready=false`，未執行DD_SWITCH T+1，canonical／forward／runtime未修改。

外傳授權已收到；本地27452c2推送失敗原因為GitHub HTTPS登入憑證缺失，遠端仍5a7fdd2；授權與實際上傳狀態分開記錄。
