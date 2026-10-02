# Modularize pass — Stage A harness + dual-paper helpers + e21 overlays (2026-10-01)

Status: **ENGINEERING** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · Path3 WITHIN **KEEP** · tipsoft DD_SWITCH tip apply + OVERRIDE stamps in `live_day_overlays` · broker **false** · Path4 **OFF**

## Done (safe)

### 1. Stage A harness + hygiene
- Extended `scripts/stagea_screen_helpers.py`: `load_nav_csv`, `returns_from_nav`, `nav_from_returns`, `tip_lift` (chal−base), `window_delta`; kept `tip_hygiene` (base−chal).
- Migrated **9** tipsoft `*_stagea.py` screens onto helpers (aliases `_utc/_pack/_tip/…`).
- Hygiene: `tests/test_stagea_screen_helpers.py` bans local helper clones in tipsoft Stage A.

### 2. Fat dual-paper — helpers first (no OPERATING sim rewrite)
- Migrated nav-compare / report helpers onto harness:
  - `tipsoft_ip3_live_override_dual_paper_ledgers.py`
  - `tipsoft_p3_nearpeak3_dual_paper_ledgers.py`
  - `fin_sat_path3_t0_dual_paper_ledgers.py`
  - `fin_sat_composite_dual_paper_ledgers.py` (pack/tip/utc only)
- **Deferred:** full `DualPaperLedgerSpec` rewrite of COMPOSITE / SAT_A20 / Path3 T0 OPERATING sims — specialty multi-pass cool+schedule; migrate only with dedicated ACCEPT + golden NAV compare.

### 3. e21 overlay orchestration extract
- New `scripts/live_day_overlays.py`: Path3 WITHIN → mute → T0 emit → tipsoft `session_meta` (behavior-preserving).
- `e21_forward_pipeline` calls `apply_path3_tipsoft_overlays` + `overlay_signal_fields`.
- Guards: `tests/test_live_day_overlays.py` + updated tipsoft wire test.

## Explicitly not done
- Split `simulate_core` / `within_sleeve_alloc` (P1 — only if needed later)
- History rewrite / Soft clip / broker / Path4 / tipsoft return-blend apply

## Label
`MODULARIZE_STAGEA_DUALPAPER_E21_2026-10-01__HARNESS__OVERLAYS__NO_SOFT_CHANGE`
