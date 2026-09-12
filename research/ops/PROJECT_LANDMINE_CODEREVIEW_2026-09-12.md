# Project Landmine Code Review — 2026-09-12

Scope: LIVE + shared ops after Soft-assist K9+ (#195) and Sleeve-tilt (#193) observe.  
Companions: `PROJECT_CODE_REVIEW_2026-09-12.md` · priors `PROJECT_LANDMINE_CODEREVIEW_2026-09-10.md`.

Soft-Frozen **[0.60, 0.90] KEEP** · KD_OPT KEEP · E45 OFF · Soft-assist / Sleeve-tilt **paper only** · no live wire / no Soft×Sleeve combo.

Label: `PROJECT_LANDMINE_CODEREVIEW_2026-09-12__CHECKLIST_ALIGN__ASOF__PARTIAL_FILL__OBS_ALERTS`

---

## Verdict

| Area | Grade | Notes |
|---|---|---|
| Soft-Frozen FINBAND live | **HEALTHY** | SSOT + tip |
| Soft-Frozen checklist vs live | **FIXED** | Was DRAFTED after ACCEPT |
| Soft-assist / Sleeve live leak | **OK + hardened** | e21 clean; new sleeve guards |
| `--asof` rewind | **FIXED** | Fail-closed |
| Partial BUY order burn | **FIXED** | Pending until full afford |
| Observe PAUSE → OPS_ALERTS | **FIXED** | Soft + Sleeve scanned |
| CI month-end artifact commit | **FIXED** | Observe repro dirs |
| Div amount parse → 0 on live | **FIXED** | Fail-closed with `require_exists` |
| Paper SELL-before-BUY | **OPEN** | Deferred |

**Overall:** Post-#195/#193 landmines were **checklist/ops drift** and two **execution edge cases** on e21 — not a Soft-Frozen or Soft-assist live wire.

---

## HIGH (fixed)

### H1 — Soft-Frozen checklist DRAFTED while live is FINBAND
Ops could read “NOT AUTHORIZED” and think the live clip flip never happened. Aligned to ACCEPTED + sibling clip citations.

### H2 — `--asof` behind `last_date`
Immutable fills skip; state rewrite → silent corruption. Now SystemExit.

### H3 — Partial BUY under `fill_id == order_id`
Residual never retried. Now skip fill when `afford < orig_q`.

---

## MEDIUM (fixed)

- Soft/Sleeve monitors in `ops_alert_scan`
- Pack note IDs + no-combo wording
- CI `git add` observe repro dirs
- Live dividend amount fail-closed
- Landmine unit guards for sleeve / asof / alert paths

---

## OPEN (carry)

| ID | Item |
|---|---|
| O1 | Paper `simulate_core` fill order |
| O2 | Non-atomic fills vs state |
| O3 | Tip `e22_version` QC assert |
| O4 | KD_OPT research dict copies |

---

## Verification

`PYTHONPATH=scripts python3 -m unittest tests.test_landmine_guards -v` → **13 OK**

---

## Non-actions

No Soft-Frozen / Soft-assist / Sleeve-tilt / E45 / DEFAULT flip · no Soft×Sleeve combo · no forward history rewrite.
