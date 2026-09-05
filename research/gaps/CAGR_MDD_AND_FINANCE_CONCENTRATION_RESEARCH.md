# CAGR / MDD Gap + Finance Concentration Research

Date: 2026-09-05  
Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no E16 prior retune in this PR.  
Repro: `scripts/gap_cagr_finance_concentration_research.py` → `repro/gap-cagr-finance-concentration/`

## Questions

1. How far is the **formal live core** from long-term targets (CAGR ≥20%, MDD ~10–15%)?
2. Is **~82% 公股金融** a temporary bull artifact, or structural to E16?
3. What research paths are still open given Stage-8 sleeve saturation?

---

## 1) Return / risk gap (measured)

Window for core books: **2012-12-04 → 2026-09-04** (`repro/e22-v2s-historical-recompute/summary.json`).

| Book | CAGR | MDD | Δ vs 20% CAGR | MDD deeper than 15% | Meets both? |
|---|---:|---:|---:|---:|---|
| E16+E18 no-div | 7.29% | −22.77% | **−12.7 pp** | **+7.8 pp** | No |
| E22_v2 cash-only | 11.25% | −22.11% | **−8.8 pp** | **+7.1 pp** | No |
| **E22_v2s formal (live books)** | **13.78%** | **−22.64%** | **−6.2 pp** | **+7.6 pp** | **No** |
| Paper CORE80+OVL20 stitch | 20.43% | −23.96% | +0.4 pp | **+9.0 pp** | **No** (MDD worse) |

Sources: E22 recompute summaries; paper stitch from `repro/gap5-6-continuation/outputs/paper_combined_mix_summary.csv`.

### Verdict on gap #1

- Formal core is **~6 pp CAGR short** and **~8 pp MDD too deep** vs targets.
- Accounting upgrades (E22 cash→stock) helped CAGR (~+2.5 pp vs cash-only) but **did not move MDD**.
- Paper overlay stitch can print ≥20% CAGR while **worsening** MDD — so “add overlay weight” is not a free MDD fix.
- **Parameter micro-tuning of E16/E18/E22 cannot close this.** Need a separate return engine **and** a separate loss engine (crisis budget / orthogonal sleeve), each gated.

---

## 2) Finance concentration (measured)

### Live mark (2026-09-04)

From `forward/e21/portfolio_state.json` × `live_market.csv` closes:

| Sleeve | Weight |
|---|---:|
| **Financial (2880/2886/2892/5880)** | **82.4%** |
| Telecom | 8.1% |
| 0050 | 7.6% |
| Cash | ~2.0% |

Signal target same day: `e16_financial ≈ 85.9%` (Bull).

### Structural E16 targets (2011-12-01 → 2026-09-04, n=3603)

Rebuilt causally via `scripts/e21_forward_pipeline.features` (same clips/priors as live):

| Metric | Financial weight |
|---|---:|
| Mean | **79.8%** |
| Median | **82.1%** |
| P10 / P90 | 66.2% / 88.1% |
| Share of days ≥70% | **83.6%** |
| Share of days ≥80% | **64.1%** |
| Min / Max | 58.0% / 91.9% |

Hard constraints in code (`scripts/e21_forward_pipeline.py`):

- Financial clip **[0.50, 0.95]** every day  
- Bull prior **0.85**, Crisis prior **0.60**, Bear 0.70, Sideways 0.85  

So ~82% finance is **by design**, not a 2026 accident.

### Co-movement / false diversifiers

Daily sleeve return correlations (same rebuild):

| Pair | Corr |
|---|---:|
| Financial–0050 | **0.59** |
| Financial–Telecom | 0.40 |
| Telecom–0050 | 0.24 |

**0050 is not an independent diversifier vs 公股金融** at the weight it usually gets (~8%).

During Financial sleeve drawdown ≤ −10% (355 days): mean weights ≈ Financial **65.7%** / Telecom **30.5%** / 0050 **3.8%**.  
Even in stress, finance stays the majority; “defense” is mostly rotating within the same three-sleeve router — not a true multi-factor book.

### Alpha-side note (C4 / TECH2)

