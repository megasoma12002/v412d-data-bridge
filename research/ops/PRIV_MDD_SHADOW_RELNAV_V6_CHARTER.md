# 民股／四類 × MDD — New Mechanism V6 Charter（Shadow 相對 NAV 連續阻尼 FinPriv）

Date: 2026-09-19  
Status: **CHARTER ACCEPTED → Stage A STOP** (`STAGE_A_SCORE_POS_GATES_FAIL` — shadow relnav: heldout often OK, **0 sealed coexist**; best tip-clean sealed `V6_C100_PUB` −0.24)  
Class: **A. Research / EXPERIMENTAL** · Soft-Frozen / live e21 flip = **Class D** later only  
Parents STOP: N1–N3 · V2 · V3 · V4 · V5 · + `SF4_DH` · decision packs on `#261`  
Human: **「ACCEPT V6 Stage-A」** (2026-09-19)

**Passing ≠ Soft-Frozen flip ≠ live e21 rewrite ≠ merge `#257`.**

---

## 0. Why V6 (not N1–V5 retune)

| Ladder | Mechanism shape | Sealed outcome |
|---|---|---|
| N1–N3 | FinPriv **self-path** DD → OFF／reloc／level | 0 coexist |
| V2 | Live **binary** sensors → FinPriv→0050 | 0 coexist |
| V3 | Continuous **M1 `s_t`** FinPriv scale | 0 coexist |
| V4 | Sealed **calendar** episode spans | A0 STOP (spans >120) |
| V5 | **DH latched window** FinPriv relocate | tip OK · sealed −0.27 best |
| Closest ever | `N2_0050_LOCAL_08` sealed **−0.04** | tip fail |

V4 autopsy: offense vs `LIVE_PUB_KD` relative DD is **shallow (~3%) but diffuse**.  
V5: sparse DH windows (~1–2%) still miss that grind.

V6 changes the **sensor + control law**:

> Build **undamped shadow** NAVs (`SF4_OFFENSE` vs `LIVE_PUB_KD`) → relative wealth  
> `W_rel` → `DD_rel` → continuous intensity `u` (Exact T+1 lag) →  
> `FinPriv' = FinPriv · (1 − c · u)` · residual → 0050／cash.  
> Same diagnostic object as V4, but **live continuous path coupling** — not calendar, not DH latch, not M1, not FinPriv-local DD.

Sealed gate **unchanged**（仍要求 sealed MDD↑ ≥ 0）.

---

## 1. WON’T

| Forbidden | Why |
|---|---|
| Re-grid N1–N5 thresholds / V3 `c`·M1 / V5 DH enter·exit | Exhausted |
| Raise V4 span cap or sealed-peek δ≈0.03 | Peek-retune |
| Re-grid SF4 FinPriv clips / `prior_priv_frac` | Exhausted |
| Soften sealed MDD↑ ≥ 0 | Not authorized |
| Use FinPriv-sleeve DD or M1 `s_t` as V6 sensor | That **is** N1 / V3 |
| Closed-loop sensor from **damped** challenger NAV | Must stay undamped shadow |
| Merge `#257` / live e21 / E45 stitch | Freeze |

---

## 2. Frozen pieces

| Piece | Value |
|---|---|
| Offense | `SF4_P60-90_V0-15_F10_KD` |
| Baseline | `LIVE_PUB_KD` |
| Shadow sensor | Undamped `SF4_OFFENSE` vs `LIVE_PUB_KD` → `DD_rel`（lag-1） |
| Depth scale δ | **0.05 FROZEN**（full `u` at −5% relative wealth DD） |
| Intensity | `u_{t-1} = clip(−DD_rel_{t-1} / δ, 0, 1)` |
| Actuator | `FinPriv'_t = FinPriv_t · (1 − c · u_{t-1})` |
| Preferred sink | residual → **0050**（ETF hi 0.35；overflow cash） |
| Coexist gates | **Identical**（sealed≥0 hard） |

δ is **not** a search axis. Stage A varies **c / sink / one deadband / one rolling ablation** only.

---

## 3. Mechanism (Stage A grid)

```
W_rel = NAV_off / NAV_base          # both rebased to 1.0 at first common date
DD_rel = W_rel / cummax(W_rel) - 1  # default: expanding peak
u = clip(-DD_rel / 0.05, 0, 1)      # lag-1 into FinPriv scale
```

| Book | c | sink | note |
|---|---:|---|---|
| `V6_C50_0050` | 0.50 | 0050 | primary |
| `V6_C75_0050` | 0.75 | 0050 | |
| `V6_C100_0050` | 1.00 | 0050 | full map of `u` |
| `V6_C50_CASH` | 0.50 | CASH | sink contrast |
| `V6_C100_CASH` | 1.00 | CASH | |
| `V6_C100_0050_DB01` | 1.00 | 0050 | deadband: `u=0` if `DD_rel > −0.01` |
| `V6_C100_0050_ROLL252` | 1.00 | 0050 | `cummax` over **252d rolling** peak（ablation） |
| `V6_C100_PUB` | 1.00 | PUB | ≤1 path-switch contrast |

**Controls:** `LIVE_PUB_KD` · `SF4_OFFENSE` · `N2_0050_LOCAL_08_REF` · `SF4_L4_08_REF`

Compact Stage A ≤ **8** V6 books + controls.

**Why new:** sensor = **shadow book-vs-baseline `DD_rel`**; actuator = continuous FinPriv damp — ≠ N1 sleeve DD · ≠ V2 binary · ≠ V3 M1 · ≠ V4 calendar · ≠ V5 DH latch.

---

## 4. Objective (unchanged)

```
score_mdd = MDD↑_heldout + 0.5 × MDD↑_sealed − 0.25 × max(0, CAGR_giveback_heldout_pp)
```

**Coexist** (all required): tip_clean · tip_mdd_ok · heldout MDD↑ ≥ 0 · **sealed MDD↑ ≥ 0** · giveback ≤ 3.0 · `score_mdd > 0`.

Honesty: continuous path coupling may lift sealed by construction on the same relative grind. **Heldout + tip** remain hard — patch-sealed-only → **STOP**.

---

## 5. Governance

| Lock | State |
|---|---|
| Soft-Frozen 公股 + FUSE + DH | **KEEP** |
| `#257` | **FROZEN** |
| Sealed gate | **unchanged** |
| δ / shadow undamped | **FROZEN** |

---

## 6. Stage A — ACCEPTED

1. Run `scripts/e16_priv_mdd_shadow_relnav_v6_stage_a.py`.  
2. Shadow NAVs from undamped `SF4_OFFENSE` + `LIVE_PUB_KD` only — **never** call M1 / DH enter / FinPriv-sleeve DD.  
3. Verdict → Stage B · or STOP V6 · Soft-Frozen KEEP.

```bash
PYTHONPATH=scripts python3 scripts/e16_priv_mdd_shadow_relnav_v6_stage_a.py
```

→ `PRIV_MDD_SHADOW_RELNAV_V6_STAGE_A.{md,json}` · decision pack.

---

## Refs

- Prior STOP: N3 · S2 · V3 · V4 · V5 decision packs  
- V4 A0: `PRIV_MDD_SEALED_EPISODE_A0.md`（diagnostic only — do not calendar-gate）  
- Freeze: `LIVE_CUTOVER_BUNDLE_257_FROZEN.md`  

Label: `PRIV_MDD_SHADOW_RELNAV_V6_CHARTER_2026-09-19__STOP`
