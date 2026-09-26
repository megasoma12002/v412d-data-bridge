# Project Architecture & Security Code Review — 2026-09-26

Scope: full-repo system architecture + security trust-boundary review on `main`  
(post Class D FinPriv V7 F05 live wire · COOL_c8 · β densify · Gate V7/V8 paper).  
Priors: `PROJECT_CODE_REVIEW_2026-09-12.md` · `ARCH_LIVE_MODULARIZE.md` · `OPS_STATUS.md`

Label: `PROJECT_ARCH_SEC_REVIEW_2026-09-26__CLASSD_FINPRIV__TIP_WRITER__BROKER_PREP`

---

## Verdict

| Area | Grade | Notes |
|---|---|---|
| System layering (data → paper → live tip → ops/CI) | **HEALTHY** | Clear Soft-Frozen tip vs paper coexistence |
| Live day modular pipeline | **HEALTHY** | Thin CLI + `live_*` modules; session lock |
| Soft-Frozen SSOT / ACCEPT gates | **HEALTHY** | `live_config` + ballots + checklists |
| Exact T+1 / QC / tip-write chain | **HEALTHY** | Fail-closed; tip gate after verify |
| Broker live-write | **PREP / FAIL-CLOSED** | Triple gate + `API_WIRED=False` |
| Class D FinPriv carve | **WIRED · MONITOR** | Fail-closed on stale priv px; nested carve |
| CI tip-writer blast radius | **ACCEPTABLE · HIGH CARE** | Owner-only issues; `contents: write` |
| Docs vs live SSOT lag | **MEDIUM** | Some archive docs still cite DH / old books |
| Overall security posture | **STRONG for paper tip** | Residual: tip-gate depth, priv data freshness, broker seam |

**Overall:** Architecture is coherent: Soft-Frozen tip is a narrow, highly gated write surface; research paper coexists via dual-ledgers without flipping live. Security controls around tip mutation, Exact T+1, path canon, and broker PREP are strong. Highest residual risks are **operational** (tip-writer blast radius, private FIN data lag, overlay complexity) rather than classic RCE/injection.

---

## 1. System architecture (current)

```
data/  ──CI refresh──►  live_market + private_fin_adjusted
                              │
research paper (repro/)  ◄────┤  share Soft-Frozen builders
                              │  NEVER write tip
                              ▼
                 e21_forward_pipeline (lock)
                   features → overlays → fills → E22 → orders → commit
                              │
                              ▼
                       forward/e21 tip
                              │
              e21_qc → post_forward_verify → tip_write_gate → bot push
                              │
                              ▼
                    research/ops control plane
```

### Live call graph (trust-relevant)

`e21_forward_pipeline` → `live_session_io` (canon paths + lock) → `live_strategy_targets` (Soft-Frozen + FUSE/COOL) → optional `live_finhc_v7_f05_cutover` (priv px merge) → `live_execution` / fills → `live_e22_day` → `live_rebalance_orders` (KD_OPT / dual carve) → `live_day_commit` (state last).

### Soft-Frozen vs paper

- Live SSOT: `e16_soft_frozen_base` · `live_config` · `within_sleeve_alloc` · tip under `forward/e21/`
- Paper: `simulate_core` / dual-paper ledgers under `repro/` · share builders · process lock via ACCEPT ballots
- Class D FinPriv: **nested carve inside Financial dollars** — not a 4th Soft-Frozen sleeve

### Live stack (ops SSOT)

E16 3-sleeve Soft-Frozen + Exact T+1 + `E22_v3_recv_pay_effdelay` + KD_OPT + TEL_EQUAL + FUSE_ADDITIVE + COOL_c8 + Class D FinPriv V7 F05 · 500M · lot 1000.

---

## 2. Security findings

### Strengths (keep)

1. **Canonical tip path gate** — `live_session_io.assert_canonical_live_paths`: Soft-Frozen `forward/e21` always requires `paper` fill port; `--allow-noncanonical-paths` does **not** unlock broker on tip.
2. **Broker triple gate** — `broker_safety.live_write_gate`: `LiveConfig.broker_live_write_accepted` ∧ `E21_BROKER_WRITE_LIVE=1` ∧ `broker_live_write_accept.json` · circuit + daily budget + process lock · covered by `tests/test_broker_safety.py`.
3. **SPARK unwired** — `yuanta_spark_adapter.API_WIRED=False`; network entrypoints raise `SparkNotWiredError`.
4. **Exact T+1 fail-closed** — pipeline exits on same-bar fills; `e21_qc` owns `qc_status.json` (not self-certified by writer).
5. **Session + tip push gates** — `e21_session.lock`; asof rewind refuse; `forward_tip_write_gate` checks post-forward `ok` + tip books version.
6. **Issue tip-trigger owner-only** — `v412f-forward-paper.yml` requires `github.actor == repository_owner` + `RUN_E21_FORWARD*` title.
7. **Landmine tests** — Soft-assist / Sleeve-tilt live wire banned; broker ACCEPT false; Class D flag guards added.
8. **Subprocess pack** — month-end pack uses fixed argv lists (no shell interpolation).

