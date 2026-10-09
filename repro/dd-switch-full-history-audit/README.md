# DD_SWITCH 全歷史資料來源稽核（截至 2026/10/08）

**最新結論：資料核對尚未全部通過，backtest_ready=False；先完成核對，再重跑。**
2026/10/09 後續交叉核對新增結果見下節。原先單一来源的「缺列0」只適用於已取得的日期基準，不能代表全歷史完整。
本次查證不是策略調參，也沒有覆寫任何 canonical 市場、股利、runtime 或成交歷史。

## 最新核對批次（2026/10/09）

### 接續 b6271f5：公告欄位與公司行動證據

- 0050 的27次配息已取得54份官方申報公告的欄位證據：時程／預估公告與最終金額公告各27份，發言時間精確到秒；除息日、支付日及最終金額與凍結股利表完全一致。這解除「27次ETF公告完全未取得」的子缺口，但不是全歷史vintage認證。
- 每個欄位各自標示reported_at；预估金額不當作最終金額，下午公告不回填到當日13:30。新增隔離research_snapshot，僅展示當時已申報欄位；沒有接入production特徵或重跑策略。
- 0050的2025/05/09申請公告及2025/06/17最終公告、00631L的2026/02/10申請公告及2026/03/30最終公告，與現有停牌、復牌、4倍／22倍股數契約一致。最終參考價與最後成交價除以倍數之差在0.005元內。
- 全表416個正股利腿中，27腿具有上述一手時點核對，389腿仍缺逐腿官方時點證據；全部修訂全集與首次發布完整性仍未認證。發言時間的現行官方重現頁，不等於原始HTTP歷史快照。
- 另列24筆「股票股利0但有除權日」候選，不推定其皆為現增或無公司行動；認股比率、繳款、權利與股數／資金處理待逐筆證明。
- sources/announcement_facts_*.json只保存抽取後事實。manifest明列normalized_facts_sha256，original_response_sha256為null，不能把抽取檔hash當作原始網頁hash。失败／局部取回與後續補查均保留。
- 最新逐腿缺口清單與結論：announcement_evidence_remaining.csv、announcement_evidence_summary.json；股利表hash不變。backtest_ready=False，沒有新的DD_SWITCH績效。
- 本批14項相關測試通過，302份年度來源SHA256重新逐檔通過，6份canonical市場／股利輸入hash不變。summary.json只補公告證據結論與兩項blocker理由，保留此前行情／NAV／成交統計；沒有宣稱本批重跑整段稽核。乾淨checkout未保存大型parents_with_off.csv／mothers_with_off.csv，中途整段稽核入口因缺該生成輸入停止，未啟動策略重建。既有輸出已恢復；可由七日重建腳本生成所需輸入後再重跑，公告核對不依賴該步。
- 本批公告證據另存announcement_evidence_bundle.zip，內含逐欄事實、欄位核對與缺口表。原sources_evidence.zip／audit_outputs.zip仍是b6271f5批次，不含本次追加內容；解壓原報告後，須再解壓此bundle並執行公告核對。

重現本批：

```bash
PYTHONPATH=scripts python scripts/dd_switch_announcement_evidence.py
PYTHONPATH=scripts python -m unittest discover -s tests -p test_dd_switch_announcement_evidence.py -v
```

下一批優先核對FIN/TEL的原始除權息申報／修訂與上述非股利事件，再完成官方日曆、因果特徵接線與共同資金T+1重建。

- 2010–2026年302個標的年度項目全部取得，32項重試成功，0項未完成；302份來源SHA256逐檔驗證通過。完整來源均為FinMind現行重抓，並非歷史公告當時版本或獨立一手雙重認證。
- 日期衝突20項已有處理依據：17項保留原交易日，2項颱風休市不補假報價，1項2023/05/25確認為原DD面板漏列。完整官方歷史日曆尚未認證。
- 原始FinMind行情及鄰日單位／調整係數核對後，獨立研究副本補34筆：核心10筆、民營金融24筆。原有核心列維持不變；核心36330列、金融32871列，無重複或未解缺列，金融另有1日合法停牌。
- 已取得的個股原價與重建原價一致。TAIEX舊面板是收盤代理，OHLC與volume不能支持盤中成交聲明。Yahoo的63223個欄位差異是來源／單位假設差異，不代表本地錯價。
- 中華電2010/01/21–02/07的13個缺價交易日，找到公司减資停牌公告的轉載依據；歸類合法停牌，不填假價。來源強度見historical_halt_additional_evidence.json。
- 公司與股務代理現行頁面69筆股利比較，金額全部精確相符；有提供支付日期者亦一致。公告版本、當時可得時間仍未認證。
- 年度行情下載已全部完成；尚須核對歷史公司行動、股利公告時點及修訂證據。backtest_ready=False，未重跑策略、未更新canonical／runtime。

