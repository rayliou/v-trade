"""Fixed-rule, next-open simulation with integer shares and cash accounting."""

import math
import statistics


def percentile(values):
    result = {}
    for symbol, value in values.items():
        less = sum(x < value for x in values.values())
        equal = sum(x == value for x in values.values())
        result[symbol] = (less + (equal - 1) / 2) / max(1, len(values) - 1)
    return result


def rank_signals(bars, dates, index, symbols, minimum_adv, quality_by_symbol=None,
                 formation="12-1/6-1"):
    """quality_by_symbol=None (default) ranks on momentum alone, unchanged from
    before -- P001's existing M10/M20/M10-risk15 behavior is untouched. When
    given a {symbol: quality-score-in-[0,1]} dict (vitalis.quality.quality_scores()'s
    "quality" field), docs/review/03 section 2's pre-registered S1 formula
    applies: Total Score = 0.5*momentum + 0.5*quality. A momentum-eligible
    symbol missing from quality_by_symbol gets the same neutral 0.5 quality.py
    itself uses for excluded sectors/missing data, rather than being dropped
    from the ranking -- that keeps the eligible pool identical to the
    momentum-only run, so a quality-vs-momentum comparison is not silently
    also a universe change.

    formation selects the momentum window and defaults to the original
    "12-1/6-1" blend (12- and 6-month returns, both skipping the most recent
    month). "1m" is P006's pre-registered single window: the plain trailing
    21-session return as of the signal day, no skip. That window sits on the
    boundary between documented short-horizon reversal and intermediate
    momentum, so its sign is not assumed -- see the P006 entry in
    docs/review/08-decisions-and-coverage.md. Either way the 252-session
    history requirement below is unchanged, so the eligible pool does not
    silently widen when the formation window shortens.
    """
    if index < 252:
        return []
    signals = {}
    for symbol in symbols:
        series = bars[symbol]
        required = dates[index - 252:index + 1]
        if not all(day in series for day in required):
            continue
        adv = statistics.mean(series[d]["dollar_volume"] for d in dates[index - 62:index + 1])
        if adv < minimum_adv:
            continue
        if formation == "1m":
            signals[symbol] = {
                "m1": (series[dates[index]]["adjclose"]
                       / series[dates[index - 21]]["adjclose"] - 1),
                "adv_usd": adv,
            }
            continue
        price = series[dates[index - 21]]["adjclose"]
        signals[symbol] = {
            "m12_1": price / series[dates[index - 252]]["adjclose"] - 1,
            "m6_1": price / series[dates[index - 126]]["adjclose"] - 1,
            "adv_usd": adv,
        }
    if formation == "1m":
        momentum_score = percentile({s: x["m1"] for s, x in signals.items()})
    else:
        first = percentile({s: x["m12_1"] for s, x in signals.items()})
        second = percentile({s: x["m6_1"] for s, x in signals.items()})
        momentum_score = {s: (first[s] + second[s]) / 2 for s in signals}
    if quality_by_symbol is None:
        total_score = momentum_score
    else:
        total_score = {s: 0.5 * momentum_score[s] + 0.5 * quality_by_symbol.get(s, 0.5) for s in signals}
    ordered = sorted(signals, key=lambda s: (-total_score[s], s))
    return [{"symbol": s, "rank": i + 1, "score": total_score[s], "momentum_score": momentum_score[s],
             **signals[s]} for i, s in enumerate(ordered)]


def choose(ranking, held, count, sectors, sector_cap):
    ranks = {row["symbol"]: row["rank"] for row in ranking}
    retained = sorted((s for s in held if s in ranks and ranks[s] <= 2 * count), key=ranks.get)
    entrants = [row["symbol"] for row in ranking if row["rank"] <= count]
    selected, allocation = [], {}
    for symbol in retained + entrants:
        sector = sectors[symbol]
        if symbol in selected or len(selected) == count:
            continue
        if allocation.get(sector, 0) + 1 / count > sector_cap + 1e-10:
            continue
        selected.append(symbol)
        allocation[sector] = allocation.get(sector, 0) + 1 / count
    return selected


