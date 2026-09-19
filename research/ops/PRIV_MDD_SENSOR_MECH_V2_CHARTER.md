# 民股／四類 × MDD — New Mechanism V2 Charter（跨資產／廣度感測器）

Date: 2026-09-19  
Status: **CHARTER ACCEPTED → S1+S2 Stage A STOP** (`STAGE_A_SCORE_POS_GATES_FAIL` — V2 sensor ladder exhausted under sealed MDD)  
Class: **A. Research / EXPERIMENTAL** · Soft-Frozen / live e21 flip = **Class D** later only  
Parent STOP: N1–N3 ladder exhausted · `PRIV_MDD_NEW_MECH_N3_DECISION_PACK.md` · S1 STOP · `PRIV_MDD_SENSOR_S1_DECISION_PACK.md`  
Human: **「ACCEPT S2（USDTWD／CBC）」** (2026-09-19)

**Passing ≠ Soft-Frozen flip ≠ live e21 rewrite ≠ merge `#257`.**  
**≠ retune N1–N3 FinPriv-local DD / rel-60d / three-state thresholds.**

---

## 0. Why V2 (not N1–N3 retune)

| Ladder | Best sealed MDD↑ | Binding fail |
|---|---:|---|
| N1 FinPriv sleeve DD / rel → OFF | −0.25 | sealed |
| N2 FinPriv → cash/0050 | **−0.04** (tip fail) | sealed + tip |
| N3 three-state | −0.37 | sealed |

All used **FinPriv self-path sensors** (sleeve DD / vs FinPub). Heldout often improved; **sealed 2023+** did not clear ≥ 0.

Freeze reopen: **new mechanism** (**≠** N1–N3 retune) **or** sealed-gate change.  
This charter = **new sensor family** · sealed gate **unchanged**.

---

## 1. What is **not** V2 (WON’T)

| Forbidden | Why |
|---|---|
| Re-grid N1 LOCAL/REL thr · N2 sink thr · N3 mid/high | Ladder retune |
| Re-grid SF4 FinPriv clip / `prior_priv_frac` / `pub_share` | Prior STOP grids |
| TAIEX DD ∈ {−8%, −10%} as **sole** search on same frozen cell | SF4 defence exhausted pairing |
| Soften sealed MDD↑ ≥ 0 | Explicitly rejected this turn |
| Priv-replace / merge `#257` / live e21 | Freeze |

---

## 2. Frozen pieces (reuse, do not retune)

| Piece | Value |
|---|---|
| Offense topology | `SF4_P60-90_V0-15_F10_KD` |
| Baseline | `LIVE_PUB_KD` |
| Preferred sink (from N2 autopsy) | FinPriv → **0050** (ETF hi **0.35**; overflow cash) when sensor fires |
| Optional contrast sink | FinPriv → **cash** (report-only arm, same sensors) |
| Sealed / heldout / tip coexist gates | **Identical** to `PUB_PRIV_COEXIST_MDD_CHARTER` |

---

## 3. New mechanism — sensor ladder S1 → S2

Execute in order. Each needs a paper pack before the next.

### S1 — Cross-section / relative **market** sensors (Stage A authorize when ACCEPT)

Trigger **lag-1** (no same-bar look-ahead). Fire → apply frozen **FinPriv→0050** relocate (N2 sink, not N1 pub-only path).

| Sensor id | Definition (from `load_market()` only) | Fire (predeclared) |
|---|---|---|
| `S1_BREADTH_SMA120` | Soft-Frozen FIN∪TEL names: share with `adj_close > SMA120` | `(1 − breadth) ≥ {0.45, 0.55}` |
| `S1_FINPUB_TAIEX_Z` | `x = log(FinPub_EW / TAIEX)`; 60d z-score of Δx | `z ≤ {−1.0, −1.5}` |
| `S1_OR_MID` | OR of mid cells only | breadth≥0.45 **or** z≤−1.0 |

**Why new:** sensors are **market breadth / FinPub-vs-TAIEX**, not FinPriv sleeve NAV DD or FinPriv–FinPub 60d relative (N1–N3).

Controls: `LIVE_PUB_KD` · `SF4_OFFENSE` · `N2_0050_LOCAL_08_REF` (prior closest sealed) · `SF4_L4_08_REF`.

Compact Stage A: 2+2+1 = **5** sensor books × sink **0050** (+ optional 2 cash contrasts at mid cells only if runtime allows — default **0050-only**).

### S2 — Macro proxies (**ACCEPT** — this ballot)

From repo CSVs (no new download). Fire **lag-1** → FinPriv→**0050**.

| Sensor | Source | Fire (predeclared) |
|---|---|---|
| `S2_USDTWD_Z` | `data/def_proxies/USDTWD_finmind.csv` | 60d log-ret z ≥ {**1.0**, **1.5**} |
| `S2_CBC_HIKE` | `data/def_proxies/cbc_rediscount_rate_daily.csv` | 63d Δ rediscount **> 0** |
| `S2_OR_MID` | OR mid | FX z≥1.0 **or** CBC hike |

S1 pack exists (STOP) — S2 authorized.

---

## 4. Objective (unchanged)

```
score_mdd = MDD↑_heldout + 0.5 × MDD↑_sealed − 0.25 × max(0, CAGR_giveback_heldout_pp)
```

**Coexist** (all required): tip_clean · tip_mdd_ok (≥ −0.5 pp) · heldout MDD↑ ≥ 0 · **sealed MDD↑ ≥ 0** · giveback ≤ 3.0 · `score_mdd > 0`.

---

## 5. Governance locks

| Lock | State |
|---|---|
| Soft-Frozen 公股 + FUSE + DH | **KEEP** |
| `#257` | **FROZEN** |
| Sealed gate | **unchanged** |
| N1–N3 | **STOP archive** — reference only |

---

## 6. Stage A ladder

### S1 — DONE / STOP
`PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sensor_s1_stage_a.py` · `PRIV_MDD_SENSOR_S1_DECISION_PACK.md`

### S2 — ACCEPTED (this ballot)
```bash
PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sensor_s2_stage_a.py
```
→ `PRIV_MDD_SENSOR_S2_STAGE_A.{md,json}` + decision pack.

---

## Refs

- Parent: `PRIV_MDD_NEW_MECHANISM_CHARTER.md` · N1/N2/N3 decision packs  
- Sensor precedent: `research/e45/E45_NEW_MECHANISM_CHARTER.md` · `E45_M1_STATE_VECTOR_V0_FROZEN.md`  
- Freeze: `LIVE_CUTOVER_BUNDLE_257_FROZEN.md`  

Label: `PRIV_MDD_SENSOR_MECH_V2_CHARTER_2026-09-19__S1S2_DRAFT`
