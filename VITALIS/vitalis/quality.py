"""Quality factor per docs/review/03-strategy-and-portfolio.md section 2.

Three as-reported, trailing-twelve-month (Sharadar "ART" dimension) metrics,
cross-sectionally percentiled within a same-period-known SIC peer group:
  - TTM operating margin: opinc / revenue
  - TTM operating cash flow / average total assets: ncfo / assetsavg
  - negative total debt / total assets: -(debt / assets)
A ticker gets the neutral fallback (quality=0.5, na=True) rather than an
computed score when it is a bank/insurer/REIT (whose operating and leverage
metrics are not comparable on this basis) or is missing any of the three
metrics — this keeps the eligible universe identical to the momentum-only
run, so a quality-vs-momentum comparison is not silently also a universe
change. This module does not itself certify that a SIC label used as a
grouping input was actually known as of that date; see `historical_evidence`
in the caller's own bookkeeping (Sharadar's `tickers` table SIC fields are a
current snapshot per docs/review/05, not a point-in-time history).
"""

from .engine import percentile

# SIC ranges this project excludes from the operating/leverage comparison
# because banks, insurers, and REITs do not report revenue/opinc/debt the
# same way a typical operating company does. Common industry convention
# (depository institutions, insurance, real estate investment trusts), not a
# figure sourced from a VITALIS-specific citation — review before relying on
# it for a real universe, and expect edge cases (e.g. diversified holding
# companies) to need manual handling later.
EXCLUDED_SIC_RANGES = (
    (6000, 6299),  # depository institutions, credit agencies, brokers/dealers
    (6300, 6499),  # insurance carriers and agents
    (6798, 6798),  # real estate investment trusts
)


def is_excluded_financial_sector(sic_code):
    if sic_code is None:
        return False
    return any(low <= int(sic_code) <= high for low, high in EXCLUDED_SIC_RANGES)


def operating_margin_ttm(row):
    revenue, opinc = row.get("revenue"), row.get("opinc")
    if revenue is None or opinc is None or revenue <= 0:
        return None
    return opinc / revenue


def cfo_to_avg_assets_ttm(row):
    assetsavg, ncfo = row.get("assetsavg"), row.get("ncfo")
    if assetsavg is None or ncfo is None or assetsavg <= 0:
        return None
    return ncfo / assetsavg


def negative_debt_to_assets(row):
    assets, debt = row.get("assets"), row.get("debt")
    if assets is None or debt is None or assets <= 0:
        return None
    return -(debt / assets)


RAW_METRICS = (operating_margin_ttm, cfo_to_avg_assets_ttm, negative_debt_to_assets)


def _sic_group(sic_code, level):
    """level 0: 2-digit SIC major group, the initial peer group.
    level 1: 1-digit SIC prefix, this project's own coarsening rule for the
    "预先确定的上级大类" merge-up step — a simple, self-documented hierarchy,
    not an official SIC division table. Review before treating it as final.
    """
    code = str(int(sic_code)).zfill(4)
    return code[:2] if level == 0 else code[:1]


def quality_scores(rows_by_ticker, sic_by_ticker, minimum_group_size=10):
    """rows_by_ticker: {ticker: as-reported TTM fundamentals row (ART dimension)}.
    sic_by_ticker: {ticker: sic_code} for the same as-of date the fundamentals
    row was selected for; the caller owns that alignment.

    Returns {ticker: {"quality", "na", "group", "peer_count", "metrics"}}. `na=True` means
    the fallback neutral 0.5 was used (excluded sector or a missing metric),
    never a computed score — report the count and weight of `na` tickers
    whenever this quality score is used; a neutral score is not "qualified".
    """
    raw = {}
    for ticker, row in rows_by_ticker.items():
        sic = sic_by_ticker.get(ticker)
        if sic is None or is_excluded_financial_sector(sic):
            raw[ticker] = None
            continue
        values = [metric(row) for metric in RAW_METRICS]
        raw[ticker] = values if all(v is not None for v in values) else None

    eligible = {t: v for t, v in raw.items() if v is not None}
    groups_l0 = {t: _sic_group(sic_by_ticker[t], 0) for t in eligible}
    counts_l0 = {}
    for g in groups_l0.values():
        counts_l0[g] = counts_l0.get(g, 0) + 1

    def group_for(ticker):
        g0 = groups_l0[ticker]
        if counts_l0[g0] >= minimum_group_size:
            return ("l0", g0)
        g1 = _sic_group(sic_by_ticker[ticker], 1)
        count_l1 = sum(1 for t in eligible if _sic_group(sic_by_ticker[t], 1) == g1)
        if count_l1 >= minimum_group_size:
            return ("l1", g1)
        return ("all", None)

    assignment = {t: group_for(t) for t in eligible}
    percentiles_by_group = {}
    for group_key in set(assignment.values()):
        level, prefix = group_key
        # A broadened peer set includes companies already assigned their own
        # finer group. Restricting it to fallback companies silently shrinks
        # the comparison below the minimum group size.
        members = [t for t in eligible if level == 'all' or
                   _sic_group(sic_by_ticker[t], 0 if level == 'l0' else 1) == prefix]
        percentiles_by_group[group_key] = {
            'size': len(members),
            'metrics': [percentile({t: eligible[t][m] for t in members}) for m in range(3)],
        }

    result = {}
    for ticker in rows_by_ticker:
        if ticker not in eligible:
            result[ticker] = {"quality": 0.5, "na": True, "group": None,
                              "peer_count": 0, "metrics": raw.get(ticker)}
            continue
        peer = percentiles_by_group[assignment[ticker]]
        pcts = [peer['metrics'][m][ticker] for m in range(3)]
        result[ticker] = {"quality": sum(pcts) / 3, "na": False,
                          "group": assignment[ticker], "peer_count": peer['size'],
                          "metrics": eligible[ticker]}
    return result


def excluded_by_quality_threshold(scores, fraction=0.25):
    """P006's pre-registered use of quality: drop the weakest `fraction` of a
    month's pool instead of blending quality into the score.

    P003b showed the 0.5/0.5 blend dilutes the momentum signal without buying
    a distinguishable drawdown improvement, so P006 registered exclusion
    instead. `scores` is quality_scores()' output. Ranking is over computed
    scores only: an `na` ticker (excluded sector, no filing, missing metric)
    carries the neutral 0.5 fallback, which is not a measured quality and must
    never be read as "weak" -- it is never excluded here. That means the
    realised exclusion count is `fraction` of the *scored* names, not of the
    pool, and the two diverge exactly when coverage is poor; report both.
    """
    if not 0.0 <= fraction < 1.0:
        raise ValueError(f"fraction must be in [0, 1): {fraction}")
    scored = sorted((entry["quality"], ticker) for ticker, entry in scores.items()
                    if not entry["na"])
    cutoff = int(len(scored) * fraction)
    return {ticker for _, ticker in scored[:cutoff]}
