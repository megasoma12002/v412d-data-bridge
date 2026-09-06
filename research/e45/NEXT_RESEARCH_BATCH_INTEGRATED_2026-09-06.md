# Next Research Batch — Integrated (2026-09-06)

Generated: `2026-09-06T06:54:33.425680+00:00`  
Status: **PAPER / SANDBOX / OPS DIAG** — Soft-Frozen **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · stitch **FORBIDDEN**  
Claimed −13.16%: **`RETIRED_HISTORICAL_NARRATIVE`** (do not invent a replacement)

## Scope (all requested)

| # | Workstream | Status | Primary artifact |
|---|---|---|---|
| 1 | Non-COVID multi-event alt levers | **DONE** | `E45_NONCOVID_MULTIEVENT_ALT_LEVERS.md` |
| 2 | COVID-ex held-out KPI | **DONE** | `E45_COVID_EX_HELDOUT_KPI.md` |
| 3 | Observe trailing PAUSE diagnostics | **DONE** | `E45_OBSERVE_PAUSE_DIAGNOSTICS.md` |
| 4 | E22_v3 Stage B sealed dual-book | **DONE** | `E22_V3_STAGE_B_SEALED_COMPARE.md` |
| 5 | Data-source Phase C follow-up | **DONE** | `DATA_SOURCE_PHASE_C_FOLLOWUP.md` |

## Cross-cut verdicts

### E45 paper
1. **Multi-event qualifiers:** incl_covid = **0**; strict_noncovid = **0** (alt levers still fail the charter).
2. **COVID-ex held-out least-bad:** `E1BIN_A05` @ `-0.11` (still negative).
3. **Observe tip gates:** still mostly PAUSE; historical first_clean existed then relapsed — stitch remains **FORBIDDEN**.

| Sleeve | Tip asof | YTD | 1y | First clean both |
|---|---|---|---|---|
| `CHAL_E45_E3` | 2026-09-04 | PAUSE_REVIEW | PAUSE_REVIEW | 2023-02-24 |
| `BLEND_E45_A25` | 2026-09-04 | PAUSE_REVIEW | PAUSE_REVIEW | 2023-02-24 |
| `BLEND_E45_A05` | 2026-09-04 | ALERT | PAUSE_REVIEW | 2023-02-24 |
| `SLEEVE_FIN_ONLY_A10` | 2026-09-04 | PAUSE_REVIEW | PAUSE_REVIEW | 2023-02-24 |

### E22_v3 Stage B
- Live DEFAULT **`E22_v2s_tw` untouched**.
- `recv_pay` end-wealth matches DEFAULT (timing shift into receivable).
- Flat tax10/tax20 drag sealed CAGR (~−0.32 / −0.64 pp) and worsen MDD — **not promote-ready**.
- Combined `recv_pay_taxW` still **NOT STARTED**.

### Data-source Phase C
- Sealed C1 DRIFT codes: `0050` (ETF Yahoo align / corr issue; MAD still small).
- Sealed C2 WARN codes: `none`.
- Soft-Frozen KEEP · no e21 primary rewrite · TAIEX Yahoo failover stays opt-in.

## Explicit non-actions

- No Soft-Frozen / DEFAULT flip  
- No live stitch / no HIGH_BETA OPEN  
- No −13.16% reinvention  
- No E22_v3 promote ballot  

## Runners

```bash
python3 scripts/e45_next_research_batch.py
python3 scripts/e22_v3_stage_b_sealed_compare.py
python3 scripts/data_source_phase_c_followup.py
```

Label: `NEXT_RESEARCH_BATCH_2026-09-06__STITCH_FORBIDDEN__DEFAULT_KEEP`
