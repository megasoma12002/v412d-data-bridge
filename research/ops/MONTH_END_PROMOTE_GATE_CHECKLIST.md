# Month-End Promote Gate Checklist — Soft-assist ∥ Sleeve-tilt (paper only)

Date: 2026-09-12 (pack asof **2026-09-11**)  
Status: **OPERATING CHECKLIST · NO LIVE WIRE** · latest row **KEEP_OBSERVE** / **KEEP_OBSERVE**  
Scope: **only** the two operating observes below. Does **not** open live cutover.  
Default after each pack: **KEEP OBSERVE** unless every gate for that track is YES **and** human issues a dedicated ACCEPT string.

| Track | Challenger | Base | Monitor | Live cutover checklist |
|---|---|---|---|---|
| Soft-assist | `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` | `LIVE_KD_OPT` | `SOFT_ASSIST_MONTH_END_MONITOR.md` | `CUTOVER_CHECKLIST_SOFT_ASSIST.md` (**BLOCKED**) |
| Sleeve-tilt | `SLEEVE_RSI14_LT30_a0225` | `LIVE_STACK` | `SLEEVE_LAYER_TILT_MONTH_END_MONITOR.md` | `CUTOVER_CHECKLIST_SLEEVE_LAYER_TILT.md` (**BLOCKED**) |

Inspired by paper→live promotion hygiene (parity / tip / kill-switch / checklist sign-off) — adapted here as **observe-month gates**, not deployment.

## How to use (each calendar month-end)

1. Run `python3 scripts/ops_month_end_paper_pack.py` (includes both monitors **and** Soft↔Sleeve overlap).  
2. Fill **Pass?** for Soft-assist and Sleeve-tilt **separately** from that month’s JSON/MD.  
3. Copy held-out overlap row from `SOFT_SLEEVE_OBSERVE_OVERLAP.md` into the month log.  
4. Record overall row verdict: `KEEP_OBSERVE` · `WATCH` · `READY_FOR_DEDICATED_ACCEPT_BALLOT`.  
5. **Never** auto-wire live. **Never** auto-combine Soft-assist × Sleeve-tilt (overlap is report-only).

## Gates (all required per track)

| # | Gate | Soft-assist Pass? | Sleeve-tilt Pass? |
|---|---|---|---|
| A | Dual-paper **OPERATING**; Exact T+1 OK on both ledgers | | |
| B | Tip YTD **and** trailing 1y: no `PAUSE_REVIEW` vs base | | |
| C | Tip YTD **and** trailing 1y: no `ALERT` (3pp giveback band) — or document WAIVE | | |
| D | Held-out score vs base **> 0** (same formula as screen) | | |
| E | Month-end monitor **alerts = none** (or only documented non-blocking notes) | | |
| F | Challenger ID unchanged since last OPEN (`…__SELL_a05` / `RSI14_a0225`) | | |
| G | Soft-Frozen / live KD / TEL / E45 **unchanged** by this pack | | |
| H | Soft-assist × Sleeve-tilt **combo not proposed** this month | | |
| I | Live cutover checklist still **BLOCKED** until dedicated human ACCEPT | | |

**Track ready for ballot only if A–I all YES for that column.**  
Ready ≠ ACCEPT. ACCEPT still requires the exact human string on the live cutover checklist.

## Soft ↔ Sleeve overlap (report-only · never unlocks combo)

Source: `SOFT_SLEEVE_OBSERVE_OVERLAP.md` · script `scripts/e16_soft_sleeve_observe_overlap.py`

| Metric | Meaning |
|---|---|
| Corr(excess) | Corr of Soft excess vs Sleeve excess (chal−base daily) |
| Same-sign | Days both excess same sign |
| Both− | Days both underperform their base |
| Joint DD days | Among days either rel-NAV DD ≤ −10bp, share both ≤ −10bp |
| Soft↓→Sleeve ex | Mean Sleeve excess on Soft underperform days |
| Sleeve↓→Soft ex | Mean Soft excess on Sleeve underperform days |

