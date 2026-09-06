# E45 Sleeve-Local Observe — OPEN 表決草案（繁中）

日期：2026-09-06  
狀態：**草案 DRAFT — 等待人工 ACCEPT**  
提議表決名：`E45 OPEN sleeve-local observe`  
英文正本（治理以英文為準）：`research/ops/E45_SLEEVE_LOCAL_OBSERVE_OPEN_BALLOT_DRAFT.md`

> **未授權。** 本檔只是**表決草案**。  
> **不會** OPEN observe sleeve、**不會**接入 month-end、**不會**翻轉 Soft-Frozen / DEFAULT、**不會**授權 stitch。  
> 在人工另行標記 **ACCEPT** 之前，sleeve-local 仍為 **僅紙上（PAPER ONLY）**。

Soft-Frozen：**[0.50, 0.95] KEEP**  
Live DEFAULT 書本：`E22_v2s_tw` **KEEP**  
Live stitch：**仍禁止 FORBIDDEN**  
−13.16% 主張：`RETIRED_HISTORICAL_NARRATIVE`  
父級 observe（本草案不改動，仍在跑）：FULL E45 + blend-α=0.25 + blend-α=0.05

---

## 擬議表決（ACCEPT 前不生效）

| 欄位 | 擬議值 |
|---|---|
| 選擇 | **OPEN sleeve-local observe**（僅紙上並行） |
| 主挑戰書（深挖首選） | **`SLEEVE_FIN_ONLY_A10`** — 僅對 **金融 Financial** sleeve 套用 E45 `E3_VOLTARGET_WINNER`，強度 **α=0.10** |
| 基準書 | `BASE_E16_E18_E22_v2s` |
| Overlay | 全書 exposure=1；僅金融 sleeve 按 `exposure = 0.90·1 + 0.10·E3_VOLTARGET_WINNER` |
| 節奏（若 ACCEPT） | 月末並行紙上 ledger + monitor |
| 接 live？ | **否** |
| 翻轉 Soft-Frozen？ | **否** |
| 授權 stitch？ | **否** |
| 退役 FULL / A25 / A05？ | **否** — 全部繼續 OPERATING |

### 備選（非預設）

若 ACCEPT 更想用較溫和的 P6 結構，而非深挖首選：

| 備選 | 規格 |
|---|---|
| `SLEEVE_FIN_0050_A05` | 金融 + 0050 @ α=0.05（電信不動） |

除非 ACCEPT 備註明確點名備選，否則預設仍為 **FIN_ONLY @ α=0.10**。

---

## 為何提議這條 sleeve（紙上證據）

依據 `E45_SLEEVE_LOCAL_DEEP_DIVE.md`（P1–P7 之後）：

1. Held-out @1× 首選：`FIN_ONLY_A10`（score **~0.285**）優於全書 `ALL_A05`（~0.222）。  
2. 成本 2× 雙胞胎仍為正（score **~0.319**）— 此強度下不是換手炸彈。  
3. 危機年 MDD 幫助仍約 **84% 集中在 2020** — 與全書 A05 同樣的誠實約束。  
4. 結構優勢在於「α 套用在哪裡」；應與全書 A05 **分開觀察**，不要混成一條 sleeve。

僅在 ACCEPT 之後才會 OPEN，且僅為 **observe**。以當前 tip 預期 YTD/1y 仍為 **PAUSE_REVIEW**（與 A05/A25 相同）。Observe ≠ stitch。

---

## 開張前檢查表（ACCEPT 時需再確認）

| # | 項目 | 草案狀態 |
|---|---|---|
| 1 | Soft-Frozen live clip 仍為 [0.50, 0.95] | **YES**（當前） |
| 2 | Live DEFAULT 仍為 `E22_v2s_tw` | **YES**（當前） |
| 3 | 父級 sleeve-local 紙上 + 深挖檔已存在 | **YES** |
| 4 | −13.16% 仍為 RETIRED | **YES** |
| 5 | 未捆綁 stitch / live-wire PR | **ACCEPT 時必填** |
| 6 | 月末負責 = `ops_month_end_paper_pack.py` / research/ops | **ACCEPT 時必填**（腳本要 ACCEPT 後才建） |
| 7 | 理解 PAUSE_REVIEW（observe ≠ stitch） | **必填** |
| 8 | FULL + A25 + A05 繼續並行 OPERATING | **YES**（必須保留） |
| 9 | 已記錄明確的人工 ACCEPT 字串 | **缺失 — 阻斷 OPEN** |

---

## 若 ACCEPT 才建立的產物（本草案不建立）

| 產物 | 計畫路徑（僅 ACCEPT 後） |
|---|---|
| OPEN 表決（轉正） | `research/ops/E45_SLEEVE_LOCAL_OBSERVE_OPEN.md` |
| Ledgers | `scripts/e45_sleeve_local_dual_paper_ledgers.py` |
| 月末 monitor | `scripts/e45_sleeve_local_month_end_monitor.py` |
| Repro | `repro/e45-sleeve-local-dual-paper-observe/` |
| Monitor JSON | `research/gaps/E45_SLEEVE_LOCAL_MONTH_END_MONITOR.json` |
| Pack 接入 | 寫入 `ops_month_end_paper_pack.py` |

**本草案不建立、不接入以上任何項。**

---

## 明確不做（草案期間有約束力）

1. **不要**把本檔當成 OPEN 授權。  
2. **不要** live-stitch E45 / 改寫 `forward/e21` 歷史。  
3. **不要**翻轉 Soft-Frozen 或 DEFAULT。  
4. **不要**僅憑本草案自動建 ledger / month-end / pack。  
5. **不要**退役 FULL / A25 / A05 observe。  
6. **不要**編造 −13.16% 替代數字。  
7. **不要**用本表決去開 crisis-gate 或溫和 `max_cut` observe。

---

## ACCEPT / REJECT 寫法（人工）

**ACCEPT** 需明確備註，例如：

> `E45 ACCEPT OPEN sleeve-local observe` — primary `SLEEVE_FIN_ONLY_A10`（或備選 `SLEEVE_FIN_0050_A05`）— Soft-Frozen KEEP — stitch FORBIDDEN

**REJECT / DEFER** 示例：

> `E45 REJECT sleeve-local observe` — 維持僅紙上  
> `E45 DEFER sleeve-local observe` — 只繼續 FULL+A25+A05 節奏

在記錄上述之一前，狀態維持 **DRAFT / NOT OPEN**。

---

## 父級證據

- `research/e45/E45_SLEEVE_LOCAL.md`（P6）  
- `research/e45/E45_SLEEVE_LOCAL_DEEP_DIVE.md`（P7 後加密網格）  
- `research/ops/E45_PAPER_P1_P7_INTEGRATED_ANALYSIS.md`  
- `research/ops/E45_OBSERVE_SLEEVES_STATUS.md`（sleeve-local 列：NOT OPEN）

---

## 標籤

`E45_SLEEVE_LOCAL_OBSERVE_OPEN_BALLOT_DRAFT_ZH_2026-09-06__AWAITING_HUMAN_ACCEPT__NOT_OPEN__STITCH_FORBIDDEN`
