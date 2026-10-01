# Project Code Review — 2026-10-01

Scope: tip Soft Exact T+1 **LIVE_OVERRIDE** LIVE WIRE (#404 / `50560a24`) + coexistence with Path3 `WITHIN_SLEEVE` + broker / Exact T+1 safety after tipsoft stack merge (0kb0–0kb5 → ACCEPT wire).  
Soft-Frozen FIN **[0.60, 0.80]** KEEP · Exact T+1 KEEP elsewhere · Path3 WITHIN **ON** · tip Soft LIVE_OVERRIDE flag **ON** · broker **false** · Path4 **OFF**

Priors: `PROJECT_CODE_REVIEW_2026-09-29.md` · ballot `TIPSOFT_IP3_LIVE_OVERRIDE_BALLOT_EXECUTED_ACCEPT.md`

Label: `PROJECT_CODEREVIEW_2026-10-01__TIPSOFT_OVERRIDE_STAMPS_ONLY__OPS_DRIFT`

---

## Verdict

| Area | Grade | Notes |
|---|---|---|
| Broker live-write fail-closed | **HEALTHY** | `broker_live_write_accepted=False` · tipsoft does not touch broker path |
| Soft-Frozen / Exact T+1 | **HEALTHY** | No same-bar fill change from tipsoft wire |
| Path3 WITHIN Soft FIN/TEL OFF | **HEALTHY** | Cutover KEEP · tipsoft does not re-enable Soft FIN/TEL |
| tip Soft LIVE_OVERRIDE flag | **LIVE WIRED (stamps)** | Gate + session stamps ON · **no order-row blend** |
| Research OVERRIDE return blend on tip | **NOT REALIZED** | Paper held +1.61 / tipY +6.04 still paper-only |
| Gate input freshness | **STALE RISK** | Frozen Stage A NAV CSVs tip **2026-09-29** |
| Dual-paper observe SSOT vs ACCEPT | **DRIFT** | Operating docs still `live_wire: false` / cutover BLOCKED |
| tipsoft unit tests | **THIN** | 5 tests · no pipeline order-invariant / K-edge / Stage A parity |

**Overall:** Broker / Path3 WITHIN / Exact T+1 remain safe — this wire is observational. Main risk is **governance false confidence**: “LIVE WIRED” language overstates mechanism vs research `OVERRIDE_LIVE_W42` return blend. Tip PnL will **not** automatically track dual-paper OVERRIDE NAV until an order-level (or sleeve) apply path exists under Soft FIN/TEL OFF constraints.

---

## Runtime: what #404 actually does

1. `LIVE.live_tipsoft_live_override=True` (SSOT flag + ballot text).
2. `live_tipsoft_live_override.session_meta(asof)` computes causal lag42/M0.5%/K3 gate from **frozen research NAV CSVs**.
3. `e21_forward_pipeline` spreads meta into **signals** after order construction — **does not mutate `order_rows`**.
4. `live_tip_meta.build_cutover_stamps` adds flag/ballot/rollback (no live gate nested dict).

Path3 WITHIN still suppresses Soft FIN∪TEL daily; Soft 0050 / clips / T0 carve / Path3 ledger unchanged.

---

## Findings

### H1 — “LIVE WIRED” ≠ research OVERRIDE return blend on live orders

- **Where:** `scripts/e21_forward_pipeline.py` (~401–406, ~505) · `scripts/live_tipsoft_live_override.py`
- **Issue:** Research Stage A sets `r = where(conf, live_r, champ_r)`. Live wire never switches sleeves, mutes Path3, or blends books when `override_on`.
- **Effect:** Ops/register imply paper edge (held +1.61 / tipY +6.04) is live; tip will not track `nav_OVERRIDE_LIVE_W42_M05_K3.csv`.
- **Action:** Either (a) rename ops language to **gate stamps / telemetry LIVE WIRED**, or (b) design apply path under Soft FIN/TEL OFF + Path3 WITHIN KEEP (separate ACCEPT).

### H2 — Gate inputs frozen at Stage A NAV tip 2026-09-29

- **Where:** `live_tipsoft_live_override.py` `DEFAULT_*_NAV` → `repro/tipsoft-ip3-*/outputs/nav_*.csv`
- **Issue:** After market tip advances, `asof` falls back to nearest prior panel date → gate freezes on last research bar. No refresh hook / alert.
- **Evidence:** `compute_gate_state()` → `asof=2026-09-29`, `override_on=False`, hist ~7.28%.
- **Action:** Plumb live tip Soft NAV rebuild (or dual-paper ledger refresh) into gate; fail-loud when `asof` < market tip.

### H3 — “force LIVE Soft+FUSE+COOL shell” wording vs Soft FIN/TEL stay OFF

- **Where:** module docstring · `force_live_shell` stamp
- **Issue:** Describes a shell switch that cannot exist under Path3 WITHIN ACCEPT (Soft FIN/TEL OFF explicit).
- **Action:** Rename stamp to `force_live_shell_diag` / clarify Soft residual-only; ballot non-action already honest — stamps should match.

### M1 — Nested gate dict in `signals.csv`

- **Where:** `session_meta` → `tipsoft_live_override_gate` dict spread into signal
- **Issue:** pandas may stringify nested dict; `override_on` not a first-class column. `portfolio_state` stamps omit gate.
- **Action:** Flatten `tipsoft_override_on` / `tipsoft_override_asof` top-level; JSON-serialize nested if kept.

### M2 — Dual-paper observe SSOT still says wire false / cutover BLOCKED

- **Where:** `TIPSOFT_IP3_LIVE_OVERRIDE_DUAL_PAPER_OBSERVE_OPERATING.md/.json` (+ repro copies)
- **Issue:** Post-ACCEPT docs claim `live_wire: false` · cutover BLOCKED — same landmine class as 2026-09-29 PREP drift.
- **Action:** Stamp OPERATING as observe KEEP + live flag ON (stamps); cutover EXECUTED ACCEPT.

### M3 — `M05` vs Stage A `M0005` naming

- **Where:** policy id `…_M05_K3` vs arm `OVERRIDE_LIVE_W42_M0005_K3`
- **Risk:** `M05` readable as margin 0.05; files match today but no test locks identity.
- **Action:** Alias test: observe NAV ≡ Stage A arm NAV; document margin=0.005.

### M4 — Safety stamps are literals, not live assertions

- **Where:** hardcoded `path4_live=False`, `broker=False`, `soft_fin_tel_stay_off=True`
- **Issue:** Do not read `LIVE.broker_live_write_accepted` / Path3 cutover state.
- **Action:** Optional assert-or-stamp from LIVE; true safety remains in broker/Path3 modules (OK).

### M5 — Duplicate ballot fields on signal

- **Where:** `tipsoft_live_override_ballot` vs `tipsoft_live_override_ballot_text` / policy_id
- **Action:** Single SSOT field from `live_config`.

### M6 — `is_on()` broad `except Exception: return False`

- **Where:** `live_tipsoft_live_override.py`
- **Risk:** Import/config errors look like “override off”.
- **Action:** Narrow to `ImportError` / log.

### L1 — Unit tests thin

- Missing: order_rows invariant with flag ON; Soft FIN/TEL still muted when `override_on=True`; K-edge / lag-1 causal; Stage A mask parity; missing/stale NAV; broker stays false.

### L2 — Unused `numpy` import in `live_tipsoft_live_override.py`

### L3 — `_trail_sum` min_periods live `max(2,w//3)` vs research `max(3,w//3)` (w=42 → both 14 today)

---

## Safety checklist (this pass)

| Constraint | Status |
|---|---|
| Broker false | **OK** — tipsoft does not open broker |
| Path3 WITHIN KEEP | **OK** — Soft FIN/TEL still suppressed |
| Soft FIN/TEL stay OFF | **OK** (by Path3, not tipsoft) |
| Path4 OFF | **OK** (absence + stamp) |
| Exact T+1 | **OK** — no fill-clock change |
| Dual-paper observe KEEP | **Partial** — ledgers remain; operating SSOT drifted |

---

## Recommended next (priority)

1. **Clarify SSOT language** — stamps/telemetry LIVE WIRED vs return-blend LIVE WIRED (H1/H3/M2).
2. **Fresh gate inputs** — rebuild tip Soft live/champ NAV to market tip or fail-loud (H2).
3. **Flatten signal columns** — `tipsoft_override_on` first-class (M1).
4. **Pipeline invariant test** — flag ON ⇒ order_rows unchanged + Soft FIN/TEL still muted (L1).
5. Only if human wants paper edge on tip: separate ACCEPT for apply-path design under Path3 WITHIN KEEP.

---

## Evidence index

- Merge: PR #404 · `50560a24`
- Module: `scripts/live_tipsoft_live_override.py`
- Pipeline: `scripts/e21_forward_pipeline.py`
- Ballot: `TIPSOFT_IP3_LIVE_OVERRIDE_BALLOT_EXECUTED_ACCEPT.md`
- Prior: `PROJECT_CODE_REVIEW_2026-09-29.md`
- Gate probe (this review): asof 2026-09-29 · override_on False · hist 7.28%

Label: `PROJECT_CODEREVIEW_2026-10-01__TIPSOFT_OVERRIDE_STAMPS_ONLY__OPS_DRIFT`
