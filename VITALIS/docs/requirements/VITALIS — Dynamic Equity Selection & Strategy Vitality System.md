# VITALIS
## Dynamic Equity Selection & Strategy Vitality System

**Document Type:** Product / System Requirements Overview  
**Status:** Living Draft  
**Primary Stage:** Personal research and decision-support system  
**Potential Future Stage:** Investable research product  
**Design Principle:** This document is intentionally designed to evolve. New evidence, failed assumptions, new data sources, and new market regimes should result in revision rather than preservation of obsolete design decisions.

---

# 1. Project Definition

**VITALIS** is a quantitative and research-assisted equity selection system for identifying a small set of high-quality, liquid, investable U.S. equities that currently exhibit superior risk-adjusted characteristics without excessive economic overlap.

The system is not intended to predict exact future prices.

Its primary purpose is to continuously answer five questions:

1. Which companies are currently among the strongest investable U.S. equities?
2. Which previously strong companies are beginning to deteriorate?
3. Which market signals still possess useful predictive power under the current market regime?
4. Which apparently different investments are actually exposures to the same underlying economic driver?
5. Which small combination of equities offers the best balance between return potential, resilience, diversification, and actual human holdability?

The system therefore combines:

- quantitative security ranking;
- quality and fundamental analysis;
- momentum and relative-strength analysis;
- downside-risk and holdability analysis;
- options-market information;
- earnings-estimate revisions;
- macro and market-regime analysis;
- company, industry, supplier, customer, and competitor relationships;
- structured event and news extraction;
- portfolio-level exposure analysis;
- strategy-decay and signal-vitality monitoring.

The intended result is not a static model.

It is a **continuously adapting investment observation and decision system**.

---

# 2. Core Philosophy

VITALIS is built around one central idea:

> **Do not attempt to identify permanent winners. Continuously identify which winners are still winning, which signals are still alive, and which risks are being unintentionally duplicated.**

Traditional index systems such as the S&P 500 and Nasdaq-100 benefit from an implicit evolutionary process:

- successful companies become larger;
- weak companies lose weight;
- deteriorating companies eventually become irrelevant or are removed;
- new winners enter.

VITALIS attempts to retain this evolutionary characteristic while adding information that capitalization-weighted indices do not explicitly use.

These additional dimensions include:

- quality;
- earnings revisions;
- risk-adjusted momentum;
- downside behavior;
- options-market expectations;
- valuation;
- industry structure;
- economic dependencies;
- market regimes.

The system should behave more like a **selection ecosystem** than a stock-picking oracle.

---

# 3. Primary Objective

The system's objective is **not**:

> Maximize backtested CAGR at any cost.

The intended optimization target is closer to:

> **Maximize sustainable realized wealth subject to acceptable drawdown, manageable psychological pain, adequate liquidity, and meaningful economic diversification.**

The system should therefore optimize a multi-dimensional utility function including:

- CAGR;
- Sharpe ratio;
- Sortino ratio;
- maximum drawdown;
- Calmar ratio;
- Ulcer Index;
- downside capture;
- time underwater;
- turnover;
- strategy stability;
- contribution concentration;
- economic-exposure concentration.

A strategy with slightly lower CAGR but substantially lower drawdown and underwater duration may be preferable to one with a spectacular backtest that is practically impossible to hold.

---

# 4. What VITALIS Is Not

VITALIS must explicitly avoid becoming:

- a day-trading system;
- a high-frequency trading platform;
- a price-prediction engine;
- a pure technical-analysis screener;
- a pure momentum strategy;
- a news-sentiment chatbot;
- an LLM-generated stock-rating system;
- a portfolio that automatically buys the numerically highest-scoring securities;
- a system optimized to reproduce the strongest historical backtest;
- a system dependent on expensive institutional data terminals.

The system should generate **evidence, rankings, warnings, regime context, and portfolio candidates**.

