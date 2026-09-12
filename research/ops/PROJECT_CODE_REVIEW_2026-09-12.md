# Project Code Review — 2026-09-12 (full repo)

Scope: whole-repo landmine + live-path review after Soft-assist K9+ observe (#195) and Sleeve-tilt observe (#193).  
Soft-Frozen Financial **[0.60, 0.90] KEEP** · live **KD_OPT** KEEP · **TEL_EQUAL** KEEP · E45 stitch **OFF** · Soft-assist / Sleeve-tilt **paper observe only** · DEFAULT **`E22_v2s_tw` KEEP** · capital **500M** · lot **1000**

Companion: `PROJECT_LANDMINE_CODEREVIEW_2026-09-12.md`  
Priors: `PROJECT_CODE_REVIEW_2026-09-10.md` · `PROJECT_LANDMINE_CODEREVIEW_2026-09-10.md`

Label: `PROJECT_CODEREVIEW_2026-09-12__SOFT_FROZEN_CHECKLIST_ALIGN__ASOF_REWIND__PARTIAL_FILL__OBS_ALERTS`

---

## Verdict

| Area | Grade | Notes |
|---|---|---|
| Soft-Frozen FIN clip `[0.60, 0.90]` | **HEALTHY** | SSOT `e16_soft_frozen_base`; tip wired |
| Soft-Frozen cutover checklist status | **FIXED this pass** | Was stale `DRAFTED_NOT_AUTHORIZED` after FINBAND ACCEPT |
| Exact T+1 / board-lot / zero-qty | **HEALTHY** | Prior P0/P1 still green |
| Live KD_OPT + TEL_EQUAL + E45 OFF | **HEALTHY** | Soft-assist / Sleeve-tilt not in e21 |
| Soft-assist / Sleeve-tilt isolation | **HARDENED this pass** | Landmine guards + alert scan coverage |
| `--asof` rewind behind `last_date` | **FIXED this pass** | Fail-closed SystemExit |
| Partial BUY fill burns `order_id` | **FIXED this pass** | Cash-short → leave pending (no residual drop) |
| Ops alert blind to Soft/Sleeve PAUSE | **FIXED this pass** | Monitors now in `ops_alert_scan` |
| Pack cutover_note stale `SOFT_BOTH` | **FIXED this pass** | K9+ + Sleeve-tilt IDs |
| Month-end CI commit miss observe repro | **FIXED this pass** | Soft-assist / Sleeve-tilt / FIN-within dirs |
| Live dividend unparseable amount → 0 | **FIXED this pass** | Fail-closed when `require_exists` |
| Paper `simulate_core` SELL-before-BUY | **OPEN MEDIUM** | Deferred (NAV churn) |
| Partial-write fills vs state | **OPEN** | Prior; transactional write later |

**Overall:** Live Soft-Frozen / KD_OPT / E45-OFF path remains healthy. This pass fixed **governance drift** (Soft-Frozen checklist still DRAFTED after ACCEPT), **ops blind spots** (Soft/Sleeve PAUSE not in OPS_ALERTS; stale SOFT_BOTH note; CI commit gaps), and two **live execution landmines** (`--asof` rewind + partial-fill order burn). No Soft-Frozen / Soft-assist / Sleeve-tilt live wire.

---

## Fixed this pass

### H1 — Soft-Frozen cutover checklist still DRAFTED after FINBAND live wire
- **Where:** `research/ops/CUTOVER_CHECKLIST_SOFT_FROZEN_CLIP.md` (+ `.json`)
- **Bug:** Live SSOT is `[0.60, 0.90]` with ACCEPT note, but checklist still said **DRAFTED — NOT AUTHORIZED** → ops could think the live flip is blocked.
- **Fix:** Status → **ACCEPTED · LIVE WIRED**; cite `SOFT_FROZEN_CLIP_FLIP_ACCEPTED_FINBAND.md`. Sibling L4/FIN50/BLEND/FIN-within checklists cite live FINBAND `[0.60, 0.90]` (still NOT AUTHORIZED for their own cutovers).

### H2 — `--asof` / session behind `last_date` rewrites `portfolio_state`
- **Where:** `scripts/e21_forward_pipeline.py`
- **Bug:** Immutable fills skip; state always overwritten → silent live book corruption on rewind.
- **Fix:** Fail-closed if `latest < last_date`.

### H3 — Cash-short BUY partial fill burns full `order_id`
- **Where:** `scripts/e21_forward_pipeline.py` fill loop
- **Bug:** `fill_id == order_id` with `q < orig_q` drops residual forever.
- **Fix:** If afford `< orig_q`, **continue** (leave pending). Full lot or wait.

### M1 — `ops_alert_scan` ignored Soft-assist / Sleeve-tilt PAUSE_REVIEW
- **Where:** `scripts/ops_alert_scan.py`
- **Fix:** Scan `SOFT_ASSIST_MONTH_END_MONITOR.json` + `SLEEVE_LAYER_TILT_MONTH_END_MONITOR.json`.

### M2 — Pack cutover_note still said Soft-assist `SOFT_BOTH`
- **Where:** `scripts/ops_month_end_paper_pack.py`
- **Fix:** `SOFT_CHAMP_PLUS_K9_LT30_a10` + `SLEEVE_BELOW_MA60_a01`; explicit no auto-combo / no live wire.

### M3 — Month-end CI commit missed observe repro dirs
- **Where:** `.github/workflows/ops-month-end-paper-pack.yml`
- **Fix:** Add soft-assist / sleeve-tilt / fin-within-sleeve repro paths (`research/ops/` already covers monitor JSON).

### M4 — Live dividend unparseable amounts silently became 0
- **Where:** `scripts/e22_dividend_accounting.py`
- **Fix:** `fail_closed_amounts` defaults to `require_exists` (live path).

### Guards
- `tests/test_landmine_guards.py` — Sleeve-tilt wire ban, alert-scan coverage, asof/partial-fill string guards.

---

## Still open (not Soft-Frozen / Soft-assist live)

| ID | Sev | Finding | Action |
|---|---|---|---|
| O1 | P1 | Paper `simulate_core` no SELL-before-BUY | Separate paper-engine PR + Soft-assist ledger refresh ACCEPT |
| O2 | P2 | Partial-write fills vs `portfolio_state` | Transactional write when next live-touched |
| O3 | P2 | Tip `nav.e22_version` not QC-asserted | Optional QC assert == DEFAULT |
| O4 | P2 | KD_OPT dict copies in research screens | Consolidate non-soft_assist shared module |
| O5 | P2 | Ops JSON key `soft_frozen_clip` vs QC `soft_frozen_fin_clip` | Rename on next ops touch |

---

## Verification

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_landmine_guards -v
# 13 tests OK
```

Dividend fail-closed smoke: unparseable live amount → `ValueError`; soft path with `fail_closed_amounts=False` still allows research.

---

## Non-actions

- No Soft-Frozen / DEFAULT / Soft-assist live / Sleeve-tilt live / E45 stitch flip  
- No Soft-assist × Sleeve-tilt auto-combo  
- No `forward/e21` history rewrite  
- No paper simulate_core fill-order change (avoid observe NAV churn)
