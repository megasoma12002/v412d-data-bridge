# 民股／四類 × MDD — New Mechanism Charter (N1 → N2 → N3)

Date: 2026-09-19  
Status: **CHARTER ACCEPTED → N1+N2+N3 Stage A STOP** (`STAGE_A_SCORE_POS_GATES_FAIL` — ladder exhausted under sealed MDD; Soft-Frozen KEEP)  
Human ACCEPT: **「ACCEPT N3」** (2026-09-19) · prior N1/N2 ACCEPT 2026-09-19  
Class: **A. Research / EXPERIMENTAL** · Soft-Frozen / live e21 flip = **Class D** later only  
Authority: freeze reopen gate · `LIVE_CUTOVER_BUNDLE_257_FROZEN.md`  
Human binding: 「民股等**新機制**或你改門檻再談」· this charter = **new mechanism** path (sealed gate **unchanged**)

**Passing ≠ Soft-Frozen flip ≠ live e21 rewrite ≠ merge `#257`.**

---

## 0. Why this charter exists

Live stays **公股 Soft-Frozen + FUSE_ADDITIVE + DH_dd06**. Cutover `#257` is **FROZEN**.  
Re-open requires a **new mechanism** charter (**≠ retune frozen SF4 cell**) **or** human sealed-gate change. This document is the former.

### Prior STOP evidence (binding)

| Track | Sealed MDD↑ ≥ 0 | Closest / best | Ref |
|---|---:|---|---|
| 公股＋民營並存 × MDD | **0/24** priv-bearing | `SF4_P60-90_V0-15_F10_KD` sealed **−0.48** · held **+0.50** | `PUB_PRIV_COEXIST_MDD_DECISION_PACK.md` |
| 四類 + DH／L4 防禦 × MDD | **0/6** | `SF4_L4_08` sealed **−0.20** (closest) | `SF4_DEFENCE_MDD_DECISION_PACK.md` |
| Earlier dual / 4-sleeve / priv-replace | STOP | FinPriv raises MDD or replace ≠ 並存 | archived STOP packs |

**Pattern:** tip + often heldout MDD can clear; **sealed 2023+** is the binding fail. Defence on the **same frozen cell** with **TAIEX-DD path / DH shrink** improves heldout/tip but does **not** clear sealed.

---

## 1. What is **not** a new mechanism (WON’T)

Do **not** charter or Stage-A these as “new”:

| Exhausted / forbidden | Why |
|---|---|
| Re-grid FinPriv clip / `prior_priv_frac` / `pub_share` after sealed peek | Retune of STOP grids |
| Re-grid DH shrink or L4 TAIEX DD ∈ {−8%, −10%} on `SF4_P60-90_V0-15_F10_KD` | Same DH／L4 pairing on same frozen cell |
| Soften sealed MDD↑ ≥ 0 from research peek | Needs **human** sealed-gate change (other reopen path) |
| Priv-**replace** (`#257`) as 並存 substitute | Freeze + PRE/POST: replace ≠ 並存 |
| Soft-Frozen live constants / e21 wire from Stage A | Class D only after coexist |
| 「無民股小包」split of `#257` | Not authorized |

---

## 2. Diagnosis (research hypothesis — to test, not soften)

Sealed fail is **regime-local**, not “FinPriv always bad”:

- Offense / small FinPriv can **help heldout** while **hurting sealed**.
- Closest sealed (`SF4_L4_08` −0.20 pp) = **path-switch to pub-only** under TAIEX DD — suggests **conditional FinPriv membership** can approach the gate, but **TAIEX −8/−10 alone** is exhausted for this cell.

Therefore next actuator must change **when FinPriv is allowed**, **where FinPriv dollars go under stress**, or **which sensor triggers that**, not **how wide the clip is**.

---

## 3. Governance locks (non-negotiable)

| Lock | State |
|---|---|
| Soft-Frozen FIN `[0.60, 0.90]` · 公股 R1 · `KD_OPT` · `TEL_EQUAL` | **KEEP** |
| Overlay live | **FUSE_ADDITIVE + DH_dd06 KEEP** |
| `#257` | **FROZEN — do not merge** |
| Sealed / heldout MDD coexist gates | **Unchanged** (same formula as prior MDD charters) |
| Books DEFAULT on main | `E22_v3_recv_pay_effdelay` (tip may lag) — **do not** promote tax10 from this charter |
| Broker live-write | **off** |

---

## 4. Objective (unchanged)

Windows: **heldout_2019_plus** + **sealed_2023_plus** (both hard) · tip YTD/1y observe.

```
score_mdd = MDD↑_heldout + 0.5 × MDD↑_sealed − 0.25 × max(0, CAGR_giveback_heldout_pp)
```

**Coexist** (all required): tip_clean · tip_mdd_ok (≥ −0.5 pp) · heldout MDD↑ ≥ 0 · **sealed MDD↑ ≥ 0** · heldout CAGR giveback ≤ 3.0 · `score_mdd > 0`.

Baseline: **`LIVE_PUB_KD`** (live-intent 公股 Soft-Frozen + KD).  
Frozen topology reference (do **not** retune clips): `SF4_P60-90_V0-15_F10_KD`.

---

## 5. Mechanism ladder (execute N1 → N2 → N3)

Do **not** skip. Each stage needs a paper pack (script + `research/ops` MD/JSON) before the next opens.

### N1 — FinPriv **regime membership** (new actuator topology)

