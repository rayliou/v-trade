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


def rank_signals(bars, dates, index, symbols, minimum_adv):
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
        price = series[dates[index - 21]]["adjclose"]
        signals[symbol] = {
            "m12_1": price / series[dates[index - 252]]["adjclose"] - 1,
            "m6_1": price / series[dates[index - 126]]["adjclose"] - 1,
            "adv_usd": adv,
        }
    first = percentile({s: x["m12_1"] for s, x in signals.items()})
    second = percentile({s: x["m6_1"] for s, x in signals.items()})
    ordered = sorted(signals, key=lambda s: (-(first[s] + second[s]), s))
    return [{"symbol": s, "rank": i + 1, "score": (first[s] + second[s]) / 2,
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
    values = [initial] + [row["nav_usd"] for row in nav]
    returns = [b / a - 1 for a, b in zip(values, values[1:])]
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
    monthly = {}
    for row, ret in zip(nav, returns):
        month = row["date"][:7]
        monthly[month] = monthly.get(month, 1.0) * (1 + ret)
    return {
        "cagr": (values[-1] / initial) ** (252 / len(returns)) - 1,
        "annual_volatility": volatility,
        "sharpe_zero_rf": statistics.mean(returns) * 252 / volatility if volatility else None,
        "max_drawdown": worst,
        "ulcer_index_percentage_points": math.sqrt(statistics.mean(squared)),
        "longest_underwater_trading_days": longest,
        "current_underwater_trading_days": underwater,
        "worst_month": min(monthly.values()) - 1,
        "ending_nav_usd": values[-1],
        "sessions": len(returns),
    }


def simulate(bars, dates, config, capital, cost_bps, variant):
    start, end = config["evaluation_start"], config["evaluation_end"]
    sessions = [d for d in dates if start <= d <= end]
    if not sessions:
        raise ValueError("No evaluation sessions")
    symbols = config["symbols"]
    is_benchmark = variant in ("QQQ", "QQQ-cash15")
    risk_control = variant in ("QQQ-cash15", "M10-risk15")
    count = 1 if is_benchmark else (20 if variant == "M20" else 10)
    cash, held = float(capital), {}
    trades, ledger, holdings, decisions, warnings = [], [], [], [], []
    contributions = {}
    cost_rate = cost_bps / 10000
    total_cost, gross_traded, turnover, dividends_total, fixed_total = 0.0, 0.0, 0.0, 0.0, 0.0
    prior_close_nav = capital
    for day in sessions:
        index = dates.index(day)
        if index == 0:
            raise ValueError("Evaluation requires a preceding signal date")
        signal_day = dates[index - 1]
        action_dividend = 0.0
        overnight_pnl = 0.0
        day_fees = 0.0
        for symbol in list(held):
            bar = bars[symbol][day]
            previous_quantity = held[symbol]
            held[symbol] *= bar["split"]
            overnight = held[symbol] * bar["open"] - previous_quantity * bars[symbol][signal_day]["close"]
            overnight_pnl += overnight
            dividend = held[symbol] * bar["dividend"]
            cash += dividend
            action_dividend += dividend
            contribution = contributions.setdefault(symbol, {"price_pnl_usd": 0.0, "dividends_usd": 0.0, "execution_cost_usd": 0.0})
            contribution["price_pnl_usd"] += overnight
            contribution["dividends_usd"] += dividend
        dividends_total += action_dividend
        pretrade_nav = cash + sum(q * bars[s][day]["open"] for s, q in held.items())
        review = day == sessions[0] or day[:7] != signal_day[:7]
        ranking = []
        selected = list(held)
        if review and (not is_benchmark or risk_control or not held):
            if is_benchmark:
                selected = ["QQQ"]
            else:
                ranking = rank_signals(bars, dates, index - 1, symbols, config["minimum_adv_usd"])
                selected = choose(ranking, held, count, symbols, config["sector_weight_cap"])
            fraction = risk_fraction(bars, dates, index - 1, selected, count,
                                     config["volatility_target"]) if risk_control else 1.0
            weights = {s: fraction / count for s in selected}
            # Reserve fees on a conservative upper bound of turnover (2*NAV).
            investable = pretrade_nav / (1 + 2 * cost_rate)
            targets = {s: math.floor(investable * w / bars[s][day]["open"]) for s, w in weights.items()}
            decisions.append({"signal_date": signal_day, "execution_date": day,
                              "selected": selected, "equity_fraction_multiplier": fraction,
                              "ranking": ranking, "target_weights": weights})
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
        fixed_fee = config["annual_system_cash_cost_usd"] / 252 if not is_benchmark else 0.0
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
                       "fixed_fee_usd": fixed_fee, "pnl_usd": nav - prior_close_nav,
                       "price_pnl_usd": overnight_pnl + intraday_pnl,
                       "execution_cost_usd": day_fees,
                       "holdings_count": len(held)})
        independent_pnl = overnight_pnl + intraday_pnl + action_dividend - day_fees - fixed_fee
        if not math.isclose(nav - prior_close_nav, independent_pnl, rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError("Independent cash/price/dividend/fee PNL reconciliation failed")
        prior_close_nav = nav
    summary = metrics(ledger, capital)
    summary.update({"variant": variant, "capital_usd": capital, "cost_bps": cost_bps,
                    "execution_cost_usd": total_cost, "fixed_cost_usd": fixed_total,
                    "dividends_usd": dividends_total, "one_way_turnover_total": turnover,
                    "gross_traded_over_initial_nav": gross_traded / capital,
                    "average_holdings": statistics.mean(r["holdings_count"] for r in ledger),
                    "hard_review_days": len(set(r["date"] for r in warnings))})
    contribution_rows = [{"symbol": s, **row,
                          "net_contribution_usd": row["price_pnl_usd"] + row["dividends_usd"] - row["execution_cost_usd"]}
                         for s, row in sorted(contributions.items())]
    reconciled = sum(r["net_contribution_usd"] for r in contribution_rows) - fixed_total
    if not math.isclose(summary["ending_nav_usd"] - capital, reconciled, rel_tol=1e-9, abs_tol=1e-5):
        raise ValueError("Contributor PNL does not reconcile with total wealth")
    positive_total = sum(max(0, r["net_contribution_usd"]) for r in contribution_rows)
    top = max(contribution_rows, key=lambda r: r["net_contribution_usd"], default=None)
    summary["top_positive_contributor"] = top["symbol"] if top else None
    summary["top_positive_contribution_share"] = max(0, top["net_contribution_usd"]) / positive_total if top and positive_total else None
    return summary, ledger, trades, holdings, decisions, warnings, contribution_rows
