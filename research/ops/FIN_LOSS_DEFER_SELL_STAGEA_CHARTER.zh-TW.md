# FIN 浮虧延後賣 Stage A — 紙上章程

日期：2026-09-28  
狀態：**Stage A DONE — `COOL_GATE_REQUIRED`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · 不下 live  
父層 live：Soft-Frozen F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] + FUSE + `SELL_a75` + `COOL_c8_f50_d21` + L1=0.05  
人話（正規化）：

```
OPEN Stage A charter: FIN 浮虧延後賣（等回本）· COOL 強制減碼仍優先 · paper only
```

動機：tip 成交顯示 **11/24** 筆賣出以 FIFO all-in 成本計為虧，另有 **12** 筆未平倉買進相對 tip 浮虧；假設**穩健金融股**可在再平衡賣出前等待回本。  
**重點：這不是改 FIFO 記帳，而是再平衡「可不可以賣／先賣誰」的 overlay。**

**Screen（2026-09-28）：** 有 COOL 閘的延後賣 **無 CAGR 提升**且 tip MDD 變差；只有關掉 COOL 閘才有 CAGR↑（約 +1.2pp）但 held MDD 變差並出現 cool-gate violations → 裁決 **`COOL_GATE_REQUIRED`**。不下 live。

Label: `FIN_LOSS_DEFER_SELL_STAGEA_CHARTER_2026-09-28__COOL_GATE_REQUIRED__NO_LIVE_WIRE`

## 哲學

| 情境 | 工作 |
|---|---|
| **平常再平衡**（COOL exposure = 1） | FIN（可選 TEL）若相對 FIFO all-in 仍虧，可**有限期**延後賣 |
| **COOL 防守**（exposure &lt; 1） | **禁止**延後 — 強制減碼／抬現金永遠優先 |
| **記帳** | FIFO／稅務 lot 仍只做研究報告；不改 tip 帳 |

要驗證的信念（可能為假）：「等一陣子一定會回本」能抬 CAGR 且不傷 held MDD。  
要拒絕的風險：延後虧損單 **放大 MDD**，跟 `COOL_c8` 對打。

## 問題

在 `BASE_LIVE_FUSE_COOL`（Exact T+1 · Soft-Frozen KEEP）上，有限的浮虧延後賣挑戰者能否同時：

1. held CAGR↑ **≥ +0.15 pp**  
2. held MDD↑ **≥ −0.25 pp**（近持平；偏好 ≥ 0）  
3. held \|MDD\| **≤ 15%**  
4. tip YTD + 1y MDD↑ **≥ 0**  
5. **COOL&lt;1 時從不壓制賣出**？

## 不做

- Soft-Frozen live clip／L1／Exact T+1／改寫 tip  
- Live wire／券商下單  
- 重開 DH／放寬 COOL  
- 改 FIFO **記帳** SSOT  
- Stage A v1 先不動 `0050`／`00631L`／FinPriv（先公股 FIN；TEL 另軌）  
- 「等到變綠才賣」無上限 — 必有 max wait，且 COOL 可覆蓋

## Base／格點／門檻

見英文 SSOT：`FIN_LOSS_DEFER_SELL_STAGEA_CHARTER.md`（grid · gates · verdicts 以英文為準）。

腳本（待 screen 落地）：`scripts/fin_loss_defer_sell_stagea.py`  
產物：`repro/fin-loss-defer-sell-stagea/`

## 裁決表（摘要）

| Verdict | 意思 |
|---|---|
| `LOSS_DEFER_HIT` | 合法書通過 CAGR＋MDD＋tip＋COOL 完整性 |
| `CAGR_SOFT` | MDD/tip OK；CAGR 未達 +0.15 |
| `MDD_BLOCK` | MDD 變差（含 NOCOOLGATE 預期失敗） |
| `NO_LIFT` | 無 CAGR 故事 |
| `COOL_GATE_REQUIRED` | 只有關掉 COOL 閘才「有效」→ 禁止無閘延後 |

即使 HIT → **只開 paper observe ballot**；live 賣出 overlay 另 ACCEPT。

## Label

`FIN_LOSS_DEFER_SELL_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`
