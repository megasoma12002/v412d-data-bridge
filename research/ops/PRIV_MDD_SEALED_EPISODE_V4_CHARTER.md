# 民股／四類 × MDD — New Mechanism V4 Charter（Sealed 事件剖檢 → 日曆／事件閘）

Date: 2026-09-19  
Status: **CHARTER ACCEPTED → Stage A STOP** (`A0_STOP_SPAN_TOO_LONG` — deepest sealed relative-DD spans **>120** sess · A1 not authorized)  
Class: **A. Research / EXPERIMENTAL** · Soft-Frozen / live e21 flip = **Class D** later only  
Parents STOP: N1–N3 · V2 S1–S2 · V3 M1-scale · decision packs on `#261`  
Human: **「ACCEPT V4 Stage-A」** (2026-09-19)

**Passing ≠ Soft-Frozen flip ≠ live e21 rewrite ≠ merge `#257`.**

---

## 0. Why V4 (not N1–N3 / V2 / V3 retune)

| Ladder | Mechanism shape | Sealed outcome |
|---|---|---|
| N1–N3 | FinPriv **self-path** DD → OFF／reloc／三態 | 0 coexist |
| V2 | **Live binary sensors** → FinPriv→0050 | 0 coexist |
| V3 | **Continuous M1 `s_t`** scale FinPriv | 0 coexist |
| Closest ever | `N2_0050_LOCAL_08` sealed **−0.04** | tip fail |

All prior ladders used **live stress signals** (or FinPriv self-DD) without asking *which sealed episodes* drive the fail.

V4 is **episode-first**:

1. **A0** — attribute sealed-window relative drawdown (offense vs `LIVE_PUB_KD`) → freeze episode list  
2. **A1** — FinPriv gate keyed only to **frozen calendar / episode windows** (not re-tuned live sensors)

Sealed gate **unchanged**（仍要求 sealed MDD↑ ≥ 0）.

---

## 1. WON’T

| Forbidden | Why |
|---|---|
| Re-grid N1/N2/N3/V2/V3 thresholds or `c` | Exhausted |
| Re-grid SF4 FinPriv clips / `prior_priv_frac` | Exhausted |
| Soften sealed MDD↑ ≥ 0 | Not authorized |
| Peek sealed metrics then invent new live sensors in A1 | Peek-retune |
| Expand episode list after A1 starts | Freeze A0 first |
| Merge `#257` / live e21 / E45 stitch | Freeze |

---

## 2. Frozen pieces

| Piece | Value |
|---|---|
| Offense | `SF4_P60-90_V0-15_F10_KD` |
| Baseline | `LIVE_PUB_KD` |
| Sink when gated OFF | FinPriv→**0050** (ETF hi 0.35; overflow cash) — same sink family as best prior closest |
| Coexist gates | **Identical**（sealed≥0 hard） |

---

## 3. Mechanism ladder

### A0 — Sealed episode autopsy (required first)

Paper-only. Inputs: daily NAV of `SF4_OFFENSE` and `LIVE_PUB_KD` on **sealed_2023_plus**.

Predeclared procedure (no free-form after peek):

1. Align NAVs; compute challenger relative wealth `W_rel = NAV_chal / NAV_base` (both rebased to sealed start).  
2. Relative drawdown `DD_rel = W_rel / cummax(W_rel) - 1`.  
3. Take the **3 deepest** `DD_rel` trough dates in sealed.  
4. For each trough, record the **peak→trough calendar span** (inclusive trading dates) and length in sessions.  
5. Freeze artifact: `PRIV_MDD_SEALED_EPISODE_A0.{md,json}` with exactly those 3 spans + trough dates.  
6. **STOP A0** if any span &gt; 120 sessions (too diffuse → do not open A1; Soft-Frozen KEEP).

A0 does **not** change gates and does **not** authorize live wire.

### A1 — Calendar FinPriv gate (only after A0 freeze)

For each frozen episode span from A0:

| Book family | Action on span dates |
|---|---|
| `V4_OFF_0050` | FinPriv→0050（cap 0.35） |
| `V4_OFF_CASH` | FinPriv→cash |
| `V4_OFF_PUB` | path-switch to Soft-Frozen pub-only 四類（N1-style）— **contrast only**, ≤1 book |

Plus **union** arms (all 3 spans): `V4_UNION_0050` · `V4_UNION_CASH`.

Compact Stage A1 ≤ **8** books + controls (`LIVE_PUB_KD` · `SF4_OFFENSE` · `SF4_L4_08_REF` · `N2_0050_LOCAL_08_REF`).

**Why new:** trigger = **frozen sealed-episode calendars**, not live DD/breadth/FX/M1 intensity.

---

## 4. Objective (unchanged)

```
score_mdd = MDD↑_heldout + 0.5 × MDD↑_sealed − 0.25 × max(0, CAGR_giveback_heldout_pp)
```

**Coexist** (all required): tip_clean · tip_mdd_ok · heldout MDD↑ ≥ 0 · **sealed MDD↑ ≥ 0** · giveback ≤ 3.0 · `score_mdd > 0`.

Honesty: A1 may look strong on sealed by construction (gating the same episodes). **Heldout + tip** remain hard gates — if A1 only “patches sealed” and fails heldout/tip → **STOP** (not coexist).

---

## 5. Governance

| Lock | State |
|---|---|
| Soft-Frozen 公股 + FUSE + DH | **KEEP** |
| `#257` | **FROZEN** |
| Sealed gate | **unchanged** |
| A0 episode list | **FROZEN before A1** |

---

## 6. Stage A — ACCEPTED

1. Run `scripts/e16_priv_mdd_sealed_episode_v4_a0.py` → freeze A0 pack.  
2. If A0 OK: run `…_v4_a1_stage_a.py` → A1 grid + decision pack.  
3. Verdict → Stage B · or STOP V4 · Soft-Frozen KEEP.

```bash
PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sealed_episode_v4_a0.py
PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sealed_episode_v4_a1_stage_a.py
```

→ `PRIV_MDD_SEALED_EPISODE_A0.{md,json}` · `PRIV_MDD_SEALED_EPISODE_V4_A1_STAGE_A.{md,json}` · decision pack.

---

## Refs

- Prior STOP: N3 · S2 · V3 decision packs  
- Freeze: `LIVE_CUTOVER_BUNDLE_257_FROZEN.md`  

Label: `PRIV_MDD_SEALED_EPISODE_V4_CHARTER_2026-09-19__STOP`