Final portfolio construction should remain governed by explicit rules and, during the personal-use stage, human review.

---

# 5. Target Investment Universe

The initial system should focus on large and liquid U.S.-listed equities.

The working universe should normally contain approximately **100–200 securities**.

Initial eligibility requirements should include configurable thresholds for:

- market capitalization;
- average daily dollar volume;
- listing venue;
- trading history;
- option availability;
- option liquidity;
- bid/ask quality;
- minimum analyst or fundamental-data coverage.

Possible initial default constraints:

- large- and mega-cap U.S. equities;
- average daily dollar volume sufficient for negligible execution impact at personal-account scale;
- actively traded listed options;
- preferably weekly options;
- preferably available LEAPS;
- exclude highly illiquid securities;
- exclude instruments dominated by one-off binary events unless explicitly classified as such.

The universe itself must be reconstructed historically using **point-in-time membership criteria**.

Today's winners must never be retroactively inserted into historical universes.

---

# 6. System Architecture

VITALIS should be separated into seven functional layers.

## Layer 1 — Security Universe

Answers:

> What is currently investable?

Responsibilities:

- universe construction;
- liquidity filtering;
- market-cap filtering;
- option-liquidity filtering;
- security-master maintenance;
- ticker and corporate-action tracking;
- delisting handling.

Output:

**Eligible Universe**

Approximately 100–200 securities.

---

## Layer 2 — Quantitative Security Engine

Answers:

> Which eligible securities are quantitatively strong?

This engine calculates objective factors from historical and current data.

Primary groups:

### Momentum

Possible inputs:

- 12-1 month momentum;
- 6-1 month momentum;
- 3-month relative strength;
- 20-day acceleration;
- performance relative to SPY, QQQ, sector, and industry;
- trend consistency.

A possible conceptual structure:

`Momentum Score = Long-Horizon Momentum + Medium-Horizon Relative Strength + Short-Horizon Acceleration`

Very short-term performance must not dominate the ranking.

Two-week or one-month Sharpe can be used as an acceleration or deterioration indicator, but not as the core signal.

---

### Holdability

This is a first-class factor, not a cosmetic metric.

Possible inputs:

- 63-day Sortino;
- 126-day Sharpe;
- Calmar ratio;
- maximum drawdown;
- Ulcer Index;
- downside beta;
- downside capture;
- time underwater;
- drawdown frequency;
- recovery speed.

The purpose is to distinguish between:

> high-return securities

and:

> high-return securities that a real human can realistically continue holding.

---

### Fundamental Quality

Possible inputs:

- revenue growth;
- EPS growth;
- free-cash-flow growth;
- FCF margin;
- operating margin;
- margin stability;
- ROIC;
- leverage;
- interest coverage;
- balance-sheet strength.

The system should prefer sustainable business improvement over superficial low valuation.

---

### Earnings and Revenue Revisions

Revision signals should eventually become a major fundamental input.

Possible measures:

- one-month EPS consensus change;
- three-month EPS consensus change;
- revenue consensus change;
- number of upward revisions;
- number of downward revisions;
- revision breadth;
- changes in next-twelve-month estimates.

The system should distinguish:

> cheap because expectations are rising

from:

> cheap because earnings are collapsing.

---

### Valuation Context

Valuation should be relative rather than purely absolute.

Possible measures:

- forward P/E;
- EV/EBITDA;
- FCF yield;
- forward sales multiple;
- valuation versus own five-year history;
- valuation versus peers;
- valuation versus growth;
- valuation versus ROIC;
- valuation versus current earnings-revision trend.

A low P/E must never automatically produce a high score.

---

# 7. Options Intelligence Layer

Options data should be treated primarily as a **market-expectation and stress sensor**, not as the core long-term alpha engine.

The system should maintain two separate outputs:

## Options Sentiment

Measures directional positioning.

Potential inputs:

