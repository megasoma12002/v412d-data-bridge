# 民股／四類 × MDD — New Mechanism V3 Charter（M1 連續強度縮放 FinPriv）

Date: 2026-09-19  
Status: **CHARTER ACCEPTED → Stage A RUNNING** — Soft-Frozen **KEEP** · `#257` **FROZEN** · sealed gate **unchanged**  
Class: **A. Research / EXPERIMENTAL** · Soft-Frozen / live e21 flip = **Class D** later only  
Parents STOP: N1–N3 · `PRIV_MDD_NEW_MECH_N3_DECISION_PACK.md` · V2 S1–S2 · `PRIV_MDD_SENSOR_S2_DECISION_PACK.md`  
Human: **「ACCEPT V3 Stage-A」** (2026-09-19)

**Passing ≠ Soft-Frozen flip ≠ live e21 rewrite ≠ merge `#257`.**

---

## 0. Why V3 (not N1–N3 / V2 retune)

| Ladder | Actuator shape | Best tip-clean sealed↑ |
|---|---|---:|
| N1–N3 | FinPriv **self-DD** → binary OFF / reloc / 三態 | −0.20（L4 ref）／−0.25 |
| V2 S1–S2 | **Single-feature binary fire** → FinPriv→0050 | −0.42（breadth）／−0.48（FX） |
| Closest overall | N2_0050_LOCAL_08 | **−0.04**（**tip fail**） |

Pattern: binary on/off or fire→0050 improves heldout often; **sealed≥0 never clears**.

V3 changes the **actuator topology**:

> **Continuous** FinPriv weight scale by frozen **E45 M1 composite intensity** `s_t`  
> （多特徵平均，非 FinPriv self-path，非 V2 單感測二元觸發）

Sealed gate **unchanged**.

---

## 1. WON’T (explicit)

| Forbidden | Why |
|---|---|
| Re-grid N1 LOCAL/REL · N2 thr · N3 mid/high | Exhausted |
| Re-grid V2 breadth/FINZ/FX/CBC fire thr | Exhausted |
| Re-grid SF4 FinPriv clip / `prior_priv_frac` | Prior STOP |
| TAIEX L4 −8/−10 as sole search | Exhausted |
| Soften sealed MDD↑ ≥ 0 | Not authorized |
| Densify E45 α / stitch | Forbidden elsewhere |
| Merge `#257` / live e21 | Freeze |

---

## 2. Frozen pieces

| Piece | Value |
|---|---|
| Offense | `SF4_P60-90_V0-15_F10_KD` |
| Baseline | `LIVE_PUB_KD` |
| Sensor | **E45 M1 v0 frozen** `s_t` = mean(`R_DD`,`R_VOL`,`R_BREADTH`,`R_FINREL`,`R_SHOCK`) · `research/e45/E45_M1_STATE_VECTOR_V0_FROZEN.md` · implemented in `e45_m1_state_signal_paper.build_m1_state` |
| Lag | exposure uses **`s_{t-1}`** (Exact T+1 honesty) |
| Coexist gates | **Identical** to pub-priv MDD charter（sealed≥0 hard） |

---

## 3. New mechanism — proportional FinPriv dampener

On frozen offense targets, each day:

```
e_t = clip(1 − c · s_{t-1}, 0, 1)
FinPriv'_t = FinPriv_t · e_t
residual_t = FinPriv_t − FinPriv'_t
```

Residual routing (predeclared arms):

| Arm | Residual goes to |
|---|---|
| `V3_TO_0050` | 0050 up to Soft-Frozen ETF hi **0.35**; overflow cash |
| `V3_TO_CASH` | cash（sum&lt;1） |

**Intensity grid (Stage A — compact):** `c ∈ {0.25, 0.50, 0.75, 1.00}` × both arms → **8** books.

Controls: `LIVE_PUB_KD` · `SF4_OFFENSE` · `SF4_L4_08_REF` · `N2_0050_LOCAL_08_REF`.

**Why this is new**

| | V2 binary | V3 proportional |
|---|---|---|
| Sensor | one feature at a time | **frozen M1 composite** `s_t` |
| Actuator | fire → FinPriv **zero** then →0050 | FinPriv **scales** with `c·s` |
| State | 2-state | continuous exposure |

≠ N1 FinPriv-local DD path · ≠ N3 three discrete states · ≠ V2 fire thresholds.

---

## 4. Objective (unchanged)

```
score_mdd = MDD↑_heldout + 0.5 × MDD↑_sealed − 0.25 × max(0, CAGR_giveback_heldout_pp)
```

**Coexist** (all required): tip_clean · tip_mdd_ok · heldout MDD↑ ≥ 0 · **sealed MDD↑ ≥ 0** · giveback ≤ 3.0 · `score_mdd > 0`.

---

## 5. Governance

| Lock | State |
|---|---|
| Soft-Frozen 公股 + FUSE + DH | **KEEP** |
| `#257` | **FROZEN** |
| Sealed gate | **unchanged** |
| E45 stitch | **FORBIDDEN** |
| M1 feature formulas | **FROZEN**（do not retune maps after peek） |

---

## 6. Stage A — when human ACCEPTs

1. Implement `scripts/e16_priv_mdd_m1_scale_v3_stage_a.py`.  
2. Run `c × {0050,CASH}` grid vs `LIVE_PUB_KD`.  
3. Write `PRIV_MDD_M1_SCALE_V3_STAGE_A.{md,json}` + decision pack.  
4. Verdict → Stage B · or STOP V3 · Soft-Frozen KEEP.

```bash
PYTHONPATH=scripts python3 scripts/e16_priv_mdd_m1_scale_v3_stage_a.py
```

---

## Refs

- M1 freeze: `research/e45/E45_M1_STATE_VECTOR_V0_FROZEN.md` · `scripts/e45_m1_state_signal_paper.py`  
- Prior STOP: N3 · S2 decision packs  
- Freeze: `LIVE_CUTOVER_BUNDLE_257_FROZEN.md`  

Label: `PRIV_MDD_M1_SCALE_V3_CHARTER_2026-09-19__DRAFT`
