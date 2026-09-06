# E45 regenerator ownership (engineering note)

Date: 2026-09-06  
Scope: **engineering only** — no Soft-Frozen / DEFAULT / stitch / HIGH_BETA change.

## Intentional split (do not merge runners)

Three research regenerators share crisis / densify *themes* but own different questions and output trees. Consolidating into one mega-runner is **not** the next eng step; keep them separate so each pack stays re-runnable and reviewable.

| Runner | Script | Output tree | Owns |
|---|---|---|---|
| Five-research batch | `scripts/e45_five_research_batch.py` | `repro/e45-five-research-batch/` | Multi-item batch (crisis-year MDD improve, FIN densify screen, cost/turnover, pause diag) |
| COVID non-2020 / FIN densify | `scripts/e45_covid_non2020_fina10_thicken.py` | `repro/e45-covid-non2020-fina10/` | COVID-framed stress years + FIN_ONLY alpha thicken vs BASE |
| Next research batch | `scripts/e45_next_research_batch.py` | `repro/e45-next-research-batch/` | Alt levers, COVID-ex KPI, observe pause refresh hooks, Phase-C follow-ups |

Shared building blocks stay in harness modules (`e45_paper_harness`, Soft-Frozen base, `WINDOWS_STANDARD`). Do **not** fork window keys or delta key names inside these runners.

## Overlap that is OK

- Crisis / stress-year MDD improve tables (same formula via `mdd_improve_pp`).
- FIN densify book IDs (`FIN_ONLY_A##` paper densify vs observe sleeve `SLEEVE_FIN_ONLY_A10` — different IDs, intentional).

## Overlap that is debt (tracked, not closed here)

- Duplicated crisis-year loop boilerplate across runners — extract a tiny shared helper only when a fourth caller appears or a bug forces a shared fix.
- Cosmetic filename debt for `mdd_help*` → `mdd_improve*` is closed in the eng-debt-cleanup PR; columns were already `mdd_improve_*`.

## Rule for future PRs

If you need a new crisis / densify cut, **extend the owning runner** (or add a new pack) rather than cross-writing another pack’s `outputs/`. Governance ballots stay out of regenerator scripts.
