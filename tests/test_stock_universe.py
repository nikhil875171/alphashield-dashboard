"""
Unit tests for the centralized stock universe and sector taxonomy registry (src/stock_universe.py).
Validates Master Specification requirements:
- 17 Standardized Sectors
- 3 Market-Cap Tiers (Large-Cap, Mid-Cap, Small-Cap)
- Dual Market Coverage (US, INDIA)
- Search and filtering capabilities
"""

import unittest
from src.stock_universe import (
    StockEntry,
    get_stock_universe,
    get_all_sectors,
    get_all_cap_tiers,
    search_stock_universe,
    infer_company_sector,
    infer_cap_tier,
    get_ticker_sector_map,
)


class TestStockUniverse(unittest.TestCase):
    def setUp(self):
        self.universe = get_stock_universe()

    def test_universe_not_empty_and_valid_schema(self):
        """Verify the universe contains equities and strictly follows StockEntry schema."""
        self.assertGreater(len(self.universe), 100)
        
        for entry in self.universe:
            self.assertIsInstance(entry, StockEntry)
            self.assertTrue(entry.ticker.strip())
            self.assertTrue(entry.name.strip())
            self.assertIn(entry.market, ["US", "INDIA"])
            self.assertIn(entry.market_cap_tier, ["Large-Cap", "Mid-Cap", "Small-Cap"])
            self.assertTrue(entry.sector.strip())
            self.assertTrue(entry.sub_sector.strip())
            self.assertTrue(entry.plain_english_role.strip())
            self.assertTrue(entry.thematic_anchor.strip())

    def test_all_17_standardized_sectors_present(self):
        """Verify all 17 standardized Master Specification sectors are represented."""
        expected_sectors = {
            "Telecommunications & Networks",
            "Textiles, Technical Fibers & Apparel",
            "FMCG (Fast-Moving Consumer Goods)",
            "Banking & Financial Services",
            "Automobile & Ancillaries",
            "IT Industry & High-Tech Software",
            "Healthcare & Pharmaceuticals",
            "Energy, Power & Utilities",
            "Consumer Durables & Electronics",
            "Industrial Products & Capital Goods",
            "Raw Materials, Metals & Mining",
            "Logistics, Freight & Maritime",
            "Derived Materials & Chemicals",
            "Agricultural & Farm Products",
            "Media & Entertainment",
            "Hospitality, Travel & Aviation",
            "Apparel & Accessories",
        }
        
        actual_sectors = set(get_all_sectors())
        for sector in expected_sectors:
            self.assertIn(sector, actual_sectors, f"Sector missing: {sector}")
        
        self.assertEqual(len(actual_sectors), 17)

    def test_all_three_market_cap_tiers_present(self):
        """Verify Large-Cap, Mid-Cap, and Small-Cap tiers exist in the universe."""
        tiers = get_all_cap_tiers()
        self.assertIn("Large-Cap", tiers)
        self.assertIn("Mid-Cap", tiers)
        self.assertIn("Small-Cap", tiers)

        # Check that we have stocks in every tier
        large_caps = [s for s in self.universe if s.market_cap_tier == "Large-Cap"]
        mid_caps = [s for s in self.universe if s.market_cap_tier == "Mid-Cap"]
        small_caps = [s for s in self.universe if s.market_cap_tier == "Small-Cap"]

        self.assertGreater(len(large_caps), 20)
        self.assertGreater(len(mid_caps), 20)
        self.assertGreater(len(small_caps), 20)

    def test_dual_market_coverage(self):
        """Verify both US and Indian markets are well represented."""
        india_stocks = [s for s in self.universe if s.market == "INDIA"]
        us_stocks = [s for s in self.universe if s.market == "US"]

        self.assertGreater(len(india_stocks), 40)
        self.assertGreater(len(us_stocks), 40)

        # Indian tickers must end with .NS or .BO
        for s in india_stocks:
            self.assertTrue(s.ticker.endswith(".NS") or s.ticker.endswith(".BO"), f"Indian ticker {s.ticker} should end with .NS or .BO")

    def test_search_and_filter_functionality(self):
        """Test searching by sector, cap tier, market, and query string."""
        # 1. Filter by Sector: Telecommunications
        telecoms = search_stock_universe(sector="Telecommunications & Networks")
        self.assertGreaterEqual(len(telecoms), 6)
        for s in telecoms:
            self.assertEqual(s.sector, "Telecommunications & Networks")

        # 2. Filter by Sector: Textiles
        textiles = search_stock_universe(sector="Textiles, Technical Fibers & Apparel")
        self.assertGreaterEqual(len(textiles), 6)
        for s in textiles:
            self.assertEqual(s.sector, "Textiles, Technical Fibers & Apparel")

        # 3. Filter by Cap Tier
        mid_caps = search_stock_universe(market_cap_tier="Mid-Cap")
        self.assertGreaterEqual(len(mid_caps), 20)
        for s in mid_caps:
            self.assertEqual(s.market_cap_tier, "Mid-Cap")

        # 4. Filter by Market
        us_only = search_stock_universe(market="US")
        for s in us_only:
            self.assertEqual(s.market, "US")

        # 5. Search query by ticker symbol
        nvda_results = search_stock_universe(query="NVDA")
        self.assertTrue(any(s.ticker == "NVDA" for s in nvda_results))

        # 6. Search query by company name
        tata_results = search_stock_universe(query="Tata")
        for s in tata_results:
            self.assertTrue(
                "tata" in s.name.lower()
                or "tata" in s.ticker.lower()
                or "tata" in s.plain_english_role.lower()
            )
        self.assertTrue(any("tata" in s.name.lower() for s in tata_results))

    def test_inference_and_ticker_mapping(self):
        """Test inference of sectors, cap tiers, and fast lookup dictionary."""
        # 1. Ticker map
        t_map = get_ticker_sector_map()
        self.assertIn("RELIANCE.NS", t_map)
        self.assertEqual(t_map["RELIANCE.NS"][0], "Energy, Power & Utilities")

        # 2. Sector keyword inference
        self.assertEqual(infer_company_sector("Vodafone Idea Telecom", "IDEA.NS"), "Telecommunications & Networks")
        self.assertEqual(infer_company_sector("Alok Textile Mills", "ALOKTEXT.NS"), "Textiles, Technical Fibers & Apparel")
        self.assertEqual(infer_company_sector("Punjab National Bank", "PNB.NS"), "Banking & Financial Services")
        self.assertEqual(infer_company_sector("Maruti Suzuki Motors", "MARUTI.NS"), "Automobile & Ancillaries")
        self.assertEqual(infer_company_sector("Cipla Pharmaceuticals", "CIPLA.NS"), "Healthcare & Pharmaceuticals")
        self.assertEqual(infer_company_sector("Tata Power Solar", "TATAPOWER.NS"), "Energy, Power & Utilities")
        self.assertEqual(infer_company_sector("Infosys Software Technologies", "INFY.NS"), "IT Industry & High-Tech Software")
        self.assertEqual(infer_company_sector("Britannia Food & FMCG", "BRITANNIA.NS"), "FMCG (Fast-Moving Consumer Goods)")

        # 3. Cap tier inference
        self.assertEqual(infer_cap_tier(25.0, category_id="penny"), "Small-Cap")
        self.assertEqual(infer_cap_tier(1500.0, turnover=2000.0, category_id="safe"), "Large-Cap")
        self.assertEqual(infer_cap_tier(250.0, turnover=100.0), "Mid-Cap")


if __name__ == "__main__":
    unittest.main()
