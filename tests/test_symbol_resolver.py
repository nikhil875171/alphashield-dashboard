"""
Unit tests for AlphaShield Symbol Resolver and Exchange Router (src/symbol_resolver.py).
Verifies:
- Mergers and rebrandings resolution (HDFC, LTI, CADILAHC, etc.)
- 6-digit BSE numeric security code resolution
- Cross-market detection (US in India mode, India in US mode)
- Dual-exchange fallback (NSE <-> BSE)
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.symbol_resolver import (
    resolve_ticker_symbol,
    check_dual_exchange_fallback,
    SYMBOL_ALIAS_MAP,
    KNOWN_US_SYMBOLS,
    KNOWN_INDIAN_SYMBOLS,
)


class TestSymbolResolver(unittest.TestCase):

    def test_merger_and_alias_resolution(self):
        """Verify historical mergers and renamed tickers resolve to active symbols."""
        ticker, note, mismatch = resolve_ticker_symbol("HDFC", is_indian=True)
        self.assertEqual(ticker, "HDFCBANK.NS")
        self.assertIsNotNone(note)
        self.assertIn("HDFC Bank", note)
        self.assertIsNone(mismatch)

        ticker_lti, note_lti, _ = resolve_ticker_symbol("LTI", is_indian=True)
        self.assertEqual(ticker_lti, "LTIM.NS")

        ticker_mind, note_mind, _ = resolve_ticker_symbol("MINDTREE", is_indian=True)
        self.assertEqual(ticker_mind, "LTIM.NS")

        ticker_cadila, note_cadila, _ = resolve_ticker_symbol("CADILAHC", is_indian=True)
        self.assertEqual(ticker_cadila, "ZYDUSLIFE.NS")

        ticker_ril, note_ril, _ = resolve_ticker_symbol("RIL", is_indian=True)
        self.assertEqual(ticker_ril, "RELIANCE.NS")

    def test_numeric_bse_code_resolution(self):
        """Verify 6-digit numeric script codes are routed to BSE (.BO)."""
        ticker, note, mismatch = resolve_ticker_symbol("532215", is_indian=True)
        self.assertEqual(ticker, "532215.BO")
        self.assertIsNotNone(note)
        self.assertIn("BSE", note)

    def test_cross_market_detection(self):
        """Verify cross-market mismatch alerts for US in India mode and vice-versa."""
        # US ticker typed while in Indian mode
        ticker_us, _, mismatch_us = resolve_ticker_symbol("NVDA", is_indian=True)
        self.assertEqual(mismatch_us, "US")

        ticker_aapl, _, mismatch_aapl = resolve_ticker_symbol("AAPL", is_indian=True)
        self.assertEqual(mismatch_aapl, "US")

        # Indian ticker typed while in US mode
        ticker_ind, _, mismatch_ind = resolve_ticker_symbol("TCS", is_indian=False)
        self.assertEqual(mismatch_ind, "INDIA")

        ticker_rel, _, mismatch_rel = resolve_ticker_symbol("RELIANCE", is_indian=False)
        self.assertEqual(mismatch_rel, "INDIA")

    def test_standard_indian_ticker_formatting(self):
        """Verify clean ticker symbols append .NS without spurious changes."""
        ticker, note, mismatch = resolve_ticker_symbol("HEROMOTORS", is_indian=True)
        self.assertEqual(ticker, "HEROMOTORS.NS")
        self.assertIsNone(note)
        self.assertIsNone(mismatch)

        ticker_with_ext, _, _ = resolve_ticker_symbol("TATAMOTORS.NS", is_indian=True)
        self.assertEqual(ticker_with_ext, "TATAMOTORS.NS")

    @patch("yfinance.Ticker")
    def test_dual_exchange_fallback(self, mock_ticker):
        """Verify dual exchange fallback redirects when primary exchange has no data."""
        mock_df = pd.DataFrame({"Close": [1.5, 1.6]}, index=pd.date_range("2026-09-01", periods=2))
        mock_ticker.return_value.history.return_value = mock_df

        res = check_dual_exchange_fallback("SHREESEC.NS")
        self.assertIsNotNone(res)
        alt_sym, msg = res
        self.assertEqual(alt_sym, "SHREESEC.BO")
        self.assertIn("BSE", msg)


if __name__ == "__main__":
    unittest.main()