本次完整來源與生成報告分別保存在sources_evidence.zip與audit_outputs.zip。解壓到本目錄後，可離線重現已取得來源的核對：

```bash
python -m zipfile -e repro/dd-switch-full-history-audit/sources_evidence.zip repro/dd-switch-full-history-audit
python -m zipfile -e repro/dd-switch-full-history-audit/audit_outputs.zip repro/dd-switch-full-history-audit
PYTHONPATH=scripts python scripts/dd_switch_full_history_audit.py
PYTHONPATH=scripts python scripts/dd_switch_history_reconciliation.py
PYTHONPATH=scripts python scripts/dd_switch_history_gap_verify.py
PYTHONPATH=scripts python scripts/dd_switch_history_candidate_integrity.py
PYTHONPATH=scripts python scripts/dd_switch_dividend_primary_check.py
```

最新狀態以summary.json、reconciliation_summary.json、gap_recovery_summary.json與candidate_integrity.json為準。以下保留首輪查證紀錄，其來源覆蓋數字不是最新批次。

## 範圍與證據強度

- 活躍 DD_SWITCH 建構市場：2011/12/01–2026/10/08；母帳與父帳實際交易自2012/12開始。
- 加查民營金融八檔輸入、2010起電信與0050原始／調整價、00631L上市後原始價、329筆現金／股票股利表。
- 不把庫內所有過時研究檔列為現行 live 輸入；八檔民營金融輸入也包含早期研究銀行，不代表八檔均為現行交易候選。
- 取得2011–2022共12份TAIEX逐年重新下載；另使用已核對的2025、2026官方交易日表。基準共3377日，包含DD市場啟動前的2011日期；DD面板實際可核對2724+428=3152日。
- FinMind重新下載與原資料有共同來源，這是版本一致性證據，**不是獨立供應商雙重認證**。2010、2023及2024缺獨立日期證據；2025以前也尚缺全段官方交易日／交割日認證。
- 官方歷史API三個年代的抽查皆遭HTTP307安全限制；供應商回傳用量上限後停止下載。全部存取／失敗紀錄與未請求清單保留，不以空結果判定「無行情」。

## 行情與日期

|資料|查證結果|處理狀態|
|---|---|---|
|修復後母帳／父帳面板|已取得日期基準內缺列0、重複0、可交易OHLC無非正值或上下界錯誤|研究版已完成；仍非全部年份官方認證|
|原canonical市場|仍保留原7日缺口；58筆缺行情，另5筆0050合法停牌無報價|沒有把研究版自動寫入正式來源|
|民營金融輸入|8代號×2日共16筆缺價：2025/02/06、2026/05/28|待取實際OHLC與當日調整係數，禁止前值補成交价|
|2884另缺2025/11/05|交易所公告證實重大訊息停牌|合法無成交行情，不列為下載漏價|
|2011電信缺列|2412共12交易日、3045共11交易日；公司文件證實現金減資停牌|發生於DD市場起始前，不應硬補成交易行情|
|0050與00631L|已知停牌／拆股分離估值、股數與成交资格|完整企業行動全集仍未認證|

TAIEX **2724筆收盤價全部與重新下載相同**。原面板歷史TAIEX是CLOSE_ONLY_PROXY：open/high/low等於close、volume=0，所以四個其他欄位出現10376個差異。這是欄位用途限制，不是10376個錯誤收盤價；不得使用這些代理欄位證明盤中或開盤訊號。TAIEX不是可交易標的。

