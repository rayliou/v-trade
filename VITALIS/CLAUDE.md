# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

`AGENTS.md` holds the project's standing objective, scope, and research-loop rules in full; read it too. This
file restates the parts a session must not lose track of, then covers what requires reading several files to
reconstruct.

## Goal (do not lose sight of this while deep in a module)

A personal US-equity research system. Total capital USD 200,000–400,000; the objective is net-of-cost return
above QQQ, with roughly 30% max drawdown as a research acceptance ceiling and total data spend ≤ USD 1,000/year.
Every one of these numbers is a real user-confirmed constraint (`docs/review/02`), not a placeholder.

**The methodology is a closed loop, and it is the point of the whole project — not a formality:**

> versioned data → frozen rules → holdings/trade/cash ledger → QQQ + risk/cost comparison → a
> continue/revise/stop/insufficient-evidence decision, with every attempt and every failure recorded.

Two rules follow directly from that loop and override any instinct to "just check if it works":
- **Engineering success and investment evidence are two different verdicts, always labeled separately.** A
  run completing without error, or a sample beating QQQ, is not investment evidence. The standing decision for
  every P001-family run (the fixed 30-survivor Yahoo sample) remains `insufficient_evidence` — see
  `docs/review/08-decisions-and-coverage.md` for the full, append-only history of what changed, why, and what
  it did and did not prove.
- **A change that isn't part of the strategy itself (an accounting fix, a new diagnostic, a data-pipeline
  improvement) must be run and registered separately from a change that could plausibly move the result**, so
  nobody can later look at one number and not know which of several simultaneous changes caused it. When in
  doubt, register it in `08-decisions-and-coverage.md` under its own dated entry before moving on.

**Historical empirical state (P004 engineering audit, 2026-09-13):** P003/P003b's investment evidence
is withdrawn: run_pit mapped month-end M universe and quality inputs to execution month M rather
than M+1, so first-of-month trading used future information. Its liquidity calculation also multiplied
nominal close by split-adjusted volume, and quality's broadened peer-group fallback silently compared
some tickers against fewer than the minimum group size. All three are now corrected, with regression
tests; the original artifacts are retained and must not be cited as credible alpha evidence.

**Once corrected, the result reverses, not just shrinks.** On the same 2005–2025 real point-in-time
universe and prices, every tested variant now *underperforms* QQQ net of the real $828/year data cost:
M10 -3.4pp, M20 -4.9pp, M10-risk15 -6.2pp, Q10 -2.8pp, Q20 -4.2pp (annualized, vs the QQQ total-return
proxy). Only M10-risk15's uncorrected-for-multiple-comparisons 90% bootstrap interval is entirely negative;
Q20 and all other intervals cross zero. These are diagnostics on an incomplete economic ledger, not formal alpha evidence. This holds across
both the 2005–2014 and 2015–2025 sub-periods and across all tested capital/cost scenarios, and is not
a cash-yield-assumption artifact (a zero-cash-yield replay moves CAGR by well under 1pp). **The old
"momentum has edge but too much drawdown" framing no longer applies — most of that apparent edge was
the look-ahead bias.** See `docs/prototype/p004-audit-and-diagnostics.md` (results) and
`docs/prototype/p004-engineering-audit.md` (what was fixed and what data gates still fail).

