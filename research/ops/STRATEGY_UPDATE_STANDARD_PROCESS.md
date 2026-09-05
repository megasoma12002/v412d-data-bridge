# Strategy Update — Standard Operating Process

Date: 2026-09-05  
Status: **BINDING process map** (docs only — does not flip Soft-Frozen)  
Live Soft-Frozen Financial clip: **[0.50, 0.95] KEEP** until a dedicated human cutover PR  

Authority chain (highest first):

1. `FROZEN_GOVERNANCE.md` — HARD / SOFT / EXPERIMENTAL classes  
2. `research/ops/HUMAN_DECISION_REGISTER.md` — live cutover verdicts  
3. `research/ops/LIVE_CLAIM_TARGET_POLICY.md` — what live may claim  
4. `research/STRATEGY_DEBT_BOARD.md` — Now / Next / Won’t  
5. This file — **how** to run an update without skipping gates  
6. Per-challenger cutover checklist — **whether** that challenger may cut over  

Research day-to-day order (hypothesis → held-out → …) remains in `E50_RESEARCH_OPERATING_RULES.md`.  
This file covers **strategy change classes → observe → cutover**, including ops-only and Soft-Frozen flips.

---

## 0. One rule

**Paper green ≠ live change.**  
Every live strategy update ends in a **dedicated human cutover PR** that quotes an all-green checklist. Nothing else (month-end pack, dual-paper PASS, CI green, agent recommendation) flips live.

---

## 1. Classify the change first

Pick **exactly one** primary class before writing code.

| Class | Examples | Live blast radius | Default path |
|---|---|---|---|
| **A. Research / EXPERIMENTAL** | New weight, threshold, router, alpha | None | Charter → paper only |
| **B. Paper sleeve / observe** | Dual-paper FIN50, L4, BLEND_025 | None (ledgers parallel) | Observe runbook + month-end |
| **C. Ops / data / tooling** | Shadow QC, failover helper, KPI, alert | None if e21 default unchanged | Resilience / ops charter |
| **D. Soft-Frozen parameter flip** | Financial clip band change | **High** | Register re-open + cutover PR only |
| **E. Live path / books cutover** | Wire L4 DD-path, BLEND weights, FIN50 clip, E22 books change | **High** | Checklist all YES + human PR |
| **F. HARD_FROZEN challenge** | Weaken Exact T+1 / PIT / embargo | Forbidden as “perf fix” | New governance version only |

If a PR mixes classes (e.g. FIN50 clip + L4 DD-path), **split it**. Bundling is a reject reason on every cutover checklist.

---

## 2. Stage pipeline (do not skip)

```
0 CLASSIFY
   │
1 CHARTER          (A/B/E usually; C if multi-step; D/E always cite register)
   │
2 IMPLEMENT PAPER  (challenger code + repro artifacts; Soft-Frozen untouched)
   │
3 VALIDATE         (OOS / held-out / sealed / costs / stress — per E50 rules)
   │
4 OBSERVE          (dual-paper or monitor sleeve; month-end pack; alerts)
   │
5 DECISION GATE    (HUMAN_DECISION_REGISTER re-open trigger must fire)
   │
6 CUTOVER CHECKLIST all YES
   │
7 HUMAN CUTOVER PR (single class; quotes checklist + fresh evidence)
   │
8 POST-CUTOVER     (live QC smoke; claim policy update; register amend)
```

**Exit ramps (normal, not failure):**

| After stage | Allowed stop |
|---|---|
| 3 VALIDATE fail | STOP or new challenger (do not retune same lock) |
| 4 OBSERVE PAUSE | Stay observe; no cutover talk |
| 5 Register says REJECT / DEFER | Do not open cutover PR |
| 6 Checklist red | Stay prep-only |

---

## 3. Stage contracts (artifacts + owners)

### Stage 1 — Charter

**Required artifact:** `research/gaps/<NAME>_CHARTER.md` (or ops charter under `research/ops/`).

Must state:

- Soft-Frozen **KEEP** (unless this charter *is* a Soft-Frozen flip proposal)  
- In scope / out of scope / WON’T  
- Pass / fail / stop criteria  
- Explicit “passing ≠ live cutover”

**Owner:** research or ops agent OK to draft; human accepts by merge of charter PR if novel live-facing work.

### Stage 2–3 — Implement + validate

Follow `E50_RESEARCH_OPERATING_RULES.md` §2–§6.

Hard constraints:

- No rewrite of `forward/e21` history  
- No silent edit of Soft-Frozen constants (`scripts/e16_soft_frozen_base.py` / Soft-Frozen single source)  
- EXPERIMENTAL must not auto-promote  
- Held-out used for tuning → new challenger id  

**Artifacts:** `repro/<slug>/`, research notes, sealed / held-out reports.

### Stage 4 — Observe

Minimum for any candidate that might later cut over:

| Piece | Requirement |
|---|---|
| Dual-paper or named monitor | Ledgers + month-end script |
| Month-end pack wire | `ops_month_end_paper_pack` step |
| Alert scan | INFO/HIGH codes; never auto-cutover |
| Claim labeling | PAPER / RESEARCH only (`LIVE_CLAIM_TARGET_POLICY`) |

Current sleeves:

| Sleeve | Observe docs | Cutover checklist |
|---|---|---|
| FIN_CAP_50 | FIN50 month-end + go-live verify | `CUTOVER_CHECKLIST_FIN50.md` |
| L4_DD_PATH | L4 month-end | `CUTOVER_CHECKLIST_L4.md` |
| BLEND_025 | BLEND dual-paper + month-end runbook | `CUTOVER_CHECKLIST_BLEND025.md` (**NOT AUTHORIZED**) |

