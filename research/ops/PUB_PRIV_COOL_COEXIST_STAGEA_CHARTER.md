# 公股＋民營並存 under COOL_c8 — Paper Charter (Stage A)

Date: 2026-09-25  
Status: **PAPER CHARTER OPEN** · Stage A **RUNNING**  
Parent live: `COOL_c8_f50_d21` LIVE (replace DH, keep FUSE) · Soft-Frozen tip **KEEP**  
Why reopen: prior `PUB_PRIV_COEXIST_MDD` **STOP** (0 sealed-MDD coexist) was **before** live COOL defense.

Label: `PUB_PRIV_COOL_COEXIST_STAGEA_CHARTER_2026-09-25__PAPER_OPEN__NO_LIVE_WIRE`

## Problem

Live stack = **公股 FIN + TEL + 0050** + FUSE + **COOL_c8**.  
Human: with COOL now live, re-test whether **公股金 + 民股金 + 電信 + 0050** can raise CAGR while MDD improves or holds flat.

Prior STOP (2026-09-19): tip/held often OK; **sealed MDD↑ 0/24** — every priv-bearing book worsened sealed MDD vs `LIVE_PUB_KD`.

## New mechanism context (not retune-after-peek)

Frozen **`COOL_c8_f50_d21`** PROXY circuit on each paper book (same recipe as live).  
This is a **new defense layer** absent from the STOP screen — justifies Stage A reopen under this charter only.

## Non-actions

- Soft-Frozen live membership / tip history rewrite  
- Live e21 universe expand from Stage A  
- Soft∥Sleeve Gate H auto-fuse  
- Broker live-write  
- DH re-enable / stack DH+COOL  

## Baseline / topology

| ID | Role |
|---|---|
| `BASE_PUB_KD_COOL` | 公股 Soft-Frozen + KD_OPT + TEL + COOL (**primary** coexist base) |
| `BASE_FUSE_COOL` | Live twin FUSE+COOL (**report-only** stretch) |

Target image (paper): FinPub R1 · FinPriv R3R4 · TEL · 0050.

## Stage A mechanism (finite)

**A — dollar-split** `FIN_DUAL_PUB_PRIV` + COOL:

| Axis | Values |
|---|---|
| `pub_share` | `{0.90, 0.85, 0.80, 0.75}` |
| FinPriv within | `{EQUAL, KD_OPT}` |
| FinPub within | `KD_OPT` frozen |
| Defense | `COOL_c8` frozen |

Optional compact **B — 4-sleeve** small FinPriv boxes only if A yields ≥1 near-miss (charter allows B follow-on; Stage A script may include a tiny B grid).

Books: Stage-E DEFAULT · capital 500M · lot 1000 · Exact T+1.

## Coexist gates (predeclared)

Vs **`BASE_PUB_KD_COOL`** (all required):

1. tip YTD + 1y CAGR gates PASS  
2. tip YTD + 1y MDD↑ ≥ **−0.5 pp**  
3. heldout MDD↑ ≥ 0  
4. sealed MDD↑ ≥ 0  
5. heldout CAGR giveback ≤ **3.0 pp**  
6. `score_mdd > 0` where  
   `score_mdd = MDD↑_held + 0.5·MDD↑_sealed − 0.25·max(0, CAGR_gb_held_pp)`

**CAGR lift stretch** (not required for coexist): held CAGR ≥ base (giveback ≤ 0).

## Verdicts

| Verdict | Meaning |
|---|---|
| `COOL_COEXIST_HIT` | ≥1 book clears all coexist gates |
| `HELD_ONLY` | held MDD OK + tip OK; sealed still fails |
| `NO_COEXIST` | no book clears gates (COOL insufficient) |

Even HIT → paper observe ballot only; live universe expand needs dedicated ACCEPT.

## Artifacts

- EN/ZH charter · screen · decision pack  
- Script: `scripts/e16_pub_priv_cool_coexist_stagea.py`  
- Repro: `repro/pub-priv-cool-coexist-stagea/`

## Label

`PUB_PRIV_COOL_COEXIST_STAGEA_CHARTER_2026-09-25__PAPER_OPEN__NO_LIVE_WIRE`
