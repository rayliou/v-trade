# Repository Guidelines

## Objective & Scope

VITALIS is a personal US-equity research system. Total investment capital is USD 200,000–400,000; strategy allocation and tax treatment remain unspecified. Prioritize net returns above QQQ, with approximately 30% maximum drawdown as a research limit. Measure holdability through underwater duration, Ulcer, turnover, concentration, and forward operational experience. Annual aggregate data fees, including relevant broker subscriptions and taxes, must not exceed USD 1,000.

Current scope: daily equities, historical universe including exits, point-in-time fundamentals, fixed momentum baseline, quality increment, corporate actions, integer-share accounting, costs, and reproducible evaluation. LEAPS, automatic execution, news/graphs, dynamic signal weighting, commercial products, and elaborate UI require separate evidence and scope decisions. IBKR read-only integration follows historical validation; Gateway is not a backtest prerequisite.

## Required Research Loop

Every experiment must deliver versioned data → frozen rules → holdings/trade/cash ledger → QQQ and risk/cost comparison → continue/revise/stop/insufficient-evidence decision. Record all attempts and failures. Separate engineering success from investment evidence. Never certify survivor samples, synthetic fixtures, or repeatedly inspected periods as untouched validation. Missing critical data blocks new recommendations; report gaps explicitly.

## Structure & Data Architecture

`vitalis/` contains adapters, simulation, timing, and CLIs; `config/` holds experiment inputs and proposed source policy; `tests/` contains checks. `docs/requirements/` preserves the original baseline; `docs/review/` contains evolving specifications. `docs/prototype/` holds experiment summaries and onboarding/storage contracts. Record decisions in review module 08 and sources in 07.

Use immutable raw files, versioned Parquet/DuckDB research data, and a SQLite ingestion catalog; deployment remains incremental. No database service is required initially. All research reads pinned local snapshots; remote acquisition belongs in explicit ingestion jobs. Share limits across workers, coalesce duplicate requests, fetch gaps/updates, checkpoint pagination, respect Retry-After, and preserve revisions. Distinguish official limits from provisional project caps. Never log credentials or signed URLs. Raw data, databases, and private runs stay in ignored `data/` and `runs/`.

## Development & Verification

Use four-space Python, `snake_case`, explicit units, and Chinese documentation. Existing CLIs use the standard library; justify and lock new dependencies before adoption.

```sh
python3 -m vitalis.run --offline
python3 -m vitalis.sample_audit --offline
python3 -m unittest discover -s tests -v
git diff --check
```

Use `unittest`, `tests/test_*.py`; no coverage minimum. Check accounting, future-data isolation, zero-network replay, idempotency, revisions, rate limits, and interrupted ingestion when implementing them. Verify documentation links and numerical claims. Commits use concise imperative subjects; PRs explain scope, assumptions, evidence, and validation.