Investment decision remains `insufficient_evidence` regardless — the data gates below are unmet
independent of the sign of the result. Corporate-action/exit settlement (last-price proxy) is
unverified — one confirmed case (MRO's 2011 Marathon Petroleum spinoff) shows an 8-to-39pp difference
between the cash-settlement proxy and the split/dividend-adjusted return, so this is not a rounding
concern. Current sector/exchange/category metadata and unresolved SIC chains remain limitations. Do
not tune a new signal, adjust risk thresholds, or add LEAPS before the corporate-action/exit ledger
(P005, proposed) and the historical-metadata gaps are closed — a new positive-looking result on this
same incomplete ledger would not be trustworthy either way.

## Bounded closeout decision (P005)

P005 completed the last authorized accounting replay with frozen signals, universe and quality. Distributed
stock is held as stock, then only inherited quantity is sold at the next session open with costs. Plain
acquisition cash and stock are additive; elections and conflicting dates remain unresolved. The primary
USD300k/10bps/$828-fee net CAGRs are M10 11.61%, M20 10.01%, M10-risk15 8.79%, Q10 11.98%, Q20 10.55%,
versus QQQ TR proxy 14.77%. No final case jointly beats QQQ and satisfies ~30% maximum drawdown.

**Stop current equity-alpha development.** Investment evidence remains insufficient; that is not an
instruction to build more infrastructure or add options. No new signals, tuning, LEAPS, IBKR, shadow trading,
database platform or product UI are authorized. Reopening requires an explicitly user-authorized hypothesis,
evidence, budget, acceptance and stop criteria. Read `docs/prototype/p005-closeout-results.md` and its protocol.
`vitalis/corporate_actions.py` and `scripts/closeout.py` implement scenarios, not verified broker settlements.
The regular `run_pit` does not activate this optional action layer; P005 must use the dedicated runner.

## P006 (user-authorized new hypothesis): rejected, not insufficient-evidence

A genuinely different candidate — whole-market relative-volume-spike pool (`vitalis.universe.monthly_hot_universe`,
`vitalis.run_p006`) instead of market cap, 1-month formation instead of 12-1/6-1, bottom-25% quality *exclusion*
instead of a blend, 3/5-name concentrated books (H3/H5) instead of 10/20, primary cost 25bps, drawdown limit
widened to 0.50 by explicit user decision. Full 2005-2025 real result: **H3 (3 names) was driven to real total
ruin — ending NAV $0.00, CAGR -100.00%; H5 (5 names) to near-total ruin — ending NAV $599.57 from $300k,
max drawdown -99.83%.** Both variants' paired block-bootstrap 90% CI for excess CAGR vs QQQ is entirely
negative at both 21- and 63-day blocks — this is a statistically decisive rejection, not a zero-crossing
"insufficient evidence" result like every prior candidate. See `docs/prototype/p006-hot-volume-results.md`.

Do not retune this shape (window length, quality fraction, hold count) — none of those look like they could
plausibly flip a -100pp-scale gap, and a parameter search here would just be overfitting to noise. The
project's own read: relative-volume-spike is very likely selecting speculative, soon-to-mean-revert names, not
the "healthy attention" the hypothesis assumed. Getting this pipeline (whole-market hot-volume screen +
1-month formation + exclusion-based quality + concentrated books) working end to end surfaced four real, now-
fixed engineering bugs worth knowing about if you touch this code again: (1) `vitalis.universe.load_dollar_volume`
had the same nominal-close-times-adjusted-volume defect P004 fixed in `sharadar_prices.py`, in a second,
previously-uncalled site; (2) a real ART fundamentals row (NGVT) has `reportperiod` after its own `date` —
`run_pit.build_quality_by_review_month` now drops such rows explicitly rather than crashing; (3) `engine.choose()`'s
sector cap and a small `count` can be arithmetically incompatible (`1/count > sector_cap` makes every slot
unfillable) — found before any real H3 result existed, not a post-hoc tune; (4) `engine.simulate()` had no way
to represent a fund driven to exactly zero NAV — a flat per-session fee capped at available cash, plus zero-
NAV-safe division in `engine.metrics()`, `vitalis.stats.daily_returns()`, and `vitalis.research_audit.diagnose_ledger()`
(all previously assumed nav_usd > 0). See the four 2026-09-14 entries in `08-decisions-and-coverage.md` for
each fix's own registration.

## Commands

```sh
python3 -m unittest discover -s tests -v          # all tests (113, some skip without licensed data present; ~180s)
python3 -m unittest tests.test_engine -v          # one module
python3 -m unittest tests.test_engine.EngineTests.test_split_and_dividend_preserve_real_wealth
python3 -m vitalis.run                            # P001 fixed-rule loop, fixed 30-symbol Yahoo sample
python3 -m vitalis.run --offline                  # replay from checksummed cache, no network
python3 -m vitalis.sample_audit                   # P002 public cross-source data audit
python3 -m vitalis.sample_audit --offline
python3 -m vitalis.build_universe                 # real point-in-time universe over a date range (needs the licensed cache)
python3 -m vitalis.run_pit                        # P003 long-history backtest: real universe + real prices (needs the licensed cache)
python3 scripts/check_free_data.py                # vendor sample reachability probe
python3 docs/review/roi_scenarios.py              # ROI scenario JSON (no market data)
git diff --check
```

`vitalis/sharadar.py`, `vitalis/quality.py`, `vitalis/universe.py`, `vitalis/sic_history.py`, and
`vitalis/reconcile.py` are library modules, not CLIs — they're driven ad hoc or from `build_universe.py`/
`run_pit.py` against the real licensed cache in `data/authorized/sharadar/` (git-ignored; not present on a
machine without that subscription's key, so their real-data tests skip cleanly). **Do not edit `vitalis/*.py`
while a long `run_pit.py`/`build_universe.py` background run is in flight** — Python has already loaded the
old bytecode into that process, so a traceback's shown source lines can come from your edit while the actual
executed logic is still the old version, which is genuinely confusing to debug (hit this for real this
session).

Standard library only, Python 3.9+ (needs the system IANA tz database); developed on 3.14.7. There is no
dependency manifest, linter, or formatter — justify and lock any new dependency before adopting it.
Four-space indent, `snake_case`, explicit units in field names (`_usd`, `_bps`, `_pp`, `_trading_days`).

Exit code 2 from `vitalis.run` / `vitalis.sample_audit` / `check_free_data.py` means the run was blocked or a
sample was unavailable — a registered failure, not a strategy loss. Exit 0 means the checks executed, **not**
that a research threshold passed; that verdict lives in the run's `decision.json` / `audit.json`.

## Architecture

- `vitalis/data.py` — Yahoo chart download, immutable checksummed cache envelopes, normalization.
- `vitalis/macro.py` — FRED cash-yield reference series (DGS3MO), forward-filled onto the trading calendar;
  feeds `engine.simulate()`'s cash-interest accrual. Not a trading signal — see its module docstring for why
  that distinction matters for look-ahead purposes.
- `vitalis/engine.py` — ranking, selection with hysteresis, risk overlay, next-open integer-share simulation,
  and the required-output metrics (`docs/review/04` section 6: Sharpe, Sortino, Calmar, Ulcer, drawdown,
  worst month/quarter, hit rate, downside capture). `simulate()`'s optional `symbols_by_review_month` lets the
  eligible pool itself change monthly (a real point-in-time universe) instead of one fixed dict for the whole
  run — a name dropping out of that month's pool exits through the normal rank-driven path, no special-casing.
  A held position with no bar on the current day but one on the prior session is settled at that last known
  price (an unverified last-price proxy, not certified delisting proceeds), logged as a `forced_exit_data_discontinued` warning, not raised as an
  error — deliberately not excluded from selection ahead of time, which would be a new form of look-ahead bias.
  `rank_signals()`'s optional `quality_by_symbol` blends in a quality score 50/50 with momentum (the Q10/Q20
  variants); omitting it (`None`) is the pure-momentum path and is fully backward compatible.
- `vitalis/stats.py` — paired circular block-bootstrap CI for a strategy-vs-benchmark CAGR/Sharpe/drawdown
  differential, preserving the shared market path between the two series (04 section 4). Not a substitute for
  the DSR-style multiple-comparison correction 04 still requires once more than one configuration is tried.
- `vitalis/pit.py` — as-reported (ARQ/ARY/ART) fundamentals availability filtering. Wired into `quality.py` and
  proven against real data, but **still not called from `engine.py`** — there is no quality factor in the P001
  simulation itself.
- `vitalis/quality.py` — the three as-reported TTM quality metrics from `docs/review/03` section 2, with the
  required neutral 0.5/N/A fallback for excluded financial sectors and missing data. Folded into the real
  point-in-time P003 universe as of the Q10/Q20 variants (`run_pit.py`'s `build_quality_by_review_month()`,
  50/50 blend with momentum in `engine.py`'s `rank_signals()`) — see `docs/prototype/p003b-pit-quality-results.md`
  and the 2026-09-13 entries in `08-decisions-and-coverage.md` for the result (inconclusive on both the return
  and drawdown axes) and for the earlier P001-only proof this superseded.
- `vitalis/universe.py` — three related pieces of point-in-time universe construction: S&P 500 membership
  reconstructed from Sharadar's `added`/`removed` event log (self-validated against the vendor's own quarterly
  snapshots, 113/113 matched); `security_master()` (one row per permaticker from the `SEP`-tagged bulk-tickers
  rows); and `monthly_universe()`, the real `docs/review/03` section 1 eligibility screen (category, exchange,
  ≥252 trading days, 63-day $20M ADV, same-issuer dedup, top-N by market cap with no padding), driven by the
  `vitalis/build_universe.py` CLI. Carries three responsibilities in one file by now — flagged in
  `docs/review/09` as worth splitting before it grows further, not yet done.
- `vitalis/sic_history.py` — point-in-time SIC classification from Sharadar's `sicchangefrom`/`sicchangeto`
  action pairs, self-validated by walking each ticker's chain forward to its current classification (98.2%
  matched). Watch the field-format trap this already caught once: the bulk `actions` table gives SIC codes as
  floats-in-a-string (`"5990.0"`), `tickers.csv` gives plain integers (`"5990"`) — always go through
  `_normalize_siccode()`, never compare the raw strings.
