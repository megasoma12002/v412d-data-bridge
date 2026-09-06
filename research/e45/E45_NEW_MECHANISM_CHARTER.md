# E45 Successor — Paper-Only New-Mechanism Charter (M1 → M2 → M3)

Date: 2026-09-06  
Status: **PAPER CHARTER OPEN** — Soft-Frozen **KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · live stitch **FORBIDDEN** · HIGH_BETA observe **DRAFT / NOT OPEN**  
Parent honesty: `E45_MULTI_EVENT_THRESHOLD_CHARTER.md` · `E45_NONCOVID_MULTIEVENT_ALT_LEVERS.md` · `E45_COVID_EX_HELDOUT_KPI.md`  
Claimed MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** — do not invent a replacement

## 0. Why this charter exists

The target claim is:

> **Non-2020 crisis help that is material, and CAGR giveback that stays small.**

Evidence on the **existing E45 family** (constant mild α, sleeve densify, crisis-gate, mild `max_cut`, TEL/FIN+0050 densify, E1 binary) does **not** support that claim:

| Finding | Binding read |
|---|---|
| Crisis MDD help is **2020-concentrated** (~84–99% depending on book) | Do not sell “all-crisis shield” |
| Strict non-COVID multi-event qualifiers | **0** |
| COVID-ex held-out least-bad still **negative** | No positive COVID-ex challenger in E45 family |
| Same-knob densify / gate / max_cut | **Exhausted** — not the next research path |

Therefore next work must be a **new mechanism**, not another twist of E45 exposure intensity / sleeve / gate.

`SLEEVE_FIN_ONLY_A10` (and cheap-protect × cost packs) remain valid as **tax-control observe / paper references**. They are **not** evidence that the KPI above is solved.

---

## 1. Governance locks (non-negotiable)

| Lock | State |
|---|---|
| Soft-Frozen FIN clip `[0.50, 0.95]` | **KEEP** |
| Live DEFAULT `E22_v2s_tw` | **KEEP** |
| E45 live stitch | **FORBIDDEN** until second human stitch ACCEPT |
| HIGH_BETA observe | **DRAFT / NOT OPEN** (unchanged by this charter) |
| Existing observe sleeves | **Unchanged** by this charter alone |
| Invented replacement for the retired MDD narrative | **Forbidden** |

This charter authorizes **paper research only**. It does **not** open Soft-Frozen, DEFAULT, stitch, or HIGH_BETA ballots.

---

## 2. Binding qualification rule (inherit + tighten)

Any M1/M2/M3 challenger that seeks a **dedicated OPEN-observe ballot** must pass **all** of:

### 2.1 Multi-event (from `E45_MULTI_EVENT_THRESHOLD_CHARTER`)

1. MDD help > **0.25 pp** vs BASE in **≥ 2** distinct years among `{2015, 2018, 2020, 2022}`.
2. Held-out score > **0** on `heldout_2019_plus`  
   `score = mdd_improve_pp − 0.5 · |cagr_giveback_pp|`.
3. Sealed score > **−1.0** on `sealed_2023_plus`.

### 2.2 Non-2020 honesty (this charter adds)

4. **Strict non-COVID multi-event:** MDD help > **0.25 pp** in **≥ 2** of `{2015, 2018, 2022}`  
   (**2020 may help, but must not be the only helper**).
5. **COVID-ex held-out score > 0** on `heldout_2019_plus` with calendar-2020 removed (same score formula).  
   Rationale: block “2020 carries the product” packaging.

### 2.3 Cost realism

6. At fee multiples **1× and 2×** (scale `BUY_FEE, SELL_FEE, SLIP, TAX_STOCK, TAX_ETF`), held-out score remains **≥ 0** and MDD help remains **> 0**.

Fail any of 1–6 → **no OPEN-observe ballot** from that challenger.

---

## 3. Mechanism ladder (execute in order 1 → 2 → 3)