**Idea:** FinPriv is a **binary sleeve** that can turn **OFF → pub-only weights**, keyed to a **new trigger family** — not clip width, not TAIEX DD ∈ {−8%, −10%} alone.

| Book family | Trigger (predeclared) | Action when true |
|---|---|---|
| `N1_PRIV_OFF_LOCAL` | FinPriv **sleeve** NAV DD from peak ≤ {−6%, −8%, −10%} | FinPriv weight → 0; residual stays Soft-Frozen pub path |
| `N1_PRIV_OFF_REL` | FinPriv vs FinPub **relative** 60d return ≤ {−3%, −5%, −8%} pp | same |
| `N1_PRIV_OFF_DUAL` | LOCAL **or** REL (OR gate) at mid cells only | same |

Controls:

| Book | Role |
|---|---|
| `LIVE_PUB_KD` | Baseline |
| `SF4_OFFENSE` | Frozen cell, no gate (expect sealed fail) |
| `SF4_L4_08_REF` | Prior closest — **reference only**, not a search axis |

**Why this is new:** changes **sleeve membership state machine**, not FinPriv clip / prior_frac / TAIEX−8/−10 grid on the same pairing.

**Stage A authorize:** N1 only (compact grid above). Stop / autopsy / decision pack before N2.

### N2 — FinPriv-scoped **relocate** (new sink)

**Stage A ACCEPTED** — human **「ACCEPT N2（FinPriv→cash/0050）」** (2026-09-19), after N1 STOP.

| Book family | Action under N1-style stress |
|---|---|
| `N2_TO_CASH` | FinPriv dollars → cash (FinPub/TEL unchanged; sum &lt; 1) |
| `N2_TO_0050` | FinPriv dollars → 0050 up to Soft-Frozen ETF hi **0.35**; overflow → cash |

Triggers (compact, from N1 autopsy — not a retune of N1 grid): `LOCAL_06` · `LOCAL_08` · `REL_05` · `DUAL_L08_R05`.

Whole-book dry-powder / global relocate already STOP’d elsewhere — **FinPriv-scoped** sink is the new role.

### N3 — Three-state risk machine (new control)

**Stage A ACCEPTED** — human **「ACCEPT N3」** (2026-09-19), after N1+N2 STOP.

| State | FinPriv | Action |
|---|---|---|
| `OFFENSE` | on | frozen SF4 weights (default) |
| `COEXIST_DEFEND` | mid stress | N2 relocate → cash **or** 0050 (ETF hi 0.35) |
| `PUB_ONLY` | high stress | Soft-Frozen pub-only path (N1 off) |

Sensor: FinPriv **sleeve-local DD** level machine (no hysteresis latch).  
Predeclared (mid, high, mid_sink): `L06/L10` · `L08/L12` · `L06/L08` · `L08/L10` × {0050, CASH where listed}.

≠ single L4 path-switch; explicit **three-state** handoff.

---

## 6. Out of scope / WON’T (repeat)

- Retune SF4 FinPriv clips / `prior_priv_frac` / dollar-split `pub_share` after peek  
- Retune DH_dd06 shrink or TAIEX L4 ∈ {−8%, −10%} as the **search**  
- Soften sealed gate  
- Merge / implement `#257`  
- Edit `e16_soft_frozen_base.py` live constants  
- Live e21 wire / Class D from Stage A  
- Skip to N2/N3 without N1 pack  

---

## 7. Stage A ladder status

### N1 — DONE / STOP
Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_new_mech_n1_stage_a.py`  
Pack: `PRIV_MDD_NEW_MECH_N1_DECISION_PACK.md`

### N2 — DONE / STOP
Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_new_mech_n2_stage_a.py`  
Pack: `PRIV_MDD_NEW_MECH_N2_DECISION_PACK.md`

### N3 — ACCEPTED (this ballot)
1. Implement `scripts/e16_priv_mdd_new_mech_n3_stage_a.py` (paper).  
2. Run N3 grid + controls vs `LIVE_PUB_KD`.  
3. Write `PRIV_MDD_NEW_MECH_N3_STAGE_A.{md,json}` + decision pack.  
4. Verdict: coexist / STOP → Stage B or human sealed-gate / new charter.

Reproduce:

```bash
PYTHONPATH=scripts python3 scripts/e16_priv_mdd_new_mech_n3_stage_a.py
```

---

## 8. Alternate reopen

- Human **sealed-gate change** — optional.  
- V2/V3/V4: **STOP**.  
- **V5** DH defend-window → FinPriv-only relocate: DRAFT · `PRIV_MDD_DH_PRIV_WINDOW_V5_CHARTER.md`

---

## Refs

- Freeze: `LIVE_CUTOVER_BUNDLE_257_FROZEN.md`  
- Prior STOP: `PUB_PRIV_COEXIST_MDD_DECISION_PACK.md` · `SF4_DEFENCE_MDD_DECISION_PACK.md`  
- Topology: `SOFT_FROZEN_4SLEEVE_CHARTER.md` · `PUB_PRIV_COEXIST_MDD_CHARTER.md` · `SF4_DEFENCE_MDD_CHARTER.md`  
- Mechanism ladder precedent: `research/e45/E45_NEW_MECHANISM_CHARTER.md` · `E45_DEFEND_HANDOFF_PAPER_CHARTER.md`  

Label: `PRIV_MDD_NEW_MECH_CHARTER_2026-09-19__N1N2N3_DRAFT`
