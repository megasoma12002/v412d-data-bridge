# Cutover checklist — Path3 strategy cutover (`PATH3_STRATEGY_CUTOVER`)

Status: **BALLOT OPEN** · default scope `WITHIN_SLEEVE_PATH3` · broker **false** · live flag **OFF**  
Charter: `FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEA_CHARTER.md` · Register **0kac** · Paper **0kam** · Ballot `PATH3_STRATEGY_CUTOVER_ACCEPT_BALLOT_OPEN.md`

## Gate

- [x] Carve / emit / fill / ledger / mute LIVE WIRED (0ka7–0kab) — flip-day status quo
- [x] Scope ladder defined (`FLIP_CARVE_ONLY` … `FULL_SOFT_REPLACE`)
- [x] Stage A `CUTOVER_SCOPE_DEFINED` decision pack filed
- [x] Paper dual Soft-carve vs `WITHIN_SLEEVE_PATH3` → **`PAPER_WITHIN_HIT`** (2026-09-30 · 0kam · still no live flag)
- [x] Sealed MDD / tip / held disposition vs Path3 observe baseline — **PASS** (`PATH3_STRATEGY_CUTOVER_PREACCEPT_DISPOSITION.md` · cite 0ka6 / 0k9r ACCEPTABLE · 0kam sealed+7.24)
- [x] Wrong-stay / 2022 residual disposition explicit — **KNOWN / ACCEPTABLE to ballot** (0ka5 / 0k9x · WITHIN 2022 +1.94 vs FLIP)
- [x] Overlay coexistence smoke — **`OVERLAY_DESIGN_COEXIST_OK`** (FIN/TEL retire · overlays KEEP · e21 dual-smoke = EXECUTED-prep)
- [x] Parent observes disposition (COMPOSITE · SAT_RELAX · P3_T0_STATE) — **KEEP OPEN** at cutover time
- [x] Confirm T+0 carve stays narrow (`T0_CARVE_FIN_SAT_SWITCH` only)
- [x] Dedicated human ACCEPT ballot (scope line exact) — **OPEN** · **separate from broker**
- [ ] Human ACCEPT / DEFER / REJECT reply
- [ ] EXECUTED wire (`live_path3_strategy_cutover=True`) — only after ACCEPT
- [ ] Broker live-write still **false** unless its own ACCEPT

Until human ACCEPT + EXECUTED: **no** `live_path3_strategy_cutover=True`.
