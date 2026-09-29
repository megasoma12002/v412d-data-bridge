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
| Path3 daily share ledger freshness | **RISK** | nearest-prior silent; refresh+QC still open |
| Ops register / PREP supersession | **DRIFT** | 0k9u/0k9w/PREP still claim flag OFF / weight not wired |
| e21 Path3+mute integration tests | **GAP** | unit helpers covered · no e21 day orchestration test |
| Weight-mode dispatch except | **FIXED this pass** | was bare `Exception` → `asof_b`; now `ImportError` only |
| Paper SELL-before-BUY (prior O1) | **CLOSED** | `sort_rows_sell_before_buy` shared in `simulate_core` path |
| Partial-write fills vs state (prior O2) | **CLOSED** | `live_day_commit` deferred fills + atomic state |

**Overall:** Live Soft-Frozen + broker gates remain healthy. Path3 flip-carve stack is correctly LIVE WIRED and fail-closed on missing plan, but **ledger SSOT is already behind tip** (silent stale mix) and **ops docs still advertise PREP/flag OFF** for paths that ACCEPT flipped ON — same class of governance drift fixed on 2026-09-12.

---

## Findings

### P0 — Sticky tip-`flip` after flip day (fixed this pass)

- **Where:** `scripts/live_path3_t0_switch_emitter.py` `switch_meta_for_asof`
- **Bug:** Matched latest `date <= asof` and reused raw `flip=True`. If signal tip ended on a flip, every later asof kept `flip=True` → re-emit `-P3T0` + Soft mute every session.
- **Evidence:** tip flip `2026-06-12` → asof `2026-06-13`/`2026-06-17` still `flip=True` (repro). Live tip today was non-flip (latent).
- **Fix:** `flip` only when matched row date **equals** asof; expose `signal_date` / `signal_exact`. Test: `Path3SwitchMetaExactFlip`.
- **Source:** [Live broker Path3 safety](bc-dc17798f-3c90-5b25-b16e-7bd3fdc731c1)

### P1 — Path3 daily ledger / signal freshness (silent nearest-prior)

- **Where:** `scripts/path3_comp_sat_daily_share_ssot.py` `shares_asof` · outputs `…/daily_shares_*.meta.json` `end=2026-09-24` · tip may be ahead
- **Bug/risk:** After ledger/signal end, plans still succeed via nearest-prior — **no `ledger_stale` / `signal_stale` reason**. Combined with pre-fix sticky flip = landmine.
- **Action:** Refresh ledger on tip catch-up; add meta stale-days; optional e21/QC warn if `asof - tip > N` sessions.

### P1 — Mute hole on flip + empty/failed Path3 plan

- **Where:** `live_soft_path3_coexist_mute.should_mute` · default `MUTE_SOFT_FIN_TEL`
- **Risk:** Flip + `delta_shares` empty/`None` (ledger miss / empty recon) → mute skips → Soft FIN/TEL Exact T+1 still emit. `MUTE_SOFT_ON_FLIP_META` would mute; live policy does not.
- **Action:** Charter/ballot to strengthen policy, or fail-closed Soft FIN/TEL on flip whenever emit ON.
- **Source:** [Live broker Path3 safety](bc-dc17798f-3c90-5b25-b16e-7bd3fdc731c1)

### P1 — COMP/SAT recon quality fail-open

- **Where:** `live_path3_t0_weight_engine.py` empty eligible → all FIN; overlay bools default True
- **Risk:** Missing buy_ok/hard150 forces moves / weakens HARD.
- **Action:** Prefer fail-closed empty delta + reason when asof_b path used; document for ledger path (mix-based).

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

### P2 — No e21 orchestration test for Path3+mute+ledger

- **Where:** `tests/test_path3_*` · `tests/test_soft_path3_coexist_mute.py` · no `test_e21_path3_*`
- **Gap:** Unit paths pass in isolation; day order Soft→mute→Path3 append untested end-to-end.
- **Action:** Thin harness: stub Soft rows + flip signal + ledger mock → assert FIN/TEL Soft muted · `-P3T0` tagged · 0050 Soft kept.

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

---

## Recommended next (not this PR)

| Pri | Item |
|---|---|
| 1 | Refresh Path3 daily share ledgers through tip; add stale meta/QC |
| 2 | Mute policy on flip+empty Path3 plan (coexistence hole) |
| 3 | Paper dual for 0kac `WITHIN_SLEEVE_PATH3` → `PAPER_WITHIN_HIT` |
| 4 | e21 Path3+mute+ledger orchestration unit test |
| 5 | Close residual Sept-12 O3/O4/O5 when next ops touch |

---

## Non-actions

- No broker ACCEPT · no Path3 strategy cutover live flag  
- No Soft clip / CONF α flip · no tip history rewrite  

## Verification

```bash
PYTHONPATH=scripts python3 -c "from live_config import LIVE; assert LIVE.broker_live_write_accepted is False; assert LIVE.live_path3_weight_engine_mode=='ledger'; assert LIVE.live_soft_path3_coexist_mute is True"
PYTHONPATH=scripts python3 -m unittest tests.test_path3_t0_weight_engine tests.test_soft_path3_coexist_mute tests.test_path3_daily_share_ssot tests.test_broker_safety -q
```
