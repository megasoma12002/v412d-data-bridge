# Kelly Criterion Exposure Overlay — Stage A Charter (paper)

Date: 2026-09-13  
Status: **PAPER CHARTER OPEN** · Stage A screen **NOT STARTED**  
Soft-Frozen **KEEP** · live **`KD_OPT` KEEP** · **`TEL_EQUAL` KEEP** · E45 stitch **OFF** (`DROP_E45_A05`)  
Soft-assist / Sleeve-tilt / FUSE_ADDITIVE / BLEND_025 / priv / **DH_dd06** observes **UNCHANGED**

Ballot label: `KELLY_EXPOSURE_STAGEA_CHARTER_2026-09-13__PAPER_OPEN__NO_LIVE`

## Why

Repo has **never** used Kelly Criterion for sizing. Live sizing is fixed rules (Soft-Frozen clips · `TEL_EQUAL` · optional discrete exposure shrinks).  
Ask: can a **fractional Kelly book-level exposure** overlay tip-clean beat or coexist with paper `LIVE_STACK`, without touching clips or within-sleeve alloc?

This is **not** dry-powder cash reserve, **not** Soft-Frozen Class D clip search, **not** TEL weight Kelly, **not** E45 defend-handoff fusion.

## Contact point（接點）— freeze

| Choice | Decision |
|---|---|
| **Primary actuator** | `kelly_exposure_t ∈ [f_lo, f_hi]` scales the **whole paper book** after Soft-Frozen + `KD_OPT` + `TEL_EQUAL` targets (same plumbing family as `e45_exposure`) |
| **In scope** | Book-level long-only exposure scale only |
| **Out of scope (Stage A)** | Soft-Frozen FIN/TEL/0050 **clip bound** changes · replacing `TEL_EQUAL` / `KD_OPT` with per-name Kelly weights · cash dry-powder sleeve · levered `f>1` · shorting · fusing with `DH_dd06` / Soft / Sleeve / FUSE |

Rationale: exposure overlay is the lowest blast-radius Kelly slot that reuses existing Exact T+1 exposure hooks and keeps Soft-Frozen governance intact.

## Edge / odds estimate（edge 怎麼估）— freeze

Use the **continuous growth-optimal** proxy (log-utility / GBM Kelly):

\[
f^\*_t = \frac{\hat\mu_t}{\hat\sigma^2_t}
\]

where \(\hat\mu_t,\hat\sigma^2_t\) are **causal** rolling estimates on **daily simple returns** (Exact T+1; no peek).

| ID | Edge source (causal) |
|---|---|
| `EDGE_LIVE_ROLL` | Paper `LIVE_STACK` twin daily returns (primary) |
| `EDGE_0050_ROLL` | `0050` adj-close daily returns (**sensitivity row only**; report separately) |

| Knobs | Finite Stage A values |
|---|---|
| Lookback \(W\) | **63 · 126 · 252** trading days |
| \(\hat\mu_t\) | mean of prior \(W\) daily returns ending \(t\) (signal for \(t{+}1\) trade) |
| \(\hat\sigma^2_t\) | sample variance of same window (ddof=1); if &lt; ε → treat as undefined |
| Sign / floor | If \(\hat\mu_t \le 0\) **or** variance undefined → set raw \(f^\*_t = 0\) (then floor via clip below) |
| Annualization | **None** — use daily μ/σ² consistently (equivalent ratio to annualized form) |

No discretionary edge; no walk-forward hyperfit beyond the finite grid below.

## Fraction（Kelly fraction）— freeze

| Symbol | Stage A freeze |
|---|---|
| Full Kelly | **Forbidden** in Stage A (`κ=1.0` not in grid) |
| Fraction \(κ\) | **`{0.25, 0.50}`** only (¼ Kelly · ½ Kelly) |
| Hard clip | \(e_t = \mathrm{clip}(κ · f^\*_t,\ f_{lo},\ f_{hi})\) |
| \(f_{lo}\) | **0.50** (never below half-book in Stage A) |
| \(f_{hi}\) | **1.00** (never lever above full book) |
| Apply | Multiply sleeve/book target notional by \(e_t\) in Exact T+1 sim (residual stays cash) |

Optional report-only diagnostic (not a promote gate): distribution of raw \(κ f^\*\) before clip.

## Live baseline (do not modify)