def risk_fraction(bars, dates, index, selected, count, target_vol):
    if not selected or index < 63:
        return 0.0
    basket_returns = []
    for j in range(index - 62, index + 1):
        basket_returns.append(sum(
            bars[s][dates[j]]["adjclose"] / bars[s][dates[j - 1]]["adjclose"] - 1
            for s in selected) / count)
    vol = statistics.stdev(basket_returns) * math.sqrt(252)
    if not math.isfinite(vol) or vol <= 1e-12:
        return 0.0
    return min(1.0, target_vol / vol)


def metrics(nav, initial):
    """Required-output metrics per docs/review/04-validation-protocol.md section 6.

    Sortino uses a zero target return and the full-sample semi-deviation
    denominator (not just the count of down days); Sharpe and Sortino are both
    undefined (None), never an unbounded number, when their denominator is zero.
    Calmar is undefined with no drawdown or under a year of sessions, matching
    "Calmar在无回撤或历史不足时也不强出数". Hit rate is defined here at the daily
    session level (share of positive-return trading days), not per trade or
    per rebalance; that definition must travel with any use of the number.
    """
    values = [initial] + [row["nav_usd"] for row in nav]
    # A fund driven to exactly zero NAV and capped there (engine.simulate()'s
    # fixed-fee-at-ruin handling) stays at zero every subsequent session --
    # define that as a 0% return (no change) rather than an undefined 0/0,
    # since a dead account cannot spontaneously move again either way.
    returns = [0.0 if a == 0 else b / a - 1 for a, b in zip(values, values[1:])]
    high, worst, underwater, longest = initial, 0.0, 0, 0
    squared = []
    for value in values[1:]:
        high = max(high, value)
        dd = value / high - 1
        worst = min(worst, dd)
        squared.append((dd * 100) ** 2)
        underwater = underwater + 1 if value < high - 1e-8 else 0
        longest = max(longest, underwater)
    volatility = statistics.stdev(returns) * math.sqrt(252) if len(returns) > 1 else 0
    downside_squared = [min(r, 0.0) ** 2 for r in returns]
    downside_deviation = math.sqrt(statistics.mean(downside_squared)) * math.sqrt(252)
    monthly, quarterly = {}, {}
    for row, ret in zip(nav, returns):
        month = row["date"][:7]
        quarter = row["date"][:4] + "Q" + str((int(row["date"][5:7]) - 1) // 3 + 1)
        monthly[month] = monthly.get(month, 1.0) * (1 + ret)
        quarterly[quarter] = quarterly.get(quarter, 1.0) * (1 + ret)
    cagr = (values[-1] / initial) ** (252 / len(returns)) - 1
    return {
        "cagr": cagr,
        "annual_volatility": volatility,
        "sharpe_zero_rf": statistics.mean(returns) * 252 / volatility if volatility else None,
        "sortino_zero_target": statistics.mean(returns) * 252 / downside_deviation if downside_deviation else None,
        "max_drawdown": worst,
        "calmar_ratio": cagr / abs(worst) if worst and len(returns) >= 252 else None,
        "ulcer_index_percentage_points": math.sqrt(statistics.mean(squared)),
        "longest_underwater_trading_days": longest,
        "current_underwater_trading_days": underwater,
        "worst_month": min(monthly.values()) - 1,
        "worst_quarter": min(quarterly.values()) - 1,
        "hit_rate_positive_sessions": sum(1 for r in returns if r > 0) / len(returns),
        "ending_nav_usd": values[-1],
        "sessions": len(returns),
    }


def downside_capture_ratio(strategy_returns, benchmark_returns):
    """Compounded downside capture: strategy's compounded return on benchmark-down
    sessions divided by the benchmark's own compounded return on those same
    sessions. Requires date-aligned, equal-length paired daily return series.
    None when the benchmark has no down session in the window (undefined, not zero).
    """
    if len(strategy_returns) != len(benchmark_returns):
        raise ValueError("Downside capture requires paired, equal-length return series")
    down_days = [i for i, r in enumerate(benchmark_returns) if r < 0]
    if not down_days:
        return None
    strategy_compounded = math.prod(1 + strategy_returns[i] for i in down_days) - 1
    benchmark_compounded = math.prod(1 + benchmark_returns[i] for i in down_days) - 1
    if benchmark_compounded == 0:
        return None
    return strategy_compounded / benchmark_compounded


def simulate(bars, dates, config, capital, cost_bps, variant, cash_annual_rate=None,
            symbols_by_review_month=None, quality_by_review_month=None,
            corporate_actions_by_date=None):
    """variant "Q10"/"Q20" (docs/review/03 section 2's S1 candidate) rank on
    0.5*momentum + 0.5*quality via quality_by_review_month (a {"YYYY-MM":
    {symbol: quality_score}} dict, e.g. from vitalis.quality.quality_scores());
    "M10"/"M20"/"M10-risk15" rank on momentum alone, exactly as before --
    quality_by_review_month is simply unused for those variants.

    P006's "H3"/"H5" hold 3/5 names ranked on the 1-month formation window.
    They deliberately do NOT use the 0.5/0.5 quality blend: P006 applies
    quality as a bottom-quantile exclusion on the eligible pool itself
    (vitalis.quality.excluded_by_quality_threshold), upstream of ranking, so
    quality_by_review_month stays unused for them too.
    """
    start, end = config["evaluation_start"], config["evaluation_end"]
    sessions = [d for d in dates if start <= d <= end]
    if not sessions:
        raise ValueError("No evaluation sessions")
    symbols = config["symbols"]
    is_benchmark = variant in ("QQQ", "QQQ-cash15")
    risk_control = variant in ("QQQ-cash15", "M10-risk15")
    holdings_by_variant = {"H3": 3, "H5": 5, "M20": 20, "Q20": 20}
    count = 1 if is_benchmark else holdings_by_variant.get(variant, 10)
    uses_quality = variant in ("Q10", "Q20")
    formation = "1m" if variant in ("H3", "H5") else "12-1/6-1"
    cash, held = float(capital), {}
    trades, ledger, holdings, decisions, warnings = [], [], [], [], []
    contributions = {}
    inherited = {}
    corporate_total = 0.0
    cost_rate = cost_bps / 10000
    total_cost, gross_traded, turnover, dividends_total, fixed_total = 0.0, 0.0, 0.0, 0.0, 0.0
    interest_total = 0.0
    prior_close_nav = capital
    for day in sessions:
        index = dates.index(day)
        if index == 0:
            raise ValueError("Evaluation requires a preceding signal date")
        signal_day = dates[index - 1]
        beginning_cash = cash
        action_dividend = 0.0
        overnight_pnl = 0.0
        day_fees = 0.0
        corporate_pnl = 0.0
        additions = []
        prior_held = dict(held)
        events = (corporate_actions_by_date or {}).get(day, [])
        mergers = {e['symbol']: e for e in events if e['kind'] == 'acquisition'}
        for event in events:
            if event['kind'] == 'unresolved' and event['symbol'] in prior_held:
                warnings.append({'date': day, 'symbol': event['symbol'],
                                 'flag': 'corporate_action_unresolved', 'reason': event['reason']})
        for symbol in list(held):
            if symbol in mergers:
                from .corporate_actions import entitlement
                event = mergers[symbol]
                quantity = held.pop(symbol)
                action_cash, action_shares, action_value = entitlement(event, quantity, bars, day)
                cash += action_cash
                additions.extend(action_shares)
                pnl = action_cash + action_value - quantity * bars[symbol][signal_day]['close']
                corporate_pnl += pnl
                contributions.setdefault(symbol, {'price_pnl_usd': 0.0, 'dividends_usd': 0.0,
                    'execution_cost_usd': 0.0}).setdefault('corporate_action_pnl_usd', 0.0)
                contributions[symbol]['corporate_action_pnl_usd'] += pnl
                inherited.pop(symbol, None)
                warnings.append({'date': day, 'symbol': symbol, 'flag': 'corporate_acquisition_scenario',
                    'source_date': event['source_date'], 'quantity': quantity,
                    'cash_consideration_usd': action_cash, 'stock_value_at_open_usd': action_value,
                    'corporate_action_pnl_usd': pnl, 'received_shares': action_shares,
                    'settlement_verified': False})
                continue
            if day not in bars[symbol]:
                if signal_day not in bars[symbol]:
                    raise ValueError(f"No bar for held position {symbol} on {day} or {signal_day} "
                                     f"({variant}); cannot determine a settlement price")
                # The position's data ends as of `signal_day` (delisting, an
                # acquisition, or a data-provider discontinuation) -- settle
                # at that last known close as an UNVERIFIED proxy. This does
                # not satisfy the economic settlement data gate; it is not
                # silently dropped. This uses only information known as of
                # signal_day; the position was selected and held right up to
                # this point exactly as an investor without foreknowledge of
                # the discontinuation would have experienced it -- it is not
                # an ex-ante avoidance of the name (that would reintroduce
                # look-ahead bias into the very test meant to remove it).
                # Zero PNL impact: the position was already marked at this
                # same close on signal_day, so this only reclassifies stock
                # value as cash, matching independent_pnl's reconciliation.
                last_price = bars[symbol][signal_day]["close"]
                quantity = held.pop(symbol)
                inherited.pop(symbol, None)
                cash += quantity * last_price
                warnings.append({"date": day, "symbol": symbol, "flag": "forced_exit_data_discontinued",
                                 "last_known_date": signal_day, "quantity": quantity,
                                 "last_price_usd": last_price})
                continue
            bar = bars[symbol][day]
            previous_quantity = held[symbol]
            held[symbol] *= bar["split"]
            if symbol in inherited:
                inherited[symbol] = (inherited[symbol][0] * bar['split'], inherited[symbol][1])
            overnight = held[symbol] * bar["open"] - previous_quantity * bars[symbol][signal_day]["close"]
            overnight_pnl += overnight
            dividend = held[symbol] * bar["dividend"]
            cash += dividend
            action_dividend += dividend
            contribution = contributions.setdefault(symbol, {"price_pnl_usd": 0.0, "dividends_usd": 0.0, "execution_cost_usd": 0.0})
            contribution["price_pnl_usd"] += overnight
            contribution["dividends_usd"] += dividend
        for event in events:
            symbol = event['symbol']
            if event['kind'] != 'spinoff' or symbol not in prior_held:
                continue
            if day not in bars[symbol]:
                warnings.append({'date': day, 'symbol': symbol,
                                 'flag': 'corporate_action_unresolved',
                                 'reason': 'spinoff_date_has_no_parent_quote_or_conflicts_with_exit'})
                continue
            from .corporate_actions import entitlement
            quantity = prior_held[symbol] * bars[symbol][day]['split']
            action_cash, action_shares, action_value = entitlement(event, quantity, bars, day)
            if action_cash:
                raise ValueError('Spinoff share distribution cannot be credited as cash')
            additions.extend(action_shares)
            corporate_pnl += action_value
            contributions[symbol].setdefault('corporate_action_pnl_usd', 0.0)
            contributions[symbol]['corporate_action_pnl_usd'] += action_value
            warnings.append({'date': day, 'symbol': symbol, 'flag': 'corporate_spinoff_shares',
                'quantity': quantity, 'cash_consideration_usd': 0.0,
                'stock_value_at_open_usd': action_value, 'corporate_action_pnl_usd': action_value,
                'received_shares': action_shares, 'settlement_verified': False})
        corporate_total += corporate_pnl
        # Dispose only inherited shares on the next session, independently of ranking.
        for symbol, (quantity, receipt_day) in sorted(list(inherited.items())):
            if receipt_day >= day or symbol not in held:
                continue
            quantity = min(quantity, held[symbol])
            price = bars[symbol][day]['open']
            amount = quantity * price
            fee = amount * cost_rate
            cash += amount - fee
            held[symbol] -= quantity
            if held[symbol] < 1e-8:
                held.pop(symbol)
            inherited.pop(symbol)
            day_fees += fee
            total_cost += fee
            gross_traded += amount
            # One-way cash-inclusive turnover: sale amount / pre-sale account NAV.
            sale_nav = cash + fee + sum(q * bars[s][day]['open'] for s, q in held.items())
            turnover += amount / sale_nav
            contributions[symbol]['execution_cost_usd'] += fee
            trades.append({'date': day, 'signal_date': receipt_day, 'symbol': symbol,
                'quantity': -quantity, 'price_usd': price, 'notional_usd': -amount,
                'execution_cost_usd': fee, 'cash_after_usd': cash,
                'reason': 'inherited_shares_next_session_disposal'})
        for symbol, quantity in additions:
            held[symbol] = held.get(symbol, 0) + quantity
            pending, due = inherited.get(symbol, (0, day))
            inherited[symbol] = (pending + quantity, min(due, day))
            contributions.setdefault(symbol, {'price_pnl_usd': 0.0, 'dividends_usd': 0.0,
                                              'execution_cost_usd': 0.0})
        dividends_total += action_dividend
        # Interest accrues on cash actually carried overnight into this session, using
        # that day's published short-duration reference rate; this is a scenario proxy
        # for obtainable cash yield, not a verified brokerage sweep-crediting formula.
        day_rate = (cash_annual_rate or {}).get(day, 0.0)
        action_interest = beginning_cash * day_rate / 252
        cash += action_interest
        interest_total += action_interest
        pretrade_nav = cash + sum(q * bars[s][day]["open"] for s, q in held.items())
        review = day == sessions[0] or day[:7] != signal_day[:7]
        ranking = []
        selected = list(held)
        if review and (not is_benchmark or risk_control or not held):
            if is_benchmark:
                selected = ["QQQ"]
            else:
                # symbols_by_review_month lets the eligible pool itself change
                # over time (a real point-in-time universe) instead of one
                # fixed dict for the whole run. A held name that drops out of
                # this month's pool is simply absent from `ranking` below, so
                # it fails the `s in ranks` retain test in choose() and exits
                # like any other rank-driven removal -- no special-casing needed.
                if symbols_by_review_month is not None and day[:7] not in symbols_by_review_month:
                    raise ValueError(f"Missing point-in-time universe for execution month {day[:7]}")
                active_symbols = (symbols_by_review_month[day[:7]]
                                  if symbols_by_review_month is not None else symbols)
                if uses_quality and quality_by_review_month is not None and day[:7] not in quality_by_review_month:
                    raise ValueError(f"Missing point-in-time quality for execution month {day[:7]}")
                quality_for_month = (quality_by_review_month.get(day[:7])
                                     if uses_quality and quality_by_review_month is not None else None)
                ranking = rank_signals(bars, dates, index - 1, active_symbols, config["minimum_adv_usd"],
                                       quality_by_symbol=quality_for_month, formation=formation)
                ordinary_held = {s: q - inherited.get(s, (0, ''))[0] for s, q in held.items()
                                 if q - inherited.get(s, (0, ''))[0] > 1e-8}
                selected = choose(ranking, ordinary_held, count, active_symbols, config["sector_weight_cap"])
            fraction = risk_fraction(bars, dates, index - 1, selected, count,
                                     config["volatility_target"]) if risk_control else 1.0
            unavailable = [s for s in selected if day not in bars[s]]
            for symbol in unavailable:
                warnings.append({"date": day, "symbol": symbol,
                                 "signal_date": signal_day,
                                 "flag": "unfilled_order_no_execution_bar"})
            # Preserve the frozen rank/selection. An unavailable quote cannot
            # fill; leave its allocation in cash without picking a substitute.
            weights = {s: fraction / count for s in selected if s not in unavailable}
            # Reserve fees on a conservative upper bound of turnover (2*NAV).
            investable = pretrade_nav / (1 + 2 * cost_rate)
            # The fixed system fee accrues every session, not just at rebalance,
            # so investing right up to the turnover-cost margin leaves nothing
            # for the sessions between now and the next monthly review. A
            # concentrated, high-cost-rate book (P006's H3/H5 at 25bps) can run
            # that gap to zero and push cash negative -- reserve worst-case-month
            # (25 sessions, safely above any real month's ~19-23) of fixed fee
            # up front, rather than relying on incidental floor()-rounding slack,
            # which is what every P001-P005 variant happened to have enough of,
            # not a designed-in guarantee. A 12-months-average reserve is not
            # enough on its own: it matches a 21-session month almost exactly,
            # so a longer real month still exhausts it (confirmed by test).
            investable = max(0.0, investable - config["annual_system_cash_cost_usd"] / 252 * 25)
            # Newly received shares are held until the frozen next-session disposal.
            pending_value = sum(q * bars[s][day]['open'] for s, (q, _) in inherited.items())
            investable = max(0.0, investable - pending_value)
            targets = {s: math.floor(investable * w / bars[s][day]["open"]) for s, w in weights.items()}
            for symbol, (quantity, _) in inherited.items():
                targets[symbol] = targets.get(symbol, 0) + quantity
            decisions.append({"signal_date": signal_day, "execution_date": day,
                              "selected": selected, "equity_fraction_multiplier": fraction,
                              "ranking": ranking, "target_weights": weights,
                              "unfilled_target_symbols": unavailable})
            # A fund driven to exactly zero NAV (no cash, no holdings -- only
            # reachable now that the fixed fee is capped at available cash
            # rather than driving cash negative) has no meaningful weights to
            # turn over; every target is already floor(0/price)=0, so there
            # is nothing to divide by and nothing to record.
            if pretrade_nav > 0:
                before = {s: q * bars[s][day]["open"] / pretrade_nav for s, q in held.items()}
                before["CASH"] = cash / pretrade_nav
                after = {s: targets[s] * bars[s][day]["open"] / pretrade_nav for s in targets}
                after["CASH"] = 1 - sum(after.values())
                turnover += 0.5 * sum(abs(after.get(s, 0) - before.get(s, 0)) for s in set(before) | set(after))
            orders = [(s, targets.get(s, 0) - held.get(s, 0)) for s in set(held) | set(targets)]
            # Sell before buying; deterministic symbol order within each side.
            orders.sort(key=lambda x: (x[1] > 0, x[0]))
            for symbol, quantity in orders:
                if abs(quantity) < 1e-10:
                    continue
                price = bars[symbol][day]["open"]
                amount, fee = quantity * price, abs(quantity * price) * cost_rate
                cash -= amount + fee
                held[symbol] = held.get(symbol, 0) + quantity
                if held[symbol] < 1e-8:
                    held.pop(symbol)
                total_cost += fee
                day_fees += fee
                contribution = contributions.setdefault(symbol, {"price_pnl_usd": 0.0, "dividends_usd": 0.0, "execution_cost_usd": 0.0})
                contribution["execution_cost_usd"] += fee
                gross_traded += abs(amount)
                trades.append({"date": day, "signal_date": signal_day, "symbol": symbol,
                               "quantity": quantity, "price_usd": price, "notional_usd": amount,
                               "execution_cost_usd": fee, "cash_after_usd": cash})
        # A flat per-session dollar fee cannot be collected once the account
        # has been driven near zero -- there is no money left to take it
        # from. This only matters for a book concentrated and unconstrained
        # enough to approach real ruin (observed for real: P006's H3 fell
        # from $300k to $2.13 over 18 years of real data, most of it in the
        # last two), which none of P001-P005's diversified, risk-bounded
        # variants ever came close to. Capping the fee at available cash is
        # a bookkeeping convention for a fund that is effectively already
        # closed, not a change to the accounting for any solvent day.
        fixed_fee = min(config["annual_system_cash_cost_usd"] / 252 if not is_benchmark else 0.0,
                        max(0.0, cash))
        cash -= fixed_fee
        fixed_total += fixed_fee
        if cash < -1e-6:
            raise ValueError(f"Cash became negative: {variant} {day}")
        stock_nav = sum(q * bars[s][day]["close"] for s, q in held.items())
        nav = cash + stock_nav
        intraday_pnl = 0.0
        for symbol, quantity in sorted(held.items()):
            intraday = quantity * (bars[symbol][day]["close"] - bars[symbol][day]["open"])
            intraday_pnl += intraday
            contributions[symbol]["price_pnl_usd"] += intraday
            weight = quantity * bars[symbol][day]["close"] / nav
            holdings.append({"date": day, "symbol": symbol, "quantity": quantity, "weight": weight})
            if not is_benchmark and weight >= 0.12:
                warnings.append({"date": day, "symbol": symbol, "weight": weight,
                                 "flag": "single_name_12_percent_review_required"})
        ledger.append({"date": day, "nav_usd": nav, "cash_usd": cash,
                       "stock_value_usd": stock_nav, "dividend_cash_usd": action_dividend,
                       "cash_interest_usd": action_interest,
                       "fixed_fee_usd": fixed_fee, "pnl_usd": nav - prior_close_nav,
                       "price_pnl_usd": overnight_pnl + intraday_pnl,
                       "execution_cost_usd": day_fees,
                       "holdings_count": len(held)})
        if corporate_actions_by_date is not None:
            ledger[-1]['corporate_action_pnl_usd'] = corporate_pnl
        independent_pnl = overnight_pnl + intraday_pnl + corporate_pnl + action_dividend + action_interest - day_fees - fixed_fee
        if not math.isclose(nav - prior_close_nav, independent_pnl, rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError("Independent cash/price/dividend/fee PNL reconciliation failed")
        prior_close_nav = nav
    summary = metrics(ledger, capital)
    summary.update({"variant": variant, "capital_usd": capital, "cost_bps": cost_bps,
                    "execution_cost_usd": total_cost, "fixed_cost_usd": fixed_total,
                    "dividends_usd": dividends_total, "cash_interest_usd": interest_total,
                    "one_way_turnover_total": turnover,
                    "gross_traded_over_initial_nav": gross_traded / capital,
                    "average_holdings": statistics.mean(r["holdings_count"] for r in ledger),
                    "hard_review_days": len(set(r["date"] for r in warnings))})
    if corporate_actions_by_date is not None:
        summary['corporate_action_pnl_usd'] = corporate_total
    contribution_rows = [{"symbol": s, **row,
                          "net_contribution_usd": row["price_pnl_usd"] + row["dividends_usd"] + row.get("corporate_action_pnl_usd", 0.0) - row["execution_cost_usd"]}
                         for s, row in sorted(contributions.items())]
    reconciled = sum(r["net_contribution_usd"] for r in contribution_rows) - fixed_total + interest_total
    if not math.isclose(summary["ending_nav_usd"] - capital, reconciled, rel_tol=1e-9, abs_tol=1e-5):
        raise ValueError("Contributor PNL does not reconcile with total wealth")
    positive_total = sum(max(0, r["net_contribution_usd"]) for r in contribution_rows)
    top = max(contribution_rows, key=lambda r: r["net_contribution_usd"], default=None)
    summary["top_positive_contributor"] = top["symbol"] if top else None
    summary["top_positive_contribution_share"] = max(0, top["net_contribution_usd"]) / positive_total if top and positive_total else None
    return summary, ledger, trades, holdings, decisions, warnings, contribution_rows
