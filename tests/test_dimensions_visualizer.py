import unittest
import math
from unittest.mock import MagicMock
from core.visualizer import (
    compute_institutional_dimension_scores,
    build_institutional_radar_chart,
)


class TestDimensionsVisualizer(unittest.TestCase):
    """Test suite for Institutional Dimension Normalization and Radar Visualization."""

    def setUp(self):
        # Mock macro
        self.macro_safe = MagicMock(vix=12.5, market_mood_color="green", market_mood_desc="Smooth skies")
        self.macro_danger = MagicMock(vix=32.0, market_mood_color="red", market_mood_desc="Stormy seas")

        # Mock factors
        self.factors_safe = MagicMock(
            altman_z_score=3.4,
            piotroski_f_score=8,
            beneish_manipulation_risk=False,
            beneish_m_score=-2.8,
            sloan_accrual_ratio=0.03,
        )
        self.factors_distress = MagicMock(
            altman_z_score=1.1,
            piotroski_f_score=3,
            beneish_manipulation_risk=True,
            beneish_m_score=-1.2,
            sloan_accrual_ratio=0.18,
        )

        # Mock tech
        self.tech_safe = MagicMock(
            current_price=2500.0,
            ema_20=2450.0,
            ema_50=2400.0,
            ema_200=2200.0,
            rsi_14=56.0,
        )
        self.tech_breakdown = MagicMock(
            current_price=1800.0,
            ema_20=1950.0,
            ema_50=2100.0,
            ema_200=2300.0,
            rsi_14=28.0,
        )

        # Mock micro
        self.micro_safe = MagicMock(
            delivery_valid=True,
            delivery_pct=58.2,
            delivery_status_msg="Heavy vault accumulation",
        )
        self.micro_churn = MagicMock(
            delivery_valid=False,
            delivery_pct=21.0,
            delivery_status_msg="Speculative day-trading churn",
        )

        # Mock thematic
        self.thematic_safe = MagicMock(
            timeframe="Next 5 Years",
            horizon_code="5_YEARS",
            horizon_title="The Power Grid & Supercycle",
            thematic_driver="Data center power capexe",
            resource_scarcity_exposure="POWER_GRID",
            plain_english_takeaway="Benefits from grid expansion",
        )

        # Mock risk
        self.risk_safe = MagicMock(
            asymmetric_rr_passed=True,
            risk_reward_ratio=3.2,
            allocated_capital=150000.0,
            max_equity_at_risk=2000.0,
            risk_pct=1.0,
        )
        self.risk_nan = MagicMock(
            asymmetric_rr_passed=False,
            risk_reward_ratio=float("nan"),
            allocated_capital=float("nan"),
            max_equity_at_risk=0.0,
            risk_pct=0.0,
        )

    def test_safe_scores_computation(self):
        """Verify scores computation for an institutional-grade profile."""
        scores = compute_institutional_dimension_scores(
            self.macro_safe,
            self.factors_safe,
            self.tech_safe,
            self.micro_safe,
            self.thematic_safe,
            self.risk_safe,
        )

        # Assert all 6 pillars exist
        expected_pillars = [
            "Market Mood",
            "Company Health",
            "Price Trend",
            "Smart Money",
            "Secular Horizon",
            "Safety Gauge",
        ]
        for p in expected_pillars:
            self.assertIn(p, scores)
            self.assertGreaterEqual(scores[p]["score"], 70)
            self.assertEqual(scores[p]["class"], "safe")

    def test_distress_and_nan_resilience(self):
        """Verify that distress metrics and NaN values do not crash and produce safe defaults."""
        scores = compute_institutional_dimension_scores(
            self.macro_danger,
            self.factors_distress,
            self.tech_breakdown,
            self.micro_churn,
            self.thematic_safe,
            self.risk_nan,
        )

        # Safety Gauge with NaN ratio should be classified as danger and scored low
        self.assertIn("Safety Gauge", scores)
        self.assertEqual(scores["Safety Gauge"]["class"], "danger")
        self.assertLessEqual(scores["Safety Gauge"]["score"], 40)
        self.assertFalse(math.isnan(scores["Safety Gauge"]["score"]))

        # Company Health with distress Z-score and manipulation risk should be danger
        self.assertEqual(scores["Company Health"]["class"], "danger")
        self.assertLessEqual(scores["Company Health"]["score"], 40)

        # Market Mood with red VIX should be danger
        self.assertEqual(scores["Market Mood"]["class"], "danger")

    def test_build_institutional_radar_chart(self):
        """Verify that the Plotly radar chart generates properly with 2 traces."""
        scores = compute_institutional_dimension_scores(
            self.macro_safe,
            self.factors_safe,
            self.tech_safe,
            self.micro_safe,
            self.thematic_safe,
            self.risk_safe,
        )
        fig = build_institutional_radar_chart(scores, ticker="TATASTEEL.NS")
        self.assertIsNotNone(fig)
        self.assertEqual(len(fig.data), 2)
        # Trace 0: Benchmark, Trace 1: Company Profile
        self.assertIn("Benchmark", fig.data[0].name)
        self.assertIn("TATASTEEL.NS", fig.data[1].name)


if __name__ == "__main__":
    unittest.main()
