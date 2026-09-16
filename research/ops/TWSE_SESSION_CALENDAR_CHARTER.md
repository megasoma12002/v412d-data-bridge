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

### 3.0 Integrated annual calendar (SSOT shape)

```text
data/calendars/twse_sessions_YYYY.csv
  date,is_session,kind,name,source,notes
```

**Build order**
1. Seed from TWSE `holidaySchedule` → every day of the year (weekend / `CLOSED_HOLIDAY` / planned `SESSION`)
2. Overlay NCDR CAP Taipei full/AM → `CLOSED_TYPHOON_INTENT`
3. Overlay MI_INDEX empty on planned sessions (only **after close** / past days) → `CLOSED_TYPHOON_OR_NODATA`
4. Optional TAIFEX TX day-session (`futDataDown`) corroboration — same closed/open fact class; **not** morning early-open
5. Optional `session_overrides.csv`

```bash
python3 scripts/twse_session_sources.py --build-year 2026 \
  --mi-facts-from 2026-07-01 \
  --taifex-facts-from 2026-07-01 \
  --out data/calendars/twse_sessions_2026.csv
python3 scripts/twse_session_sources.py --asof 2026-07-10   # uses pinned CSV if present
```

`nth_session_after(sessions, fill_date, 2)` uses `is_session=1` rows — shared by Exact T+1 / T+2 estimate.

Weekend that is also on `holidaySchedule` (e.g. 2026-02-28) is labeled **`CLOSED_HOLIDAY`**, not bare `WEEKEND`.


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

## 4.1 Typhoon / disaster close — how to get the signal

### Rule of authority (TWSE)

休市與**台北市**公教停班綁定（非「任一縣市停班」）：

| 台北市宣布 | 集中市場 |
|---|---|
| 全日停止上班 | **全日休市** |
| 上午停止上班 | **全日休市** |
| 僅下午停止上班 | **不休市**（收盤後其他交易停止） |

SSOT 說明：<https://www.twse.com.tw/zh/clearing/suspended.html> · FAQ <https://www.twse.com.tw/zh/about/suspended_faq.html>  
法規：天然災害侵襲處理措施（證交所法規庫）。

全日休市時：**應屆交割款券順延**（與 T+2 session 偏移一致）。

證交所通常另發**新聞稿**（媒體轉述常見）；**沒有**穩定的「颱風休市 JSON API」。年曆 API `holidaySchedule` **只有国定假／春節等**，不含颱風（已核：2026 年曆無颱風列）。

### Data sources (automation ladder)

| Priority | Source | URL / pattern | Latency | Use |
|---|---|---|---|---|
| **1. Primary (same-day fact)** | TWSE `MI_INDEX` JSON | `https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date=YYYYMMDD&type=ALLBUT0999` | After session would have data | `stat != "OK"` / no tables → treat as **no session** (weekend / holiday / typhoon). Repo already uses this in `v412f_append_twse_daily.py`. Probe 2026-09-12 Sat → `stat: 很抱歉，沒有符合條件的資料!`; weekday OK → `tables` present. |
| **2. Planned holiday** | TWSE `holidaySchedule` | `https://www.twse.com.tw/holidaySchedule/holidaySchedule?response=json` | Year ahead | 国定假 only — **not** typhoon |
| **3. Taipei 停班 (intent)** | 人事總處 NDS 頁 | <https://www.dgpa.gov.tw/typh/daily/nds.html> | Eve ~19–22h; or ~04:30 same morning | Human / scrape fragile; look for **臺北市** 全日或上午停班 |
| **4. Machine-readable 停班** | NCDR CAP ATOM | <https://alerts.ncdr.nat.gov.tw/RssAtomFeed.ashx?AlertType=33> · data.gov.tw dataset 20457 | ~1 min feed | Parse CAP XML; filter **臺北市** + 停止上班（非僅停課）. Spec: NCDR CapDocument_WSC.pdf |
| **5. Optional corroboration** | TAIFEX TX day session | OpenAPI latest-only · historical `POST https://www.taifex.com.tw/cht/3/futDataDown` (`commodity_id=TX`, `交易時段=一般`) | Daily reports lag like MI_INDEX; history OK for backfill | Overlay only — see §4.2. Not morning early-open. |
| **6. Confirming press** | TWSE / CNA / 櫃買 news | ad-hoc | After DGPA | Ops alert only — not SSOT |
| **7. Override** | `session_overrides.csv` | repo | Manual | When feed lag / ambiguous afternoon-only |

### Recommended automation for this repo

Implemented prototype: `scripts/twse_session_sources.py` (+ `tests/test_twse_session_sources.py`).

```bash
python3 scripts/twse_session_sources.py --asof YYYY-MM-DD
```

Algorithm:

```text
probe_session(asof):
  if weekend -> WEEKEND (broker BLOCK)
  if holidaySchedule lists closed name -> CLOSED_HOLIDAY (BLOCK)
  if NCDR CAP AlertType=33 has 臺北市 city-wide FULL_DAY|MORNING for asof
       -> CLOSED_TYPHOON_INTENT (BLOCK)   # early / morning-safe
  if Taipei AFTERNOON only -> note; board still OPEN
  MI_INDEX(asof):
    if stat==OK -> OPEN (ALLOW)
    if empty AND Taipei local hour>=14 (or asof < today) -> CLOSED_TYPHOON_OR_NODATA (BLOCK)
    if empty AND before 14:00 -> UNKNOWN (BLOCK broker; do NOT treat as typhoon yet)
```

