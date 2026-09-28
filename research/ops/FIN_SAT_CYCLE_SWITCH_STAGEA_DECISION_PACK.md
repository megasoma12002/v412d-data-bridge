# FIN_SAT_CYCLE_SWITCH_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T13:25:18Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false** · **not year-switch**

Charter: `FIN_SAT_CYCLE_SWITCH_STAGEA_CHARTER.md`
Screen: `FIN_SAT_CYCLE_SWITCH_STAGEA_SCREEN.md`
Parents: 0k9g mutex TIP_MDD_ONLY · COMPOSITE · SAT_RELAX · register **0k9h**

## Verdict

**`TIP_MDD_ONLY`**

SAT held CAGR↑ = 0.3343pp.

## Cycle diagnosis

Regime-episode COMP win-rate / mean Δpp: `{"Bear": {"n_episodes": 19, "mean_len": 16.9, "comp_win_rate": 42.1, "mean_comp_minus_sat_pp": 0.053}, "Bull": {"n_episodes": 32, "mean_len": 75.6, "comp_win_rate": 37.5, "mean_comp_minus_sat_pp": -0.184}, "Crisis": {"n_episodes": 11, "mean_len": 36.3, "comp_win_rate": 45.5, "mean_comp_minus_sat_pp": -0.002}, "Sideways": {"n_episodes": 7, "mean_len": 12.3, "comp_win_rate": 28.6, "mean_comp_minus_sat_pp": -0.42}}`

No cycle switch cleared tip-clean economic gates.

**Reading:** 週期框架正確（非年切）。Regime-episode 層 Bull 並非穩定 COMP 勝（win-rate 37.5% · mean Δ −0.18pp）——0k9g 年聚合掩蓋片段雜訊。  
ZigZag8 抬 held↑+1.75 且 vsSAT，但 tipCAGR↑ −17（峰谷半週期未對齊 tip HARD 拖累）。月／季 REL 同樣 tip CAGR−。

## Switch books

- `SW_ZZ08_BEAR_SAT` · %SAT=18.01 flips=36 · heldCAGR↑ 1.7476 tipCAGR↑ -17.0269 · tipClean=False econ=True vsSAT=True
- `SW_ZZ12_BEAR_SAT` · %SAT=8.71 flips=18 · heldCAGR↑ 0.5491 tipCAGR↑ -12.761 · tipClean=False econ=True vsSAT=True
- `SW_CRISIS_K5` · %SAT=12.45 flips=18 · heldCAGR↑ 0.2889 tipCAGR↑ -13.0042 · tipClean=False econ=True vsSAT=False
- `SW_BEARCRISIS_K5` · %SAT=23.3 flips=34 · heldCAGR↑ 0.026 tipCAGR↑ -13.0042 · tipClean=False econ=False vsSAT=False
- `SW_MONTH_REL63` · %SAT=43.48 flips=45 · heldCAGR↑ 0.1324 tipCAGR↑ -7.0588 · tipClean=False econ=True vsSAT=False
- `SW_QTR_REL126` · %SAT=48.68 flips=15 · heldCAGR↑ 0.0103 tipCAGR↑ -3.279 · tipClean=False econ=False vsSAT=False

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. **Not year-switch** · do not promote calendar oracle
4. Do not expand cycle thresholds after peek
5. Even HIT → paper observe ballot DRAFT only · no live wire

Label: `FIN_SAT_CYCLE_SWITCH_STAGEA_DECISION_PACK_2026-09-28__TIP_MDD_ONLY__NO_LIVE`
