# Project Code Review — 2026-09-29 (full repo)

Scope: whole-repo live-safety + Path3 LIVE WIRED stack (0ka7–0kac) + ops hygiene after mute/ledger ACCEPT (#368/#369) and strategy-cutover charter (#370).  
Soft-Frozen FIN **[0.60, 0.80]** KEEP · Exact T+1 KEEP elsewhere · Path3 flip carve **ON** · broker **false** · Path3 strategy cutover **BLOCKED** (0kac charter only)

Priors: `PROJECT_CODE_REVIEW_2026-09-12.md` · `ARCH_LIVE_MODULARIZE.md`

Label: `PROJECT_CODEREVIEW_2026-09-29__PATH3_LIVE_WIRED__LEDGER_STALE__OPS_DRIFT`

---

## Verdict

| Area | Grade | Notes |
|---|---|---|
| Broker live-write fail-closed | **HEALTHY** | `broker_live_write_accepted=False` · triple gate (flag+env+ballot) |
| Soft-Frozen clips / Exact T+1 | **HEALTHY** | Path3 carve narrow; untagged same-bar still fail-closed |
| Path3 fill/emit/ledger/mute flags | **LIVE WIRED** | fill/emit True · `mode=ledger` · mute True |
| Path3 strategy cutover | **CHARTER ONLY** | 0kac `CUTOVER_SCOPE_DEFINED` · live flag absent |
| Path3 daily share ledger freshness | **RISK** | ledger `end=2026-09-24` · tip `last_date=2026-09-29` · silent nearest-prior |
| Ops register / PREP supersession | **DRIFT** | 0k9u/0k9w/PREP still claim flag OFF / weight not wired |
| e21 Path3+mute integration tests | **GAP** | unit helpers covered · no e21 day orchestration test |
| Paper SELL-before-BUY (prior O1) | **IMPROVED** | `sort_rows_sell_before_buy` shared in `simulate_core` path |
| Partial-write fills vs state (prior O2) | **IMPROVED** | `live_day_commit` deferred fills + atomic state |

**Overall:** Live Soft-Frozen + broker gates remain healthy. Path3 flip-carve stack is correctly LIVE WIRED and fail-closed on missing plan, but **ledger SSOT is already behind tip** (silent stale mix) and **ops docs still advertise PREP/flag OFF** for paths that ACCEPT flipped ON — same class of governance drift fixed on 2026-09-12.

---

## Findings

### P1 — Path3 daily ledger stale vs tip (silent nearest-prior)

- **Where:** `scripts/path3_comp_sat_daily_share_ssot.py` `shares_asof` · outputs `…/daily_shares_*.meta.json` `end=2026-09-24` · `forward/e21/portfolio_state.json` `last_date=2026-09-29`
- **Bug/risk:** After ledger end, `plan_delta_shares_ledger` still returns `ledger_scaled_recon` using last panel row — **no `ledger_stale` reason / QC alert**. Live flip after 2026-09-24 uses frozen within-sleeve mix.
- **Action:** Refresh ledger on tip catch-up; add meta `ledger_asof` + stale-days in plan meta; optional e21/QC warn if `asof - ledger_end > N` sessions.

### P1 — Register / OPS / PREP supersession drift (flags ON, docs say OFF)

- **Where:**
  - `HUMAN_DECISION_REGISTER.md` rows **0k9u / 0k9w** still **PREP / flag OFF**
  - `OPS_STATUS.md` Path3 fill PREP / emitter PREP bullets still `fill=False` / `emit=False` / weight not wired
  - `LIVE_PATH3_T0_SWITCH_EMITTER_PREP.md` §Implemented still “hook gated OFF … weight engine not wired”
  - `LIVE_T0_CARVE_FIN_SAT_SWITCH_FILL_PREP.md` still weight engines flag OFF
  - Row **0ka7** still says weight engine **not wired** (superseded by 0kab)
- **Effect:** Same landmine class as Soft-Frozen checklist DRAFTED-after-ACCEPT (2026-09-12 H1).
- **Action:** Mark 0k9u/0k9w **SUPERSEDED by 0ka7**; stamp PREP docs EXECUTED; fix 0ka7 weight clause → ledger ON (0kab).

### P2 — `plan_or_none_for_pipeline` bare `except Exception` → silent `asof_b`

- **Where:** `scripts/live_path3_t0_weight_engine.py` ~398–403
- **Risk:** Any import/getattr failure on `LIVE` falls back to Stage B asof recon while live_config says `ledger` — ops think ledger is live.
- **Action:** Narrow except; log/meta `mode_fallback_asof_b`; fail-closed preferred if LIVE missing.

### P2 — Mute coupled only inside emit-ON branch

- **Where:** `scripts/e21_forward_pipeline.py` ~337–367
- **Risk:** If emit flag ever flipped OFF while mute stays True, Soft FIN/TEL mute never runs (by design of `should_mute(emit_enabled=…)`). Documented coupling; easy to miss on rollback.
- **Action:** Landmine comment + test: emit OFF ⇒ mute applied false even if mute flag True; optional QC field.

### P2 — No e21 orchestration test for Path3+mute+ledger

- **Where:** `tests/test_path3_*` · `tests/test_soft_path3_coexist_mute.py` · no `test_e21_path3_*`
- **Gap:** Unit paths pass in isolation; day order Soft→mute→Path3 append untested end-to-end.
- **Action:** Thin harness: stub Soft rows + flip signal + ledger mock → assert FIN/TEL Soft muted · `-P3T0` tagged · 0050 Soft kept.

### P2 — Mute module docstring stale

- **Where:** `scripts/live_soft_path3_coexist_mute.py` header “Flag default OFF until … ACCEPT”
- **Fix:** Note ACCEPT 0kaa LIVE WIRED / flag True.

### P2 — Strategy cutover charter not wired (expected)

- **Where:** `live_config` has **no** `live_path3_strategy_cutover` yet (0kac Stage A only)
- **Note:** Correct — do not treat as bug. Next is paper `PAPER_WITHIN_HIT`.

### Info — Broker gate looks correct

- Triple gate: `broker_live_write_accepted` + `E21_BROKER_WRITE_LIVE` + ballot `accepted`
- Landmine `test_broker_live_write_still_fail_closed` present
- No production `broker_live_write_accepted=True` in scripts/

### Info — Prior O1/O2 partially closed

- Paper SELL-before-BUY: shared `sort_rows_sell_before_buy` in early-stack / fill core
- Day commit: deferred fills/divs then `atomic_write_json` portfolio_state

---

## Fixed this pass (hygiene)

- Supersede stale 0k9u / 0k9w / PREP / OPS Path3 bullets to match LIVE WIRED reality
- Stamp emitter PREP “Implemented” section for 0ka7–0kab
- Clarify 0ka7 weight-engine clause → see 0kab

---

## Recommended next (not this PR)

| Pri | Item |
|---|---|
| 1 | Refresh Path3 daily share ledgers through tip; add stale meta/QC |
| 2 | Paper dual for 0kac `WITHIN_SLEEVE_PATH3` → `PAPER_WITHIN_HIT` |
| 3 | e21 Path3+mute+ledger orchestration unit test |
| 4 | Narrow `except Exception` in pipeline weight-mode dispatch |

---

## Non-actions

- No broker ACCEPT · no Path3 strategy cutover live flag  
- No Soft clip / CONF α flip · no tip history rewrite  

## Verification

```bash
PYTHONPATH=scripts python3 -c "from live_config import LIVE; assert LIVE.broker_live_write_accepted is False; assert LIVE.live_path3_weight_engine_mode=='ledger'; assert LIVE.live_soft_path3_coexist_mute is True"
PYTHONPATH=scripts python3 -m unittest tests.test_path3_t0_weight_engine tests.test_soft_path3_coexist_mute tests.test_path3_daily_share_ssot tests.test_broker_safety -q
```
