"""
AlphaShield Intelligent Symbol Resolver & Cross-Market Exchange Router.

Provides:
1. Corporate Mergers, Rebrandings & Colloquial Aliases (e.g. HDFC -> HDFCBANK, LTI -> LTIM).
2. Dual-Exchange Fallback for Indian Markets (NSE .NS <-> BSE .BO for penny & exclusive listings).
3. Cross-Market Mismatch Detection (prompts user when a US ticker is searched in India mode or vice-versa).
"""

from typing import Dict, Optional, Tuple, Set
import yfinance as yf


# =============================================================================
# 1. CORPORATE MERGERS, REBRANDINGS & TICKER ALIASES
# =============================================================================

SYMBOL_ALIAS_MAP: Dict[str, Tuple[str, str]] = {
    # Mergers & Consolidations
    "HDFC": ("HDFCBANK.NS", "Housing Development Finance Corp (HDFC) merged with HDFC Bank in July 2023. Automatically routed to HDFCBANK.NS."),
    "HDFC.NS": ("HDFCBANK.NS", "Housing Development Finance Corp (HDFC) merged with HDFC Bank in July 2023. Automatically routed to HDFCBANK.NS."),
    "HDFC.BO": ("HDFCBANK.BO", "Housing Development Finance Corp (HDFC) merged with HDFC Bank. Automatically routed to HDFCBANK.BO."),
    "LTI": ("LTIM.NS", "L&T Infotech merged with Mindtree to form LTIMindtree. Automatically routed to LTIM.NS."),
    "LTI.NS": ("LTIM.NS", "L&T Infotech merged with Mindtree to form LTIMindtree. Automatically routed to LTIM.NS."),
    "MINDTREE": ("LTIM.NS", "Mindtree merged with L&T Infotech to form LTIMindtree. Automatically routed to LTIM.NS."),
    "MINDTREE.NS": ("LTIM.NS", "Mindtree merged with L&T Infotech to form LTIMindtree. Automatically routed to LTIM.NS."),
    "IDFC": ("IDFCFIRSTB.NS", "IDFC merged into IDFC FIRST Bank. Automatically routed to IDFCFIRSTB.NS."),
    "IDFC.NS": ("IDFCFIRSTB.NS", "IDFC merged into IDFC FIRST Bank. Automatically routed to IDFCFIRSTB.NS."),
    "TATASTEELBSL": ("TATASTEEL.NS", "Tata Steel BSL merged into Tata Steel. Automatically routed to TATASTEEL.NS."),
    "TATAMTRDVR": ("TATAMOTORS.NS", "Tata Motors DVR shares were converted into ordinary shares. Automatically routed to TATAMOTORS.NS."),
    "TATAMTRDVR.NS": ("TATAMOTORS.NS", "Tata Motors DVR shares were converted into ordinary shares. Automatically routed to TATAMOTORS.NS."),
    
    # Rebrandings & Corporate Name Changes
    "CADILAHC": ("ZYDUSLIFE.NS", "Cadila Healthcare rebranded to Zydus Lifesciences. Automatically routed to ZYDUSLIFE.NS."),
    "CADILAHC.NS": ("ZYDUSLIFE.NS", "Cadila Healthcare rebranded to Zydus Lifesciences. Automatically routed to ZYDUSLIFE.NS."),
    "MOTHERSUMI": ("MOTHERSON.NS", "Motherson Sumi Systems was reorganized into Samvardhana Motherson International. Routed to MOTHERSON.NS."),
    "MOTHERSUMI.NS": ("MOTHERSON.NS", "Motherson Sumi Systems was reorganized into Samvardhana Motherson International. Routed to MOTHERSON.NS."),
    "L&TFH": ("LTF.NS", "L&T Finance Holdings rebranded to L&T Finance Ltd (LTF). Routed to LTF.NS."),
    "L&TFH.NS": ("LTF.NS", "L&T Finance Holdings rebranded to L&T Finance Ltd (LTF). Routed to LTF.NS."),
    "MCDOWELL-N": ("UNITDSPR.NS", "McDowell / United Spirits traded under UNITDSPR. Routed to UNITDSPR.NS."),
    "MCDOWELL-N.NS": ("UNITDSPR.NS", "McDowell / United Spirits traded under UNITDSPR. Routed to UNITDSPR.NS."),
    
    # Colloquial Shortcuts & Common Synonyms
    "RIL": ("RELIANCE.NS", "Colloquial acronym for Reliance Industries Limited."),
    "INFOSYS": ("INFY.NS", "Full company name for Infosys Limited."),
    "BHARTI": ("BHARTIARTL.NS", "Colloquial name for Bharti Airtel Limited."),
    "TCSL": ("TCS.NS", "Tata Consultancy Services Limited."),
    "MARUTISUZUKI": ("MARUTI.NS", "Maruti Suzuki India Limited."),
    "BAJAJ": ("BAJAJ-AUTO.NS", "Colloquial name for Bajaj Auto Limited."),
    "SBI": ("SBIN.NS", "State Bank of India."),
    "L&T": ("LT.NS", "Larsen & Toubro Limited."),
}

