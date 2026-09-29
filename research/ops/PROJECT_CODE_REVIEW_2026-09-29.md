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
| Sticky tip-`flip` landmine | **FIXED this pass** | flip only on exact signal date |
| Path3 strategy cutover | **CHARTER ONLY** | 0kac `CUTOVER_SCOPE_DEFINED` · live flag absent |
| Path3 daily share ledger freshness | **HARDENED** | `ledger_stale` fail-closed (max_stale=0); panel tip still 2026-09-24 vs market 2026-09-29 |
| Ops register / PREP supersession | **DRIFT** | 0k9u/0k9w/PREP still claim flag OFF / weight not wired |
| e21 Path3+mute integration tests | **FIXED this pass** | `tests/test_e21_path3_mute_ledger.py` orchestration harness |
| Weight-mode dispatch except | **FIXED this pass** | was bare `Exception` → `asof_b`; now `ImportError` only |
| Paper SELL-before-BUY (prior O1) | **CLOSED** | `sort_rows_sell_before_buy` shared in `simulate_core` path |
| Partial-write fills vs state (prior O2) | **CLOSED** | `live_day_commit` deferred fills + atomic state |

**Overall:** Live Soft-Frozen + broker gates remain healthy. Path3 flip-carve stack is LIVE WIRED; this pass closes mute-on-empty, ledger stale fail-closed, empty-mix fail-closed, and e21 orchestration tests. Ledger/signal panel tip still **2026-09-24** while market tip is **2026-09-29** (refresh blocked until Path3 signal catches market). Ops PREP/register drift remains.

---

## Findings

### P0 — Sticky tip-`flip` after flip day (fixed this pass)

- **Where:** `scripts/live_path3_t0_switch_emitter.py` `switch_meta_for_asof`
- **Bug:** Matched latest `date <= asof` and reused raw `flip=True`. If signal tip ended on a flip, every later asof kept `flip=True` → re-emit `-P3T0` + Soft mute every session.
- **Evidence:** tip flip `2026-06-12` → asof `2026-06-13`/`2026-06-17` still `flip=True` (repro). Live tip today was non-flip (latent).
- **Fix:** `flip` only when matched row date **equals** asof; expose `signal_date` / `signal_exact`. Test: `Path3SwitchMetaExactFlip`.
- **Source:** [Live broker Path3 safety](bc-dc17798f-3c90-5b25-b16e-7bd3fdc731c1)

### P1 — Path3 daily ledger / signal freshness (silent nearest-prior) — **FIXED this pass** (code)

- **Where:** `scripts/path3_comp_sat_daily_share_ssot.py` `shares_asof_detail` · `plan_delta_shares_ledger`
- **Was:** After ledger end, plans still succeeded via nearest-prior with no stale reason.
- **Fix:** `ledger_asof` / `ledger_lag_calendar_days` / `ledger_stale` meta; default `max_stale_calendar_days=0` → return `None` + `reason=ledger_stale`. Empty sleeve mix with ledger names present → fail-closed keep live (no equal-weight recon unless `allow_equal_fallback=True`).
- **Residual ops:** panel `end=2026-09-24` · Path3 signal tip same · market tip `2026-09-29`. Full ledger rebuild deferred until signal catches market tip.

### P1 — Mute hole on flip + empty/failed Path3 plan — **FIXED this pass**

- **Where:** `live_soft_path3_coexist_mute.should_mute` · default `MUTE_SOFT_FIN_TEL`
- **Was:** Flip + empty/`None` Path3 deltas → mute skipped → Soft FIN/TEL Exact T+1 still emitted.
- **Fix:** `MUTE_SOFT_FIN_TEL` / `MUTE_SOFT_ON_FLIP_META` / `MUTE_SOFT_ALL_SLEEVES` mute on flip whenever emit ON (even if Path3 plan empty). Only `MUTE_OVERLAP_CODES` still requires non-empty deltas.
- **Source:** [Live broker Path3 safety](bc-dc17798f-3c90-5b25-b16e-7bd3fdc731c1)

### P1 — COMP/SAT recon quality fail-open (asof_b path; ledger mix hardened)

- **Where:** `live_path3_t0_weight_engine.py` empty eligible → all FIN; overlay bools default True
- **Risk:** Missing buy_ok/hard150 forces moves / weakens HARD on **asof_b** path (ACCEPT mode is ledger).
- **Ledger path:** empty-mix fail-closed landed this pass (see above).
- **Action:** Prefer fail-closed empty delta + reason when asof_b path used.

### P1 — Register / OPS / PREP supersession drift (flags ON, docs say OFF)

- **Where:**
  - `HUMAN_DECISION_REGISTER.md` rows **0k9u / 0k9w** still **PREP / flag OFF**
  - `OPS_STATUS.md` Path3 fill PREP / emitter PREP bullets still `fill=False` / `emit=False` / weight not wired
  - `LIVE_PATH3_T0_SWITCH_EMITTER_PREP.md` §Implemented still “hook gated OFF … weight engine not wired”
  - `LIVE_T0_CARVE_FIN_SAT_SWITCH_FILL_PREP.md` still weight engines flag OFF
  - Row **0ka7** still says weight engine **not wired** (superseded by 0kab)
