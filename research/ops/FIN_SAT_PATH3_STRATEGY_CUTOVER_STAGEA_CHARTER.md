# FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEA_CHARTER

Date: 2026-09-29  
Status: **Stage A CHARTER — Path3 strategy cutover (replace Soft as primary router?)** · Soft-Frozen clips **KEEP** pending ladder pick · Path3 emit/fill/ledger/mute **ON** (0ka7–0kab) · broker **false** · live cutover flag **OFF**  
Parents: 0kab ledger LIVE WIRED · 0kaa mute LIVE WIRED · 0ka9 Stage B · 0ka7 θ=0.005 T+0 · 0k9r carve · dual-paper COMP/SAT observe  
Register: **0kac**

## Question

Can live e21 **promote Path3 COMP↔SAT to the primary within-sleeve (or full Soft) router** — retiring Soft Exact T+1 FIN/TEL coexistence — with paper evidence that tip/held/sealed stay acceptable, **without** broker live-write and **without** expanding T+0 beyond `T0_CARVE_FIN_SAT_SWITCH`?

## Why this is open

Path3 is already **LIVE WIRED as a flip-day carve**, not as Soft's replacement:

| Layer | Today (post 0kaa/0kab) | Soft role |
|---|---|---|
| Soft 3-sleeve clips FIN/TEL/0050 | Soft-Frozen SSOT | **primary daily** |
| Soft Exact T+1 within-sleeve | `build_live_order_rows` | **primary daily** (FIN/TEL muted only on Path3 flip) |
| Path3 `-P3T0` | ledger-scaled recon on **flip only** | carve overlay |
| Soft mute | `MUTE_SOFT_FIN_TEL` on flip+hit | coexistence patch |
| COOL / FUSE / CONF_RET3 / FinPriv | overlays / satellites | KEEP |

So “Path3 strategy cutover” ≠ broker SendOrder. It means: **Path3 becomes the day-to-day book owner** (scope ladder below), Soft stops fighting it.

## Binding findings (pre-registered)

| Fact | SSOT |
|---|---|
| Flip-day Path3 + mute already ON | 0ka7 emit/fill · 0kaa mute · 0kab `mode=ledger` |
| Soft clips / Exact T+1 elsewhere KEEP | all Path3 ballots to date |
| Broker `broker_live_write_accepted=False` | `live_config` · separate track |
| Dual-paper COMP/SAT observe OPEN | 0k9b COMPOSITE · 0k9d SAT_RELAX · 0k9r Path3 observe |
| Sealed MDD −0.17pp ACCEPTABLE | `FIN_SAT_PATH3_T0_SEALED_MDD_DISPOSITION.md` |
| Wrong-stay / 2022 still known residual | 0ka5 · 0k9x — cutover must cite disposition |

## Scope ladder (Stage A must pick one default)

| Scope ID | Soft sleeve clips | Soft Exact T+1 FIN/TEL | Soft Exact T+1 0050 | Path3 ledger recon | Overlays |
|---|---|---|---|---|---|
| `FLIP_CARVE_ONLY` | KEEP | mute on flip only (**status quo**) | KEEP | flip only | KEEP |
| `WITHIN_SLEEVE_PATH3` (**default candidate**) | KEEP | **retire** (Path3 owns FIN∪TEL every day) | KEEP | **daily** toward active book | KEEP |
| `SLEEVE_AND_WITHIN_PATH3` | Path3 / dual-paper owns sleeve % too | retire Soft sleeve+within | Path3 or Soft 0050 TBD | daily | KEEP or re-home |
| `FULL_SOFT_REPLACE` | Soft router OFF | Soft orders OFF | Soft OFF | Path3 = sole Soft-universe router | re-home each overlay |

**Stage A default to evidence:** `WITHIN_SLEEVE_PATH3`  
— Soft clips + 0050 Exact T+1 + COOL/FUSE/CONF/FinPriv **KEEP**  
— Soft FIN/TEL Exact T+1 **OFF** when cutover flag ON  
— every session: recon live FIN∪TEL to active Path3 book via `P3_COMP_SAT_DAILY_POS_LEDGER_A` (flip or not)  
— non-flip days still emit tagged deltas if drift ≥ board lot (or L1 gate TBD)

