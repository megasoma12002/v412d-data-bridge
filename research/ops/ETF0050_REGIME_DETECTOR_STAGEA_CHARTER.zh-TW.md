# ETF 0050 regime × 多空偵測器 Stage A — 紙上章程

日期：2026-09-28  
狀態：**Stage A OPEN** · Soft-Frozen **KEEP** · β clip **KEEP** · 不下 live  
父層：`1d`/`1e` **`TIP_BLOCK`** · `1c` densify **`CAGR_SOFT`**（不重開 clip densify）

人話：

```
OPEN Stage A: 0050 多空都做 · (A) live regime 閘 Δw · (B) 新 0050 多空偵測器閘 Δw · tip-safe + CAGR↑ · KEEP clip · paper only
```

Label: `ETF0050_REGIME_DETECTOR_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## 雙軌

1. **REG** — 用 live `Bull/Bear/Crisis/Sideways` 決定何時可加／減 0050  
2. **DET** — 新 0050 自身 MA60／MACD 多空偵測器閘 Δw  

不改 Soft-Frozen clip 上下限。

## 重現

```bash
PYTHONPATH=scripts python3 scripts/etf0050_regime_detector_stagea.py
```

詳見英文章程。
