# 最近 PR 審閱與後續研究：因果不變性稽核

審閱時間：2026-10-09（台灣時間）。來源為 megasoma12002/v412d-data-bridge 最近更新的 30 個 PR（#405～#434，部分編號順序因 updated 排序不同）。主線仍是 DD_SWITCH；#434 尚為草稿，原 main 未部署該修復。

## PR 脈絡與結論

| PR | 狀態／作用 | 後續研究處置 |
|---|---|---|
| #409～#412 | 已合併；指出 Soft FIN/TEL OFF 造成 OFF 日 ownership／refill 缺口，研究高 ON 比例搭配 cash | 這是 #434 清空後無法回補問題的前史；需要明示資本預算與重進場規則，不能用 return-blend 假裝帳戶自行回補 |
| #413～#420 | 已合併；cash twin、TRAIL42／L4 DD_SWITCH、OPEN 與 ACCEPT tip apply | 研究收益數字不等於逐筆成交收益；先固定同一成交時鐘及控制來源 |
| #421 | 已合併；關閉舊 COMPOSITE／SAT／P3 observe 的 month-end／alert 更新 | 關閉研究 observe 不等於可以停止 LIVE 依賴資料更新；需把控制輸入當正式每日依賴 |
| #422～#425 | 已合併；穩定主線與 SOAK_OPEN | 工程穩定／QC 狀態不代表策略驗證通過；60 overlap、20 tip days、28 calendar days等 soak 門檻應建立在實際完整、同日期資料上 |
| #426～#428 | 未合併；2020 overlay 只有 MDD、偵測單訊號弱、200 組中 12 組 REFINE_HIT | 可保留為探索，不能把多臂挑出的 2020 HIT 視為獨立 OOS |
| #429 | 未合併；2015 無 OOS_HIT、2018 弱、2008／2011 無資料 | 保留 OVERFIT_2020 結論；NO_DATA 不能當 PASS |
| #430～#431 | 未合併；CLIFF／GRIND 分裂、跨年代 DD atlas 部分有效 | 急殺和長跌應分開觀察；事件形狀是事後診斷标签，不能直接當事前路由器 |
| #432 | 未合併；router 7 根 bar 全在 2020，其他年代沒有改善 | 不應升為 LIVE；需 train-only 配置與跨年代重測 |
| #433 | 未合併；229 組 HIT 0、PARTIAL 6，champ k2::pct252::cool_defend_l1 只在 2022 ERA_HIT | 先修驗證流程；本次追加資料實驗證實它會重寫歷史特徵 |
| #434 | 草稿；資料與成交重建修復候選 | 維持獨立，不把部分公股核心 R1 控制模型宣稱為完整現行策略長期績效 |

以上狀態以本次 GitHub 查詢為準；讀了 PR 描述、changed files、相關研究程式及決策報告。不是僅按標題排序，也沒有合併任何 PR。

## 已完成的後續實驗

來源 #433 head：94de1e9c（完整 head 以 GitHub PR branch 為準）。原 build_panel 範圍為 2012-12-04～2026-09-29。

步驟：
1. 用截至 2018-12-31 的 panel 建立特徵。
2. 用完整截至 2026-09-29 的 panel 再建立特徵。
3. 比較兩次 2018-12-31 以前的相同日期、相同候選特徵。

若模型是純粹依過去資料計算，加入未來資料不應重寫已生成的歷史特徵。

| 模式 | 比較候選數（AND grid 前） | 過去值改變的候選數 | 改變的歷史值數 |
|---|---:|---:|---:|
| #433 原始建構 | 201 | 86 | 38,765 |
| 研究示範：訓練段固定方向＋只用过去分布 | 201 | 0 | 0 |

原始程式既有 5 項單元測試通過，仍未覆蓋這種未來追加不變性問題。

## 具體原因

- scripts/tipsoft_ip3_crisis_feat_despec_stagea.py::_orient_stress：用全期間 fwd_mdd_10 的相關性決定特徵方向；測試期間的未來回撤參與了特徵定義。
- _rank_pct：用 Series.rank 對全期間排名；新資料會改變舊樣本的 percentile，AND 與後續警報會受影響。
- k-confirm 透過 helper::_alert_mask 取得全期間分位數門檻，並非當時已知的門檻。
- score_arm_on_era 在每個 eval 視窗自身 fit 分位數，ERA_HIT 的 precision／recall 是視窗分布內診斷，不能當固定門檻的真正時間外推。
- run 先用所有 eras 排名，挑前 40／60 組候選並建立 AND 組合，再做 leave-one-era-out；held era 已參與候選池生成。除去 held era 的最後排名不足以排除這層選模洩漏。
- PARTIAL champ 全期間 IC 0.0034、ex-2020 IC 0.0021，弱於其單一 2022 ERA_HIT 的敘事；沒有統計或交易證據支持升版。

上述不表示 #433 的所有描述性統計都無效。它仍可說明「哪些舊特徵在什麼歷史片段有關聯」，但不能據此宣稱可成交、真正未知樣本、或因果 LIVE 優勢。

## 示範修正與限制

本次示範僅在獨立稽核程式裡替換三個函式：方向只用 2014-11-30 以前資料估計（對 2015 前訓練截止留一個月 purge），percentile 用截至前一天的 252 日分布，警報門檻用截至前一天的 252 日分位數（最少 50 筆）。沒有修改 #433 原始分支或 LIVE。示範通过 append-future 不變性，但未修正全樣本候選筛选，未宣稱績效改善。

## 接續研究順序（固定，不再次大規模掃參）

1. 先把 #434 分離成純資料修復、原控制方法延伸、R1 控制方法變更三個比較，避免來源變更被誤稱資料修復收益。
2. 定義 Path3 現金回補資本预算與 pending order 取消／更新規則。保留舊規則作基線；候選版只在 sandbox，不重新開啟普通 Soft FIN/TEL LIVE 訂單。
3. 危機訊號使用按時間走的 outer split；每次的方向、標準化、警報門檻、候選池、AND 組合都只從訓練段生成；forward label 至少 purge 10 個交易日。
4. 固定小候選集，分别報 CLIFF／GRIND；按全期間、年代、事件、false alarm 與重新進場代價核對。不用事後事件形狀驅動 LIVE 路由。
5. 最後才在包含 FinPriv／TEL_T3 的正式 T+1 逐筆帳戶上測訊號，列入佣金、稅、滑價、停牌、分割、股利、現金不足、掛單與容量限制。

結論：目前應 RETAIN_BASELINE／NO_LIVE_PROMOTION。優先解決驗證因果性與回補缺口，比再挑一組 2020 更漂亮的特徵重要。

## 重現

```bash
git fetch origin refs/pull/433/head:refs/remotes/origin/pr-433
git worktree add --detach ../pr-research origin/pr-433
python scripts/recent_pr_causality_review.py ../pr-research
```

產物：prefix_invariance.csv、summary.json。這是結構稽核，不是新策略績效回測。

PR 連結：
https://github.com/megasoma12002/v412d-data-bridge/pull/433
https://github.com/megasoma12002/v412d-data-bridge/pull/432
https://github.com/megasoma12002/v412d-data-bridge/pull/429
https://github.com/megasoma12002/v412d-data-bridge/pull/420
https://github.com/megasoma12002/v412d-data-bridge/pull/434
