# 民股金控 — Gate V8 AND 確認堆疊（最大 CAGR × 最小 MDD）研究 Charter

日期：2026-09-25  
狀態：**CHARTER OPEN · Stage A READY** · Soft-Frozen live **不動** · live wire **false**

## 目標（寫死）

- **Maximize CAGR**（held / sealed 分窗）  
- **Minimize MDD**（尤其 sealed）  
- 宇宙：公股 R1 **KEEP** + 民股金控 **新增機制**（何時開、開多少、與公股如何共存）  
- Soft-Frozen live **不動**直到明確 **ACCEPT**

## 為何 V8（不是重調 V7）

V7 單閘 OR 族已 sealed peek → **SOFT** · **禁止**再擴 V7 grid。  
V8 = **新機制**：FinPriv 只在 **所有 active confirms 同時為 1**（AND）時才 carve。

## 新機制（V8 AND-confirm carve-out）

- Base：`BASE_LIVE_FUSE_COOL`（Soft+Sleeve+COOL live twin）  
- Confirm：regime ∈ {Bull, Bull+Side} **∧** trend ∈ {MA60, MA120}  
- 可選 cool-full：僅在 COOL exposure == 1.0（非防衛）時 carve → tag `_COOL1`  
- `priv_frac∈{0.05,0.08,0.10}` · within ∈ {EQUAL, PRIV_KD_MAY}  
- 上限 ≤ 48 challengers + BASE

## 門檻（同 V7 HIT）

1. sealed MDD↑ ≥ 0（硬）  
2. held MDD↑ ≥ −0.25 pp  
3. held CAGR↑ ≥ +0.20 pp  
4. tip YTD/1y clean + tip MDD↑ ≥ −0.5  

Verdict：`PRIV_FINHC_V8_HIT` / `PRIV_FINHC_V8_SOFT` / `MDD_BLOCK` / `NO_LIFT`  
HIT ≠ 上 live；上 live 要另開 Class D ACCEPT。

英文全文：`PRIV_FINHC_GATE_V8_CHARTER.md`
