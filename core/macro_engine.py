import concurrent.futures
from typing import List
import feedparser
import pandas as pd
import yfinance as yf
from core.schemas import MacroSnapshot


def _fetch_single_metric(ticker_symbol: str, default_val: float) -> float:
    """Helper to fetch latest price/yield from yfinance with fast fallback."""
    try:
        t = yf.Ticker(ticker_symbol)
        hist = t.history(period="5d")
        if not hist.empty:
            return round(float(hist["Close"].dropna().iloc[-1]), 2)
    except Exception:
        pass
    return default_val


def fetch_macro_headlines(max_items: int = 5) -> List[str]:
    """Scrapes latest global/macro financial headlines via financial RSS feeds."""
    headlines = []
    feed_urls = [
        "https://finance.yahoo.com/news/rssindex",
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    ]

    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_items]:
                title = entry.get("title", "").strip()
                if title and title not in headlines:
                    headlines.append(title)
            if len(headlines) >= max_items:
                break
        except Exception:
            continue

    if not headlines:
        headlines = [
            "Global central banks maintain vigilance on persistent core inflation rates.",
            "Bond yields consolidate around benchmark levels amidst monetary policy reviews.",
            "Geopolitical developments remain monitored across key energy transit corridors."
        ]
    return headlines[:max_items]


def get_macro_snapshot(is_indian_market: bool = False) -> MacroSnapshot:
    """Aggregates macro signals and evaluates the macro regime and volatility kill-switch."""
    # Symbols
    vix_symbol = "^INDIAVIX" if is_indian_market else "^VIX"

    # Parallelize fetch of macro indicators for instant UI response
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        f_10y = executor.submit(_fetch_single_metric, "^TNX", 4.35)
        f_short = executor.submit(_fetch_single_metric, "^IRX", 4.85)
        f_vix = executor.submit(_fetch_single_metric, vix_symbol, 14.50)
        f_dxy = executor.submit(_fetch_single_metric, "DX-Y.NYB", 103.50)
        f_crude = executor.submit(_fetch_single_metric, "CL=F", 75.00)
        f_gold = executor.submit(_fetch_single_metric, "GC=F", 2650.00)

        yield_10y = f_10y.result()
        yield_short = f_short.result()
        vix = f_vix.result()
        dxy = f_dxy.result()
        crude = f_crude.result()
        gold = f_gold.result()

    yield_spread = round(yield_10y - yield_short, 2)
    headlines = fetch_macro_headlines()

    # Regime Determination & Volatility Kill-Switch
    # VIX > 25 indicates elevated volatility, VIX > 30 represents severe market panic
    volatility_kill_switch = vix >= 28.0

    if volatility_kill_switch or yield_spread < -0.60:
        regime = "DEFENSIVE"
    elif vix <= 16.5 and yield_spread >= 0.0:
        regime = "EXPANSION"
    else:
        regime = "NEUTRAL"

    return MacroSnapshot(
        yield_10y=yield_10y,
        yield_short=yield_short,
        yield_spread_10y_2y=yield_spread,
        vix=vix,
        dxy=dxy,
        crude_oil=crude,
        gold=gold,
        macro_regime=regime,
        volatility_kill_switch_active=volatility_kill_switch,
        top_headlines=headlines,
    )