| Layer | Live / paper twin |
|---|---|
| Soft-Frozen | FINBAND **[0.60, 0.90]** · TEL **[0.03, 0.35]** · 0050 **[0.00, 0.35]** |
| FIN within-sleeve | **`KD_OPT`** |
| TEL / 0050 | **EQUAL** |
| Books / capital / lot | `E22_v2s_tw` · 500M · board-lot 1000 |
| E45 | stitch **OFF** |

Baseline book: paper **`LIVE_STACK`** (`e45_exposure=None` · `kelly_exposure=None` ≡ 1.0).

## Finite Stage A screen

Grid (cap):

- Edge family: `EDGE_LIVE_ROLL` (required) + optional `EDGE_0050_ROLL` sensitivity  
- \(W ∈ \{63,126,252\}\) · \(κ ∈ \{0.25,0.50\}\)  
- Primary challengers ≤ **6** (`LIVE` edge × 3W × 2κ) + baseline  
- Sensitivity `0050` rows ≤ **6** (report-only; do not drive promote)  
- Total Stage A books ≤ **~13**

Per book report: full / `heldout_2019_plus` / `sealed_2023_plus` **CAGR + MDD**; tip YTD + trailing 1y vs live; held-out score vs live (same formula as peer screens); mean/p50/p10 of \(e_t\).

| Verdict | Meaning |
|---|---|
| `KELLY_PROMOTE_SHAPED` | tip-clean **and** held-out score > 0 vs `LIVE_STACK` **and** tip YTD/1y MDD not worse than base |
| `COEXIST_NO_LIFT` | tip-clean but held-out score ≤ 0 |
| `NO_LIFT` | no tip-clean challenger (or all fail hygiene) |
| `ESTIMATE_UNSTABLE` | raw \(f^\*\) hits clip bounds &gt;80% of days **and** no tip-clean lift (autopsy label) |

Even `KELLY_PROMOTE_SHAPED` → **paper observe ballot only**; **never** live wire from this charter.

## Hard locks（硬鎖）

1. **No Soft-Frozen clip flip** (Class D needs dedicated ballot + evidence unrelated to this charter).  
2. **No live** KD_OPT / TEL_EQUAL / Soft-assist / Sleeve / FUSE / BLEND_025 / priv / E45 / DH wire.  
3. **No Soft∥Sleeve ops auto-fuse** (Gate H unchanged).  
4. **No E45 stitch reopen** · no undo of `DROP_E45_A05`.  
5. **No fusion** of Kelly exposure with `DH_dd06_vz1p0` / Soft / Sleeve / FUSE in Stage A (separate books only).  
6. **No full Kelly** · **no \(f_{hi}>1\)** · **no shorts**.  
7. **No open search** beyond the finite grid; expanding \(W\)/κ/`f_lo` needs a new charter amendment.  
8. Exact T+1 · causal only · no invented payment/announce dates.

## Design honesty

- Daily μ/σ² is a **noisy** edge; fractional Kelly + hard clip is mandatory because raw \(f^\*\) often ≫ 1.  
- Floor \(f_{lo}=0.50\) biases against “go to cash” Kelly; if Stage A fails on MDD, Stage B may amend floor **only** under a new ballot (not auto).  
- Distinct from dry-powder (`w_powder` cash idle) and from E45 defend SHRINK (event window). Do not re-interpret a prior `NO_LIFT` archive as Kelly evidence.

## Artifacts (Stage A)

| Role | Path |
|---|---|
| Charter (EN) | `research/ops/KELLY_EXPOSURE_STAGEA_CHARTER.md` (this file) |
| Charter (ZH) | `research/ops/KELLY_EXPOSURE_STAGEA_CHARTER.zh-TW.md` |
| Machine stub | `research/ops/KELLY_EXPOSURE_STAGEA_CHARTER.json` |
| Screen script (next) | `scripts/e16_kelly_exposure_stagea_screen.py` |
| Results (next) | `research/ops/KELLY_EXPOSURE_STAGEA_SCREEN.md` (+ `.json`) |
| Repro (next) | `repro/kelly-exposure-stagea/` |

## Next authorized action

Implement + run **Stage A paper screen only** per this freeze.  
Do **not** open observe, cutover, or live wire until Stage A verdict + dedicated human ballot.

## Label

`KELLY_EXPOSURE_STAGEA_CHARTER_2026-09-13__PAPER_OPEN__NO_LIVE`
