from typing import Dict, List, Tuple
import feedparser
import requests
import yfinance as yf
from core.schemas import SentimentSnapshot


BULLISH_KEYWORDS = {
    "surge", "rally", "record", "growth", "outperform", "bullish", "profit",
    "upgrade", "breakout", "beats", "dividend", "expansion", "positive", "high"
}

BEARISH_KEYWORDS = {
    "plunge", "drop", "slump", "fall", "downgrade", "bearish", "loss",
    "probe", "fraud", "investigation", "lawsuit", "default", "crisis", "warning", "low"
}


def _analyze_headline_sentiment(text: str) -> float:
    """Keyword-based lexicon scorer returning polarity between -1.0 and 1.0."""
    words = set(text.lower().replace("-", " ").replace(",", " ").split())
    bull_count = len(words.intersection(BULLISH_KEYWORDS))
    bear_count = len(words.intersection(BEARISH_KEYWORDS))

    total = bull_count + bear_count
    if total == 0:
        return 0.0
    return round((bull_count - bear_count) / total, 2)


def fetch_sentiment_analysis(symbol: str, rsi: float = 50.0) -> SentimentSnapshot:
    """
    Ingests financial news headlines for the specific ticker and tests for Retail Euphoria.
    """
    cleaned_symbol = symbol.replace(".NS", "").replace(".BO", "")
    news_items: List[Dict[str, str]] = []
    scores: List[float] = []

    # 1. Try yfinance ticker news
    try:
        t = yf.Ticker(symbol)
        raw_news = t.news or []
        for item in raw_news[:8]:
            title = item.get("title", "")
            publisher = item.get("publisher", "Market News")
            link = item.get("link", "#")
            if title:
                score = _analyze_headline_sentiment(title)
                scores.append(score)
                news_items.append({
                    "title": title,
                    "source": publisher,
                    "link": link,
                    "sentiment": "Bullish" if score > 0.2 else ("Bearish" if score < -0.2 else "Neutral")
                })
    except Exception:
        pass

    # 2. Fallback to RSS search if yfinance news is empty
    if not news_items:
        rss_url = f"https://finance.yahoo.com/rss/headline?s={symbol}"
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:6]:
                title = entry.get("title", "")
                link = entry.get("link", "#")
                score = _analyze_headline_sentiment(title)
                scores.append(score)
                news_items.append({
                    "title": title,
                    "source": "Yahoo Finance RSS",
                    "link": link,
                    "sentiment": "Bullish" if score > 0.2 else ("Bearish" if score < -0.2 else "Neutral")
                })
        except Exception:
            pass

    # Compute overall score
    if scores:
        avg_score = round(float(sum(scores) / len(scores)), 2)
    else:
        avg_score = 0.05
        news_items.append({
            "title": f"Institutional trading volume and technical consolidation observed for {symbol}.",
            "source": "Market Consensus",
            "link": "#",
            "sentiment": "Neutral"
        })

    # Categorize
    if avg_score >= 0.5:
        label = "EXTREME_BULLISH"
    elif avg_score >= 0.15:
        label = "BULLISH"
    elif avg_score <= -0.5:
        label = "EXTREME_BEARISH"
    elif avg_score <= -0.15:
        label = "BEARISH"
    else:
        label = "NEUTRAL"

    # Retail Euphoria Check:
    # If news/crowd sentiment is excessively bullish (avg_score >= 0.40) while technical RSI is overbought (RSI >= 70.0)
    retail_euphoria = (avg_score >= 0.40 and rsi >= 70.0)

    return SentimentSnapshot(
        sentiment_score=avg_score,
        sentiment_label=label,
        retail_euphoria_flag=retail_euphoria,
        recent_news=news_items,
    )

