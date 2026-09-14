# Repository Guidelines

## Objective & Scope

VITALIS researches personal US equities. Total capital is USD 200,000–400,000; allocation and tax treatment remain unspecified. Prioritize net returns above QQQ, with approximately 30% maximum drawdown as a research limit. Measure holdability through underwater duration, Ulcer, turnover and concentration. Annual aggregate data fees, including relevant broker subscriptions and taxes, must not exceed USD 1,000.

## Bounded Closeout

P005 is the last authorized equity-alpha accounting replay. Follow `docs/prototype/p005-closeout-protocol.json`: no new signals or parameter searches. Credit spinoffs as stock holdings, never `spinoffdividend` cash. Keep ambiguous elections and conflicting dates unverified. Stop current equity-alpha development without a credible joint return/risk/data pass. Missing evidence does not authorize more engineering. Reopening requires a user-authorized hypothesis, budget, acceptance and stop criteria. LEAPS, IBKR, shadow trading, automatic execution, database platforms and product UI are outside this closeout.

## Required Research Loop

Deliver versioned data → frozen rules → holdings/trade/cash ledger → QQQ and risk/cost comparison → continue/revise/stop/insufficient-evidence decision. Register every attempt and failure. Separate engineering success from investment evidence. Month-end M inputs drive only M+1 trades; missing months fail. Unverified settlements fail the data gate. Broader quality peer groups include all matching eligible members. Survivor samples and repeatedly inspected periods are never untouched validation. Critical gaps block recommendations.

## Structure & Data

`vitalis/` contains adapters, simulation and CLIs; `config/` holds inputs and proposed source policy; `tests/` contains checks. `docs/requirements/` preserves the original vision; `docs/review/` evolves specifications. `docs/prototype/` holds protocols and results. Record decisions in review module 08 and sources in 07.

Read pinned local snapshots; acquisition uses separate explicit jobs. Preserve immutable raw files and revisions. Share source limits, coalesce requests, fetch gaps, checkpoint pagination and respect Retry-After. Distinguish official limits from project caps. SQLite is currently a snapshot catalog; Parquet/DuckDB remain proposed. Keep credentials, raw data, databases and private runs in ignored `.env`, `data/`, `runs/`.

## Development & Verification

Use four-space Python, `snake_case`, explicit units and Chinese documentation. Standard library only; justify and lock new dependencies.

```sh
python3 -m unittest discover -s tests -v
python3 -m scripts.closeout --stage spinoff
python3 -m scripts.closeout --stage acquisition
git diff --check
```

Use `unittest`, `tests/test_*.py`; no coverage minimum. Verify accounting, future-data isolation, offline replay, revisions and limits. Check document links and numerical claims. Use imperative commits; PRs explain scope, assumptions, evidence and validation.
