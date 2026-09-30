# FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEB_CHARTER

Date: 2026-09-30
Status: **Stage B — Path3 strategy cutover paper dual** · Soft **KEEP** · broker **false** · live cutover flag **OFF**
Parent: 0kac `CUTOVER_SCOPE_DEFINED` · scope `WITHIN_SLEEVE_PATH3`
Register: **0kam** · mech `PATH3_STRATEGY_CUTOVER`

## Question

Does paper `WITHIN_SLEEVE_PATH3` (daily Path3 FIN∪TEL Soft-core ownership, sticky 0050) beat status-quo flip-carve on tip/held/sealed enough to justify cutover ACCEPT later?

## Arms

- `FLIP_CARVE` — flip-only FIN∪TEL recon · sticky 0050 (status quo)
- `WITHIN_DAILY` — daily FIN∪TEL → active book · sticky 0050 (challenger)
- `FULL_DAILY` — context: Soft-core = book daily (0050 moves too)

## Gates → `PAPER_WITHIN_HIT`

- held CAGR lift > 0 · sealed MDD improve ≥ -0.25 pp · tipY ≥ -1.0 pp · edge vs flip-carve

## Non-goals

- `live_path3_strategy_cutover=True` · broker · Soft clip flip · FULL_SOFT_REPLACE

Label: `FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEB_CHARTER_2026-09-30__PAPER_WITHIN__NO_LIVE`
