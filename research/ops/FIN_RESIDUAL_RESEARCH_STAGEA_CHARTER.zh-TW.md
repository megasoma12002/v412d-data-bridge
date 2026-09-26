# FIN 剩餘研究 Stage A — 五軌（紙上）

日期：2026-09-26  
狀態：**Stage A OPEN** · Soft-Frozen／Exact T+1 **KEEP** · 不進 live  
人話：每條都研究（sleeve／執行成本／within-FIN／再平衡／關閉 observe）

## 五軌

1. **SLEEVE** — 關掉 sleeve tilt／TEL 改 PRE_EXDIV_KD  
2. **EXEC** — cost_multiple 0／2（仍 Exact T+1 開盤日）  
3. **WITHIN** — FIN_EQUAL／FIN_TOP2_EQUAL  
4. **REBAL** — L1 門檻 0.05／0.10  
5. **CLOSE** — 1–4 都不過成交閘 → 建議關閉本選單 observe  

閘門：sealed FIN BUY adj ±5d ≥0.25pp；heldout NAV near-flat。

複現：`PYTHONPATH=scripts python3 scripts/fin_residual_research_stagea.py`