- call versus put volume;
- call versus put open interest;
- delta-weighted put/call ratios;
- call-side demand;
- changes in skew.

## Options Stress

Measures how much protection or convexity the market is demanding.

Potential inputs:

- ATM implied volatility;
- IV percentile;
- IV rank;
- realized volatility;
- variance risk premium;
- 25-delta put skew;
- 25-delta call skew;
- volatility term structure;
- unusual changes in open interest;
- earnings-related volatility distortions.

Important derived measures may include:

`VRP = IV² – RealizedVol²`

and:

`25D Skew = IV(25Δ Put) – IV(25Δ Call)`

Option-flow calculations should preferably exclude extremely low-delta lottery contracts and use standardized DTE ranges.

A future implementation may calculate delta-weighted put/call activity only for contracts within ranges such as:

- 7–90 DTE;
- absolute delta between approximately 0.15 and 0.70.

Options data must not be interpreted mechanically.

For example:

- low IV is not automatically bullish;
- high put volume is not automatically bearish;
- high call volume may reflect selling rather than buying;
- open interest is not equivalent to new directional positioning.

---

# 8. Event and Information Layer

VITALIS should not ask an LLM:

> Is today's news bullish or bearish?

That design is too ambiguous and difficult to validate.

Instead, the information layer should convert text into structured events.

Example event classes:

- demand increase/decrease;
- customer win/loss;
- backlog increase/decrease;
- pricing increase/decrease;
- capacity expansion;
- supply constraint;
- guidance increase/cut;
- earnings surprise;
- capital expenditure change;
- acquisition;
- divestiture;
- regulatory action;
- export restriction;
- product launch;
- product failure;
- executive departure;
- financing;
- buyback;
- dividend change.

Where possible, events should contain measurable fields:

`metric`

`old_value`

`new_value`

`percentage_change`

`event_date`

`publication_time`

`source`

`confidence`

The LLM's role should primarily be:

> **information extraction and contextual explanation**

rather than numerical alpha generation.

---

# 9. Economic Relationship Graph

Traditional sector classification is insufficient.

VITALIS should eventually maintain a graph containing entities such as:

- companies;
- customers;
- suppliers;
- competitors;
- products;
- technologies;
- commodities;
- countries;
- market themes;
- macro drivers.

Possible relationships include:

`Company → Customer`

`Company → Supplier`

`Company → Competitor`

`Company → Product`

`Company → Commodity Exposure`

`Company → Revenue Driver`

`Company → CapEx Driver`

Example:

NVDA, AVGO, MU, and VRT may belong to different formal industries but share a major underlying driver:

> hyperscaler AI capital expenditure.

The graph is therefore primarily a **portfolio risk and overlap tool**.

Its initial purpose is not to generate backtested alpha.

---

# 10. Macro and Market-Regime Engine

Signals should not be assumed to work equally under all market regimes.

The regime engine should describe conditions such as:

- growth acceleration/deceleration;
- inflation acceleration/deceleration;
- monetary tightening/easing;
- credit expansion/stress;
- low/high volatility;
- market breadth;
- yield-curve state;
- commodity regime;
- liquidity regime.

Potential inputs include:

- policy rate;
- 2Y Treasury;
- 10Y Treasury;
- yield curve;
- inflation;
- unemployment;
- credit spreads;
- VIX;
- USD;
- oil;
- industrial production;
- breadth indicators.

The regime layer should modify confidence or allowable exposure rather than continuously optimize dozens of factor weights.

---

# 11. Multi-Horizon Signal Architecture

Signals decay at different speeds.

VITALIS must not combine them as though they share the same useful horizon.

## Slow Signals

Typical horizon:

6 months to several years.

Examples:

- ROIC;
- balance-sheet quality;
- competitive position;
- industry structure;
- durable customer relationships.

## Medium Signals

Typical horizon:

1–12 months.

Examples:

- momentum;
- relative strength;
- earnings revisions;
- revenue revisions;
- improving margins.