`industry_cap=5` is a **name-count** limit (≤5 names per industry), then equal-weight.  
With `top_k=22` that caps *names* at ~23% of the sleeve **if** the industry fills the cap — it does **not** cap portfolio *weight* the way E16’s 82% finance weight is capped (E16 has no finance weight cap below 95%).

---

## 3) Prior research already tried (do not re-grid blindly)

| Line | Outcome | Implication |
|---|---|---|
| Stage-8 TECH2 stress / DEF / cash sleeves | **SATURATED** / MIXED_HELDOUT | No more TECH2 remix grids |
| Stage-8C multi-sleeve | MIXED; DEF weak on boot | Orthogonal residual (Track B S1) is the intended next family |
| Defensive ETF sleeve workstream | historically STOP’d / not live | Reopen only with new hypothesis + frozen charter |
| E45 crisis MDD −13.16% | **NOT_VERIFIED** | Cannot cite as live MDD fix |
| Dual-track A/B | A=S9A1 monitor; B=S1 residual OOF | Correct place to seek *orthogonal* stress alpha — still not live |

---

## 4) FIN_CAP follow-through (executed 2026-09-05)

Predeclared OOF challengers under E22_v2s books; selection **2011–2018 only**.

| Book | OOF CAGR | OOF MDD | Fin mean | MDDΔ vs BASE | CAGR giveback | OOF pass |
|---|---:|---:|---:|---:|---:|---|
| BASE_E16 | 8.85% | −17.41% | 0.802 | — | — | — |
| FIN_CAP_60 | 8.75% | −14.54% | 0.597 | +2.88 pp | 0.10 pp | **Yes** |
| **FIN_CAP_50** | 8.50% | **−12.84%** | **0.500** | **+4.57 pp** | 0.35 pp | **Yes (lock)** |

OOF decision: `OOF_FIN_CAP_PASS_READY_FOR_HELDOUT` → locked **FIN_CAP_50**.

One-shot held-out (2019+, no retune):

| | CAGR | MDD |
|---|---:|---:|
| BASE | 18.24% | −22.64% |
| FIN_CAP_50 | 16.60% | −19.58% |

- MDD improve **+3.06 pp**; CAGR giveback **1.63 pp**; finance max respects 0.50  
- Decision: **`PASS_HELDOUT_FIN_CAP`**

**Still not live.** Explicit promote PR required to change E16 clips; keep BASE ledger for comparison.  
Artifacts: `research/gaps/FIN_CAP_OOF.md`, `FIN_CAP_HELDOUT.md`, `repro/gap-cagr-finance-concentration/fin_cap_oof/`.

### Remaining research order

1. **Optional promote proposal** (separate PR): E16 Financial clip → [0.35, 0.50] cutover-only; dual paper ledgers.  
2. **Return gap**: dual-track B residual adv-lite (FIN_CAP does not close CAGR≥20%).  
3. **MDD≤15%**: still needs a separate loss engine — FIN_CAP_50 held MDD −19.6% improves vs −22.6% but **misses 15%**.  
4. **Won’t**: Stage-8 TECH2 re-grid; silent live prior edit; cite unverified E45 −13.16%.

---

## 5) Artifacts

| Path | Content |
|---|---|
| `scripts/gap_cagr_finance_concentration_research.py` | Concentration / gap regenerator |
| `scripts/e16_fin_cap_oof_challenger.py` | FIN_CAP OOF runner |
| `scripts/e16_fin_cap_heldout.py` | Locked FIN_CAP_50 held-out decision |
| `repro/gap-cagr-finance-concentration/outputs/*` | Live weights + E16 history stats |
| `repro/gap-cagr-finance-concentration/fin_cap_oof/` | FIN_CAP NAVs + OOF/held-out JSON |
| `research/gaps/FIN_CAP_OOF.md` / `FIN_CAP_HELDOUT.md` | Human memos |

## Label

`RESEARCH_CAGR_MDD_GAP_AND_FINANCE_CONCENTRATION__FIN_CAP50_PASS_HELDOUT__NO_LIVE_WIRE`