`FLIP_CARVE_ONLY` = already LIVE WIRED → Stage A **not** a cutover HIT.  
`FULL_SOFT_REPLACE` = refuse unless separate overlay re-home charter.

## Mechanism ID: `PATH3_STRATEGY_CUTOVER`

### Proposed live flag (OFF until ACCEPT)

```text
LIVE.live_path3_strategy_cutover: bool = False
LIVE.live_path3_strategy_cutover_scope: str = "WITHIN_SLEEVE_PATH3"
```

When **True** + scope `WITHIN_SLEEVE_PATH3`:

1. Soft FIN/TEL Exact T+1 **not built** (stronger than flip mute).  
2. Soft 0050 Exact T+1 **KEEP**.  
3. Path3 `plan_or_none_for_pipeline` / ledger recon runs **daily** toward `book` from `P3_T0_STATE` (θ=0.005), not only on `flip`.  
4. Fill carve stays `T0_CARVE_FIN_SAT_SWITCH` for tagged `-P3T0`; Soft remainder Exact T+1.  
5. Mute flag becomes redundant under this scope (document as superseded-when-ON).  
6. Broker still false unless separate ACCEPT.

### Stage A method (paper — no live flag flip)

1. **Define** scope SSOT + checklist gates (this charter + `CUTOVER_CHECKLIST_PATH3_STRATEGY.md`).  
2. **Paper dual:** Soft status-quo tip vs `WITHIN_SLEEVE_PATH3` (daily ledger recon on Soft capital) over Path3 observe window.  
3. Metrics: tipY / held CAGR / sealed CAGR+MDD / yearly W–L / flip-day order count / non-flip drift trade rate.  
4. Compare to status-quo carve (flip-only + mute).  
5. Overlay coexistence smoke: COOL/FUSE/CONF still attach.  
6. **No** `live_config` cutover True in Stage A.

### Wire points (post-HIT ACCEPT only — not Stage A)

| File | Change |
|---|---|
| `scripts/live_config.py` | `live_path3_strategy_cutover` + scope + ballot |
| `scripts/live_path3_strategy_cutover.py` | NEW — daily book target / Soft FIN-TEL suppress |
| `scripts/e21_forward_pipeline.py` | Gate Soft FIN/TEL build; daily Path3 plan when flag ON |
| `scripts/live_path3_t0_weight_engine.py` | Optional `require_flip=False` path when cutover ON |
| tests | flag OFF = status quo · flag ON = Soft FIN/TEL empty · daily ledger deltas |

## Non-goals

- Broker `SendOrder` / `broker_live_write_accepted`  
- Soft clip densify / CONF α A10↔A20  
- Expanding T+0 carve beyond `T0_CARVE_FIN_SAT_SWITCH`  
- Tip history wipe / Soft tip rewrite  
- Auto-promote `FULL_SOFT_REPLACE` without overlay re-home  
- Closing COMPOSITE / SAT_RELAX observes without human disposition

## Verdict ladder

| Verdict | Meaning |
|---|---|
| `CUTOVER_SCOPE_DEFINED` | Charter+checklist+scope ladder locked · no live flag |
| `PAPER_WITHIN_HIT` | `WITHIN_SLEEVE_PATH3` paper tip/held/sealed acceptable vs carve status-quo |
| `PAPER_MDD_BLOCK` | sealed/held MDD fails gate |
| `PAPER_NO_EDGE` | daily Path3 ≤ flip-carve (no reason to cut over) |
| `SCOPE_AMBIGUOUS` | ladder disagreement — need human pick |
| `BLOCK` | would require broker / Soft clip flip / full Soft replace without re-home |

Stage A exit HIT = **`CUTOVER_SCOPE_DEFINED`** (definition pack).  
Paper HIT **`PAPER_WITHIN_HIT`** is Stage A+ / Stage B before any live ACCEPT.

## Accept posture (after paper HIT only)

```text
ACCEPT Path3 strategy cutover: WITHIN_SLEEVE_PATH3
(Soft clips+0050 Exact T+1 KEEP · Soft FIN/TEL Exact T+1 OFF · Path3 ledger daily ·
 T0_CARVE_FIN_SAT_SWITCH KEEP · broker false · overlays KEEP)
```

Broker remains a **separate** ballot.

## Label

`FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEA_CHARTER_2026-09-29__WITHIN_SLEEVE_PATH3__NO_BROKER`
