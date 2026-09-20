import unittest
from src.ancillary_screener import screen_ancillary_supplier, KNOWN_CUSTOMER_CONCENTRATION


class TestAncillaryScreener(unittest.TestCase):
    def test_known_concentration_lookup(self):
        """Verify customer concentration lookup for known high-leverage suppliers."""
        res_motherson = screen_ancillary_supplier("MOTHERSON.NS")
        self.assertGreaterEqual(res_motherson.customer_concentration_pct, 10.0)
        self.assertIn("Maruti", res_motherson.customer_concentration_flag)

        res_vrt = screen_ancillary_supplier("VRT")
        self.assertGreaterEqual(res_vrt.customer_concentration_pct, 10.0)
        self.assertIn("Microsoft", res_vrt.customer_concentration_flag)

    def test_operating_leverage_multiplier(self):
        """Verify operating leverage calculations are bounded and reasonable."""
        res = screen_ancillary_supplier("SONACOMS.NS", info={"sector": "Consumer Cyclical", "industry": "Auto Parts"})
        self.assertGreaterEqual(res.operating_leverage_multiplier, 1.5)
        self.assertLessEqual(res.operating_leverage_multiplier, 4.5)

    def test_capex_lead_lag_model(self):
        """Verify capex horizon phases are assigned based on industrial taxonomy."""
        res_elec = screen_ancillary_supplier("ETN", info={"sector": "Industrials", "industry": "Electrical Equipment"})
        self.assertEqual(res_elec.capex_phase, "PHASE_2_EQUIPMENT")


if __name__ == "__main__":
    unittest.main()

