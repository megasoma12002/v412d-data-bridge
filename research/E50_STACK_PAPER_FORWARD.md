# E50 Stack Paper Forward — Status

Date: 2026-09-04  
Package: `forward/e50_stack/`  
Script: `scripts/e50_stack_forward_pipeline.py`

## Result

| Check | Value |
|---|---|
| QC | **PASS** |
| Window | 2019-01-02 → 2026-08-28 (1851 days; alpha NAV end) |
| Split | 80% core / 20% alpha |
| CAGR | ~14.9% |
| MDD | ~−23.1% |
| Util | ~0.033 |

States (ops labels): NORMAL / ALPHA_WEAK / CRISIS from E45 exposure + alpha 20d trail.

## Governance bindings

- E45: decision **B** → signal-only alpha-cut-first (core not scaled)
- Alpha: **3B saturated** → locked A3-R1 MIXED only
- Does not modify `forward/e21/`

## Files

- `nav_combined.csv`, `nav_core.csv`, `nav_alpha.csv`, `exposure_e45.csv`
- `state_machine.csv`, `audit_chain.jsonl`, `qc_status.json`, `config.json`