# =============================================================================
# 2. CROSS-MARKET TICKER DICTIONARIES
# =============================================================================

KNOWN_US_SYMBOLS: Set[str] = {
    "NVDA", "AAPL", "MSFT", "TSLA", "GOOGL", "GOOG", "AMZN", "META",
    "AMD", "PLTR", "COIN", "NFLX", "AVGO", "ARM", "SMCI", "ORCL",
    "INTC", "QCOM", "CRM", "UBER", "DIS", "BA", "BABA", "BWA",
    "MOD", "APTV", "JPM", "V", "MA", "WMT", "COST", "UNH", "LLY",
    "NKE", "LULU", "RL", "VZ", "T", "AMT", "CIEN", "CEG", "VRT", "ETN",
    "SPY", "QQQ", "IWM", "DIA"
}

KNOWN_INDIAN_SYMBOLS: Set[str] = {
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL",
    "ITC", "LT", "TATAMOTORS", "MARUTI", "BAJFINANCE", "TATAPOWER", "SUZLON",
    "HAL", "BEL", "ADANIENT", "ADANIPORTS", "ZOMATO", "SWIGGY", "PAYTM",
    "HEROMOTORS", "HEROMOTOCO", "EICHERMOT", "WIPRO", "HCLTECH", "TITAN",
    "SUNPHARMA", "ULTRACEMCO", "JSWSTEEL", "POWERGRID", "NTPC", "COALINDIA",
    "AXISBANK", "KOTAKBANK", "ONGC", "GRASIM", "HINDALCO", "CIPLA", "DRREDDY"
}


# =============================================================================
# 3. CORE RESOLUTION FUNCTIONS
# =============================================================================

def resolve_ticker_symbol(
    raw_input: str,
    is_indian: bool = True
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Intelligently cleans and normalizes user ticker input.
    
    Returns:
        (resolved_ticker, alias_notice, market_mismatch)
        - resolved_ticker: Normalized ticker string
        - alias_notice: Explanatory message if a merger/alias was substituted
        - market_mismatch: "US" if a US ticker was typed in India mode, "INDIA" if vice-versa
    """
    if not raw_input or not raw_input.strip():
        default_ticker = "RELIANCE.NS" if is_indian else "NVDA"
        return default_ticker, None, None

    cleaned = raw_input.strip().upper()
    alias_notice = None
    market_mismatch = None

    # Check Alias Map first (exact match)
    if cleaned in SYMBOL_ALIAS_MAP:
        resolved, note = SYMBOL_ALIAS_MAP[cleaned]
        cleaned = resolved
        alias_notice = note

    # Check Cross-Market Mismatch
    raw_base = cleaned.replace(".NS", "").replace(".BO", "").strip()
    
    if is_indian:
        if raw_base in KNOWN_US_SYMBOLS and not (cleaned.endswith(".NS") or cleaned.endswith(".BO")):
            market_mismatch = "US"
        
        # Numeric 6-digit code -> BSE code (e.g., 532215)
        if cleaned.isdigit() and len(cleaned) == 6:
            cleaned = f"{cleaned}.BO"
            alias_notice = f"Identified 6-digit BSE security code. Routed to {cleaned}."
        elif not (cleaned.endswith(".NS") or cleaned.endswith(".BO")):
            cleaned = f"{cleaned}.NS"
    else:
        # In US mode
        if raw_base in KNOWN_INDIAN_SYMBOLS or cleaned.endswith(".NS") or cleaned.endswith(".BO"):
            market_mismatch = "INDIA"
            cleaned = raw_base

    return cleaned, alias_notice, market_mismatch


def check_dual_exchange_fallback(symbol: str) -> Optional[Tuple[str, str]]:
    """
    Checks if an alternative Indian exchange (.BO <-> .NS) has active trading data.
    Useful for penny stocks exclusive to BSE or tickers migrating between exchanges.
    """
    alt_symbol = None
    target_exchange = None

    if symbol.endswith(".NS"):
        base = symbol[:-3]
        alt_symbol = f"{base}.BO"
        target_exchange = "BSE (Bombay Stock Exchange)"
    elif symbol.endswith(".BO"):
        base = symbol[:-3]
        alt_symbol = f"{base}.NS"
        target_exchange = "NSE (National Stock Exchange of India)"

    if not alt_symbol:
        return None

    try:
        t = yf.Ticker(alt_symbol)
        df_alt = t.history(period="5d", interval="1d")
        if not df_alt.empty and len(df_alt) >= 1:
            msg = f"Auto-routed to {alt_symbol}: Active trading session resolved via {target_exchange}."
            return alt_symbol, msg
    except Exception:
        pass

    return None

