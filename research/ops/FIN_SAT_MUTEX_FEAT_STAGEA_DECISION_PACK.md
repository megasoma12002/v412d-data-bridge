# FIN_SAT_MUTEX_FEAT_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T13:18:57Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_MUTEX_FEAT_STAGEA_CHARTER.md`
Screen: `FIN_SAT_MUTEX_FEAT_STAGEA_SCREEN.md`
Parents: 0k9e/0k9f TIP_MDD_ONLY · COMPOSITE · SAT_RELAX · register **0k9g**

## Verdict

**`TIP_MDD_ONLY`**

SAT held CAGR↑ = 0.3343pp.

## Mutex diagnosis

- COMP-win years (7): [2012, 2014, 2017, 2019, 2020, 2023, 2025]
- SAT-win years (8): [2013, 2015, 2016, 2018, 2021, 2022, 2024, 2026]
- Feat Δ(COMP−SAT means): `{"pct_bull": 22.077, "pct_bear": -2.359, "pct_crisis": -13.488, "pct_sideways": -6.232, "mean_mdd0050_63": 2.011, "min_mdd0050_63": 1.52, "mean_r0050_63": 0.145, "comp_minus_sat_pp": 6.362}`
- Oracle year (lookahead, not HIT): held CAGR↑ 2.7486 · tipCAGR↑ 0.6801 · tipClean=True

**Reading:** 互斥真實——COMP-win 年 Bull 占比高約 +22pp、Crisis 低約 −13pp。Oracle 年切（不可實作）同時 tip-clean + held↑+2.75 + vsSAT，證明「若能預測當年勝方」切換有 HIT 上界。  
預註冊 lag-1（Crisis／BearCrisis／Bull／0050 DD／ret63）仍全數 tip CAGR−（最佳經濟 `SW_0050DD08` held↑+1.46 但 tipCAGR↑ −5.8）。日頻 regime／0050 訊號尚未對齊 tip 窗口的 HARD 拖累。

No pre-registered switch cleared tip-clean economic gates.

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. Do not expand feature thresholds after peek · do not reopen blend/REL grids
4. Oracle year is diagnosis only · not an observe candidate
5. Even HIT → paper observe ballot DRAFT only · no live wire

Label: `FIN_SAT_MUTEX_FEAT_STAGEA_DECISION_PACK_2026-09-28__TIP_MDD_ONLY__NO_LIVE`
