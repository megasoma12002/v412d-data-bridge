# FIN_SAT_PATH3_THETA_DOWN_GRID_STAGEA_DECISION_PACK

Date: 2026-09-29 · Verdict: **`THETA_DOWN_CONFIRM`**
Status: Soft-Frozen **KEEP** · Path3 observe θ=0.01 **KEEP** · fill/emit **OFF** · no live
Register: **0ka4** · Parents: 0ka3 / 0k9r

## Answer

Parent θ=0.01: tipY↑ 2.7325 · held↑ 3.4758 · y2022 -0.75 · flips 153.
0ka3 ref θ=0.005: tipY↑ 2.877 · held↑ 3.771 · y2022 -0.67 · flips 199.
Dense-grid best `THETA_0.005` θ=0.005: tipY↑ 2.877 · held↑ 3.771 · y2022 -0.67 · flips 199 · beats_parent=True · beats_0.005=False.
Pareto set: `[0.001, 0.0015, 0.004, 0.0045, 0.005, 0.0055, 0.0085, 0.009, 0.0095]`.

讀法：θ∈[0.005,0.006] 是 tip-clean 且勝 parent 的平台；θ≤0.004 tip 掉、held／偶發 2022 變好但不成尖端冠軍。θ→0.001 近高 %SAT（~44%），tip 塌到 ~0.4。

## Implication

- `THETA_DOWN_HIT`：新冠軍（優於 0.005）→ 可開 observe retune DRAFT 至該 θ。
- `THETA_DOWN_CONFIRM`：加密確認 **θ=0.005**（鄰域 0.005–0.006）；retune 候選仍 0.005，不繼續往下挖。
- `THETA_DOWN_SOFT`／`KEEP`：不 retune；observe θ=0.01 KEEP。
- Soft-Frozen KEEP · fill/emit OFF · cutover BLOCKED · no live。

Screen: `FIN_SAT_PATH3_THETA_DOWN_GRID_STAGEA_SCREEN.md` · Charter: `FIN_SAT_PATH3_THETA_DOWN_GRID_STAGEA_CHARTER.md`

Label: `FIN_SAT_PATH3_THETA_DOWN_GRID_STAGEA_DECISION_PACK_2026-09-29__THETA_DOWN_CONFIRM__NO_LIVE`
