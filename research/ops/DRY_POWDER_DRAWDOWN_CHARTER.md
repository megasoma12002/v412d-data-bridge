# Dry-Powder Drawdown Sleeve — Research Charter (paper)

Date: 2026-09-10  
Status: **PAPER DONE / STOP** (Stage A `NO_LIFT` — 0 tip-clean challengers · 0 coexist · live KEEP)  
Human: **「乾粉 10% + 組合／大盤回撤門檻進場 + 固定出場」vs 現況 live，看 tip／heldout／sealed，而不是「等 MDD」**  
Soft-Frozen **KEEP** · live **KD_OPT KEEP** · **TEL_EQUAL KEEP** · E45 stitch **OFF** · Soft-assist observe **unchanged**  
Screen: `DRY_POWDER_DRAWDOWN_SCREEN.md` · script `scripts/e16_dry_powder_drawdown_screen.py`

## Question

Does reserving **~10% dry powder**, deploying it on **observable drawdown gates** (portfolio and/or TAIEX), then exiting on **fixed rules**, tip-clean beat or coexist with the **current live stack**?

**Not in scope:** waiting for “maximum drawdown” (unknowable ex ante).

## Live baseline (do not modify)

| Layer | Live |
|---|---|
| Soft-Frozen | FINBAND **[0.60, 0.90]** · TEL **[0.03, 0.35]** · 0050 **[0.00, 0.35]** |
| FIN within-sleeve | **`KD_OPT`** (`KD_APR15_MAY15_Klt30_T15`) |
| TEL / 0050 | EQUAL |
| Books / capital / lot | `E22_v2s_tw` · 500M · board-lot 1000 |
| E45 | stitch **OFF** |

Paper challenger = **same live stack** + dry-powder overlay (or equivalent sleeve-weight schedule). Comparison books must report **full / heldout_2019_plus / sealed_2023_plus** CAGR+MDD and tip YTD+1y vs live.

## Mechanism (paper)

### Sleeve / cash

- Hold **`w_powder = 0.10`** of NAV in **cash or near-cash proxy** (default: cash in Exact T+1 sim; optional DEF/`0050` sensitivity later).
- Remaining **0.90** follows **live Soft-Frozen + KD_OPT + TEL_EQUAL** renormalized onto the investable sleeve (Soft-Frozen clips still applied on the traded book).

### Entry (observable only)

Trigger when **either** (screen both; report separately):

| Gate id | Signal (causal) |
|---|---|
| `PORT_DD` | Live-stack paper NAV peak-to-trough drawdown ≤ **−D%** |
| `TAIEX_DD` | TAIEX adj close peak-to-trough drawdown ≤ **−D%** |
| `PORT_OR_TAIEX` | either fires |
| `PORT_AND_TAIEX` | both fire |

Finite **D** grid (paper): **8% · 10% · 12% · 15%** (no “historical MDD” target).

On trigger: deploy dry powder into **Financial equal / KD_OPT tilt / Soft-Frozen cand** — pick one deploy mode per book; default **`DEPLOY_FIN_EQUAL`** among Soft-Frozen FIN names (simplest). Optional sensitiviies: deploy into full Soft-Frozen target weights.

### Exit (fixed)

Finite exits (one primary per book; no discretionary “take profit when feels good”):

| Exit id | Rule |
|---|---|
| `HOLD_N` | Hold deployed sleeve **N** trading days then flatten powder back to cash (**N ∈ {20, 40, 60}**) |
| `RECOVER_HALF` | Exit when NAV recovers **50%** of the trigger drawdown depth |
| `RECOVER_FULL` | Exit when NAV makes new peak vs pre-trigger peak |
| `TIME_OR_HALF` | earlier of `HOLD_40` and `RECOVER_HALF` |

No overlapping redeploy until powder is flat again (one powder lot at a time).

## Design honesty

- Cash drag in bull regimes is expected; gate must beat live on **risk-adjusted / tip-clean** terms, not only MDD cherry-picks.
- Distinct from E45 crisis exposure (different actuator). Do **not** re-open E45 stitch from this charter.
- Distinct from Soft-assist (within-sleeve scores). May **later** combine only under a new ballot after both coexist.

## Finite Stage A screen

1. Baseline: `LIVE_STACK` (FINBAND + KD_OPT + TEL_EQUAL).  
2. Challengers: `w_powder=0.10` × gate family × D × exit (cap **≤ ~40 books** for Stage A; expand only if tip-clean lift appears).  
3. Report per book: full / heldout / sealed **CAGR + MDD**; tip YTD+1y giveback vs live; held-out score vs live (same formula as other screens).  
4. Verdict labels: `NO_LIFT` · `COEXIST_NO_LIFT` · `BEATS_LIVE` · `NEAR_NO_BEAT`.

## Gates

| Gate | Rule |
|---|---|
| Tip | YTD + trailing 1y vs live: PASS (ALERT 3pp / PAUSE 5pp giveback) |
| Coexist | tip-clean **and** held-out score > 0 vs live baseline |
| Beat-live | coexist **and** held-out score > live self-score (Δ>0) |
| Sealed | report-only for Stage A (do not require sealed beat to OPEN observe) |

## Artifacts (Stage A)

| Role | Path |
|---|---|
| Charter | `research/ops/DRY_POWDER_DRAWDOWN_CHARTER.md` (this file) |
| Screen script | `scripts/e16_dry_powder_drawdown_screen.py` |
| Results | `research/ops/DRY_POWDER_DRAWDOWN_SCREEN.md` (+ `.json` · `.zh-TW.md`) |
| Repro | `repro/dry-powder-drawdown/` |

## Stage A outcome (2026-09-10)

- Grid: 3 gates × D∈{10%,12%,15%} × 4 exits = **36** challengers + `LIVE_STACK` (**37** books).
- Verdict: **`NO_LIFT`** — **0** tip-clean challengers · **0** coexist · **0** beat-live.
- Cash drag dominates: held-out scores all **&lt; 0** (best ≈ −0.57); most books tip **PAUSE_REVIEW**.
- Next: **STOP / archive** unless human expands grid (e.g. D=8%, HOLD_20/60, `PORT_AND_TAIEX`). **No live wire.**

## Non-actions

- No Soft-Frozen clip flip  
- No live KD_OPT / TEL change  
- No E45 stitch  
- No Soft-assist live wire from this charter  
- No “wait until max DD” books  
- No invent payment/announce dates  

## Out of scope

- Optimizing powder % beyond {0.10} in Stage A (optional Stage B: 0.05 / 0.15 if Stage A tip-clean)  
- Levered entries / shorts  
- Replacing Soft-Frozen regime router  

## Success → next step

If Stage A shows tip-clean beat-live or strong coexist → draft **OPEN observe** ballot (dual-paper `LIVE_STACK` ∥ champion).  
Else → **STOP** / archive; keep live unchanged.

**Applied:** Stage A → **STOP / archive**; live unchanged.

## Label

`DRY_POWDER_DRAWDOWN_CHARTER_2026-09-10__PAPER_DONE_STOP__NO_LIFT__LIVE_KEEP`