## Fast Signals

Typical horizon:

days to weeks.

Examples:

- options skew;
- option flow;
- news/event shocks;
- volume acceleration;
- earnings reactions.

Fast signals should normally affect:

> timing, confidence, stress, and risk sizing

rather than redefining:

> whether the company is fundamentally high quality.

---

# 12. Dynamic Ranking Model

The initial scoring system should remain intentionally simple.

An example high-level structure may be:

`Total Score = Momentum + Holdability + Fundamentals + Options + Regime`

A preliminary weighting concept could be approximately:

- 30% Momentum / Relative Strength
- 25% Holdability
- 25% Fundamental + Revisions
- 10% Options
- 10% Industry / Regime

However, these values are hypotheses, not fixed product requirements.

They must be tested.

The system must avoid optimizing weights to excessive precision.

For example, weights such as:

23.74%, 17.81%, 31.26%

should be treated as suspicious.

Prefer coarse and interpretable weights such as:

0%, 10%, 20%, 30%, 40%.

---

# 13. Watchlist State Machine

A security should not simply be classified as BUY or SELL.

VITALIS should maintain persistent states.

Possible states:

## A — Core Candidate

Strong ranking and no major structural warning.

## B — Watch

Strong enough to remain under active observation.

## C — Deteriorating

Previously strong but showing multi-factor weakening.

## D — Removed

No longer qualifies for active consideration.

A separate:

## Risk Flag

should be possible regardless of ranking.

Examples:

- major guidance cut;
- severe revision deterioration;
- extreme downside skew;
- loss of major customer;
- accounting concern;
- regulatory intervention.

---

# 14. Hysteresis and Turnover Control

The ranking system must avoid excessive churn.

Entering and leaving the watchlist should require different thresholds.

Example conceptual rule:

Enter:

`Rank ≤ 20`

Remain:

`Rank ≤ 35`

Remove:

`Rank > 35 for two consecutive review periods`

This hysteresis prevents insignificant rank changes such as:

#19 → #22 → #18

from generating unnecessary portfolio actions.

Update cadence should also differ by layer.

Possible defaults:

**Daily**

- prices;
- current options;
- events;
- alerts.

**Weekly**

- rankings;
- momentum;
- holdability;
- options state;
- deterioration.

**Monthly**

- portfolio rebalancing review.

Immediate review should occur only after a material hard event.

---

# 15. Portfolio Construction

The ranking system and portfolio constructor must be separate systems.

High individual scores do not guarantee a good combination.

The funnel should conceptually be:

**100–200 Eligible Securities**

↓

**Top 20–30 Research Watchlist**

↓

**Top 8–12 Portfolio-Eligible Candidates**

↓

**Economic-Exposure and Risk Filtering**

↓

**Final Portfolio**

The final number of holdings must be determined empirically.

The system should test:

- Top 3;
- Top 5;
- Top 8;
- Top 10;
- Top 20.

The design must not assume in advance that three or four securities are optimal.

---

# 16. Portfolio Independence

Portfolio diversification should be evaluated through more than return correlation.

VITALIS should examine:

- return correlation;
- downside correlation;
- sector;
- industry;
- customer overlap;
- supplier overlap;
- commodity exposure;
- capital-expenditure driver;
- interest-rate sensitivity;
- geographic exposure;
- policy exposure;
- business-model similarity.

For example:

NVDA + AVGO + MU + VRT

may be treated as substantially fewer than four independent bets.

The goal is not maximum numerical diversification.

The goal is:

> **independent economic drivers with individually strong securities.**

---

# 17. Position Sizing

Equal-dollar weighting should not be the default assumption.

Candidate methods include:

- inverse volatility;
- inverse downside volatility;
- equal risk contribution;
- capped conviction weighting.

Risk sizing should consider:

- downside volatility;
- expected drawdown;
- economic overlap;
- options exposure;
- concentration limits.