原始電信／ETF彙整檔截止2026/09/01，調整價檔與現行市場延伸至10/08；分檔截止不同明列於input_inventory.csv，不將封存檔冒稱全部最新。

## 股利與公開時間

329筆表拆為273筆現金與143筆股票正股利腿，共416腿；除權息日／支付日缺值0，支付早於除權息0、公告晚於除權息0、重複事件0。與可用原始記錄比對的金額不一致0；未有外部比對的欄位不視作已驗證。

重新取得元大官方0050歷史32筆；2010以後27筆均與現有表的金額、除息日及支付日一致。另5筆在本表起始前，不誤報缺資料。然而這27筆缺公告日期／時間，官方API亦無公告時間，不能自行推定。

支付來源分為：27腿元大官方歷史、186腿FinMind有支付日期、29腿Yahoo補入、174腿尚無逐列支付日期primary證明（包括股票股利腿）。有支付日期不代表當時已公開；本次没有把FinMind原始記錄或Yahoo標成一手來源。

2891一筆表定cash_ex=2026/07/10落在官方非交易日。既有effective-ex router會依日期規則處理，但仍需原始公告／延期證據，不能只靠規則證明真實有效日期。

## 現行特徵的公告前綴實驗

直接呼叫現行build_kd_season_tilt_scores與build_pre_exdiv_window_buy_ok，參數由LIVE_KD讀取：K<30、4/15–5/15、除息前15交易日、score=1.5。每次市場都截到相同日期，只移除表內announcement_date晚於截止的股利事件。

2012–2026每年4月底、5/15及7/1，共45個截止／180個金融代號比較，**111個KD分數不同**；這批抽查時點buy mask差異0。另逐事件核對前15日窗口，有**259個名稱日**在表內公告日前就受除息窗口影響。

這證實現有特徵對完整未限制公告表有依賴，不能當作已通過PIT。它不等於111筆成交錯誤、259日NAV損失或111/180的策略偷看比例。表內公告可能不是最早公布除息日期的公告；必須補當時公告版本／available_at，才能判定每一日期實際可知與收益影響。前綴過濾對照是診斷，不是推薦部署的替代策略。

## NAV與成交日期

9條父／母／shadow NAV在可取得基準內均缺列0、重複0、無非正NAV。五個逐筆成交帳無同日／早於訊號成交、無00631L上市前成交、無已知ETF停牌成交、無面板外日期成交。

已取得日期證據的成交中，5564筆晚於第一個T+1合格日；另3932筆處於2023/2024等未取得日期證據區間。延後不自動等於時鐘違規：原引擎會等待資金／處理pending，需逐筆查資金不足、餘量、舊目標與更新替代。完整延後清單另存，尚不能把長期父帳宣稱為所有單都exact-next-open。這不改變前次短視窗production重播或固定核心方案的已核對結果。

DD/TRAIL原shadow與收益拼接、歷史全帳共同資金與競價深度也仍有限制；本次不重新宣稱長期live報酬或最優門檻。

## 阻擋與修復順序

1. 補民營金融16筆真實行情，依當日企業行動恢復調整係數，再核對其實際使用路徑。
2. 先補除息日期公告的available_at／修訂版本；建立因果訊號對照，再重跑同一批固定策略，衡量實際收益依賴。
3. 取得剩餘年份官方交易／交割日及個股全歷史一手行情、企業行動全集。用量恢復後先補2023/2024日期，不付費或使用未授权憑證。
4. 逐筆歸因長期延後成交，再做完整live共同資金歷史認證。九個blockers未解除前publication_allowed=False。

## 可重跑

```bash
python scripts/dd_switch_full_history_sources.py --offline
PYTHONPATH=scripts python scripts/dd_switch_full_history_audit.py
```

只在供應商用量已恢復後使用來源下載入口（遇402/429自動停止後續新請求）：

```bash
python scripts/dd_switch_full_history_sources.py --codes TAIEX --workers 2
```

同一目錄保存summary.json、blockers.json、各輸入SHA256、來源下載JSON與hash、日期／缺價／欄位比較、逐股利事件、公告前綴實驗及成交日期證據。資料表與程式可編譯、重跑完成；這不是全歷史認證PASS。未合併、部署、發布正式runtime或券商交易。
