import unittest
from src.macro_engine import MacroRegimeState
from src.risk_engine import calculate_algorithmic_execution, ExecutionRiskReport


class TestRiskSizingEngine(unittest.TestCase):
    def setUp(self):
        self.portfolio_equity = 100_000.0  # $100k account
        self.entry_price = 100.0
        self.atr_14 = 5.0

    def test_dynamic_atr_stop_loss_normal_regime(self):
        """Verify normal regime (VIX < 20) uses 2.0x ATR for hard stop."""
        macro_normal = MacroRegimeState(
            regime_label="EXPANSION",
            liquidity_bias=0.4,
            vix=14.5,
        )
        report = calculate_algorithmic_execution(
            portfolio_equity=self.portfolio_equity,
            current_price=self.entry_price,
            atr=self.atr_14,
            macro=macro_normal,
            resistance_target=125.0,  # 2.5x R:R
            user_risk_pct=1.0,
        )
        expected_stop = round(self.entry_price - (2.0 * self.atr_14), 2)  # 100 - 10 = 90.0
        self.assertEqual(report.algorithmic_stop_loss, expected_stop)
        self.assertEqual(report.per_share_risk, 10.0)

    def test_fixed_fractional_capital_preservation(self):
        """Verify 1% fixed-fractional sizing caps total dollar risk to exactly 1% of equity."""
        macro_normal = MacroRegimeState(
            regime_label="EXPANSION",
            liquidity_bias=0.4,
            vix=14.5,
        )
        report = calculate_algorithmic_execution(
            portfolio_equity=self.portfolio_equity,
            current_price=self.entry_price,
            atr=self.atr_14,
            macro=macro_normal,
            resistance_target=125.0,
            user_risk_pct=1.0,
        )
        # 1% of 100,000 = $1,000 max risk
        self.assertEqual(report.max_equity_at_risk, 1_000.0)
        # Per-share risk = $10.0 => 1000 / 10 = 100 shares
        self.assertEqual(report.calculated_shares, 100)
        # Total capital allocated = 100 * 100.0 = $10,000 (10% of portfolio)
        self.assertEqual(report.allocated_capital, 10_000.0)

    def test_asymmetric_risk_reward_gate(self):
        """Verify the 2.5:1 minimum Asymmetric Risk-Reward Hurdle."""
        macro = MacroRegimeState(regime_label="EXPANSION", liquidity_bias=0.4, vix=15.0)

        # Target offering only 1.5:1 R:R (Target = 115, Entry = 100, Stop = 90 => Reward = 15, Risk = 10 => 1.5x)
        report_fail = calculate_algorithmic_execution(
            portfolio_equity=self.portfolio_equity,
            current_price=self.entry_price,
            atr=self.atr_14,
            macro=macro,
            resistance_target=115.0,
            user_risk_pct=1.0,
        )
        self.assertFalse(report_fail.asymmetric_rr_passed)
        self.assertIn("POOR R:R", report_fail.execution_verdict)

        # Target offering 3.0:1 R:R (Target = 130, Entry = 100, Stop = 90 => Reward = 30, Risk = 10 => 3.0x)
        report_pass = calculate_algorithmic_execution(
            portfolio_equity=self.portfolio_equity,
            current_price=self.entry_price,
            atr=self.atr_14,
            macro=macro,
            resistance_target=130.0,
            user_risk_pct=1.0,
        )
        self.assertTrue(report_pass.asymmetric_rr_passed)
        self.assertIn("APPROVED", report_pass.execution_verdict)

    def test_vix_exposure_switch_scaling(self):
        """Verify VIX exposure tiers: Choppy (tightened ATR), High Risk (-50% sizing), Panic (Halt)."""
        # Choppy Regime: 20 <= VIX <= 25 (e.g. VIX = 22.0)
        macro_choppy = MacroRegimeState(regime_label="EXPANSION", liquidity_bias=0.1, vix=22.0)
        report_choppy = calculate_algorithmic_execution(
            portfolio_equity=self.portfolio_equity,
            current_price=self.entry_price,
            atr=self.atr_14,
            macro=macro_choppy,
            resistance_target=125.0,
        )
        # Tightened ATR multiple is 1.6x: 100 - (1.6 * 5.0) = 92.0
        self.assertEqual(report_choppy.algorithmic_stop_loss, 92.0)

        # High Risk: 25 < VIX <= 32 (e.g. VIX = 28.0)
        macro_stress = MacroRegimeState(regime_label="DEFENSIVE", liquidity_bias=-0.4, vix=28.0)
        report_stress = calculate_algorithmic_execution(
            portfolio_equity=self.portfolio_equity,
            current_price=self.entry_price,
            atr=self.atr_14,
            macro=macro_stress,
            resistance_target=125.0,
        )
        self.assertEqual(report_stress.vix_scale_factor, 0.50)

        # Panic Volatility Halt: VIX > 32 (e.g. VIX = 35.0)
        macro_halt = MacroRegimeState(regime_label="VOLATILITY_HALT", liquidity_bias=-0.8, vix=35.0)
        report_halt = calculate_algorithmic_execution(
            portfolio_equity=self.portfolio_equity,
            current_price=self.entry_price,
            atr=self.atr_14,
            macro=macro_halt,
            resistance_target=125.0,
        )
        self.assertEqual(report_halt.calculated_shares, 0)
        self.assertIn("VOLATILITY HALT", report_halt.execution_verdict)


if __name__ == "__main__":
    unittest.main()