The system must support position caps.

Potential constraints:

- maximum security weight;
- maximum structural-theme exposure;
- maximum high-beta exposure;
- maximum options leverage;
- maximum effective delta exposure.

---

# 18. Personal Trader Layer

VITALIS is initially designed for an individual investor, not an institutional fund.

This matters.

An individual may have advantages unavailable to institutions:

- low capacity requirements;
- freedom to hold cash;
- ability to ignore benchmarks;
- ability to concentrate selectively;
- ability to use LEAPS;
- negligible market impact;
- ability to remain inactive;
- no redemption pressure;
- no mandate forcing continuous exposure.

The system should therefore optimize **personal utility**, not institutional tracking error.

Relevant configurable preferences include:

- maximum acceptable drawdown;
- desired number of holdings;
- willingness to hold cash;
- acceptable leverage;
- use of options;
- holding horizon;
- tax consequences;
- financing cost;
- psychological tolerance for volatility.

This layer should be configurable rather than embedded into universal stock scores.

---

# 19. Backtesting Philosophy

VITALIS explicitly rejects the idea that:

> a strategy that worked from 2007–2026 should automatically be trusted in 2027.

Long historical data remains valuable, but for different purposes.

## Full-History Testing

Purpose:

- catastrophic failure detection;
- stress testing;
- regime diversity.

Old data should not receive equal weight when estimating current alpha.

## Rolling Analysis

Required windows may include:

- rolling 3-year;
- rolling 5-year;
- rolling 8-year.

Track over time:

- Sharpe;
- Sortino;
- Information Coefficient;
- drawdown;
- turnover;
- factor contribution.

## Walk-Forward Testing

This should be the primary evidence.

Example:

Train:

2015–2019

Test:

2020

Then:

2016–2020 → 2021

2017–2021 → 2022

and so forth.

Future data must never influence historical parameter selection.

## Recent-Regime Validation

Recent market structure should receive greater relevance when deciding whether a signal is currently usable.

---

# 20. Signal Vitality

A defining feature of VITALIS is that the **strategies themselves are ranked and monitored**.

The system must not only ask:

> Which stock is strong?

It must also ask:

> Is momentum still useful?

> Is earnings revision still predictive?

> Has this options signal decayed?

Each factor should maintain a **Signal Vitality Profile**.

Possible inputs:

- recent Information Coefficient;
- rolling Sharpe;
- rolling hit rate;
- alpha half-life;
- cross-sectional breadth;
- parameter stability;
- contribution concentration;
- regime dependence.

A conceptual measure may be:

`Vitality = Recent Predictive Power + Recent Risk-Adjusted Performance + Stability + Breadth`

A factor showing:

IC = 0.08 → 0.05 → 0.02 → 0.00

should lose importance even if its twenty-year average remains attractive.

---

# 21. Alpha Decay Analysis

Each signal should be tested across forecast horizons.

For example:

1D  
5D  
20D  
60D  
120D  
252D

Calculate:

`IC(horizon)`

The resulting alpha-decay curve reveals whether a signal's useful lifetime has shortened.

Possible outcomes:

- options flow predicts only several days;
- earnings revision predicts several months;
- momentum predicts several months;
- quality operates over multi-year horizons.

Signals must be applied according to their natural horizon.

---

# 22. Robustness Requirements

A strategy must not be accepted because one optimized parameter produces a beautiful curve.

The system should test nearby parameter values.

Example:

If 63-day momentum works but:

60 days fails  
65 days fails  
70 days fails

the signal should be considered fragile.

Good signals should survive modest changes to:

- lookback;
- rebalance date;
- weighting;
- universe threshold;
- transaction cost assumptions;
- entry threshold;
- exit threshold.

---

# 23. Contribution Concentration

A strategy whose historical success comes primarily from one or two exceptional securities should not be treated as broadly validated.

The system must measure:

- contribution by security;
- contribution by sector;
- contribution by theme;
- contribution by regime.

Possible concentration statistics include:

- top-1 contribution;
- top-5 contribution;
- HHI;
- effective number of contributors.

If most historical alpha came from a single security, strategy confidence should be reduced.

---

# 24. Required Backtest Outputs

Every strategy variation should report at least:

- CAGR;
- annualized volatility;
- Sharpe;
- Sortino;
- maximum drawdown;
- Calmar;
- Ulcer Index;
- downside capture;
- worst month;
- worst quarter;
- time underwater;
- turnover;
- hit rate;
- rolling 3Y Sharpe;
- rolling 5Y Sharpe;
- Information Coefficient;
- alpha decay;
- contribution concentration;
- average number of holdings;
- sector concentration;
- economic-driver concentration.

An equity curve alone is insufficient.

---

# 25. Data Architecture

The system should not depend on one vendor.

A layered data architecture is preferred.

## IBKR

Primary role:

**Current Market + Options + Portfolio + Execution**

Use for:

- real-time stock quotes;
- historical price bars where appropriate;
- current IV;
- current options;
- open interest;
- options volume;
- current volatility metrics;
- account positions;
- portfolio exposure;
- eventual execution.

IBKR should not be treated as the master historical research database.

---

## SEC EDGAR

Primary role:

**Authoritative corporate disclosures**

Use for:

- 10-K;
- 10-Q;
- 8-K;
- XBRL facts;
- filings;
- event extraction.

Cost target:

**Free**

---

## FRED / ALFRED

Primary role:

**Macro and point-in-time macro history**

Use for:

- rates;
- inflation;
- unemployment;
- credit conditions;
- economic releases;
- macro vintages.

Cost target:

**Free**

---

## Point-in-Time Fundamental Dataset

Potential source:

Sharadar or equivalent.

Purpose:

- historical fundamentals;
- delisted companies;
- historical universes;
- filing dates;
- restatement-aware values;
- survivorship-bias control.

This should be purchased only when serious historical testing requires it.

---

## Historical Options

Potential source:

ORATS or equivalent.

Purpose:

- historical IV surfaces;
- Greeks;
- skew;
- term structure;
- historical options backtesting.

Do not initially purchase expensive intraday data.

Near-EOD historical data is sufficient for the first serious options study.

---

## Estimates / Revisions

Possible sources:

- Alpha Vantage initially;
- professional estimates dataset later if justified.

This layer should be added only after the base model demonstrates value.

---

## Historical News

Not a Phase-1 dependency.

Long-horizon point-in-time news archives are comparatively expensive and messy.

Initial substitutes:

- SEC filings;
- earnings calls;
- guidance;
- structured corporate events.

From the start of live operation, VITALIS should archive its own news/event history so that a proprietary point-in-time dataset gradually develops.

---

# 26. Cost Constraint

VITALIS must be designed as a **low-cost personal research system**.

Phase-1 incremental data cost target:

> approximately zero to tens of dollars per month.

Phase-2 may justify:

> several hundred dollars of one-time historical-data purchases.

The system should not initially require:

- Bloomberg;
- FactSet;
- Refinitiv/LSEG enterprise terminals;
- expensive real-time institutional feeds;
- institutional supply-chain datasets.

No expensive data source should be purchased unless an incremental-alpha test demonstrates that the data materially improves:

- Sharpe;
- Sortino;
- drawdown;
- signal stability;
- portfolio decisions.

---

# 27. Computing Constraint

The system should run on a normal personal workstation.

It should not require:

- GPU clusters;
- cloud data warehouses;
- distributed compute;
- low-latency infrastructure.

Preferred initial environment:

- Python;
- Polars and/or Pandas;
- DuckDB;
- Parquet;
- SQLite or PostgreSQL;
- scheduled daily jobs;
- local or inexpensive LLM inference where appropriate.

Optional cloud deployment may be added later.

