"""Illustrative project economics, not a backtest or a return forecast.

Run from the project root: python3 docs/review/roi_scenarios.py
All currency values are USD. Delta returns exclude fixed system costs;
taxes/financing must be reflected consistently by the caller.
"""

import argparse
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capital", nargs="+", type=float,
                        default=[50_000, 100_000, 200_000, 250_000, 400_000, 500_000, 1_000_000])
    parser.add_argument("--delta-pp", nargs="+", type=float,
                        default=[-2, 0, 1, 2, 3])
    parser.add_argument("--cash-cost", type=float, default=600)
    parser.add_argument("--build-hours", type=float, default=160)
    parser.add_argument("--maintenance-hours", type=float, default=20)
    parser.add_argument("--hourly-value", type=float, default=50)
    parser.add_argument("--amortization-years", type=float, default=3)
    args = parser.parse_args()
    if min(args.capital) <= 0 or args.amortization_years <= 0:
        parser.error("Capital and amortization years must be positive.")
    if min(args.cash_cost, args.build_hours, args.maintenance_hours,
           args.hourly_value) < 0:
        parser.error("Costs and hours cannot be negative.")
    annual = (args.cash_cost + args.maintenance_hours * args.hourly_value
              + args.build_hours * args.hourly_value / args.amortization_years)
    first_year = (args.cash_cost + (args.maintenance_hours + args.build_hours)
                  * args.hourly_value)
    rows = []
    for capital in args.capital:
        for delta in args.delta_pp:
            incremental = capital * delta / 100
            rows.append({
                "capital_usd": capital,
                "assumed_delta_percentage_points": delta,
                "cash_break_even_percentage_points": round(100 * args.cash_cost / capital, 6),
                "economic_break_even_percentage_points": round(100 * annual / capital, 6),
                "annual_cash_net_usd": round(incremental - args.cash_cost, 2),
                "annual_economic_net_usd": round(incremental - annual, 2),
                "first_year_economic_net_usd": round(incremental - first_year, 2),
                "economic_project_roi_percent":
                    round(100 * (incremental - annual) / annual, 4) if annual else None,
            })
    print(json.dumps({
        "status": "illustrative assumptions; not observed investment performance",
        "currency": "USD",
        "inputs": vars(args),
        "annual_economic_cost_usd": round(annual, 2),
        "first_year_economic_cost_usd": round(first_year, 2),
        "scenarios": rows,
    }, indent=2))


if __name__ == "__main__":
    main()