**Reading:** high corr / same-sign / joint DD → keep observes **independent** (anti-combo evidence). Low corr does **not** authorize combo either — combo still needs a separate charter.

Seed (asof 2026-09-10, heldout): corr **−0.025** · same-sign **55%** · both− **26.5%** · joint DD days **33%** · Soft↓→Sleeve ≈ **0** · flags high_overlap=`False` high_joint_dd=`False`.

## Month log (fill each pack)

| Month asof | Soft A–I | Soft verdict | Sleeve A–I | Sleeve verdict | Heldout corr / same-sign / both− / jointDD | Combo? | Operator |
|---|---|---|---|---|---|---|---|
| 2026-09-10 | tip clean · held≈+0.086 · alerts=0 | `KEEP_OBSERVE` | YTD/1y/sealed MDD ALERTs | `KEEP_OBSERVE` | −0.025 / 55% / 26.5% / 33% | no | seed |
| 2026-09-11 | A–I YES · tip YTD/1y clean · held≈+0.101 · alerts=0 · ID=`…__SELL_a05` | `KEEP_OBSERVE` | A–I YES · tip alerts=0 · held≈+0.099 · YTD tip score≈−0.007 (no ALERT) · ID=`RSI14_a0225` | `KEEP_OBSERVE` | +0.112 / 48.1% / 25.1% / 46.9% · high_joint_dd=`True` | no (Gate H; joint-DD argues against fuse) | 2026-09-12 pack |

## Verdict meanings

| Verdict | Meaning |
|---|---|
| `KEEP_OBSERVE` | Continue dual-paper; no ballot |
| `WATCH` | Tip OK-ish but held/alerts soft; wait another clean month |
| `READY_FOR_DEDICATED_ACCEPT_BALLOT` | Draft cutover ballot text only — still **no live wire** until human ACCEPT + PR |

## Forbidden (this page)

- Live Soft-assist / Sleeve-tilt / Soft-Frozen / KD / TEL / E45 wire  
- Soft-assist × Sleeve-tilt auto-combo or joint ACCEPT  
- Overlap report does not authorize combo (high or low)  
- Using paper CAGR/MDD claim badges as live badges  
- Treating a single clean month as sustained promote  

## Operator commands

```bash
python3 scripts/ops_month_end_paper_pack.py
# review:
#   research/ops/SOFT_ASSIST_MONTH_END_MONITOR.md
#   research/ops/SLEEVE_LAYER_TILT_MONTH_END_MONITOR.md
#   research/ops/SOFT_SLEEVE_OBSERVE_OVERLAP.md
# then fill this checklist for the asof month
```

## Label

`MONTH_END_PROMOTE_GATE_CHECKLIST_2026-09-12__SOFT_SELL_A05__SLEEVE_RSI14__KEEP_OBSERVE__NO_LIVE`

## FUSE_ADDITIVE (third paper observe · independent)

| Track | Challenger | Base | Monitor | Cutover |
|---|---|---|---|---|
| FUSE_ADDITIVE | `FUSE_ADDITIVE` | `LIVE_STACK` | `FUSE_ADDITIVE_MONTH_END_MONITOR.md` | `CUTOVER_CHECKLIST_FUSE_ADDITIVE.md` (**BLOCKED**) |

Paper-only. Does **not** authorize Soft∥Sleeve ops auto-fuse or live wire. Soft-assist and Sleeve-tilt observes remain independent KEEP.

## E45 defend→handoff `DH_dd06_vz1p0` (paper observe · independent)

| Track | Challenger | Base | Monitor | Cutover |
|---|---|---|---|---|
| E45 defend-handoff | `DH_dd06_vz1p0` | `LIVE_STACK` | `E45_DEFEND_HANDOFF_MONTH_END_MONITOR.md` | `CUTOVER_CHECKLIST_E45_DEFEND_HANDOFF.md` (**BLOCKED**) |

Paper-only. Stage A `HANDOFF_PROMOTE_SHAPED`. Does **not** reopen E45 stitch / undo `DROP_E45_A05` / live wire. Soft / Sleeve / FUSE observes KEEP independent.