- `vitalis/reconcile.py` — independent cross-source close-price comparison (Yahoo vs. real Sharadar prices;
  30-symbol proof only). `vitalis/sharadar_prices.py` is the module that actually turns real Sharadar
  `stocks`/`actions` rows into engine.py's bars schema for real backtesting — see its module docstring for the
  field conventions it had to verify empirically (open/close are split- but not dividend-adjusted;
  `closeunadj` is already nominal, unlike Yahoo; `dividend` needs the same future-split-factor scaling Yahoo's
  does). `find_gap_free_tickers()` identifies internal gaps; the corrected runner blocks on them instead
  of excluding historical candidates using future gaps. Halt modeling remains unimplemented.
- `vitalis/sharadar.py` — authenticated Sharadar REST + bulk-zip adapter under a Personal Use License. The API
  key is read only from `SHARADAR_API_KEY` (kept in a git-ignored local `.env`); every persisted URL has it
  stripped. `TABLE_TIERS` keeps 13F-derived holdings tables isolated from the ranking engine (public-disclosure
  lag risk, not just an unfinished feature). `check_and_record_quota()` enforces a self-imposed 200-req/day
  cap; `check_retention()` computes the license's post-termination deletion deadline but is informational only
  — this project's own subscription is being retained indefinitely by the user's choice, so nothing calls it
  automatically. See the module docstring and `docs/review/07-evidence-register.md` E10/E17 for the verified
  license text before changing any of this.
