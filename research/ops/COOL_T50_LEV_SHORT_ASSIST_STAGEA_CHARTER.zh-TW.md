# COOL × 00631L 短線輔助 — 紙上憲章（Stage A · 軌道 1–4）

日期：2026-09-26  
狀態：**CHARTER OPEN · Stage A DONE → `SHORT_ASSIST_HIT`** · Soft-Frozen **KEEP** · 不上 live  

HIT（2）：`CONF_RET3_A10_H5`（+0.54pp CAGR · sealed MDD↑ +0.02）· `CONF_RET1_A10_H3`（+0.25pp）。  
THIN／STOP／RESIDUAL 無 HIT。第5條 near-flat **未做**。僅 paper observe 候選。

## 四軌

| 軌 | 內容 |
|---|---|
| T1 THIN | α∈{0.03,0.05,0.08} × H∈{1,2} |
| T2 CONFIRM | exit 且 0050 RET1／RET3／RET1+PROXY 確認 × α∈{0.10,0.25} × H∈{3,5} |
| T3 STOP | 脈衝內正2 停損 stop∈{3%,5%} × α∈{0.10,0.25} × H∈{5,10} |
| T4 RESIDUAL | OFF＝α×剛釋放 residual × H∈{1,2,3} · α∈{0.50,1.00} |

第5條（改 CAGR／MDD 門檻）**不做**。

## 重跑

```bash
PYTHONPATH=scripts python3 scripts/cool_t50_lev_short_assist_stagea.py
```

標籤：`COOL_T50_LEV_SHORT_ASSIST_STAGEA_CHARTER_2026-09-26__OPEN`
