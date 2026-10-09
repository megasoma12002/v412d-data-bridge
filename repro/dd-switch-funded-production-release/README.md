# DD_SWITCH 實際退場資金／T+1 回補實作

此變更僅在 draft PR，尚未合併、部署或送出券商委託。原 DD 門檻與母帳不變。

`live_dd_funding.py` 把實際 FIN/TEL DD 賣出淨款記為帳戶現金內的專屬保留額。不是額外 NAV，也不以原母帳 NAV 或訊號日持股市值創造現金。FIN/TEL 各自保留資金，其他 0050／私銀路徑只能使用未被保留的現金。回補預算為實際股票市值＋本 sleeve 保留現金；僅對新投入現金估算買進費用與滑價。真實開盤價格仍逐筆檢查整張、手續費與資金，買單不足維持原本整單不成交規則。

保留額在 ON 後持續追蹤，剩餘整張尾款不自動轉给其他策略。實際支付股利、畸零股現金才計入；應收款不列可買進現金。股票股利的零股保留。舊 OFF 帳本無現金來源時明確阻擋，需要由實際成交重建，不能用全帳戶現金猜配額。DD 有資金所有權時關閉 DD 或換到非 paper port 會阻擋，避免丟失保留額。

funding events 與其他日帳共同延後寫入，portfolio_state 最後原子提交，audit chain 包含 funding events。重複事件、超支、超出全帳戶現金、孤兒日帳均阻擋；同日重跑不改既有帳本。

## 驗證

- 82 個既有 DD 測試＋10 個新資金測試＋3 個 overlay 測試＋13 個 DD gate 測試通過，共108。
- 一般重播135筆成交與先前核對版本逐欄一致。完整32交易日 NAV 542,920,983.15 元，報酬8.5842%，MDD -5.1556%；此次功能修復没有增加這個一般 ON 視窗的績效。
- 人工 OFF 9/30、10/1，再於10/2 ON：10/1七檔核心SELL成交；10/2七檔回補單產生；10/5五檔BUY成交，10/6另外兩檔經重新規劃成交。10/3、10/4為週末，沒有同日成交。
- 此人工情境只驗證資金與成交流程，其報酬不可當作DD策略績效。完整帳務最大 NAV 誤差1.79e-7元，資金事件累計對狀態誤差5.97e-8元。
- `idempotency.json`：10/8重跑回傳 ALREADY_COMMITTED，所有日帳、現金狀態與audit chain hash不變。

## 重現

```bash
python scripts/dd_switch_live_replay.py --inputs-dir repro/dd-switch-live-repair-runtime-certified --out repro/my-funding-baseline
python scripts/dd_switch_live_replay.py --inputs-dir repro/dd-switch-live-repair-runtime-certified --out repro/my-funding-probe --crisis-lifecycle-probe
python scripts/dd_switch_funding_validation.py --baseline repro/my-funding-baseline --probe repro/my-funding-probe --out repro/my-funding-validation
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_live_dd_funding.py'
```

Paper 成交規則已驗證；本變更沒有券商真實成交與流動性證明。歷史價格／控制缺列修復見 `repro/dd-switch-history-gap-recovery/README.md`，固定危機方案重跑見 `repro/dd-switch-crisis-profit-recovered-release/README.md`。
