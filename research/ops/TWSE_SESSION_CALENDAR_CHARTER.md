# TWSE session calendar — holidays & typhoon closes

Status: **CHARTER / OPS** — paper-safe today · **required before broker live submit**  
Soft-Frozen / LIVE_* unchanged · no cutover in this doc  
Related: `ARCH_LIVE_MODULARIZE.md` · `live_execution.FillPort` · workflow `v412f-forward-paper`

## 1. Problem

| Layer today | Holiday / typhoon behavior |
|---|---|
| GHA cron `30 8 * * 1-5` | Skips **weekends only** — still fires on weekday 国定假 / 颱風假 |
| Session detection | **Data-driven**: date is a session iff all required codes exist in `live_market.csv` |
| TWSE append | `v412f_append_twse_daily` skips Sat/Sun; weekday with empty MI_INDEX → no bars |
| Exact T+1 | Next **market** session, not next calendar day |
| Broker (future) | No explicit “do not submit today” gate |

Paper is mostly safe (no bar → no new session). Broker submit without a calendar gate is **not** safe.

## 2. Definitions

| Term | Meaning |
|---|---|
| **Session day** | TWSE regular board is open for continuous trading (normal hours) |
| **国定假 / 休市** | Announced non-session weekday (New Year, Tomb Sweeping, …) |
| **颱風假 / 天然災害休市** | Same-day or short-notice close (often announced morning-of) |
| **Half-day / early close** | Session exists but shortened — treat as **session** for ledger unless charter revises |
| **补班日** | Rare make-up weekday that *is* a session — must not be skipped as “holiday” |

Authority for “is today a session?” must be **exchange/official**, not a hardcoded weekend list.

## 3. Method (recommended stack)

### 3.1 Two signals (AND for broker submit)

```
is_session_day(asof) =
    calendar_says_open(asof)     # planned calendar / holiday table
    AND market_bars_present(asof)  # live_market or TWSE MI_INDEX probe
```

| Signal | Role | Failure mode |
|---|---|---|
| **A. Calendar** | Planned 国定假 / 补班 | Misses same-day 颱風假 |
| **B. Market presence** | Bars for required universe (or MI_INDEX non-empty) | Lag / partial feed false negative |

- **Paper / GHA day job:** B alone is enough (status quo). Optional A → quieter cron.
- **Broker submit / poll:** **A ∧ B** (fail-closed). If either says closed → no orders, no fill poll that books live.

### 3.2 Calendar source (A) — phased

| Phase | Source | Notes |
|---|---|---|
| **A0** | Weekend skip only (today) | Insufficient for broker |
| **A1** | Yearly TWSE holiday file in repo (`data/calendars/twse_sessions_YYYY.csv`) + manual ACCEPT | Simple; refresh each Dec/Jan |
| **A2** | Official TWSE / competent-authority published holiday list (fetch + pin hash) | Prefer over scraping HTML |
| **A3** | Same-day open probe: MI_INDEX (or equivalent) returns tradeable rows for `asof` | Covers 颱風假 without waiting for holiday CSV |

**颱風假:** do **not** rely on A1 alone. Use **A3** (or B with “bars for asof”) as the same-day veto. Morning cron may run before announcement → allow **re-check** at open / mid-morning, or treat “calendar open + zero bars by cutoff” as `SESSION_UNKNOWN` → broker **no-submit**.

### 3.3 Market presence (B) — already mostly implemented

Reuse pipeline rule:

- Required codes: Soft-Frozen FIN + TEL + `0050` + `TAIEX` (same as `e21_forward_pipeline`)
- `asof` is a session iff that set is subset of codes on that date in `live_market.csv`
- Optional fast path: MI_INDEX fetch for `asof` non-empty for watchlist (same pattern as `v412f_append_twse_daily.fetch`)

### 3.4 Decision table

| Calendar A | Bars B | Paper forward | Broker submit | Notes |
|---|---|---|---|---|
| closed | — | skip / no-op | **BLOCK** | 国定假 |
| open | present | run | allow (if ACCEPT) | Normal |
| open | absent (before cutoff) | wait / no new session | **BLOCK** (`SESSION_UNKNOWN`) | 颱風假 or data lag |
| open | absent (after cutoff) | no-op; alert | **BLOCK** | Treat as closed for broker |
| weekend | — | cron already off | **BLOCK** | |