Do **not** skip ahead. Each stage needs a paper pack (script + `research/e45` MD/JSON + `research/ops` pointer) before the next stage opens.

### M1 — New state-signal family (replace the sensor)

**Problem M1 solves:** E45-like vol/crisis compression fires on 2020-style liquidity shocks; it is weak or harmful on 2018/2022-style rate / valuation / breadth shocks.

**In scope**

| ID | Deliverable |
|---|---|
| M1.1 | Define a **non-E45 state vector** from available series only (no paid TEJ/Bloomberg required for v0): e.g. TW rates / curve proxy, TWD FX stress, market breadth (advance/decline or limit-down count if available), credit/proxy spread if available, valuation z if available |
| M1.2 | Map state → **risk-off intensity** `s_t ∈ [0,1]` with **frozen** transform (no walk-forward retune inside sealed) |
| M1.3 | Apply `s_t` as book exposure scale **or** sleeve scale on BASE early-stack (Exact T+1); E45 may be **absent** or used only as a **nested ablation**, not the primary engine |
| M1.4 | Report multi-event + COVID-ex + cost-× tables vs BASE and vs `BLEND_E45_A05` / `SLEEVE_FIN_ONLY_A10` references |

**Out of scope for M1**

- Retuning frozen E45 `E3_VOLTARGET_WINNER` / Soft-Frozen clip  
- Crisis-gate on E45 α (already failed)  
- Live stitch / Soft-Frozen flip  

**M1 pass (to unlock M2 design rights)**

- At least one M1 challenger clears **§2 rules 1–6**, **or**
- Documented failure with a clear “signal family insufficient on TW stack” autopsy (then M2 may still proceed with **external hedge sleeve**, because M2 does not require M1 pass)

**M1 default if stuck:** publish failure autopsy; do **not** quietly densify E45 α again.

---

### M2 — Cash / defensive sleeve relocation (replace the actuator)

**Problem M2 solves:** Scaling equity exposure ≤1 cuts risk but often taxes CAGR every calm day. A dedicated **destination sleeve** (cash / short-duration / defensive ETF proxy) can move weight **to** a hedge leg instead of only shrinking equities.

**In scope**

| ID | Deliverable |
|---|---|
| M2.1 | Define paper **DEF sleeve** instrument set (cash proxy and/or short-rate / defensive ETF available in `live_market` / approved paper proxies — document each proxy’s honesty limits) |
| M2.2 | Weight-relocation rule: when risk-off intensity rises, move weight from equity sleeves → DEF (sum-to-one), Exact T+1 fills, cost-× stress |
| M2.3 | Ablations: (a) equity-shrink-only (E45-like), (b) relocate-to-DEF, (c) hybrid |
| M2.4 | Same §2 KPI tables; emphasize CAGR giveback vs M1/E45 references |

**Out of scope for M2**

- Buying live options / OTC hedges  
- Changing Soft-Frozen sleeve weights in production  
- Treating DEF proxy as risk-free without stating tracking error  

**M2 pass (to unlock M3)**

- Relocate-to-DEF beats equity-shrink-only on COVID-ex held-out score **and** meets §2.2 rule 4 **or** 5, **or**
- Failure autopsy shows DEF proxy data too weak → charter amendment required before M3

---

### M3 — Three-state risk machine (replace continuous mild overlay)

**Problem M3 solves:** Continuous mild overlay pays tax on calm days. Sparse deep gates (already tested on E45) failed. Need a **small discrete state machine** with enter/exit rules that are frozen and auditable.

**States (v0)**

| State | Intent | Typical action (paper) |
|---|---|---|
| `NORMAL` | Earn risk premium | Full BASE equity policy (no E45 tax) |
| `SLOW_BEAR` | Grind / rate / valuation stress | Partial relocate to DEF and/or modest equity scale |
| `CRASH` | Breadth/liquidity shock | Strong relocate / hard equity scale floor |

**In scope**

