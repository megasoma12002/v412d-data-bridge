# TIPSOFT Soak + Eng-Debt Backlog — 2026-10-03

Status: **SOAK_OPEN** · register **0kbf** · Soft-Frozen **KEEP** · broker **false** · Path4 **OFF**  
Parents: soak gate `TIPSOFT_DD_SWITCH_SOAK_GATE` · inventory `TIPSOFT_LIVE_OBSERVE_INVENTORY_2026-10-02` · modularize #408 MERGED

## Soak cadence (2026-10-03) — SUCCEEDED

| Step | Result |
|---|---|
| dual-paper ledgers | OK · `n_compare=3360` |
| month-end monitor | OK · asof **2026-09-29** · alerts `[]` · `n_windows=6` |
| `ops_alert_scan --report-only` | OK · overall HIGH (legacy L4/FIN_BUY PAUSE_REVIEW only; **no** tipsoft DD_SWITCH HIGH) |
| `tipsoft_dd_switch_soak_gate` | OK · status **SOAK_OPEN** |
| `e21_live_vs_paper_recon` | OK · `overlap_n=18` |

### Current soak numbers

| Metric | Value | Floor | State |
|---|---|---|---|
| Live tip | 2026-10-02 | — | QC PASS |
| Nav tip days since ACCEPT (2026-10-01) | **2** | 20 | OPEN |
| Calendar days since ACCEPT | **1** | 28 | OPEN |
| Live↔paper overlap_n | **18** | 60 | OPEN |
| DD_SWITCH monitor pause | none | none | PASS |
| Gate status | **SOAK_OPEN** | SOAK_PASS | waiting |

Cadence command block: see `TIPSOFT_DD_SWITCH_SOAK_GATE.md` § Cadence.

## Frozen until SOAK_PASS

- Soft FIN/TEL Exact T+1 refill ACCEPT / reopen
- Path4 live
- Broker EXECUTE / live-write
- Yearmix / year-oracle / year-switch commit
- New tip Soft mechanism Stage A / tip apply
- DualPaperLedgerSpec full OPERATING rewrite (needs golden NAV)

## Allowed eng-debt queue

### P0 — cadence (do now / every tip day)

1. Run soak cadence scripts; refresh `TIPSOFT_DD_SWITCH_SOAK_GATE.{md,json}`
2. Refresh ops alert scan + live↔paper recon (`overlap_n`)
3. Keep Soft FIN/TEL · Path4 · broker freeze stamps honest in register / OPS_STATUS

### P1 — docker / UAT prep (docs + smoke only; no live wire)

1. Docker ops QC smoke docs / CI already present — cheap doc polish only (`ARCH_LIVE_MODULARIZE` § Docker)
2. Yuanta SPARK UAT howto remains PREP — no `API_WIRED` flip
3. TWSE session calendar charter — required before broker submit (still blocked by soak)

### P2 — DualPaperLedgerSpec defer

1. Full OPERATING rewrite of remaining ledger wrappers → `DualPaperLedgerSpec` **deferred** until golden NAV + SOAK_PASS
2. Safe under soak: charter/doc pointers only (this backlog · `ARCH_LIVE_MODULARIZE` Next)
3. Do **not** change Soft clips, Path3 semantics, tip apply, or broker ports

### Soak-safe hygiene (landed / queue)

| Item | State |
|---|---|
| Stale SUPERSEDED observe OPEN labels (0kaw/0kba/0kbb + Path3 shadows) | **this PR** |
| Hygiene unittest for closed-by SUPERSEDED OPEN stamps | **this PR** |
| Yearmix / yearly backtest untracked WIP | leave untracked · **NOT OPEN** |

## Explicit non-actions

- Does not flip Soft-Frozen / broker / Path4
- Does not reopen Soft FIN/TEL or CLOSED observes
- Does not promote Path4 or year-oracle
- Does not rewrite forward/e21 history
- Does not force-push / amend

Label: `TIPSOFT_SOAK_ENG_DEBT_BACKLOG_2026-10-03__SOAK_OPEN__CADENCE_OK`
