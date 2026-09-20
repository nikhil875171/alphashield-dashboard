"""
NSE Full-Market Ingestion & Quantitative Classification Engine.

Dynamically ingests and monitors all 2,500+ equity securities listed on the
National Stock Exchange of India (NSE) directly from official exchange feeds:
1. Official NSE Equity Master: archives.nseindia.com/content/equities/EQUITY_L.csv
2. Daily Security Bhavdata: archives.nseindia.com/products/content/sec_bhavdata_full_<ddmmyyyy>.csv

Provides complete market-wide coverage without hardcoding.
"""

import os
import io
import datetime
import urllib.request
from typing import Optional, Tuple
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CACHE_FILE = os.path.join(CACHE_DIR, "nse_market_cache.csv")
MASTER_CACHE_FILE = os.path.join(CACHE_DIR, "nse_equity_master.csv")

NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _http_get(url: str, timeout: int = 12) -> bytes:
    """Executes a resilient HTTP GET request against NSE archive endpoints."""
    req = urllib.request.Request(url, headers=NSE_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_nse_equity_master() -> pd.DataFrame:
    """
    Fetches the official master list of all listed equity companies on the NSE.
    Contains Symbol, Company Name, Series, and Date of Listing.
    """
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        raw_bytes = _http_get(url)
        df = pd.read_csv(io.BytesIO(raw_bytes))
        df.columns = [c.strip() for c in df.columns]

        # Clean string fields
        for col in df.columns:
            try:
                df[col] = df[col].astype(str).str.strip()
            except Exception:
                pass

        # Save to local cache
        os.makedirs(CACHE_DIR, exist_ok=True)
        df.to_csv(MASTER_CACHE_FILE, index=False)
        return df
    except Exception:
        # Fallback to local cache if available
        if os.path.exists(MASTER_CACHE_FILE):
            return pd.read_csv(MASTER_CACHE_FILE)
        return pd.DataFrame()


def fetch_latest_nse_bhavcopy(days_lookback: int = 7) -> Tuple[pd.DataFrame, str]:
    """
    Auto-detects and fetches the most recent official daily Bhavcopy from NSE.
    Automatically steps back across weekends and market holidays.
    """
    today = datetime.date.today()

    for days_ago in range(days_lookback):
        target_date = today - datetime.timedelta(days=days_ago)
        d_str = target_date.strftime("%d%m%Y")
        url = f"https://archives.nseindia.com/products/content/sec_bhavdata_full_{d_str}.csv"

        try:
            raw_bytes = _http_get(url, timeout=10)
            if len(raw_bytes) > 50_000:  # Valid bhavcopy is ~350KB+
                df = pd.read_csv(io.BytesIO(raw_bytes))
                df.columns = [c.strip() for c in df.columns]

                # Strip whitespace from text columns
                for col in df.columns:
                    try:
                        df[col] = df[col].astype(str).str.strip()
                    except Exception:
                        pass

                return df, target_date.strftime("%d-%b-%Y")
        except Exception:
            continue

    return pd.DataFrame(), ""


def get_full_nse_market_snapshot(force_refresh: bool = False) -> pd.DataFrame:
    """
    Returns the complete, unified snapshot of all active NSE equity stocks.
    
    Merges master company metadata with the latest session Bhavcopy:
    - SYMBOL, TICKER (e.g. FILATFASH.NS)
    - NAME_OF_COMPANY
    - SERIES (EQ, BE, BZ, SM, ST)
    - CLOSE_PRICE, PREV_CLOSE, CHANGE_PCT
    - TTL_TRD_QNTY (Volume), TURNOVER_LACS, DELIV_PER
    - DATE_OF_LISTING
    
    Caches locally with a 2-hour TTL to ensure sub-second UI responsiveness.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Check local cache validity (< 2 hours old)
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            file_mtime = os.path.getmtime(CACHE_FILE)
            age_seconds = datetime.datetime.now().timestamp() - file_mtime
            if age_seconds < 7200:  # 2 hours
                cached_df = pd.read_csv(CACHE_FILE)
                if not cached_df.empty and "SYMBOL" in cached_df.columns:
                    return cached_df
        except Exception:
            pass

    # 1. Fetch Company Master & Daily Bhavcopy
    master_df = fetch_nse_equity_master()
    bhav_df, session_date = fetch_latest_nse_bhavcopy()

    if bhav_df.empty:
        # If live fetch fails, fallback to existing cache regardless of age
        if os.path.exists(CACHE_FILE):
            return pd.read_csv(CACHE_FILE)
        return pd.DataFrame()

    # 2. Filter for active equity series: EQ (Normal), BE (Trade-to-Trade), BZ (Z-group), SM/ST (SME)
    valid_series = ["EQ", "BE", "BZ", "SM", "ST"]
    eq_df = bhav_df[bhav_df["SERIES"].isin(valid_series)].copy()

    # 3. Merge with Master company directory
    if not master_df.empty and "SYMBOL" in master_df.columns:
        keep_cols = ["SYMBOL", "NAME OF COMPANY", "DATE OF LISTING"]
        existing_cols = [c for c in keep_cols if c in master_df.columns]
        merged = pd.merge(eq_df, master_df[existing_cols], on="SYMBOL", how="left")
        if "NAME OF COMPANY" in merged.columns:
            merged["NAME_OF_COMPANY"] = merged["NAME OF COMPANY"].fillna(merged["SYMBOL"])
        else:
            merged["NAME_OF_COMPANY"] = merged["SYMBOL"]
        if "DATE OF LISTING" in merged.columns:
            merged["DATE_OF_LISTING"] = merged["DATE OF LISTING"].fillna("")
        else:
            merged["DATE_OF_LISTING"] = ""
    else:
        merged = eq_df
        merged["NAME_OF_COMPANY"] = merged["SYMBOL"]
        merged["DATE_OF_LISTING"] = ""

    # 4. Standardize numeric columns
    merged["CLOSE_PRICE"] = pd.to_numeric(merged["CLOSE_PRICE"], errors="coerce").fillna(0.0)
    merged["PREV_CLOSE"] = pd.to_numeric(merged["PREV_CLOSE"], errors="coerce").fillna(0.0)
    
    # Calculate % change accurately
    def calc_chg(row):
        prev = row["PREV_CLOSE"]
        curr = row["CLOSE_PRICE"]
        if prev > 0:
            return ((curr - prev) / prev) * 100.0
        return 0.0

    merged["CHANGE_PCT"] = merged.apply(calc_chg, axis=1)
    merged["TTL_TRD_QNTY"] = pd.to_numeric(merged["TTL_TRD_QNTY"], errors="coerce").fillna(0).astype(int)
    merged["TURNOVER_LACS"] = pd.to_numeric(merged["TURNOVER_LACS"], errors="coerce").fillna(0.0)
    merged["DELIV_PER"] = pd.to_numeric(merged["DELIV_PER"], errors="coerce").fillna(0.0)

    # 5. Format standardized Yahoo Finance compatible Ticker symbol
    merged["TICKER"] = merged["SYMBOL"].astype(str) + ".NS"
    merged["SESSION_DATE"] = session_date

    # Drop non-essential columns for memory efficiency
    cols_to_keep = [
        "SYMBOL", "TICKER", "NAME_OF_COMPANY", "SERIES",
        "CLOSE_PRICE", "PREV_CLOSE", "CHANGE_PCT",
        "TTL_TRD_QNTY", "TURNOVER_LACS", "DELIV_PER",
        "DATE_OF_LISTING", "SESSION_DATE"
    ]
    final_cols = [c for c in cols_to_keep if c in merged.columns]
    result_df = merged[final_cols].drop_duplicates(subset=["SYMBOL"]).copy()

    # Save to local cache
    try:
        result_df.to_csv(CACHE_FILE, index=False)
    except Exception:
        pass

    return result_df


def build_full_nse_thematic_radar():
    """
    Categorizes the entire 2,500+ NSE equity universe into 5 institutional radar categories:
    1. 'penny': All stocks <= ₹100 (1,300+ stocks, lowest price first).
    2. 'trending': Top % gainers and volume breakout stocks across the market.
    3. 'new': Recently listed IPOs and SME platform issues.
    4. 'safe': High-turnover market pillars and large-cap anchors.
    5. 'future': High institutional delivery percentage (demat accumulation).
    """
    from src.market_radar import ThematicStockItem

    df = get_full_nse_market_snapshot()
    if df.empty:
        return {}

    # 1. Penny / Small-Priced: All stocks <= 100 Rs sorted ascending
    penny_df = df[(df["CLOSE_PRICE"] <= 100.0) & (df["CLOSE_PRICE"] > 0.0)].sort_values("CLOSE_PRICE")
    penny_items = []
    for r in penny_df.itertuples():
        p = float(r.CLOSE_PRICE)
        chg = float(r.CHANGE_PCT)
        vol = int(r.TTL_TRD_QNTY)
        if p < 1.0:
            badge = "🔴 Nano-Penny (<₹1)"
            risk = "Sub-Rupee Micro-Cap"
        elif p < 10.0:
            badge = "🔴 Micro-Penny (<₹10)"
            risk = "Sub-₹10 Micro-Cap"
        elif p <= 50.0:
            badge = "🟡 Low-Priced Small-Cap"
            risk = "Moderate Risk Small-Cap"
        else:
            badge = "🟢 Sub-₹100 Small-Cap"
            risk = "Liquid Small-Cap / PSU"

        penny_items.append(ThematicStockItem(
            ticker=r.TICKER,
            name=r.NAME_OF_COMPANY,
            approx_price=f"₹{p:,.2f}",
            category_id="penny",
            category_title="🪙 Small-Priced (< ₹100)",
            catalyst_driver=f"⚡ NSE Session: Traded at ₹{p:,.2f} ({chg:+.2f}%) on {vol:,} volume.",
            why_it_matters=f"Official NSE Equity | Series: {r.SERIES} | Traded Value: ₹{r.TURNOVER_LACS:,.2f}L.",
            risk_level=risk,
            risk_badge=badge,
            change_pct=chg,
            change_str=f"{chg:+.2f}%",
            volume_multiple=1.0,
            news_url=""
        ))

    # 2. Trending Today (Top Momentum & Volume Gainers)
    trending_df = df[df["TTL_TRD_QNTY"] >= 50000].sort_values("CHANGE_PCT", ascending=False)
    trending_items = []
    for r in trending_df.head(100).itertuples():
        p = float(r.CLOSE_PRICE)
        chg = float(r.CHANGE_PCT)
        vol = int(r.TTL_TRD_QNTY)
        badge = "🟢 Upper Momentum" if chg >= 5.0 else ("🟢 Bullish Momentum" if chg > 0 else "⚡ Heavy Volume Action")
        trending_items.append(ThematicStockItem(
            ticker=r.TICKER,
            name=r.NAME_OF_COMPANY,
            approx_price=f"₹{p:,.2f}",
            category_id="trending",
            category_title="🔥 Trending Today (Top Momentum)",
            catalyst_driver=f"⚡ Top Market Momentum: {chg:+.2f}% surge on {vol:,} shares traded.",
            why_it_matters=f"High-Volume Mover | Series: {r.SERIES} | Turnover: ₹{r.TURNOVER_LACS:,.2f}L.",
            risk_level=f"High Momentum ({chg:+.1f}%)",
            risk_badge=badge,
            change_pct=chg,
            change_str=f"{chg:+.2f}%",
            volume_multiple=2.0 if chg > 3 else 1.2,
            news_url=""
        ))

    # 3. New & Emerging (Recently listed since 2022 or SME platform)
    df_copy = df.copy()
    df_copy["DATE_PARSED"] = pd.to_datetime(df_copy["DATE_OF_LISTING"], format="%d-%b-%Y", errors="coerce")
    new_df = df_copy[(df_copy["DATE_PARSED"] >= "2022-01-01") | (df_copy["SERIES"].isin(["SM", "ST"]))].sort_values("TURNOVER_LACS", ascending=False)
    new_items = []
    for r in new_df.head(100).itertuples():
        p = float(r.CLOSE_PRICE)
        chg = float(r.CHANGE_PCT)
        badge = "🌱 SME Growth Platform" if r.SERIES in ["SM", "ST"] else "🌱 Recent IPO / Listing"
        date_str = r.DATE_OF_LISTING if r.DATE_OF_LISTING else "Recent"
        new_items.append(ThematicStockItem(
            ticker=r.TICKER,
            name=r.NAME_OF_COMPANY,
            approx_price=f"₹{p:,.2f}",
            category_id="new",
            category_title="🌱 New & Emerging Disruptors",
            catalyst_driver=f"⚡ Emerging Growth: Listed on {date_str} | Closed at ₹{p:,.2f} ({chg:+.2f}%).",
            why_it_matters=f"New Market Entrant | Series: {r.SERIES} | Listing Date: {date_str}.",
            risk_level="Emerging Growth / Innovation",
            risk_badge=badge,
            change_pct=chg,
            change_str=f"{chg:+.2f}%",
            volume_multiple=1.5,
            news_url=""
        ))

    # 4. Safe Havens (Large-Cap Anchors with massive turnover)
    safe_df = df[(df["TURNOVER_LACS"] >= 1500.0) & (df["CLOSE_PRICE"] > 50.0)].sort_values("TURNOVER_LACS", ascending=False)
    safe_items = []
    for r in safe_df.head(100).itertuples():
        p = float(r.CLOSE_PRICE)
        chg = float(r.CHANGE_PCT)
        safe_items.append(ThematicStockItem(
            ticker=r.TICKER,
            name=r.NAME_OF_COMPANY,
            approx_price=f"₹{p:,.2f}",
            category_id="safe",
            category_title="🏰 Safe Havens & Blue-Chips",
            catalyst_driver=f"⚡ Liquid Institutional Anchor: ₹{r.TURNOVER_LACS:,.1f}L session turnover at ₹{p:,.2f}.",
            why_it_matters=f"Market Pillar | Massive institutional liquidity and sovereign investor participation.",
            risk_level="Low Volatility / Blue-Chip",
            risk_badge="🟢 Safe Haven",
            change_pct=chg,
            change_str=f"{chg:+.2f}%",
            volume_multiple=1.0,
            news_url=""
        ))

    # 5. Future Supercycles / Institutional Delivery Accumulation
    future_df = df[(df["DELIV_PER"] >= 50.0) & (df["TURNOVER_LACS"] >= 200.0) & (df["CHANGE_PCT"] >= 0.0)].sort_values("DELIV_PER", ascending=False)
    future_items = []
    for r in future_df.head(100).itertuples():
        p = float(r.CLOSE_PRICE)
        chg = float(r.CHANGE_PCT)
        deliv = float(r.DELIV_PER)
        future_items.append(ThematicStockItem(
            ticker=r.TICKER,
            name=r.NAME_OF_COMPANY,
            approx_price=f"₹{p:,.2f}",
            category_id="future",
            category_title="🚀 Future Supercycles (Institutional Accumulation)",
            catalyst_driver=f"⚡ Strong Demat Delivery: {deliv:.1f}% delivery accumulation at ₹{p:,.2f} ({chg:+.2f}%).",
            why_it_matters=f"Institutional Handover | High delivery buying signals sustained multi-quarter accumulation.",
            risk_level="Secular Supercycle / Delivery",
            risk_badge=f"🚀 {deliv:.0f}% Demat Delivery",
            change_pct=chg,
            change_str=f"{chg:+.2f}%",
            volume_multiple=1.3,
            news_url=""
        ))

    return {
        "penny": penny_items,
        "trending": trending_items,
        "new": new_items,
        "safe": safe_items,
        "future": future_items,
    }

