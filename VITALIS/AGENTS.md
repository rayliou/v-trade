# Repository Guidelines

## Objective & Scope

VITALIS researches US equities/options for USD 200,000–400,000 retail capital; allocation and tax treatment remain unspecified. R011 prioritizes whole-account net compound annual growth against QQQ. On 2026-09-19, the user removed the 30% drawdown screen. Still report drawdowns, ruin/financing risk, underwater duration, turnover and concentration. Annual aggregate data fees, including relevant broker subscriptions and taxes, must not exceed USD 1,000.

## Frozen Checkpoint

R011 authorizes public-source retail research; see review module 12. R010 still freezes implementation: P005 closed the original momentum/quality line; P006 rejected hot-volume/short-momentum; P007 only implemented Sharpe ranking and remains unexecuted. Do not purchase data, acquire market datasets, run new variants, tune parameters, or extend execution, databases or UI under the research authorization. Retain prior evidence. A new experiment requires a user-authorized hypothesis, mechanism, budget, data gate and stop rule. Separate leverage/risk premiums from stock-selection alpha.

## Required Research Loop

Deliver versioned data → frozen rules → holdings/trade/cash ledger → QQQ and risk/cost comparison → continue/revise/stop/insufficient-evidence decision. Register every attempt and failure. Separate engineering success from investment evidence. For monthly rules, month-end M inputs drive only M+1 trades; missing months fail. Event rules must respect public disclosure times. Unverified settlements fail the data gate. Broader quality peer groups include all matching eligible members. Survivor samples and repeatedly inspected periods are never untouched validation. Critical gaps block investment recommendations.

## Structure & Data

`vitalis/` contains adapters, simulation and CLIs; `config/` holds inputs and proposed source policy; `tests/` contains checks. `docs/requirements/` preserves the original vision; `docs/review/` evolves specifications. `docs/prototype/` holds protocols and results. Record decisions in review module 08 and sources in 07.

Read pinned local snapshots; acquisition requires separate explicit authorization and currently remains frozen. Preserve immutable raw files and revisions. Share source limits, coalesce requests, fetch gaps, checkpoint pagination and respect Retry-After. Distinguish official limits from project caps. SQLite is currently a snapshot catalog; Parquet/DuckDB remain proposed. Keep credentials, raw data, databases and private runs in ignored `.env`, `data/`, `runs/`.

## Development & Verification

Use four-space Python, `snake_case`, explicit units and Chinese documentation. Standard library only; justify and lock new dependencies.

```sh
python3 -m unittest discover -s tests -v
python3 -m scripts.closeout --stage spinoff
python3 -m scripts.closeout --stage acquisition
git diff --check
```

Use `unittest`, `tests/test_*.py`; no coverage minimum. Verify accounting, future-data isolation, offline replay, revisions and limits. Check document links and numerical claims. Use imperative commits; PRs explain scope, assumptions, evidence and validation.