**Cutoff (ops knob, not strategy):** e.g. Taipei 10:00 — if still no bars and calendar said open → typhoon/lag → broker stays blocked that day.

### 3.5 Exact T+1 across holidays

- Pending orders stay pending across 国定假 / 颱風假.
- Fill date = **next session** open (paper: next date with bars; broker: exchange ack date).
- Do **not** force calendar+1 fill.
- `signal_date < fill_date` remains the Exact T+1 invariant.

### 3.6 Where to plug in (code seams — future PR)

| Hook | Behavior |
|---|---|
| `scripts/twse_session_calendar.py` (new) | `is_session_day(asof) -> SessionVerdict` |
| `v412f-forward-paper` job start | If closed → exit 0 + write `session_skip.json` (optional noise cut) |
| `e21_forward_pipeline` | Optional preflight; still data-driven by default |
| `FillPort` / broker port | **Hard** preflight: non-session → refuse submit/poll that writes live fills |
| Docker / Cloud Run cron | Same preflight before QC-only vs forward |

`SessionVerdict` sketch:

```text
status: OPEN | CLOSED_HOLIDAY | CLOSED_TYPHOON_OR_NODATA | WEEKEND | UNKNOWN
source: calendar | mi_index | live_market
asof: YYYY-MM-DD
broker_submit_allowed: bool   # True only if OPEN and bars present
```

## 4. Typhoon-specific runbook

1. **Night before / early morning:** calendar may still say OPEN.
2. **Announcement (縣市停班停課 / TWSE 宣布休市):** treat as CLOSED for broker immediately (manual override file or ops flag ok for v1).
3. **Automated:** MI_INDEX empty + required bars missing after cutoff → `CLOSED_TYPHOON_OR_NODATA`.
4. **Do not** invent fills or advance `portfolio_state.last_date` on that calendar day.
5. **Resume:** next OPEN session runs normal Exact T+1 (pending from pre-close signal fills at that open).

Manual override (optional v1):

```text
data/calendars/session_overrides.csv
date,status,reason
2026-07-21,CLOSED,typhoon_ops_override
```

Overrides win over A1 calendar; still prefer B/A3 confirmation when possible.

## 5. Non-goals

- Soft-Frozen / LIVE_* edits
- Changing paper NAV history for past holidays
- Modeling half-day microstructure in v1
- Using 元大股息抓取 / Yahoo calendar as TWSE session SSOT
- Auto-enabling broker submit from this charter alone

## 6. Implementation phases (when authorized)

| Phase | Deliverable | Broker gate |
|---|---|---|
| **P0 doc** | This charter | — |
| **P1** | `twse_session_calendar.is_session_day` + holiday CSV for current year + unit tests | Block unknown ports |
| **P2** | Wire GHA forward job skip + `session_skip` artifact | Paper noise↓ |
| **P3** | MI_INDEX same-day probe + cutoff / override | **Required before live submit** |
| **P4** | Broker `FillPort` calls P3 preflight fail-closed | ACCEPT cutover PR |

## 7. Acceptance tests (when coded)

- Known 国定假 weekday → `CLOSED_HOLIDAY`, cron skip, no live fill write
- Weekend → `WEEKEND`
- Synthetic “calendar open + empty MI_INDEX after cutoff” → broker blocked
- Override CLOSED → blocked even if stale bars exist from prior mistaken append
- Normal session → `OPEN` and paper path unchanged vs baseline

## 8. Pointers

- TWSE daily probe pattern: `scripts/v412f_append_twse_daily.py`
- Live session selection: `scripts/e21_forward_pipeline.py` (common complete dates)
- Fill ports: `scripts/live_execution.py`
- Daily schedule: `.github/workflows/v412f-forward-paper.yml`

Label: `TWSE_SESSION_CALENDAR__HOLIDAY_TYPHOON_CHARTER`