- `vitalis/run.py` — P001 CLI: freezes config, fetches, simulates every scenario on the fixed 30-symbol Yahoo
  sample, writes the run directory. Also exports `write_csv()` (used by `run_pit.py` too — it unions field
  names across all rows rather than trusting `rows[0]`, because `engine.py`'s `warnings` list can now mix two
  schemas). The primary-scenario bootstrap jobs (variant × block-length, 10) run in parallel via
  `ProcessPoolExecutor` — one process per independent resample job.
- `vitalis/build_universe.py` — CLI wrapper around `universe.py`'s eligibility screen for an arbitrary date
  range; writes a frozen config + per-source-file-hash manifest like `run.py` does.
- `vitalis/run_pit.py` — corrected P004 CLI: the long-history backtest on the real point-in-time universe and real
  Sharadar prices (2005–2025 by default; see its module docstring for why 2005, not earlier). The genuinely
  independent CPU-bound steps (per-ticker price normalization across ~800 real tickers, the ~260-month
  eligibility screen, and the seven base simulations — QQQ/QQQ-cash15/M10/M20/M10-risk15/Q10/Q20) each run across a
  `ProcessPoolExecutor`; the eligibility-screen and simulation pools use an `initializer` so the large shared
  read-only data (master, market-cap/dollar-volume history, bars) is pickled once per worker, not once per
  task — follow this same pattern for any future parallelization of large-shared-data, many-small-tasks work,
  rather than passing the big structures as per-task arguments. `build_quality_by_review_month()` streams the
  real bulk fundamentals file once (ART dimension, evaluation-window date range) and computes each month's
  quality percentiles scoped to that month's own eligible set, not the whole 21-year candidate union.
- `vitalis/sample_audit.py` — P002 CLI: cross-source AAPL price/action check plus PIT timing boundary test.
- `config/*.json` — frozen experiment inputs. `data-source-policy.json` describes a coordinated-ingestion
  design that no CLI fully implements yet; `vitalis/sharadar.py` is a real, working adapter but a simpler one
  (per-request caching + a quota file, not the SQLite catalog the policy file describes) — see its
  `adapter_note` field.

### Non-obvious invariants

