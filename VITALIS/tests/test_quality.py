"""Quality-factor metrics, SIC grouping fallback, and neutral-score policy."""

import glob
import json
import unittest
from pathlib import Path

from vitalis.pit import fundamentals_asof, normalize_fundamentals
from vitalis.quality import (
    cfo_to_avg_assets_ttm, is_excluded_financial_sector,
    negative_debt_to_assets, operating_margin_ttm, quality_scores,
)
from vitalis.sic_history import load_sic_changes, sic_by_ticker_asof
from vitalis.universe import security_master


def row(revenue=None, opinc=None, ncfo=None, assetsavg=None, assets=None, debt=None):
    return {"revenue": revenue, "opinc": opinc, "ncfo": ncfo,
            "assetsavg": assetsavg, "assets": assets, "debt": debt}


class MetricTests(unittest.TestCase):
    def test_raw_metrics_use_denominator_from_the_matching_field(self):
        r = row(revenue=1000, opinc=200, ncfo=150, assetsavg=500, assets=800, debt=300)
        self.assertAlmostEqual(operating_margin_ttm(r), 0.2)
        self.assertAlmostEqual(cfo_to_avg_assets_ttm(r), 0.3)
        self.assertAlmostEqual(negative_debt_to_assets(r), -0.375)

    def test_nonpositive_or_missing_denominator_is_missing_not_zero(self):
        self.assertIsNone(operating_margin_ttm(row(revenue=0, opinc=5)))
        self.assertIsNone(operating_margin_ttm(row(revenue=None, opinc=5)))
        self.assertIsNone(cfo_to_avg_assets_ttm(row(assetsavg=-10, ncfo=5)))
        self.assertIsNone(negative_debt_to_assets(row(assets=0, debt=5)))

    def test_excluded_sic_ranges_cover_banks_insurance_and_reits(self):
        self.assertTrue(is_excluded_financial_sector(6022))   # bank
        self.assertTrue(is_excluded_financial_sector("6411"))  # insurance agent
        self.assertTrue(is_excluded_financial_sector(6798))   # REIT
        self.assertFalse(is_excluded_financial_sector(3571))  # electronic computers
        self.assertFalse(is_excluded_financial_sector(None))


class QualityScoresTests(unittest.TestCase):
    def test_excluded_sector_and_missing_metric_both_get_neutral_na(self):
        rows = {
            "BANK": row(revenue=100, opinc=10, ncfo=5, assetsavg=50, assets=80, debt=30),
            "MISSING": row(revenue=None, opinc=10, ncfo=5, assetsavg=50, assets=80, debt=30),
            "OK": row(revenue=100, opinc=20, ncfo=10, assetsavg=50, assets=80, debt=30),
        }
        sic = {"BANK": 6022, "MISSING": 3571, "OK": 3571}
        result = quality_scores(rows, sic, minimum_group_size=10)
        self.assertEqual(result["BANK"], {"quality": 0.5, "na": True, "group": None, "peer_count": 0, "metrics": None})
        self.assertEqual(result["MISSING"], {"quality": 0.5, "na": True, "group": None, "peer_count": 0, "metrics": None})
        self.assertFalse(result["OK"]["na"])

    def test_small_group_merges_up_then_falls_back_to_all_eligible(self):
        # Two tickers share a 2-digit group (too small alone); a third only
        # shares the 1-digit prefix; with minimum_group_size=2 the first pair
        # should group at level 0, the third should fall through further.
        rows = {t: row(revenue=100, opinc=10 + i, ncfo=5, assetsavg=50, assets=80, debt=30)
                for i, t in enumerate(["A", "B", "C"])}
        sic = {"A": 3571, "B": 3572, "C": 2011}
        result = quality_scores(rows, sic, minimum_group_size=2)
        # A and B share 2-digit group "35" (count=2, meets minimum) -> level l0.
        self.assertEqual(result["A"]["group"], ("l0", "35"))
        self.assertEqual(result["A"]["group"][0], "l0")
        self.assertEqual(result["B"]["group"][0], "l0")
        # C is alone at 2-digit "20"; falls to 1-digit "2" then to "all" if
        # still short of the minimum (here count at level1 is 1 < 2 -> "all").
        self.assertEqual(result["C"]["group"], ("all", None))

    def test_broadened_group_includes_finer_group_members_without_overwriting_their_ranks(self):
        rows = {t: row(revenue=100, opinc=10*(i+1), ncfo=10*(i+1),
                       assetsavg=100, assets=100, debt=40-10*i)
                for i,t in enumerate(['A','B','C','D'])}
        result = quality_scores(rows, {'A':3571, 'B':3572, 'C':3671, 'D':2011}, minimum_group_size=2)
        self.assertEqual(result['A']['peer_count'], 2)
        self.assertEqual(result['B']['peer_count'], 2)
        self.assertEqual(result['C']['peer_count'], 3)
        self.assertEqual(result['D']['peer_count'], 4)
        self.assertEqual(result['A']['quality'], 0)
        self.assertEqual(result['B']['quality'], 1)
        self.assertEqual(result['C']['quality'], 1)
        self.assertEqual(result['D']['quality'], 1)

    def test_all_three_metrics_required_for_a_computed_score(self):
        rows = {
            "A": row(revenue=100, opinc=10, ncfo=5, assetsavg=50, assets=80, debt=30),
            "B": row(revenue=100, opinc=20, ncfo=None, assetsavg=50, assets=80, debt=30),
        }
        sic = {"A": 3571, "B": 3571}
        result = quality_scores(rows, sic)
        self.assertFalse(result["A"]["na"])
        self.assertTrue(result["B"]["na"])