The initial implementation should remain reproducible on a single machine.

---

# 28. Suggested Data Tables

The internal data model should eventually contain tables resembling:

`security_master`

`daily_price`

`corporate_action`

`universe_snapshot`

`fundamental_pit`

`estimate_revision`

`option_surface_daily`

`option_contract_snapshot`

`macro_vintage`

`event_fact`

`company_relationship`

`factor_snapshot`

`factor_vitality`

`ranking_snapshot`

`portfolio_candidate`

`portfolio_snapshot`

`backtest_run`

`strategy_version`

This structure allows every historical decision to be reconstructed.

---

# 29. Explainability Requirement

Every ranking change should be explainable.

If a company changes from:

Rank #4 → Rank #18

the system should be able to state:

- momentum contribution changed by X;
- relative strength deteriorated;
- revisions remained stable;
- options stress increased;
- valuation changed;
- no fundamental warning detected.

The explanation must derive from stored data.

The LLM should explain the evidence.

It should not invent the evidence.

---

# 30. Desired User Interface

The primary interface should be a persistent master table.

Potential columns:

- Symbol;
- Sector;
- Structural Theme;
- Market Cap;
- Liquidity;
- 20D Return;
- 60D Return;
- 12-1 Momentum;
- Relative Strength;
- Sharpe;
- Sortino;
- Max Drawdown;
- Ulcer Index;
- EPS Revision;
- Revenue Revision;
- Quality Score;
- Valuation Score;
- IV;
- IV Percentile;
- IV–RV;
- Put/Call;
- Skew;
- Option Stress;
- Regime Fit;
- Composite Score;
- Rank;
- Previous Rank;
- State;
- Risk Flags.

Each security should have a detail view showing:

- score decomposition;
- score history;
- rank history;
- fundamental trends;
- revisions;
- option state;
- price regime;
- major structured events;
- major competitors;
- customers;
- suppliers;
- economic exposure;
- portfolio overlap.

---

# 31. Strategy Dashboard

The system should also rank **strategies and factors**.

Examples:

| Signal | Current Vitality | 3Y IC | 3Y Sharpe | Trend | Status |
|---|---:|---:|---:|---|---|
| 12-1 Momentum | 74 | | | Stable | Active |
| Quality | 82 | | | Improving | Active |
| EPS Revision | 88 | | | Strong | Active |
| Option Skew | 55 | | | Decaying | Reduced |
| Short-Term Momentum | 21 | | | Weak | Disabled |

This is a core differentiator of VITALIS.

The system is not only a stock dashboard.

It is:

> **a dashboard for whether the investment logic itself is still working.**

---

# 32. Kill Criteria

Development must stop or a factor must be rejected when evidence does not support it.

Examples:

- out-of-sample Sharpe improvement < 0.10;
- no meaningful drawdown improvement;
- no persistent Information Coefficient;
- performance disappears under reasonable transaction costs;
- only one short historical period works;
- nearby parameter values fail;
- performance depends on a few exceptional stocks;
- signal has clearly decayed in recent years;
- implementation cost exceeds measurable incremental benefit.

The purpose of a failed experiment is to eliminate an unproductive idea quickly.

---

# 33. Success Criteria

The initial project should not promise extraordinary returns.

A successful system should aim to produce one or more of the following:

- equal or higher CAGR than a relevant benchmark;
- meaningfully higher Sharpe;
- meaningfully higher Sortino;
- materially smaller drawdown;
- lower Ulcer Index;
- shorter time underwater;
- lower hidden thematic concentration;
- better identification of deteriorating former winners;
- more disciplined replacement of weak holdings;
- reduced emotional decision-making.

A possible aspirational result might resemble:

Benchmark:

CAGR 16%  
Sharpe 0.8  
Max Drawdown -35%

VITALIS:

CAGR 17–19%  
Sharpe approximately 1.0+  
Max Drawdown approximately -20% to -28%