**Two price universes coexist per bar.** `normalize()` reconstructs *nominal* historical `open`/`close`/
`dividend` from Yahoo's split-adjusted quotes by multiplying by the product of all split ratios **after** that
day within the requested window; `adjclose` stays as the total-return proxy. Trading and cash accounting use
nominal prices; momentum signals and the benchmark reference use `adjclose`. Never mix them. This
reconstruction can only see splits inside the request window, so a snapshot whose `data_end_exclusive` lies in
the past will silently mis-scale if a split happened afterwards. P001 still runs entirely on Yahoo data. P003
(`run_pit.py`) uses real Sharadar prices instead, via `sharadar_prices.py` — there `closeunadj` is already
nominal (no reconstruction needed), but the `dividend` action field turned out to need the same
future-split-factor scaling Yahoo's does (verified empirically against AAPL's real pre-split dividend, not
assumed). Do not mix the two adapters' bars in one simulation.

**P001 config is frozen before any download.** `run.py` writes `config.json`, copies every `vitalis/*.py` with its
SHA-256, and writes `manifest.json` *before* fetching, so results cannot be reverse-fitted to a config. Run
directories are `runs/<UTC timestamp>-<config hash prefix>/` and must never be overwritten; the cache uses
`open("x")` for the same reason (`download_bulk_table()` in `sharadar.py` uses a stream-to-`.partial`-then-
atomic-rename variant of the same idea, since a multi-hundred-MB transfer can be interrupted mid-write).
P001 and the corrected P004 runner append one line to `docs/prototype/experiments.jsonl`, including failed runs — do not prune it.

**Accounting self-checks are hard failures.** The simulator re-derives each day's PNL from price moves,
dividends, cash interest, execution fees, and fixed fees and raises if it disagrees with the NAV delta; it
also reconciles per-security contributions to ending wealth, and raises on negative cash or on any
evaluation-window session missing from a symbol. Missing data blocks the run instead of being dropped.
Preserve this behavior when changing the engine.

**Timing discipline.** Signals are computed on session `t-1` and executed at the open of `t`; a rebalance
happens on the first session of each month. `pit.py` exposes a filing only after the close of the *next*
trading session and rejects restated (`MR`) dimensions outright — report period and download date must never
substitute for filing date. Cash-yield interest (`macro.py`) is the one exception to needing this kind of
gating: it is applied strictly on the day it was earned using that day's real rate, and never used to make a
forward-looking decision, so it carries no look-ahead risk the way a ranking input would.

**Benchmarks are plural on purpose.** `QQQ` (integer-share ledger, dividends left in cash), `QQQ-cash15`
(same risk overlay as the strategy), and `QQQ-total-return-proxy` (adjusted-close reference, the primary
return yardstick) are reported separately and must not be merged.

## Working rules that shape code changes

Engineering success and investment evidence are separate verdicts and must stay separately labeled. The
current P001 sample is 30 surviving tickers with static present-day sector labels, so no result from it may
be described as validated strategy evidence — the standing decision is `insufficient_evidence`. Do not tune
parameters against the 2021–2025 window that has already been inspected, and do not call it a holdout.
Keep every scenario (capital × cost × variant), including losers; never publish only the winner. A genuinely
new capability proven against real data (quality scoring, a reconstructed historical universe) does not
automatically get folded into an official experiment — it needs its own registered decision saying why it
either is or is not ready to change P001/P003's result, exactly like every other change here.

Documentation is written in Chinese; code comments and identifiers are English. Raw data and run artifacts
stay in the git-ignored `data/` and `runs/`; the real licensed Sharadar cache lives under `data/authorized/`
specifically, and the API key lives only in a git-ignored `.env`, read via `SHARADAR_API_KEY` — never write a
credential into a config file, cache envelope, or persisted URL. Record cross-module decisions in
`docs/review/08-decisions-and-coverage.md` and sources in `07-evidence-register.md`; a dated top-level entry
under `docs/prototype/` (e.g. `2026-09-13-sharadar-session-log.md`) is a good scannable index into a large
batch of same-day 08 entries — write one when a session's changes span several themes, rather than making the
reader reconstruct scope from commit messages.

## Where the authoritative numbers live

`docs/requirements/` is the preserved original vision and is explicitly **not** the current plan; `docs/review/`
supersedes it. User goals and ROI: `review/02`. Strategy parameters: `review/03`. Experiment design and
acceptance: `review/04`. Vendors, budget, and storage: `review/05`. Roadmap: `review/06`. Vendor/license facts
that were independently verified (not just quoted from a pasted summary): `review/07`. Every cross-module
decision, in chronological append-only order: `review/08`. Prototype status and the next experiment's data
gate: `docs/prototype/`.
