"""
Unit tests for AlphaShield Full-Market NSE Ingestion and Dynamic Radar Classifier.
Verifies market-wide capture (2,500+ stocks), schema validation, and pure dynamic sorting.
"""

import unittest
import pandas as pd
from src.nse_full_market import (
    get_full_nse_market_snapshot,
    build_full_nse_thematic_radar,
)


class TestNSEFullMarket(unittest.TestCase):

    def test_full_nse_snapshot_structure(self):
        """Verify that the full NSE market snapshot returns thousands of valid equities."""
        df = get_full_nse_market_snapshot()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty, "NSE market snapshot should not be empty")
        self.assertGreater(len(df), 2000, "Should capture more than 2,000 listed NSE equities")

        # Verify essential columns exist
        expected_cols = [
            "SYMBOL", "TICKER", "NAME_OF_COMPANY", "SERIES",
            "CLOSE_PRICE", "PREV_CLOSE", "CHANGE_PCT", "TTL_TRD_QNTY"
        ]
        for col in expected_cols:
            self.assertIn(col, df.columns, f"Missing required column: {col}")

        # Verify ticker formatting (e.g. RELIANCE.NS)
        sample_ticker = df["TICKER"].iloc[0]
        self.assertTrue(sample_ticker.endswith(".NS"), "Ticker should have .NS suffix")

    def test_full_nse_thematic_radar_categories(self):
        """Verify dynamic categorization of the entire market into all 5 institutional tabs."""
        radar = build_full_nse_thematic_radar()
        self.assertIsInstance(radar, dict)

        for cat in ["penny", "trending", "new", "safe", "future"]:
            self.assertIn(cat, radar, f"Missing category: {cat}")
            self.assertGreater(len(radar[cat]), 0, f"Category {cat} should have stocks")

        # Verify penny stock price constraints (< ₹100) and ascending sorting
        penny_stocks = radar["penny"]
        self.assertGreater(len(penny_stocks), 500, "Should have hundreds of penny/small-priced stocks")

        # First stock should be sub-₹1 nano penny
        first_price = float(penny_stocks[0].approx_price.replace("₹", "").replace(",", ""))
        self.assertLess(first_price, 1.0, "First penny stock should be sub-rupee nano penny")

        # Verify ascending price order
        prev_price = 0.0
        for item in penny_stocks[:50]:
            p = float(item.approx_price.replace("₹", "").replace(",", ""))
            self.assertLessEqual(p, 100.0, f"Stock {item.ticker} exceeded ₹100 ceiling")
            self.assertGreaterEqual(p, prev_price, "Penny stocks must be sorted in ascending price order")
            prev_price = p

    def test_popular_penny_stocks_included(self):
        """Verify that popular Indian micro-cap and penny stocks are captured dynamically."""
        radar = build_full_nse_thematic_radar()
        penny_tickers = {item.ticker for item in radar["penny"]}

        expected_symbols = [
            "FILATFASH.NS", "SANWARIA.NS", "SITINET.NS", "SHRENIK.NS",
            "FEL.NS", "GTLINFRA.NS", "VIKASECO.NS", "RCOM.NS",
            "FCSSOFT.NS", "IDEA.NS", "RPOWER.NS", "YESBANK.NS"
        ]
        found = [s for s in expected_symbols if s in penny_tickers]
        self.assertGreaterEqual(len(found), 8, f"Expected popular penny stocks in radar, found: {found}")


if __name__ == "__main__":
    unittest.main()

