# Next-Step Research Plan (post Stage-1…7)

Date: 2026-09-04  
Branch: `cursor/e50a3r1-turnover-diagnosis-d049` (draft PR #19)  
Status: **planning + diagnosis only** — no new challenger locked; no promotion; E45 untouched.

## 1. What we already know (saturation map)

| Layer | Result |
|---|---|
| Portfolio rules C2/C4/C8 | `MIXED_HELDOUT` (sealed OK, val boot fail) |
| TECH2/PRICE8 × λ / family×regime / atomic F1 | No lasting held-out win; F1 worse on val boot |
| Horizon / orth / blend | No dual-gate winner |
| Risk overlays (static / mild cash) | MDD↓ but boot/CAGR tradeoff; R6B1 `MIXED_HELDOUT` |
| Crisis cash / defensive sleeve / crisis rebalance | No **crisis-profit** dual-gate winner |

User goal remains: **高獲利 + 低風險 + 即時換手 + 股災也賺**.  
Current sleeve (slow C4 + TECH2) cannot deliver that as one object.

## 2. New diagnosis (Stage-7 follow-up) — critical

Market crisis flags used in Stage-7 (**vote≥2** and **strict DD/vote3**):

| Window | vote2 crisis share | strict crisis share |
|---|---:|---:|
| OOF 2011–2018 | 13.8% | 12.1% |
| VAL 2019–2022 | 6.3% | 3.0% |
| **2021–2022 only** | **5.3%** | **1.0%** |

On C4 validation NAV, when those flags *do* fire, crisis-period excess is often **still positive**.

But the **13 shared C2/C4/C8 bad months** from Stage-3 autopsy have:

**crisis-flag coverage = 0.00 for every bad month (both defs).**

So the failure mode is **not** “classic EW crisis (deep DD / high vol / low breadth)” that E1-style overlays target.  
It is closer to: **RISK_ON / non-crisis market where TECH2 underperforms the proxy** (alpha drawdown, not market crash).

That is why Stage-7 cash/defensive overlays could not solve “股災也賺” for *this* book: we were controlling the wrong regime.

## 3. What NOT to do next

1. More TECH2 tilts / family recombinations / PRICE8 λ grids  
2. More static or crisis-cash overlays expecting crash-alpha  
3. Retune C2/C4/C8/F1/R6B1 after held-out looks  
4. Edit E45 in place, or promote 2.5% / 0.70 gates to “make it pass”  
5. Merge PR #19 as a production strategy

## 4. Recommended next iteration (Stage-8)

### Stage-8A — Failure-regime taxonomy (diagnosis, may inspect 2021–22)

**Question:** What observable *T-known* state marks the 13 bad months, if not EW crisis votes?

Candidates to measure (held-out diagnosis → then map to OOF analogs):

- Breadth/mom still RISK_ON while cross-sectional mom IC collapses  
- Factor crowding (top industry / top10 name gross)  
- Growth vs value / large vs small relative performance  
- Vol of cross-section (dispersion) not EW vol  
- Turnover/cost spikes vs excess

**Deliverable:** a short “failure signature” report + proposed **OOF-analog detector** (causal features only).  
No parameter lock from held-out.

### Stage-8B — OOF “alpha-stress” controller (selection)

Using only the **OOF-analog detector** from 8A (or a pre-registered variant):

| Challenger class | Idea |
|---|---|
| Soft de-risk | When signature on → exposure 0.85–0.90 (mild; Stage-6B style) |
| Sleeve switch | When signature on → quality/value/defensive score book (must beat baseline on that OOF stress set) |
| Skip-rebalance / freeze | When signature on → hold names, cut new mom adds |

**Pass rule (OOF):** dual gates + **stress-window excess ≥ baseline** (strict, like corrected 7B) + utility not wrecked.  
Then **one** held-out. No retune.

### Stage-8C — Only if 8B fails: escalate architecture

If no OOF dual-gate stress winner:

1. Treat E50-A TECH2+C4 as **bull-sleeve only** with documented failure mode  
2. Open a **separate E45-class / multi-sleeve portfolio challenger** under higher process bar (not in-place E45 edit)  
3. Optionally open an **EXPERIMENTAL fast-execution** track (reb≪42) as its own hypothesis — do not mix into crisis work until stress sleeve exists

## 5. Mapping to user goals

| Goal | Next lever |
|---|---|
| 高獲利 | Keep TECH2/C4 as risk-on engine; don’t dilute with blind cash |
| 低風險 | Need stress detector that hits **alpha failure**, not only EW crisis |
| 即時換手 | Defer until stress sleeve works; else conflicts with turnover gate |
| 股災／壞月也賺 | Stage-8A/B: control **bad-month signature**; classic crisis overlay was wrong tool |

## 6. Immediate action choice

**Best next move:** run **Stage-8A diagnosis** (failure signature of 13 bad months + OOF analogs), then **8B OOF screen** of controllers on that signature.

Do **not** start another Stage-7-like EW-crisis cash grid.

Artifacts to add alongside this plan when 8A runs:

- `E50-A3-R1_STAGE8A_FAILURE_SIGNATURE.md`  
- later `E50-A3-R1_STAGE8B_...` if detectors clear OOF screens