These are design aspirations, not promised outcomes.

The project should be considered successful even if CAGR remains similar to the benchmark while risk-adjusted returns and holdability materially improve.

---

# 34. Development Sequence

## Phase 0 — Research Specification

Freeze:

- universe definition;
- metrics;
- bias controls;
- benchmark;
- backtest protocol;
- kill criteria.

No dashboard work yet.

---

## Phase 1 — Core Quant Engine

Implement only:

- price;
- liquidity;
- momentum;
- relative strength;
- quality;
- holdability;
- hysteresis;
- portfolio concentration.

Goal:

Determine whether the basic framework improves risk-adjusted performance.

If not, stop or redesign.

---

## Phase 2 — Point-in-Time Fundamentals and Revisions

Add:

- proper historical universe;
- fundamentals;
- earnings revisions;
- valuation context.

Perform incremental-alpha tests.

---

## Phase 3 — Options Intelligence

Add:

- IV percentile;
- IV/RV;
- skew;
- term structure;
- delta-weighted put/call measures;
- options stress.

Again test incremental contribution.

---

## Phase 4 — Market Regime

Add conditional signal weighting and regime diagnostics.

Do not permit unrestricted optimization.

---

## Phase 5 — Economic Relationship Graph

Add:

- customers;
- suppliers;
- competitors;
- commodities;
- structural themes.

Use first for portfolio overlap and risk control.

---

## Phase 6 — Event Intelligence

Add structured extraction from:

- SEC;
- earnings calls;
- selected news;
- company announcements.

The LLM acts as an extractor and research assistant.

---

## Phase 7 — Personal Decision System

Integrate:

- portfolio holdings;
- cash;
- margin;
- options;
- tax-aware considerations;
- position sizing;
- replacement analysis.

---

## Phase 8 — Productization

Only after prolonged successful personal use should VITALIS be considered for external users.

Productization must not precede demonstrated usefulness.

---

# 35. Core Design Principles

The system should continuously follow these principles:

**Evidence over narrative.**

**Recent predictive power over historical reputation.**

**Point-in-time data over convenient hindsight.**

**Walk-forward evidence over optimized full-history curves.**

**Robustness over precision.**

**Risk-adjusted wealth over maximum headline return.**

**Economic diversification over ticker diversification.**

**Structured facts over vague sentiment.**

**Incremental-alpha testing over feature accumulation.**

**Human holdability over theoretical optimality.**

**Signals may die. Models must be allowed to change.**

---

# 36. The Central Product Question

Every future feature should answer:

> **Does this information help us identify stronger securities, detect deterioration earlier, reduce hidden risk, improve timing, or improve the probability that the resulting portfolio can actually be held?**

If the answer cannot be demonstrated quantitatively or operationally, the feature should not be added simply because it is interesting.

---

# 37. Long-Term Vision

The mature form of VITALIS should function as a personal **Investment Operating System**.

At any moment it should be possible to ask:

> What are the strongest investable companies now?

> Which former leaders are deteriorating?

> Which sectors or economic drivers are strengthening?

> Which positions are secretly the same bet?

> Which options markets are signaling unusual stress?

> Which fundamental expectations are being revised?

> Which strategies that worked historically are currently losing predictive power?

> What changed since last week?

> If capital must be allocated today, what are the best independent opportunities available?

Its purpose is not to eliminate uncertainty.

Its purpose is to convert a very large, noisy market into a smaller, continuously maintained set of **high-quality decisions with explicit evidence, explicit uncertainty, and explicit risk**.

---

# 38. Living-Document Rule

This document must remain versioned.

Every important design change should record:

- date;
- previous assumption;
- new assumption;
- evidence causing the change;
- expected impact;
- validation requirement.

No design decision should be treated as permanent merely because it appeared in an earlier version.

VITALIS should apply to itself the same rule it applies to investment strategies:

> **Anything that stops working must be allowed to change.**