**Timing (measured 2026-09-16 ~09:06 Taipei):** same-day `MI_INDEX` returned no data while prior weekdays OK — daily report is **post-close**. Night-before / morning typhoon must use **CAP**, not MI_INDEX.

CAP parse rules (offline-tested patterns):
- ATOM: `https://alerts.ncdr.nat.gov.tw/RssAtomFeed.ashx?AlertType=33` → each `entry/link@href` `.cap`
- Keep `status=Actual`; ignore Test/Draft
- `areaDesc` must be city-wide **臺北市** (district-only e.g. 臺北市中正區 → ignore for TWSE)
- Target date from description: `今天` / `明天` / `M/D`
- Class: 下午停班 → AFTERNOON (market open); 上午/全日/已達停止上班 → close

`holidaySchedule` JSON is year-ahead 国定假 only — never lists typhoon.

### 4.2 TAIFEX futures open — useful overlay, not early-open detector

| Idea | Reality (probed 2026-09-16 Taipei morning) |
|---|---|
| TX day board **08:45–13:45** opens before cash **09:00** | Hours align under Taipei 停班: full/AM stop → **futures day board closed** with cash |
| OpenAPI `DailyMarketReportFut` as live “opened?” | **No.** At ~09:50 on open weekday still dated **prior** session; `?date=` ignored / returns Swagger HTML |
| OpenAPI `TimeAndSalesData` tick stream | **No.** Same morning still only through prior trade date (~800k rows, max Date=yesterday) |
| Historical `POST futDataDown` TX + `交易時段=一般` | **Yes** for backfill. 2026-07-10 typhoon → **0** TX rows; 07-09 / 07-13 open; 端午/勞動 国定假 → absent |
| Night / 盤後 | Separate rule: Taipei stop announced **before 14:00** → that evening night session off. Do **not** treat 盤後 as cash-board session |

**Recommendation:** keep CAP + MI_INDEX as primary same-day stack. Add TAIFEX TX day-session presence as **optional corroborating overlay** for annual CSV / trailing closed-day audits (`--taifex-facts-from`). Do **not** replace cash SSOT with futures; do **not** claim OpenAPI detects 08:45 open for broker morning gate.

```bash
python3 scripts/twse_session_sources.py --build-year 2026 \
  --mi-facts-from 2026-07-01 \
  --taifex-facts-from 2026-07-01 \
  --out data/calendars/twse_sessions_2026.csv
```

### Timing notes (ops)

- 全日／上午停班：原則前一日 19–22 時發布；當日惡化可至約 04:30。  
- 下午停班：當日約 10:30 前 — **市場仍開**；不要當成全日休市。  
- 其他縣市停班 ≠ 台股休市（除非台北市也停）。
- 期貨夜盤：台北市 **14:00 前**宣布當日停班 → 當日夜盤休；14:00 後宣布 → 夜盤通常照開（以期交所公告為準）。
## 5. Non-goals

- Soft-Frozen / LIVE_* edits
- Changing paper NAV history for past holidays
- Modeling half-day microstructure in v1
- Using 元大股息抓取 / Yahoo calendar as TWSE session SSOT
- Auto-enabling broker submit from this charter alone
- Treating non-Taipei 停班 as TWSE close

## 6. Implementation phases (when authorized)

| Phase | Deliverable | Broker gate |
|---|---|---|
| **P0 doc** | This charter | — |
| **P1** | `twse_session_calendar.is_session_day` + holiday CSV / `holidaySchedule` fetch + unit tests | Block unknown ports |
| **P2** | Wire GHA forward job skip + `session_skip` artifact | Paper noise↓ |
| **P3** | MI_INDEX same-day probe + cutoff / override (+ NCDR CAP Taipei filter) — prototype `twse_session_sources.py` | **Required before live submit** |
| **P4** | Broker `FillPort` calls P3 preflight fail-closed | ACCEPT cutover PR |

## 7. Acceptance tests (when coded)

- Known 国定假 weekday → `CLOSED_HOLIDAY`, cron skip, no live fill write
- Weekend → `WEEKEND`
- Synthetic “calendar open + empty MI_INDEX after cutoff” → broker blocked
- Override CLOSED → blocked even if stale bars exist from prior mistaken append
- Normal session → `OPEN` and paper path unchanged vs baseline
- CAP Taipei morning 停班 → intent CLOSED; afternoon-only → still OPEN for board

## 8. Pointers

- TWSE daily probe pattern: `scripts/v412f_append_twse_daily.py`
- Session / typhoon auto sources: `scripts/twse_session_sources.py`
- Live session selection: `scripts/e21_forward_pipeline.py` (common complete dates)
- Fill ports: `scripts/live_execution.py`
- Daily schedule: `.github/workflows/v412f-forward-paper.yml`
- TWSE 天然災害休市原則: `https://www.twse.com.tw/zh/clearing/suspended.html`
- TWSE 年曆 JSON: `holidaySchedule?response=json`
- 人事總處停班查詢: `https://www.dgpa.gov.tw/typh/daily/nds.html`
- NCDR 停班 CAP ATOM: `https://alerts.ncdr.nat.gov.tw/RssAtomFeed.ashx?AlertType=33`
- TAIFEX OpenAPI (latest day): `https://openapi.taifex.com.tw/v1/DailyMarketReportFut`
- TAIFEX historical TX day: `POST https://www.taifex.com.tw/cht/3/futDataDown`

Label: `TWSE_SESSION_CALENDAR__HOLIDAY_TYPHOON_CHARTER`
