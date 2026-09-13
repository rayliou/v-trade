import unittest

from vitalis.pit import fundamentals_asof, normalize_fundamentals
from vitalis.sample_audit import compare_sample


class PitTests(unittest.TestCase):
    def setUp(self):
        self.sessions = ["2025-01-02", "2025-01-03", "2025-01-06", "2025-01-07", "2025-01-08"]
        self.row = dict(ticker="TEST", dimension="ART", date="2025-01-03",
                        reportperiod="2024-12-31", assets="100", ncfo="N/A")

    def test_filing_close_is_unavailable_until_next_session_close(self):
        rows = normalize_fundamentals([self.row], self.sessions)
        self.assertEqual(fundamentals_asof(rows, "2025-01-03"), {})
        self.assertEqual(rows[0]["available_on_close"], "2025-01-06")
        self.assertIsNone(fundamentals_asof(rows, "2025-01-06")["TEST"]["ncfo"])

    def test_future_filing_cannot_change_past_snapshot(self):
        future = dict(self.row, date="2025-01-07", assets="999")
        base = normalize_fundamentals([self.row], self.sessions)
        all_rows = normalize_fundamentals([self.row, future], self.sessions)
        self.assertEqual(fundamentals_asof(base, "2025-01-06"), fundamentals_asof(all_rows, "2025-01-06"))

    def test_new_filing_of_older_period_does_not_replace_newest_period(self):
        old = dict(self.row, date="2025-01-07", reportperiod="2024-09-30", assets="20")
        rows = normalize_fundamentals([self.row, old], self.sessions)
        self.assertEqual(fundamentals_asof(rows, "2025-01-08")["TEST"]["assets"], 100)

    def test_restatement_duplicate_and_short_calendar_fail(self):
        for rows in ([dict(self.row, dimension="MRT")], [self.row, self.row],
                     [dict(self.row, date="2025-01-08")]):
            with self.assertRaises(ValueError):
                normalize_fundamentals(rows, self.sessions)

    def test_partial_success_is_not_full_history(self):
        bars = {d: dict(close=10, dividend=0, split=1) for d in self.sessions}
        result = compare_sample([dict(date=self.sessions[-1], closeunadj=10)], [], bars,
                                dict(start=self.sessions[0], end=self.sessions[-1],
                                     price_relative_tolerance=.0005, action_absolute_tolerance=.00001))
        self.assertEqual(result["compared_price_sessions"], 1)
        self.assertEqual(result["missing_price_sessions"], 4)
        self.assertFalse(result["full_requested_price_history"])

    def test_invalid_source_value_cannot_pass_comparison(self):
        config = dict(start="2025-01-03", end="2025-01-03",
                      price_relative_tolerance=.0005, action_absolute_tolerance=.00001)
        bars = {"2025-01-03": dict(close=10, dividend=1, split=1)}
        for value in (float("nan"), 0, -1):
            with self.assertRaises(ValueError):
                compare_sample([dict(date="2025-01-03", closeunadj=value)], [], bars, config)
        with self.assertRaises(ValueError):
            compare_sample([dict(date="2025-01-03", closeunadj=10)],
                           [dict(date="2025-01-03", action="dividend", value="nan")], bars, config)


if __name__ == "__main__":
    unittest.main()
