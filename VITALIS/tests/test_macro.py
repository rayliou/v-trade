"""Cash-yield reference series: parsing and forward-fill, no network access."""

import unittest

from vitalis.macro import daily_rate_by_trading_day, normalize_series


class MacroTests(unittest.TestCase):
    def envelope(self, csv):
        return {"series_id": "DGS3MO", "payload": {"csv": csv}}

    def test_normalize_skips_unpublished_observations(self):
        csv = "observation_date,DGS3MO\n2020-01-02,1.54\n2020-01-20,.\n2020-01-21,1.56\n"
        values = normalize_series(self.envelope(csv))
        self.assertEqual(values, {"2020-01-02": 1.54, "2020-01-21": 1.56})

    def test_normalize_rejects_duplicate_or_negative_observations(self):
        with self.assertRaises(ValueError):
            normalize_series(self.envelope("observation_date,DGS3MO\n2020-01-02,1.5\n2020-01-02,1.6\n"))
        with self.assertRaises(ValueError):
            normalize_series(self.envelope("observation_date,DGS3MO\n2020-01-02,-1.0\n"))

    def test_forward_fill_carries_last_published_rate_over_bond_holidays(self):
        # 2020-07-03 is an equity trading day (early close) but a bond-market holiday.
        percent_by_date = {"2020-07-02": 1.20, "2020-07-06": 1.24}
        trading_days = ["2020-07-02", "2020-07-03", "2020-07-06"]
        rates = daily_rate_by_trading_day(percent_by_date, trading_days)
        self.assertEqual(rates, {"2020-07-02": 0.012, "2020-07-03": 0.012, "2020-07-06": 0.0124})

    def test_missing_leading_coverage_is_a_hard_error(self):
        with self.assertRaises(ValueError):
            daily_rate_by_trading_day({"2020-01-03": 1.5}, ["2020-01-02", "2020-01-03"])


if __name__ == "__main__":
    unittest.main()