### Stage 5 — Decision gate

Only `HUMAN_DECISION_REGISTER.md` re-open triggers restart a live agenda.

Examples already binding (2026-09-05):

| Topic | Re-open only when |
|---|---|
| Soft-Frozen flip | Explicit human cutover PR (never pack green alone) |
| FIN50 static | Verify **not** `NOT_READY_SEALED_CAGR` **and** Gate E clean |
| L4 live | ≥1 clean month-end (no YTD/1y PAUSE) + L4 checklist all YES |
| BLEND → live | Sustained clean trailing **and** checklist authorized + human PR |
| E45 / odd-lot / tax books | New charter accepted |

Ops waits that are **not** strategy votes: grow live sessions (~60), post-forward E22 evidence, calendar month-end.

### Stage 6–7 — Checklist + cutover PR

Checklist file must be **prep-complete** before PR; PR body must paste gate table with **all YES** and attach fresh JSON/MD evidence (≤ current month-end pack age).

**Cutover PR shape (mandatory):**

1. Title starts with `Cutover:` and names the single class (D or E)  
2. Links register row + checklist label  
3. Soft-Frozen / live path change is the **only** strategy diff  
4. Forbidden bundle: other challengers, history rewrite, claim badge without post-QC  
5. CI green is necessary, not sufficient  

### Stage 8 — Post-cutover

Within one weekday forward cycle:

1. `e21_qc` / live QC smoke PASS  
2. Update `LIVE_CLAIM_TARGET_POLICY` if a numeric live badge is newly authorized  
3. Amend `HUMAN_DECISION_REGISTER` (old KEEP → new live fact)  
4. Update `OPS_STATUS` + `STRATEGY_DEBT_BOARD` snapshot  
5. Run live↔paper recon; note thin history if still short  

Rollback = another human PR (same process, inverse change) — no silent revert.

---

## 4. Worked paths (current fleet)

### Soft-Frozen KEEP (steady state)

No strategy update. Operate: weekday forward → QC → month-end pack → alerts.  
Claims: stack + clip only; **no** CAGR/MDD live badges.

### BLEND_025 (sole sealed-CAGR successor today)

```
CHARTER/screen DONE → dual-paper OBSERVE (#65 path) → sustained trailing
→ register #5 re-open → CUTOVER_CHECKLIST_BLEND025 all YES
→ human PR Soft-Frozen → BLEND weights → post-QC + claim update
```

Today: stop at OBSERVE. Checklist exists but **NOT AUTHORIZED**.

### L4 DD-path

```
Held-out PASS → dual-paper OBSERVE → clean month-end (no PAUSE)
→ register #4 re-open → CUTOVER_CHECKLIST_L4 all YES → human PR
```

Today: DEFER (YTD/1y PAUSE_REVIEW).

### FIN50 static clip

```
Go-live verify must clear sealed CAGR → Gate E clean
→ register #2 re-open (currently REJECT) → CUTOVER_CHECKLIST_FIN50
→ human PR clip [0.50,0.95]→[0.35,0.50]
```

Today: **REJECT for now**. Do **not** retune the locked FIN50 definition; successor research goes BLEND / new charter.

### Ops / data (e.g. resilience Phase A–C)

```
Ops charter → implement shadows/helpers (e21 default unchanged)
→ KPI + pack + alert wire → DONE when probes PASS
```

Runtime primary switch (e.g. TAIEX Yahoo as e21 default) is class **E**, not C — needs its own cutover PR.

### New alpha / E45 / odd-lot default

```
New charter accepted (register #6) → full A→H pipeline
```

No charter → **DEFER** (do not “just paper it into live”).

---

## 5. Forbidden shortcuts

| Shortcut | Why banned |
|---|---|
| Agent / CI auto-merge cutover | Live blast radius; register requires human |
| Treat dual-paper or held-out PASS as promote | Explicit in every checklist |
| Soft-Frozen constant edit inside an observe PR | Silent live change |
| Retune FIN50 lock after sealed fail | Structural fail → new charter / successor |
| Bundle L4 + FIN50 + BLEND in one PR | Ambiguous rollback; checklists forbid |
| Claim live CAGR/MDD from paper prints | `LIVE_CLAIM_TARGET_POLICY` |
| Rewrite `forward/e21` to “fix” history | Governance + audit chain |
| Re-open Goodinfo/Wantgoo/CMoney as backups | Resilience WON’T |
| Skip month-end because “research already PASS” | Trailing risk is the live residual |

---

## 6. Operator checklist (copy into PR / issue)

```markdown
## Strategy update intake
- [ ] Class A/B/C/D/E/F named (single primary)
- [ ] Soft-Frozen KEEP asserted OR this is an explicit flip charter
- [ ] Charter path linked (or N/A with reason for pure C)
- [ ] Validate artifacts linked (repro + sealed/held-out as required)
- [ ] Observe sleeve wired (month-end + alerts) if cutover-candidate
- [ ] HUMAN_DECISION_REGISTER row: KEEP / OBSERVE / DEFER / REJECT / re-open?
- [ ] Cutover checklist path + all gates YES (only if opening Cutover: PR)
- [ ] Claim policy: no live target badge until Stage 8
- [ ] No forbidden bundle / no e21 history rewrite
```

---

## 7. Maintenance

- When a new challenger sleeve is added: create observe runbook + `CUTOVER_CHECKLIST_<NAME>.md` (start **NOT AUTHORIZED**) and link here §4.  
- When register verdicts change: update §4 “Today” lines in the same PR as the register.  
- This SOP does not replace per-challenger numeric gates; it only sequences them.

## Label

`STRATEGY_UPDATE_STANDARD_PROCESS_2026-09-05`