| ID | Deliverable |
|---|---|
| M3.1 | Enter/exit rules from M1 state vector (hysteresis required — no single-day flicker) |
| M3.2 | Per-state action table (exposure / DEF weight) frozen before sealed eval |
| M3.3 | Compare vs continuous M1/M2 overlays on §2 KPIs + turnover |
| M3.4 | Pause/giveback diagnostics on trailing YTD/1y (observe-style gates as **diagnostics only**) |

**Out of scope for M3**

- Promoting state machine to Soft-Frozen / live without separate ballots  
- Using sealed window to retune enter/exit thresholds  

**M3 pass**

- Clears full §2 (rules 1–6) **and** COVID-ex held-out score ≥ continuous M2 challenger  
- Else: fail closed; keep observe E45 sleeves as tax-control references only

---

## 4. Shared paper protocol

### 4.1 Stack

- Exact T+1 early-stack BASE (`E16` Soft-Frozen + Exact T+1 + `E22_v2s_tw` as configured at call site)  
- Import windows from `e45_paper_harness.WINDOWS_STANDARD` (`heldout_2019_plus`, `sealed_2023_plus`, …)  
- Cost multiples: `{0,1,2,3}` for stress; qualification uses **1× and 2×** (§2.3)

### 4.2 Required artifacts per stage

| Artifact | Path pattern |
|---|---|
| Regenerator | `scripts/e45_m{1,2,3}_*_paper.py` (must use `e45_paper_harness`) |
| Research note | `research/e45/E45_M{1,2,3}_*.md` + `.json` |
| Ops pointer | `research/ops/E45_M{1,2,3}_*.md` |
| Repro | `repro/e45-m{1,2,3}-*/` |

### 4.3 Required scoreboard columns

Book · mechanism stage · window · cost × · `mdd_improve_pp` · `cagr_giveback_pp` · `score` · years helped (2015/2018/2020/2022) · COVID-ex held-out score · turnover/yr · fees

### 4.4 Reference books (always include)

- `BASE_E16_E18_E22_v2s`  
- `BLEND_E45_A05`  
- `SLEEVE_FIN_ONLY_A10` (observe OPERATING id — reference only; do not imply this charter opens anything)

---

## 5. Explicit non-actions

1. Do **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots from this charter alone.  
2. Do **not** densify E45 mild-α / crisis-gate / mild-`max_cut` as a substitute for M1–M3.  
3. Do **not** claim multi-crisis protection from 2020-only MDD help.  
4. Do **not** invent a replacement for the retired MDD narrative.  
5. Do **not** rewrite e21 primary from Phase C `0050` C1 spikes (prefer adj_close / C2 + quarantine).  
6. Do **not** auto-OPEN observe for any M1/M2/M3 challenger without a **dedicated human ballot** after §2 pass.

---

## 6. Exit matrix

| Outcome | Action |
|---|---|
| M1 clears §2 | Paper promote note + optional human ballot draft for **paper observe** only |
| M1 fails, M2 still viable | Proceed M2 with documented M1 autopsy |
| M2 relocate beats shrink-only on COVID-ex | Proceed M3 |
| M3 clears §2 | Dedicated OPEN-observe ballot draft (stitch still FORBIDDEN) |
| All stages fail §2 | Close ladder as **mechanism search failed on current data**; keep E45 cheap-protect observe as tax-control only; Soft-Frozen KEEP |

---

## 7. Immediate next step (authorized by this charter)

**Start M1 paper pack only:**

1. Freeze v0 state-vector definition + transform (write before running sealed metrics).  
2. Implement Exact T+1 paper screen vs BASE / A05 / sleeve-A10.  
3. Emit §2 scoreboard including COVID-ex + cost ×.  
4. Stop for human read before M2.

Label: `E45_NEW_MECHANISM_CHARTER_M1M2M3_2026-09-06__PAPER_ONLY__STITCH_FORBIDDEN`
