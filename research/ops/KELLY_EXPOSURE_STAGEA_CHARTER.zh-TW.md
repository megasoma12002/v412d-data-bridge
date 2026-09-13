# Kelly 曝險 Overlay — Stage A 憲章（paper）

日期：2026-09-13  
狀態：**PAPER CHARTER OPEN** · Stage A 螢幕 **尚未開工**  
Soft-Frozen **KEEP** · live **`KD_OPT`／`TEL_EQUAL` KEEP** · E45 stitch **OFF**  
Soft／Sleeve／FUSE／BLEND_025／priv／**DH_dd06** observe **不動**

Ballot：`KELLY_EXPOSURE_STAGEA_CHARTER_2026-09-13__PAPER_OPEN__NO_LIVE`

## 在問什麼

專案從未用過 Kelly Criterion。能否用 **fractional Kelly 的整本書曝險縮放**（不動 clip、不動袖內權重）在 paper 上 tip-clean 勝過或共存於 `LIVE_STACK`？

## 接點（凍結）

| 項目 | 決定 |
|---|---|
| **主致動器** | `kelly_exposure_t ∈ [0.50, 1.00]`，在 Soft-Frozen + KD_OPT + TEL_EQUAL 之後縮放**整本 paper 書**（同 `e45_exposure` 族） |
| **Stage A 不做** | Soft-Frozen clip 翻邊 · 用 Kelly 取代 `TEL_EQUAL`／`KD_OPT` · 乾粉現金袖 · \(f>1\) 槓桿 · 放空 · 與 DH／Soft／Sleeve／FUSE 融合 |

## Edge 怎麼估（凍結）

連續近似：\(f^\*_t = \hat\mu_t / \hat\sigma^2_t\)（因果 rolling；Exact T+1）。

| ID | 來源 |
|---|---|
| `EDGE_LIVE_ROLL` | paper `LIVE_STACK` 日報酬（主） |
| `EDGE_0050_ROLL` | `0050` 日報酬（僅敏感度列） |

Lookback \(W ∈ \{63,126,252\}\)；\(\hat\mu\le 0\) 或變異數無效 → raw \(f^\*=0\)（再經下方 clip）。

## Fraction（凍結）

| 項目 | Stage A |
|---|---|
| \(κ\) | **僅** `{0.25, 0.50}`（¼／½ Kelly；**禁止 full Kelly**） |
| Clip | \(e_t=\mathrm{clip}(κ·f^\*_t,\ 0.50,\ 1.00)\) |
| 施加 | Exact T+1 目標名目 × \(e_t\)；餘額現金 |

## Stage A 網格

主挑戰 ≤ **6**（LIVE edge × 3W × 2κ）+ baseline；0050 敏感度 ≤ 6（不驅動 promote）；總書 ≤ ~13。

| 裁決 | 意義 |
|---|---|
| `KELLY_PROMOTE_SHAPED` | tip-clean 且 held-out score>0 且 tip MDD 不劣於 base |
| `COEXIST_NO_LIFT` / `NO_LIFT` / `ESTIMATE_UNSTABLE` | 見英文憲章 |

即使 `KELLY_PROMOTE_SHAPED` → **僅可開 paper observe ballot**；**不可** live。

## 硬鎖

1. 不翻 Soft-Frozen clip  
2. 不上 live（KD／TEL／Soft／Sleeve／FUSE／BLEND／priv／E45／DH）  
3. 不 ops Soft∥Sleeve auto-fuse  
4. 不重開 E45 stitch／不撤銷 `DROP_E45_A05`  
5. Stage A 不與 DH／Soft／Sleeve／FUSE 融合  
6. 禁止 full Kelly、\(f_{hi}>1\)、放空  
7. 禁止開放搜尋；改 \(W\)／κ／`f_lo` 需修憲  
8. Exact T+1／因果 only

## 下一步

實作並跑 **Stage A paper screen**（`scripts/e16_kelly_exposure_stagea_screen.py`）。  
未出裁決 + 專用人類 ballot 前，不開 observe／cutover／live。

英文全文：`KELLY_EXPOSURE_STAGEA_CHARTER.md`