class RealDataSmokeTests(unittest.TestCase):
    """Sanity-checks the module against real Sharadar ART fundamentals pulled
    for the P001 universe (data/authorized/sharadar/, git-ignored). Skips if
    that local, licensed cache is not present — this is not a public fixture.
    """

    def setUp(self):
        self.cache_dir = Path("data/authorized/sharadar")
        if not self.cache_dir.exists():
            self.skipTest("no local authorized Sharadar cache present")

    def test_real_art_fundamentals_produce_finite_quality_scores(self):
        rows_by_ticker = {}
        for path in glob.glob(str(self.cache_dir / "fundamentals-*.json")):
            envelope = json.loads(Path(path).read_text())
            if "payload" not in envelope:
                continue  # a bulk-download provenance sidecar, not a per-ticker REST cache entry
            art_rows = [r for r in envelope["payload"]["data"] if r["dimension"] == "ART"]
            if not art_rows:
                continue
            ticker = art_rows[0]["ticker"]
            sessions = sorted({r["date"] for r in art_rows} | {"2099-01-01"})
            normalized = normalize_fundamentals(art_rows, sessions)
            latest = fundamentals_asof(normalized, "2099-01-01", dimension="ART")
            if ticker in latest:
                rows_by_ticker[ticker] = latest[ticker]
        if len(rows_by_ticker) < 5:
            self.skipTest("not enough real fundamentals pulled yet")
        tickers_path = self.cache_dir / "tickers-bulk-full.csv.zip"
        actions_path = self.cache_dir / "actions-bulk-full.csv.zip"
        if not tickers_path.exists() or not actions_path.exists():
            self.skipTest("no local bulk tickers/actions cache present for real SIC lookup")
        master = security_master(tickers_path)
        current_siccode = {info["ticker"]: info["siccode"] for info in master.values()}
        changes, _ = load_sic_changes(actions_path)
        # As-of the P001 evaluation start, not today's classification -- this is
        # the actual historical-SIC gap docs/review/09's audit flagged: a prior
        # version of this test used the same placeholder SIC for every ticker,
        # so it never actually exercised bank/insurance exclusion on real data.
        sic_by_ticker = sic_by_ticker_asof(current_siccode, changes, "2021-01-04")
        for bank in ("JPM", "BAC"):
            if bank in rows_by_ticker:
                self.assertTrue(is_excluded_financial_sector(sic_by_ticker.get(bank)),
                                f"{bank}'s real historical SIC {sic_by_ticker.get(bank)} should be excluded")
        result = quality_scores(rows_by_ticker, sic_by_ticker)
        computed = [r for r in result.values() if not r["na"]]
        self.assertTrue(computed, "expected at least one real ticker with all three metrics present")
        for entry in computed:
            self.assertTrue(0.0 <= entry["quality"] <= 1.0)
        for bank in ("JPM", "BAC"):
            if bank in result:
                self.assertEqual(result[bank], {"quality": 0.5, "na": True, "group": None, "peer_count": 0, "metrics": None})


if __name__ == "__main__":
    unittest.main()
