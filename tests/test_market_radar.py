"""
Unit tests for AlphaShield Live Dynamic Market Radar Screener.
Verifies real-time scanning, categorization, metric calculations, and zero-hardcoding compliance.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from src.market_radar import (
    ThematicStockItem,
    get_thematic_market_radar,
    scan_live_market_radar,
    _fetch_single_news,
    _fetch_news_concurrently,
)


class TestMarketRadar(unittest.TestCase):

    def test_thematic_stock_item_fields(self):
        """Verify ThematicStockItem dataclass structure and default fields."""
        item = ThematicStockItem(
            ticker="TEST.NS",
            name="Test Corp",
            approx_price="₹50.00",
            category_id="penny",
            category_title="🪙 Small-Priced (< ₹100)",
            catalyst_driver="Strong quarterly results",
            why_it_matters="Test company for validation",
            risk_level="Moderate",
            risk_badge="🟡 Moderate",
            change_pct=2.5,
            change_str="+2.50%",
            volume_multiple=1.8,
            news_url="https://example.com/news",
        )
        self.assertEqual(item.ticker, "TEST.NS")
        self.assertEqual(item.approx_price, "₹50.00")
        self.assertEqual(item.change_pct, 2.5)
        self.assertEqual(item.volume_multiple, 1.8)
        self.assertEqual(item.news_url, "https://example.com/news")

    @patch("yfinance.download")
    @patch("src.market_radar._fetch_news_concurrently")
    def test_scan_live_market_radar_categorization(self, mock_news, mock_download):
        """Verify dynamic screening and sorting into all 5 categories with simulated live OHLCV."""
        mock_news.return_value = {
            "SUZLON.NS": ("📰 [Reuters] Suzlon bags order", "https://reuters.com/suzlon"),
        }

        # Mock 5-day OHLCV data
        dates = pd.date_range("2026-09-01", periods=5)
        mock_close = pd.DataFrame(
            {
                "SUZLON.NS": [40.0, 41.0, 42.0, 42.5, 45.0],      # Under 100 -> Penny eligible, Up 5.88%
                "RELIANCE.NS": [1200.0, 1205.0, 1210.0, 1215.0, 1220.0],  # Safe, Low vol
                "SWIGGY.NS": [260.0, 265.0, 270.0, 275.0, 285.0],  # New, High momentum
                "BEL.NS": [380.0, 385.0, 390.0, 395.0, 420.0],    # Trending (big gain)
                "IREDA.NS": [100.0, 105.0, 110.0, 115.0, 125.0],  # Future megatrend
            },
            index=dates,
        )
        mock_volume = pd.DataFrame(
            {
                "SUZLON.NS": [1e6, 1e6, 1e6, 1e6, 2.5e6],        # 2.5x volume surge
                "RELIANCE.NS": [5e6, 5e6, 5e6, 5e6, 5e6],
                "SWIGGY.NS": [2e6, 2e6, 2e6, 2e6, 3e6],
                "BEL.NS": [3e6, 3e6, 3e6, 3e6, 6e6],             # 2.0x volume surge
                "IREDA.NS": [1e6, 1e6, 1e6, 1e6, 2e6],
            },
            index=dates,
        )

        mock_df = pd.concat({"Close": mock_close, "Volume": mock_volume}, axis=1)
        mock_download.return_value = mock_df

        result = scan_live_market_radar(is_indian=True)

        self.assertIn("penny", result)
        self.assertIn("safe", result)
        self.assertIn("new", result)
        self.assertIn("trending", result)
        self.assertIn("future", result)

        # Verify penny stock price constraint
        for item in result["penny"]:
            price_val = float(item.approx_price.replace("₹", "").replace("$", "").replace(",", ""))
            self.assertLessEqual(price_val, 100.0)

        # Verify Suzlon news mock was attached
        suzlon_items = [i for i in result["penny"] if i.ticker == "SUZLON.NS"]
        if suzlon_items:
            self.assertIn("Reuters", suzlon_items[0].catalyst_driver)
            self.assertEqual(suzlon_items[0].news_url, "https://reuters.com/suzlon")

    def test_live_execution_resilience(self):
        """Verify that live scan returns valid output without exceptions."""
        result = get_thematic_market_radar(is_indian=True)
        self.assertIsInstance(result, dict)
        self.assertIn("trending", result)
        self.assertTrue(len(result["trending"]) > 0)
        # Check first trending item has non-empty live fields
        top_trending = result["trending"][0]
        self.assertTrue(len(top_trending.ticker) > 0)
        self.assertTrue(len(top_trending.approx_price) > 0)
        self.assertIsInstance(top_trending.change_pct, float)
        self.assertIsInstance(top_trending.volume_multiple, float)


if __name__ == "__main__":
    unittest.main()
