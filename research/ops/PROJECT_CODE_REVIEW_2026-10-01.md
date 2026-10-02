# Project Code Review — 2026-10-01

Scope: tip Soft Exact T+1 **LIVE_OVERRIDE** LIVE WIRE (#404 / `50560a24`) + coexistence with Path3 `WITHIN_SLEEVE` + broker / Exact T+1 safety after tipsoft stack merge (0kb0–0kb5 → ACCEPT wire).  
Soft-Frozen FIN **[0.60, 0.80]** KEEP · Exact T+1 KEEP elsewhere · Path3 WITHIN **ON** · tip Soft LIVE_OVERRIDE flag **ON** · broker **false** · Path4 **OFF**

Priors: `PROJECT_CODE_REVIEW_2026-09-29.md` · ballot `TIPSOFT_IP3_LIVE_OVERRIDE_BALLOT_EXECUTED_ACCEPT.md`

Label: `PROJECT_CODEREVIEW_2026-10-01__TIPSOFT_OVERRIDE_STAMPS_FIXED__GATE_STALE_FAILLOUD`

---

## Verdict (post-fix)

| Area | Grade | Notes |
|---|---|---|
| Broker live-write fail-closed | **HEALTHY** | `broker_live_write_accepted=False` · tipsoft does not touch broker path |
| Soft-Frozen / Exact T+1 | **HEALTHY** | No same-bar fill change from tipsoft wire |
| Path3 WITHIN Soft FIN/TEL OFF | **HEALTHY** | Cutover KEEP · tipsoft does not re-enable Soft FIN/TEL |
| tip Soft LIVE_OVERRIDE flag | **LIVE WIRED (gate stamps / telemetry)** | `wire_mode=gate_stamps_telemetry` · **no order-row blend** |
| Research OVERRIDE return blend on tip | **NOT REALIZED (explicit)** | `return_blend_applied=False` stamped · paper edge paper-only |
| Gate input freshness | **FAIL-LOUD when stale** | `market_tip` > panel tip → `reason=nav_stale` · `override_on=None` |
| Dual-paper observe SSOT vs ACCEPT | **ALIGNED** | Operating: live flag ON · stamps mode · cutover EXECUTED ACCEPT |
| tipsoft unit tests | **EXPANDED** | K-edge · lag-1 · stale/missing NAV · M05≡M0005 · mute KEEP · e21 invariant |

**Overall:** Broker / Path3 WITHIN / Exact T+1 remain safe. Wire is **observational gate stamps / telemetry**. Tip PnL still will **not** track dual-paper OVERRIDE NAV until a separate ACCEPT designs an apply path under Soft FIN/TEL OFF + Path3 WITHIN KEEP.

---

## Runtime: what the wire does (after fix)

1. `LIVE.live_tipsoft_live_override=True` (SSOT flag + ballot text).
2. `live_tipsoft_live_override.session_meta(asof, market_tip=…)` computes causal lag42/M0.5%/K3 gate; fail-loud on stale NAV panel.
3. `e21_forward_pipeline` spreads **flattened** meta into **signals** after order construction — **does not mutate `order_rows`**.
4. `live_tip_meta.build_cutover_stamps` stamps `wire_mode` + LIVE-derived coexistence (broker / Path3 / Path4).

Path3 WITHIN still suppresses Soft FIN∪TEL daily; Soft 0050 / clips / T0 carve / Path3 ledger unchanged.

---

## Findings disposition

### H1 — “LIVE WIRED” ≠ research OVERRIDE return blend — **FIXED this pass**

- Ops / module / stamps now say **gate stamps / telemetry**; `wire_mode=gate_stamps_telemetry`; `return_blend_applied=False`.
- Apply-path (research `r=where(conf,…)`) remains out of scope — separate ACCEPT.

### H2 — Gate inputs frozen at Stage A NAV tip — **FIXED this pass** (fail-loud)

- `compute_gate_state(..., market_tip=)` → `ok=False` · `reason=nav_stale` · `override_on=None` when tip ahead of panel.
- e21 passes `market_tip=latest`. Full live NAV rebuild still deferred (no silent nearest-prior freeze).

### H3 — “force LIVE Soft+FUSE+COOL shell” wording — **FIXED this pass**

- Stamp renamed `force_live_shell_diag`; docstring clarifies Soft FIN/TEL stay OFF under Path3 WITHIN.

### M1 — Nested gate dict in `signals.csv` — **FIXED this pass**

- Flattened: `tipsoft_override_on` / `_asof` / `_ok` / `_stale` / `_reason` / `_panel_tip`.

### M2 — Dual-paper observe SSOT drift — **FIXED this pass**

- OPERATING: live flag ON · stamps mode · cutover EXECUTED ACCEPT (observe KEEP).

### M3 — `M05` vs Stage A `M0005` naming — **FIXED this pass**

- `STAGE_A_ARM_ID=OVERRIDE_LIVE_W42_M0005_K3`; alias test locks observe NAV ≡ Stage A arm NAV.

### M4 — Safety stamps literals — **FIXED this pass**

- Derived from `LIVE` (Path3 cutover / broker / Path4 absence).

### M5 — Duplicate ballot fields on signal — **FIXED this pass**

- Dropped `tipsoft_live_override_ballot_text` / `policy_id`; SSOT via `session_meta` + `live_config`.

### M6 — `is_on()` broad except — **FIXED this pass**

- `ImportError` only.

### L1 — Unit tests thin — **FIXED this pass**

- Expanded: K-edge · lag-1 causal · stale/missing · M05 alias · Soft mute KEEP · e21 order invariant · broker false.

### L2 — Unused `numpy` — **FIXED this pass**

- Removed.

### L3 — `_trail_sum` min_periods drift — **FIXED this pass**

- Live matches research: `max(3, w // 3)`.

---

## Safety checklist (this pass)

| Constraint | Status |
|---|---|
| Broker false | **OK** |
| Path3 WITHIN KEEP | **OK** |
| Soft FIN/TEL stay OFF | **OK** (by Path3, not tipsoft) |
| Path4 OFF | **OK** |
| Exact T+1 | **OK** |
| Dual-paper observe KEEP | **OK** |
| No return-blend on tip orders | **OK** (stamped) |

---

## Remaining (not this pass)

1. Rebuild tip Soft live/champ NAV to market tip (H2 root) — fail-loud is in; refresh pipeline separate.
2. Apply path under Path3 WITHIN KEEP — Stage A **`APPLY_TIPY_OWNERSHIP_BLOCK`** (0kb6): tipY gap ≈ MUTE_S3_SAT vs always-WITHIN; force-LIVE/soft-α tipY≈0; **KEEP stamps**; no apply wire without new ACCEPT · `TIPSOFT_IP3_APPLY_PATH_STAGEA_DECISION_PACK.md`.

---

## Evidence index

- Merge: PR #404 · `50560a24`
- Fix branch: `cursor/tipsoft-override-wire-fix-b78a`
- Module: `scripts/live_tipsoft_live_override.py`
- Pipeline: `scripts/e21_forward_pipeline.py`
- Ballot: `TIPSOFT_IP3_LIVE_OVERRIDE_BALLOT_EXECUTED_ACCEPT.md`
- Prior: `PROJECT_CODE_REVIEW_2026-09-29.md`

Label: `PROJECT_CODEREVIEW_2026-10-01__TIPSOFT_OVERRIDE_STAMPS_FIXED__GATE_STALE_FAILLOUD`