- **Effect:** Same landmine class as Soft-Frozen checklist DRAFTED-after-ACCEPT (2026-09-12 H1).
- **Action:** Mark 0k9u/0k9w **SUPERSEDED by 0ka7**; stamp PREP docs EXECUTED; fix 0ka7 weight clause → ledger ON (0kab).

### P2 — `plan_or_none_for_pipeline` broad `except Exception` → silent `asof_b`

- **Where:** `scripts/live_path3_t0_weight_engine.py` mode dispatch
- **Was:** Any exception → Stage B `asof_b` while ACCEPT SSOT is `ledger`
- **Fixed this pass:** narrow to `ImportError` only

### P2 — Mute coupled only inside emit-ON branch

- **Where:** `scripts/e21_forward_pipeline.py` ~337–367
- **Risk:** If emit flag ever flipped OFF while mute stays True, Soft FIN/TEL mute never runs (by design of `should_mute(emit_enabled=…)`). Documented coupling; easy to miss on rollback.
- **Action:** Landmine comment + test: emit OFF ⇒ mute applied false even if mute flag True; optional QC field.

### P2 — No e21 orchestration test for Path3+mute+ledger — **FIXED this pass**

- **Where:** `tests/test_e21_path3_mute_ledger.py`
- **Fix:** Stub Soft rows + flip signal + ledger mock → Soft FIN/TEL muted · `-P3T0` tagged · 0050 Soft kept; also asserts flip+empty Path3 still mutes.

### P2 — Mute / emitter test docstring stale

- **Where:** `scripts/live_soft_path3_coexist_mute.py` · `tests/test_path3_t0_switch_emitter.py`
- **Fixed this pass:** docstrings note 0kaa/0ka7 LIVE WIRED / flag ON.

### P2 — Strategy cutover charter not wired (expected)

- **Where:** `live_config` has **no** `live_path3_strategy_cutover` yet (0kac Stage A only)
- **Note:** Correct — do not treat as bug. Next is paper `PAPER_WITHIN_HIT`.

### Info — Broker gate looks correct

- Triple gate: `broker_live_write_accepted` + `E21_BROKER_WRITE_LIVE` + ballot `accepted`
- Landmine `test_broker_live_write_still_fail_closed` present
- No production `broker_live_write_accepted=True` in scripts/

### Info — Prior Sept-12 open items status

| ID | Then | Now |
|---|---|---|
| O1 paper SELL-before-BUY | OPEN | **Closed** — `sort_rows_sell_before_buy` in simulate_core |
| O2 partial-write fills vs state | OPEN | **Closed** — deferred day-commit + atomic state |
| O3 tip `nav.e22_version` == DEFAULT | OPEN | **Partial** — present/match asserted; not `== DEFAULT` |
| O4 KD_OPT dict copies in research | OPEN | **Still open** |
| O5 ops `soft_frozen_clip` vs QC `soft_frozen_fin_clip` | OPEN | **Still open** |

---

## Fixed this pass (hygiene + code)

- **P0 sticky tip-`flip`**: exact-date flip gate + tests
- Supersede stale 0k9u / 0k9w / PREP / OPS Path3 bullets to match LIVE WIRED reality
- Stamp emitter / fill PREP “Implemented” sections for 0ka7–0kab
- Clarify 0ka7 weight-engine clause → see 0kab
- Narrow weight-mode `except Exception` → `ImportError`
- Stale mute/emitter test module docstrings
- **P1 mute hole**: default policy mutes Soft FIN/TEL on flip even if Path3 deltas empty
- **P1 ledger stale**: `shares_asof_detail` + `ledger_stale` fail-closed (`max_stale_calendar_days=0`)
- **P1 empty-mix**: ledger names present but mix empty → keep live (no equal recon by default)
- **P2 e21 orchestration**: `tests/test_e21_path3_mute_ledger.py`

---

## Recommended next (not this PR)

| Pri | Item |
|---|---|
| 1 | Refresh Path3 signal + daily share ledgers through market tip (2026-09-29) |
| 2 | Paper dual for 0kac `WITHIN_SLEEVE_PATH3` → `PAPER_WITHIN_HIT` |
| 3 | asof_b empty-eligible fail-closed (ACCEPT mode is ledger; residual) |
| 4 | Close residual Sept-12 O3/O4/O5 when next ops touch |

---

## Non-actions

- No broker ACCEPT · no Path3 strategy cutover live flag  
- No Soft clip / CONF α flip · no tip history rewrite  

## Verification

```bash
PYTHONPATH=scripts python3 -c "from live_config import LIVE; assert LIVE.broker_live_write_accepted is False; assert LIVE.live_path3_weight_engine_mode=='ledger'; assert LIVE.live_soft_path3_coexist_mute is True"
PYTHONPATH=scripts python3 -m unittest tests.test_path3_t0_weight_engine tests.test_soft_path3_coexist_mute tests.test_path3_daily_share_ssot tests.test_e21_path3_mute_ledger tests.test_broker_safety -q
```
