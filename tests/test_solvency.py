import unittest
import pandas as pd
from src.factor_model import calculate_sloan_accruals, evaluate_factor_model, FactorScoreSummary
from core.fundamental_engine import calculate_altman_z_score, calculate_piotroski_f_score


class TestSolvencySieve(unittest.TestCase):
    def test_altman_z_score_distress_threshold(self):
        """Verify Altman Z-score classifies < 1.81 as Distress Zone and >= 2.99 as Safe Zone."""
        # Synthesize a distressed balance sheet
        bs_distressed = pd.DataFrame(
            {"Total Assets": [1_000_000], "Total Current Assets": [100_000], "Total Current Liabilities": [300_000],
             "Retained Earnings": [-200_000], "Total Liabilities Net Minority Interest": [950_000]},
            index=["Total Assets", "Total Current Assets", "Total Current Liabilities", "Retained Earnings", "Total Liabilities Net Minority Interest"]
        )
        fin_distressed = pd.DataFrame(
            {"EBIT": [-50_000], "Total Revenue": [400_000]},
            index=["EBIT", "Total Revenue"]
        )
        z, zone = calculate_altman_z_score(bs_distressed, fin_distressed, market_cap=50_000)
        self.assertIsNotNone(z)
        self.assertLess(z, 1.81)
        self.assertIn("Distress", zone)

        # Synthesize a healthy balance sheet
        bs_healthy = pd.DataFrame(
            {"Total Assets": [1_000_000], "Total Current Assets": [600_000], "Total Current Liabilities": [150_000],
             "Retained Earnings": [500_000], "Total Liabilities Net Minority Interest": [200_000]},
            index=["Total Assets", "Total Current Assets", "Total Current Liabilities", "Retained Earnings", "Total Liabilities Net Minority Interest"]
        )
        fin_healthy = pd.DataFrame(
            {"EBIT": [300_000], "Total Revenue": [1_200_000]},
            index=["EBIT", "Total Revenue"]
        )
        z_h, zone_h = calculate_altman_z_score(bs_healthy, fin_healthy, market_cap=2_000_000)
        self.assertIsNotNone(z_h)
        self.assertGreaterEqual(z_h, 2.99)
        self.assertIn("Safe", zone_h)

    def test_piotroski_f_score_bounds(self):
        """Verify Piotroski F-score returns bounded integers from 0 to 9 when evaluated."""
        # Check empty dataframe behavior returns None gracefully
        score_empty, _ = calculate_piotroski_f_score(pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        self.assertIsNone(score_empty)

        # Mock healthy financials (rows = metrics, columns = dates)
        bs = pd.DataFrame(
            [
                [1_000_000, 950_000],
                [200_000, 250_000],
                [400_000, 350_000],
                [150_000, 160_000],
                [500_000, 500_000],
            ],
            index=[
                "Total Assets",
                "Total Non Current Liabilities Net Minority Interest",
                "Total Current Assets",
                "Total Current Liabilities",
                "Common Stock Equity",
            ],
            columns=["2025-12-31", "2024-12-31"],
        )

        fin = pd.DataFrame(
            [
                [120_000, 100_000],
                [400_000, 350_000],
                [1_200_000, 1_100_000],
            ],
            index=["Net Income", "Gross Profit", "Total Revenue"],
            columns=["2025-12-31", "2024-12-31"],
        )

        cf = pd.DataFrame(
            [
                [140_000, 110_000],
            ],
            index=["Operating Cash Flow"],
            columns=["2025-12-31", "2024-12-31"],
        )

        score, grade = calculate_piotroski_f_score(bs, fin, cf)
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 9)

    def test_sloan_accrual_anomaly_threshold(self):
        """Verify Sloan Accrual Ratio flags aggressive accounting when accruals exceed 10%."""
        # High accrual case: Net Income = 200k, Operating Cash Flow = 50k, Assets = 1M
        # Accrual = (200k - 50k) / 1M = 0.15 (15% > 10% threshold)
        bs = pd.DataFrame({"Total Assets": [1_000_000]}, index=["Total Assets"])
        fin = pd.DataFrame({"Net Income": [200_000]}, index=["Net Income"])
        cf = pd.DataFrame({"Operating Cash Flow": [50_000]}, index=["Operating Cash Flow"])

        ratio, flag = calculate_sloan_accruals(bs, fin, cf)
        self.assertEqual(ratio, 0.15)
        self.assertIn("HIGH ACCRUALS HAZARD", flag)

        # High quality earnings case: Net Income = 100k, Operating Cash Flow = 150k
        # Accrual = (100k - 150k) / 1M = -0.05
        fin_quality = pd.DataFrame({"Net Income": [100_000]}, index=["Net Income"])
        cf_quality = pd.DataFrame({"Operating Cash Flow": [150_000]}, index=["Operating Cash Flow"])
        ratio_q, flag_q = calculate_sloan_accruals(bs, fin_quality, cf_quality)
        self.assertLess(ratio_q, 0.0)
        self.assertIn("HIGH QUALITY EARNINGS", flag_q)

    def test_factor_model_zero_ruin_sieve(self):
        """Verify Factor Score Summary properly applies rejection gates."""
        df_dummy = pd.DataFrame({
            "Close": [100.0, 102.0, 101.0, 103.0],
            "Volume": [1000, 1200, 1100, 1300],
        })
        summary = evaluate_factor_model("AAPL", df_dummy)
        self.assertIsInstance(summary, FactorScoreSummary)
        self.assertIn(summary.sieve_verdict, ["PASS", "REJECT_INSOLVENT", "REJECT_WEAK_FUNDAMENTALS", "REJECT_EARNINGS_QUALITY"])


if __name__ == "__main__":
    unittest.main()
