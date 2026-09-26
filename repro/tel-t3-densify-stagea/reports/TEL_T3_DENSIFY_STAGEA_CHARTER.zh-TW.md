# 電信 within-sleeve — T3 densify／T2 半開／近持平（Stage A）

日期：2026-09-26  
狀態：**Stage A `TEL_NEARFLAT_READY`** · Soft-Frozen **KEEP** · 不上 live  
人令：三路徑都研究  

結論：densify **無 HIT**；僅 parent `D3_A100_C100_B00`（=`T3_COOL_INV_VOL20`）過近持平 +0.15；T2 半開仍修不好 sealed MDD。READY ≠ ACCEPT ≠ live。

1. **T3 densify** — `INV_VOL20` 振幅 × 防守深度 × DIST60 混權  
2. **T2 半開** — 弱 tilt／與 cool 成比例  
3. **近持平 +0.15** — 同書二次門檻（paper policy；需人令 ACCEPT）

```bash
PYTHONPATH=scripts python3 scripts/tel_t3_densify_stagea.py
```
