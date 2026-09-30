# Path3 strategy cutover — pre-ACCEPT disposition

Date: 2026-09-30  
Status: **PRE-ACCEPT DISPOSITION** · live cutover flag still **OFF** · Soft KEEP · broker **false**  
Parents: 0kac Stage A · **0kam** Stage B `PAPER_WITHIN_HIT` · sealed 0k9r · wrong-stay 0ka5 · 2022 0k9x · window 0ka6

Closes cutover checklist items that are **evidence-bound** before the human ACCEPT ballot. Does **not** flip `live_path3_strategy_cutover`.

## 1 — Paper HIT (0kam)

| Metric (WITHIN_DAILY − FLIP_CARVE) | Value |
|---|---:|
| held CAGR lift | **+3.0409** pp |
| tipY / tip1y | **+0.2679** / **+0.778** |
| sealed MDD improve | **+7.2414** pp |
| yearly ret W–L | **14–1** |

SSOT: `FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEB_DECISION_PACK.md` (PR `cursor/path3-cutover-paper-within-0d95`).

## 2 — Sealed MDD / tip / held vs Path3 observe baseline

| Source | Disposition |
|---|---|
| 0k9r sealed −0.17pp vs BASE | Human **ACCEPTABLE** (`FIN_SAT_PATH3_T0_SEALED_MDD_DISPOSITION.md`) |
| 0ka6 window pack | full/held/sealed CAGR↑ · sealed MDD −0.17ok · yearly **14–1** |
| 0kam WITHIN vs FLIP | sealed MDD **improves +7.24** · tipY **+0.27** · held **+3.04** |

**Cutover disposition:** sealed/tip/held gates **PASS** for `WITHIN_SLEEVE_PATH3` paper vs flip-carve status quo. Observe baseline sealed ACCEPTABLE remains binding for P3_T0_STATE observe.

## 3 — Wrong-stay / 2022 residual (0ka5 / 0k9x)

| Fact | SSOT |
|---|---|
| Wrong-stay **recurrent · θ-insensitive** | 0ka5 `WRONG_STAY_RECURRENT__THETA_INSENSITIVE` |
| Only **2022** is Path3 year-loss vs BASE (−0.75) | 0ka5 · 0k9x |
| 2022 drag = COMP stay miss (Mar + summer), not May–Jun whipsaw | 0k9x `COMP_STAY_MISS` |
| WITHIN vs FLIP **2022** ret lift **+1.94** pp (WITHIN wins) | 0kam yearly dual |

**Cutover disposition:** residual **KNOWN / ACCEPTABLE to proceed to ballot** — not a blocker for WITHIN_SLEEVE_PATH3. Does **not** close repair research (enter/confirm COMP stay remains paper track). Does **not** authorize θ retune.

## 4 — Overlay coexistence smoke (design)

Under scope `WITHIN_SLEEVE_PATH3`:

| Overlay / layer | Posture |
|---|---|
| Soft clips F/T/E | **KEEP** |
| Soft Exact T+1 **0050** | **KEEP** |
| Soft Exact T+1 FIN∪TEL | **retire** (Path3 owns daily) |
| COOL / FUSE / CONF_RET3 / FinPriv | **KEEP** (satellites attach to Soft remainder / sleeve) |
| Flip mute `MUTE_SOFT_FIN_TEL` | **superseded-when-ON** (no Soft FIN/TEL to mute) |
| T+0 carve | **narrow KEEP** `T0_CARVE_FIN_SAT_SWITCH` only |

**Smoke verdict:** `OVERLAY_DESIGN_COEXIST_OK` — no Soft FIN/TEL daily fight with Path3 under this scope. Full e21 dual-ledger smoke remains **EXECUTED-prep** (after ACCEPT, before/with wire), not a Stage B paper gate.

## 5 — Parent observes at cutover time

| Observe | Disposition at cutover ballot |
|---|---|
| COMPOSITE `COMP_H150_x_A20` (0k9b) | **KEEP OPEN** — independent dual-paper |
| SAT_RELAX (0k9d) | **KEEP OPEN** — independent |
| P3_T0_STATE (0k9r) | **KEEP OPEN** — cutover consumes daily Path3 book; observe ledger stays |

Cutover does **not** close parent observes.

## 6 — T+0 carve narrow confirm

`T0_CARVE_FIN_SAT_SWITCH` only · Soft remainder Exact T+1 · broker false. **Confirmed** for ACCEPT scope line.

## Binding non-actions

- No `live_path3_strategy_cutover=True` from this disposition alone
- No broker live-write
- No `FULL_SOFT_REPLACE` / Soft clip flip / CONF α change
- No Path4 Soft-0050 wire

## Next

Human ACCEPT ballot: `PATH3_STRATEGY_CUTOVER_ACCEPT_BALLOT_OPEN.md`

Label: `PATH3_STRATEGY_CUTOVER_PREACCEPT_DISPOSITION_2026-09-30__GATES_CITED__NO_LIVE`