### Findings (prioritized)

| ID | Sev | Finding | Where | Remediation |
|---|---|---|---|---|
| S1 | **P2** | Tip-write gate does not re-assert `qc_status.json` `status==PASS` / `exact_t1_ok` | `forward_tip_write_gate.py` | Defense-in-depth: require QC PASS artifact before push (workflow already fails on QC, but gate is reusable standalone) |
| S2 | **P2** | Class D silently depends on FinMind tip freshness; lag >5d force-disables FinPriv without Soft-Frozen-looking alarm in tip gate | `live_finhc_v7_f05_cutover.py` · ops alerts | Add ops alert / tip-day signal when `fin_priv_skipped_missing_px` or lag>N; schedule priv panel refresh in CI |
| S3 | **P2** | Tip writer workflow has `contents: write` + bot push of `forward/` — high blast radius if job logic drifts | `v412f-forward-paper.yml` | Keep concurrency; consider path-filtered push / required status checks; never broaden issue prefixes |
| S4 | **P3** | Multiple workflows inject `FINMIND_TOKEN`; issue-triggered jobs already owner-gated — good — but token lives in many E50 research jobs | `.github/workflows/e50a*.yml` | Prefer job-level secret scoping; audit which workflows truly need token |
| S5 | **P3** | `check_e45_paper_hygiene.py` `exec(compile(...))` on harness file | hygiene tooling | Acceptable (trusted repo file); avoid generalizing to untrusted paths |
| S6 | **P3** | Dual books / triple cash clocks increase mis-merge risk (R4 into NAV) | docs + R4 observe | Keep R4 out of NAV (already asserted); document in tip-gate / QC note |
| S7 | **P3** | Docs lag: some KEEP/ARCHIVE notes still cite DH live / older books while `live_config` says COOL + Class D | `RESEARCH_PORTFOLIO_*`, older reviews | Sync archive banners to `OPS_STATUS` / `live_config` |
| S8 | **INFO** | Broker / SPARK seam is deliberately half-built | `live_fill_broker` · `yuanta_spark_adapter` | Do not flip `API_WIRED` or `broker_live_write_accepted` without dedicated ACCEPT + checklist |
| S9 | **INFO** | Overlay stack density (FUSE+COOL+Class D+KD) — composition errors are strategy risk more than exploit | `live_strategy_targets` · `live_rebalance_orders` | Keep DH∧COOL refuse; add composition smoke in QC if FinPriv gate meta missing on tip signals |

### Not observed (good)

- No `pickle` / `yaml.load` unsafe loads on live path
- No `shell=True` subprocess on live tip path
- No `pull_request_target` tip-write workflows
- Broker ACCEPT remains `False` on `LiveConfig`

---

## 3. Architecture risks (non-exploit)

1. **Shared Soft-Frozen base** — edits to `e16_soft_frozen_base.py` instantly change live + paper BASE; rely on process + hygiene.
2. **Class D nested carve vs STOP’d 4-sleeve** — easy to confuse V7 live carve with universe topology expand.
3. **Ops artifact volume** — hundreds of ballots/screens; discoverability + stale-doc risk.
4. **Promotion path complexity** — many parallel observes; Gate H forbids auto-fuse of independents while live FUSE is a separate recipe.

---

## 4. Recommended next actions

1. Harden `forward_tip_write_gate.py` to require `forward/e21/qc_status.json` PASS + `exact_t1_ok` (S1).
2. Wire Class D skip/stale into `ops_alert_scan` + optional CI refresh of `private_fin_adjusted` tip (S2).
3. Sweep docs that still claim DH live / pre–Class D Soft-Frozen membership (S7).
4. Keep broker PREP: no `API_WIRED` / no `broker_live_write_accepted` without Class D–style ACCEPT pack.

---

## 5. Review method

- Architecture map: live modular call graph + ops/CI control plane on `main` @ `298025f` (post #282–#291 merges).
- Security: trust-boundary read of tip writer, session/path gates, broker_safety, SPARK adapter, Class D cutover, QC/tip gate, workflow permissions/secrets, subprocess/hygiene surfaces.
- Note: dedicated Security Review subagent skipped empty branch-diff; this pack is a full-repo surface review instead.

## Label

`PROJECT_ARCH_SEC_REVIEW_2026-09-26__HEALTHY_TIP__BROKER_PREP__CLASSD_MONITOR`
