# ETF 0050 買賣品質 Stage A — 紙上章程

日期：2026-09-28  
狀態：**Stage A DONE — `TIP_BLOCK`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · β densify clip **KEEP** · 不下 live  
父層 live：Soft-Frozen F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] + FUSE + `SELL_a75` + `COOL_c8_f50_d21` + L1=0.05  

先前 0050 軌（**勿重開同旋鈕**）：
- β densify → **HIT → LIVE clip**
- 非對稱 Bull 加碼 → **`CAGR_SOFT`**
- BUY fill / slew → **`METRIC_ARTIFACT_ONLY`**
- 除息行事曆 → **`NEAR_NO_BEAT` / STOP**

人話（正規化）：

```
OPEN Stage A charter: 0050 買賣品質過濾 · 加減碼時機 · MDD持平/改善 + CAGR↑ · 勝率診斷 · KEEP clip/SELL_a75 · paper only
```

Label: `ETF0050_BOTH_QUALITY_STAGEA_CHARTER_2026-09-28__DONE_TIP_BLOCK__NO_LIVE_WIRE`

## 為何開這軌

0050 是**單檔袖**（沒有 FIN 那種 within-sleeve `buy_ok`）。Clip densify 與 BUY slew 已耗盡。剩餘槓桿是：**何時**允許 Soft-Frozen+FUSE+COOL **加／減** 0050 目標權重——品質閘 Δw，不改 clip 上下限。

## 問題

在 live twin 上，有限的 buy×sell 品質網格能否同時：

1. held CAGR↑ ≥ **+0.15pp**（**chal − base**）  
2. held MDD 近持平且 tip MDD 不惡化  
3. 0050 BUY 或 SELL 前瞻勝率（H=21）診斷↑ ≥ +0.5pp（HIT 門；不足則 `WIN_SOFT`）

## 非目標

- 不改 Soft-Frozen clip／Exact T+1／tip  
- 不重開 densify／slew／除息曆  
- 不降 `SELL_a75`；不下 live（HIT 最多紙上 observe ballot）

## 重現

```bash
PYTHONPATH=scripts python3 scripts/etf0050_both_quality_stagea.py
```

詳見英文章程 `ETF0050_BOTH_QUALITY_STAGEA_CHARTER.md`。
