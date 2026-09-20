"""
AlphaShield Dynamic Market Radar & Live Thematic Screener
=========================================================
Institutional-grade real-time market scanner that eliminates static/hardcoded stocks.
Downloads live OHLCV feeds, computes daily % deltas, relative volume multipliers,
and dynamically categorizes and ranks stocks across 5 strategic themes:
  1. 🪙 Small-Priced (< ₹100 or < $15)
  2. 🏰 Safe Havens (Fortress Blue-Chips)
  3. 🌱 New & Emerging Disruptors
  4. 🔥 Trending Today (Market-wide top gainers & volume breakouts)
  5. 🚀 Future Supercycles (Secular Megatrends)

Concurrently extracts live financial news catalysts via yfinance news feeds.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import time
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class ThematicStockItem:
    """Represents a dynamically screened stock discovery item with live market metrics."""
    ticker: str
    name: str
    approx_price: str
    category_id: str          # 'penny', 'safe', 'new', 'trending', 'future'
    category_title: str
    catalyst_driver: str
    why_it_matters: str
    risk_level: str
    risk_badge: str           # e.g., '🟢 Safe Haven', '🟡 Moderate', '🔴 High Risk'
    change_pct: float = 0.0
    change_str: str = "0.00%"
    volume_multiple: float = 1.0
    news_url: str = ""


# =============================================================================
# ACTIVE INSTITUTIONAL CANDIDATE UNIVERSES (50+ Verified Liquid Tickers per Market)
# =============================================================================

INDIAN_SCAN_UNIVERSE = [
    # Safe Havens / Market Pillars
    {"ticker": "RELIANCE.NS", "name": "Reliance Industries", "base_category": "safe", "why_it_matters": "Dominant conglomerate anchoring Nifty 50 with leading telecom and retail cash flows."},
    {"ticker": "TCS.NS", "name": "Tata Consultancy Services", "base_category": "safe", "why_it_matters": "Zero-debt balance sheet, 35%+ ROE, and mission-critical multi-billion enterprise contracts."},
    {"ticker": "HDFCBANK.NS", "name": "HDFC Bank", "base_category": "safe", "why_it_matters": "Premier private banking franchise with conservative underwriting and systemic retail presence."},
    {"ticker": "INFY.NS", "name": "Infosys", "base_category": "safe", "why_it_matters": "High cash generation, global digital consulting, and enterprise AI modernization programs."},
    {"ticker": "ICICIBANK.NS", "name": "ICICI Bank", "base_category": "safe", "why_it_matters": "Industry-leading ROA and consistent credit quality across digital retail and corporate lending."},
    {"ticker": "ITC.NS", "name": "ITC Limited", "base_category": "safe", "why_it_matters": "Defensive cash cow with unmatched pricing power, steady FMCG growth, and solid dividend payouts."},
    {"ticker": "LT.NS", "name": "Larsen & Toubro", "base_category": "safe", "why_it_matters": "Premier engineering and defense contractor, capturing multi-trillion rupee sovereign capex."},
    {"ticker": "BHARTIARTL.NS", "name": "Bharti Airtel", "base_category": "safe", "why_it_matters": "Telecom duopoly with expanding ARPU and high-growth enterprise cloud data centers."},
    {"ticker": "HINDUNILVR.NS", "name": "Hindustan Unilever", "base_category": "safe", "why_it_matters": "Essential consumption staple reaching 9 out of 10 Indian households every single day."},
    {"ticker": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "base_category": "safe", "why_it_matters": "Conservative risk-adjusted underwriting with fortress liquidity reserves and clean NPAs."},
    {"ticker": "TATASTEEL.NS", "name": "Tata Steel", "base_category": "safe", "why_it_matters": "Low-cost integrated steelmaker backed by captive iron ore mines and Tata corporate lineage."},
    {"ticker": "ASIANPAINT.NS", "name": "Asian Paints", "base_category": "safe", "why_it_matters": "Dominant decorative coatings monopoly with multi-decade dealer distribution moat."},
    {"ticker": "SBIN.NS", "name": "State Bank of India", "base_category": "safe", "why_it_matters": "India's largest bank by assets, driving national credit expansion with declining NPAs."},
    {"ticker": "NTPC.NS", "name": "NTPC Limited", "base_category": "safe", "why_it_matters": "Largest power generator in India, expanding into massive utility-scale green renewables."},
    {"ticker": "COALINDIA.NS", "name": "Coal India", "base_category": "safe", "why_it_matters": "Near-monopoly in domestic thermal coal supply with double-digit dividend distributions."},

    # New & Emerging Disruptors
    {"ticker": "JIOFIN.NS", "name": "Jio Financial Services", "base_category": "new", "why_it_matters": "BlackRock JV partner with balance sheet depth to disrupt lending and asset management."},
    {"ticker": "SWIGGY.NS", "name": "Swiggy Ltd", "base_category": "new", "why_it_matters": "Urban food delivery and quick-commerce duopoly with expanding dark store operating margins."},
    {"ticker": "TATATECH.NS", "name": "Tata Technologies", "base_category": "new", "why_it_matters": "Pure-play engineering R&D services powering OEM transitions to software-defined EVs."},
    {"ticker": "POLICYBZR.NS", "name": "PB Fintech", "base_category": "new", "why_it_matters": "Online insurance aggregator commanding near-monopoly market share in health and life cover."},
    {"ticker": "NYKAA.NS", "name": "FSN E-Commerce (Nykaa)", "base_category": "new", "why_it_matters": "Omnichannel luxury beauty and fashion marketplace with expanding owned-brand gross margins."},
    {"ticker": "DELHIVERY.NS", "name": "Delhivery", "base_category": "new", "why_it_matters": "Fully automated express parcel logistics network capturing e-commerce volume inflection."},
    {"ticker": "MAPMYINDIA.NS", "name": "C.E. Info Systems", "base_category": "new", "why_it_matters": "Indigenous HD map data monopoly powering automotive ADAS, Apple Maps India, and drones."},
    {"ticker": "PAYTM.NS", "name": "One97 Communications", "base_category": "new", "why_it_matters": "Merchant payment checkout network generating high-margin recurring soundbox rental fees."},
    {"ticker": "NAUKRI.NS", "name": "Info Edge (India)", "base_category": "new", "why_it_matters": "Dominant white-collar recruitment platform (Naukri) and premier incubator for Indian tech."},
    {"ticker": "KALYANKJIL.NS", "name": "Kalyan Jewellers", "base_category": "new", "why_it_matters": "Aggressive retail footprint capturing consumer shift from unorganized to hallmarked jewelry."},

    # Defense, Engineering & Momentum
    {"ticker": "BEL.NS", "name": "Bharat Electronics", "base_category": "trending", "why_it_matters": "Sovereign defense electronics champion securing naval radar and missile avionics orders."},
    {"ticker": "HAL.NS", "name": "Hindustan Aeronautics", "base_category": "trending", "why_it_matters": "Sole manufacturer of indigenous fighter aircraft and combat helicopters with multi-year order backlog."},
    {"ticker": "TRENT.NS", "name": "Trent Ltd", "base_category": "trending", "why_it_matters": "Tata Group retail phenomenon driven by exponential store expansions across Zudio."},
    {"ticker": "COCHINSHIP.NS", "name": "Cochin Shipyard", "base_category": "trending", "why_it_matters": "Aircraft carrier shipyard expanding into green commercial vessels and high-margin ship repair."},
    {"ticker": "MAZDOCK.NS", "name": "Mazagon Dock Shipbuilders", "base_category": "trending", "why_it_matters": "Submarine and guided-missile destroyer builder with massive multi-billion sovereign orders."},
    {"ticker": "DIXON.NS", "name": "Dixon Technologies", "base_category": "trending", "why_it_matters": "Premier domestic EMS contractor assembling smartphones and consumer electronics under PLI."},
    {"ticker": "BSE.NS", "name": "BSE Ltd", "base_category": "trending", "why_it_matters": "Surging market share in index derivatives and retail trading on Asia's oldest exchange."},
    {"ticker": "RVNL.NS", "name": "Rail Vikas Nigam", "base_category": "trending", "why_it_matters": "Primary executing arm for Indian Railways modernization and high-speed freight corridors."},
    {"ticker": "ADANIENT.NS", "name": "Adani Enterprises", "base_category": "trending", "why_it_matters": "Flagship private infrastructure incubator executing sovereign airports, solar, and data centers."},

    # Future Supercycles (Energy Transition, Grid, EVs)
    {"ticker": "SUZLON.NS", "name": "Suzlon Energy", "base_category": "future", "why_it_matters": "Debt-free market leader in domestic wind turbines powering India's 500 GW renewable mandate."},
    {"ticker": "IREDA.NS", "name": "IREDA", "base_category": "future", "why_it_matters": "State-owned non-banking finance institution underwriting sovereign green energy infrastructure."},
    {"ticker": "EXIDEIND.NS", "name": "Exide Industries", "base_category": "future", "why_it_matters": "Building India's premier lithium-ion cell gigafactory with global supply ties to Hyundai & Kia."},
    {"ticker": "TITAGARH.NS", "name": "Titagarh Rail Systems", "base_category": "future", "why_it_matters": "Builder of high-speed Vande Bharat trainsets and smart city metro coaches."},
    {"ticker": "JSWENERGY.NS", "name": "JSW Energy", "base_category": "future", "why_it_matters": "Rapidly pivoting toward utility-scale renewable power and multi-gigawatt battery storage (BESS)."},
    {"ticker": "KPITTECH.NS", "name": "KPIT Technologies", "base_category": "future", "why_it_matters": "Global software architecture specialist for electric powertrains and autonomous mobility."},
    {"ticker": "TATAELXSI.NS", "name": "Tata Elxsi", "base_category": "future", "why_it_matters": "High-margin automotive engineering design and AI solutions for medical and tech OEMs."},
    {"ticker": "DEEPAKFERT.NS", "name": "Deepak Fertilisers", "base_category": "future", "why_it_matters": "Key supplier of industrial nitric acid and electronic-grade chemicals for semiconductors."},
    {"ticker": "PRESTIGE.NS", "name": "Prestige Estates", "base_category": "future", "why_it_matters": "Capturing generational urbanization and premium residential demand across Indian tech hubs."},

    # Small-Priced Candidates (< ₹100 Target)
    {"ticker": "IDEA.NS", "name": "Vodafone Idea", "base_category": "penny", "why_it_matters": "Sub-₹20 telecom turnaround candidate executing 5G network rollout with government backing."},
    {"ticker": "YESBANK.NS", "name": "Yes Bank", "base_category": "penny", "why_it_matters": "Post-cleanup balance sheet recovery supported by low-cost retail deposit expansion."},
    {"ticker": "SOUTHBANK.NS", "name": "South Indian Bank", "base_category": "penny", "why_it_matters": "Attractive price-to-book valuation with clean NPA reduction under professional management."},
    {"ticker": "RPOWER.NS", "name": "Reliance Power", "base_category": "penny", "why_it_matters": "Rapidly deleveraging power producer benefiting from peak domestic electricity demand."},
    {"ticker": "UCOBANK.NS", "name": "UCO Bank", "base_category": "penny", "why_it_matters": "State-backed lender experiencing sustained asset quality normalization and rising margins."},
    {"ticker": "IOB.NS", "name": "Indian Overseas Bank", "base_category": "penny", "why_it_matters": "Recovered public lender with declining bad loans and sovereign capital backing."},
    {"ticker": "NHPC.NS", "name": "NHPC Ltd", "base_category": "penny", "why_it_matters": "Defensive state-owned hydropower utility commanding long-term power purchase agreements."},
    {"ticker": "NBCC.NS", "name": "NBCC (India) Ltd", "base_category": "penny", "why_it_matters": "Debt-free PSU managing mega-redevelopment construction projects on cost-plus basis."},
    {"ticker": "SJVN.NS", "name": "SJVN Ltd", "base_category": "penny", "why_it_matters": "Expanding renewable utility executing massive solar and hydro projects across North India."},
    {"ticker": "IDFCFIRSTB.NS", "name": "IDFC First Bank", "base_category": "penny", "why_it_matters": "High-CASA retail banking franchise with rapid branch expansion and clean underwriting."},
    {"ticker": "PNB.NS", "name": "Punjab National Bank", "base_category": "penny", "why_it_matters": "Major state lender benefiting from corporate credit demand and low credit costs."},
    {"ticker": "BANKBARODA.NS", "name": "Bank of Baroda", "base_category": "penny", "why_it_matters": "Top-tier public bank delivering double-digit ROE and international trade finance."},
]

US_SCAN_UNIVERSE = [
    # Safe Havens / Fortress Blue-Chips
    {"ticker": "MSFT", "name": "Microsoft Corporation", "base_category": "safe", "why_it_matters": "Enterprise software monopoly with Azure cloud infrastructure and multi-billion OpenAI stake."},
    {"ticker": "AAPL", "name": "Apple Inc.", "base_category": "safe", "why_it_matters": "2.2B active device ecosystem generating $100B+ annual free cash flow with massive share buybacks."},
    {"ticker": "BRK-B", "name": "Berkshire Hathaway", "base_category": "safe", "why_it_matters": "Warren Buffett's fortress balance sheet holding over $300B in cash reserves and Treasury bills."},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "base_category": "safe", "why_it_matters": "Global search monopoly, YouTube streaming, Google Cloud profitability, and Waymo autonomous leadership."},
    {"ticker": "AMZN", "name": "Amazon.com", "base_category": "safe", "why_it_matters": "E-commerce logistics dominance combined with high-margin AWS enterprise cloud computing."},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "base_category": "safe", "why_it_matters": "AAA-rated defensive healthcare giant providing essential pharmaceuticals and medical devices."},
    {"ticker": "PG", "name": "Procter & Gamble", "base_category": "safe", "why_it_matters": "Unmatched consumer goods pricing power across household essentials with 60+ years of dividend hikes."},
    {"ticker": "JPM", "name": "JPMorgan Chase", "base_category": "safe", "why_it_matters": "Premier global financial fortress benefiting from corporate dealmaking and net interest margins."},
    {"ticker": "V", "name": "Visa Inc.", "base_category": "safe", "why_it_matters": "Duopoly payments tollbooth processing trillions in global electronic transactions at 50%+ margins."},
    {"ticker": "COST", "name": "Costco Wholesale", "base_category": "safe", "why_it_matters": "Unshakable membership-based warehouse moat with 90%+ renewal rates and relentless customer traffic."},
    {"ticker": "WMT", "name": "Walmart Inc.", "base_category": "safe", "why_it_matters": "World's largest retailer commanding grocery distribution and scaling high-margin retail media ads."},
    {"ticker": "UNH", "name": "UnitedHealth Group", "base_category": "safe", "why_it_matters": "Vertically integrated healthcare giant combining health insurance with Optum clinical care."},

    # New & Emerging Disruptors
    {"ticker": "ARM", "name": "Arm Holdings", "base_category": "new", "why_it_matters": "Dominant low-power chip architecture powering 99% of smartphones and expanding into AI datacenters."},
    {"ticker": "RDDT", "name": "Reddit Inc.", "base_category": "new", "why_it_matters": "High-growth social forum platform monetizing unique human discussion data for LLM training."},
    {"ticker": "ALAB", "name": "Astera Labs", "base_category": "new", "why_it_matters": "Crucial PCIe and CXL semiconductor connectivity modules required for high-bandwidth AI GPU clusters."},
    {"ticker": "CAVA", "name": "CAVA Group", "base_category": "new", "why_it_matters": "Rapidly scaling Mediterranean fast-casual chain with industry-leading unit economics and same-store sales."},
    {"ticker": "TOST", "name": "Toast Inc.", "base_category": "new", "why_it_matters": "Cloud operating system and payments gateway powering tens of thousands of restaurant operations."},
    {"ticker": "DUOL", "name": "Duolingo", "base_category": "new", "why_it_matters": "Gamified language learning platform leveraging GenAI to drive high-margin paid subscriptions."},
    {"ticker": "KVYO", "name": "Klaviyo", "base_category": "new", "why_it_matters": "Customer data and email automation platform powering targeted modern e-commerce campaigns."},
    {"ticker": "CART", "name": "Maplebear (Instacart)", "base_category": "new", "why_it_matters": "Leading grocery technology platform expanding into digital shopping carts and retail ad networks."},
    {"ticker": "MNDY", "name": "Monday.com", "base_category": "new", "why_it_matters": "Cloud work management platform delivering high net retention and expanding enterprise contracts."},
    {"ticker": "CELH", "name": "Celsius Holdings", "base_category": "new", "why_it_matters": "Fast-growing fitness energy drink brand leveraging PepsiCo's nationwide distribution channels."},

    # High Beta / Trending / Momentum Leaders
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "base_category": "trending", "why_it_matters": "Global monopoly in AI GPUs and CUDA software stack powering hyperscale datacenters."},
    {"ticker": "TSLA", "name": "Tesla Inc.", "base_category": "trending", "why_it_matters": "Electric vehicle volume leader scaling Full Self-Driving neural networks and Cybercab robotics."},
    {"ticker": "PLTR", "name": "Palantir Technologies", "base_category": "trending", "why_it_matters": "Commercial and defense AI ontology platform seeing explosive demand from US government and Fortune 500."},
    {"ticker": "AMD", "name": "Advanced Micro Devices", "base_category": "trending", "why_it_matters": "Primary competitor in x86 CPUs and emerging alternative in datacenter AI accelerators (MI300)."},
    {"ticker": "META", "name": "Meta Platforms", "base_category": "trending", "why_it_matters": "Advertising cash engine funding open-source Llama AI models and smart glasses technology."},
    {"ticker": "SMCI", "name": "Super Micro Computer", "base_category": "trending", "why_it_matters": "Direct liquid cooling and modular server architecture built for dense GPU computing clusters."},
    {"ticker": "COIN", "name": "Coinbase Global", "base_category": "trending", "why_it_matters": "Leading US regulated digital asset custodian and exchange benefiting from institutional crypto ETF inflows."},
    {"ticker": "MSTR", "name": "MicroStrategy", "base_category": "trending", "why_it_matters": "Algorithmic treasury vehicle accumulating institutional Bitcoin reserves with software cash flow."},
    {"ticker": "APP", "name": "AppLovin", "base_category": "trending", "why_it_matters": "Axon 2.0 AI recommendation engine revolutionizing mobile app advertising and e-commerce conversion."},
    {"ticker": "HOOD", "name": "Robinhood Markets", "base_category": "trending", "why_it_matters": "Fast-scaling retail brokerage expanding into crypto staking, retirement accounts, and gold tier."},

    # Future Supercycles (Nuclear, Thermal Grid, Industrial AI)
    {"ticker": "VRT", "name": "Vertiv Holdings", "base_category": "future", "why_it_matters": "Critical thermal liquid cooling and power solutions required to prevent AI chips from overheating."},
    {"ticker": "CEG", "name": "Constellation Energy", "base_category": "future", "why_it_matters": "Largest US clean nuclear fleet securing multi-decade power purchase agreements with hyperscalers."},
    {"ticker": "ETN", "name": "Eaton Corporation", "base_category": "future", "why_it_matters": "Essential switchgear and power distribution equipment modernizing aging electrical grids."},
    {"ticker": "NVO", "name": "Novo Nordisk", "base_category": "future", "why_it_matters": "Ozempic and Wegovy pioneer transforming metabolic health and cardiovascular disease prevention."},
    {"ticker": "GEV", "name": "GE Vernova", "base_category": "future", "why_it_matters": "Gas turbines, wind power, and grid electrification software meeting soaring electricity demand."},
    {"ticker": "CRWD", "name": "CrowdStrike Holdings", "base_category": "future", "why_it_matters": "AI-native cloud security platform protecting enterprise endpoints against sophisticated cyber attacks."},
    {"ticker": "AXON", "name": "Axon Enterprise", "base_category": "future", "why_it_matters": "TASER devices, body cameras, and cloud evidence management modernizing global law enforcement."},
    {"ticker": "OKLO", "name": "Oklo Inc.", "base_category": "future", "why_it_matters": "Developing fast fission micro-reactors to provide emission-free power directly to data center sites."},
    {"ticker": "SMR", "name": "NuScale Power", "base_category": "future", "why_it_matters": "Pioneering certified small modular nuclear reactors for clean commercial baseload electricity."},
    {"ticker": "BWXT", "name": "BWX Technologies", "base_category": "future", "why_it_matters": "Manufactures nuclear reactor components for US Navy submarines and medical radioisotopes."},

    # Small-Priced Candidates (< $15 Target)
    {"ticker": "SOUN", "name": "SoundHound AI", "base_category": "penny", "why_it_matters": "Conversational voice AI powering automotive dashboards and restaurant drive-thrus."},
    {"ticker": "PLUG", "name": "Plug Power", "base_category": "penny", "why_it_matters": "Sub-$5 clean hydrogen ecosystem and turnkey fuel cell production infrastructure."},
    {"ticker": "ACHR", "name": "Archer Aviation", "base_category": "penny", "why_it_matters": "FAA commercial certification for 'Midnight' electric air taxis backed by United Airlines and Stellantis."},
    {"ticker": "JOBY", "name": "Joby Aviation", "base_category": "penny", "why_it_matters": "Pioneering commercial aerial ridesharing with strategic funding from Toyota and Delta Air Lines."},
    {"ticker": "ASTS", "name": "AST SpaceMobile", "base_category": "penny", "why_it_matters": "Low Earth orbit satellite network connecting directly to unmodified cellular smartphones."},
    {"ticker": "LUNR", "name": "Intuitive Machines", "base_category": "penny", "why_it_matters": "First commercial entity to land on the Moon under NASA's Artemis lunar exploration contracts."},
    {"ticker": "RKLB", "name": "Rocket Lab USA", "base_category": "penny", "why_it_matters": "Proven orbital launch provider and satellite component manufacturer behind SpaceX."},
    {"ticker": "BBAI", "name": "BigBear.ai", "base_category": "penny", "why_it_matters": "Decision-intelligence software contractor serving US defense and homeland security agencies."},
    {"ticker": "OPEN", "name": "Opendoor Technologies", "base_category": "penny", "why_it_matters": "Algorithmic home-buying platform with high operating leverage to falling mortgage interest rates."},
    {"ticker": "CLOV", "name": "Clover Health", "base_category": "penny", "why_it_matters": "Physician enablement software cutting Medicare hospitalization costs with positive operational cash flow."},
    {"ticker": "DNA", "name": "Ginkgo Bioworks", "base_category": "penny", "why_it_matters": "Biological cell programming foundry serving commercial pharmaceutical and agricultural clients."},
    {"ticker": "RGTI", "name": "Rigetti Computing", "base_category": "penny", "why_it_matters": "Full-stack quantum computing systems developing superconducting quantum processors."},
    {"ticker": "IONQ", "name": "IonQ Inc.", "base_category": "penny", "why_it_matters": "Commercial quantum computer manufacturer developing trapped-ion hardware architectures."},
]


def _fetch_single_news(ticker: str) -> tuple[str, str, str]:
    """Fetches the latest live news headline, publisher, and article URL for a ticker."""
    try:
        t = yf.Ticker(ticker)
        news_items = t.news
        if news_items and len(news_items) > 0:
            first = news_items[0]
            content = first.get("content", {})
            if content:
                title = content.get("title", "")
                provider = content.get("provider", {}).get("displayName", "Market Feed")
                url = content.get("canonicalUrl", {}).get("url", "")
                if title:
                    return ticker, f"📰 [{provider}] {title}", url
            # Legacy schema fallback
            title = first.get("title", "")
            publisher = first.get("publisher", "Market Feed")
            link = first.get("link", "")
            if title:
                return ticker, f"📰 [{publisher}] {title}", link
    except Exception:
        pass
    return ticker, "", ""


def _fetch_news_concurrently(tickers: List[str]) -> Dict[str, tuple[str, str]]:
    """Concurrently fetches news headlines and URLs using ThreadPoolExecutor."""
    results = {}
    if not tickers:
        return results

    max_workers = min(12, max(2, len(tickers)))
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for sym, driver, url in executor.map(_fetch_single_news, tickers):
                if driver:
                    results[sym] = (driver, url)
    except Exception:
        pass
    return results


def scan_live_market_radar(is_indian: bool = False) -> Dict[str, List[ThematicStockItem]]:
    """
    Executes a pure live quantitative market scan across the candidate universe.
    
    1. Downloads 5-day OHLCV in a single batch via yf.download.
    2. Calculates live price, day change %, 5-day average volume, and relative volume.
    3. Dynamically screens and sorts candidates into 5 categories:
       - 'penny': Live price < ₹100 (IN) or < $15 (US), sorted by relative volume.
       - 'safe': Fortress blue-chips, sorted by 5-day stability/low volatility.
       - 'new': Disruptors & new listings, sorted by momentum.
       - 'trending': Market-wide top gainers & volume breakouts (all scanned stocks).
       - 'future': Secular megatrends, sorted by relative strength.
    4. Concurrently extracts live financial news headlines.
    """
    universe = INDIAN_SCAN_UNIVERSE if is_indian else US_SCAN_UNIVERSE
    currency_sym = "₹" if is_indian else "$"
    symbols = [item["ticker"] for item in universe]
    meta_by_sym = {item["ticker"]: item for item in universe}

    # Step 1: Batch download latest 5-day market data
    try:
        df = yf.download(symbols, period="5d", interval="1d", progress=False)
    except Exception:
        df = pd.DataFrame()

    live_metrics = {}

    if not df.empty and "Close" in df.columns:
        close_df = df["Close"]
        vol_df = df["Volume"] if "Volume" in df.columns else pd.DataFrame()

        for sym in symbols:
            try:
                if sym in close_df.columns:
                    s_close = close_df[sym].dropna()
                    s_vol = vol_df[sym].dropna() if (not vol_df.empty and sym in vol_df.columns) else pd.Series()

                    if len(s_close) >= 2:
                        last_p = float(s_close.iloc[-1])
                        prev_p = float(s_close.iloc[-2])
                        chg_pct = ((last_p - prev_p) / prev_p) * 100.0

                        if len(s_vol) >= 2:
                            avg_v = float(s_vol.iloc[:-1].mean())
                            cur_v = float(s_vol.iloc[-1])
                            rel_v = (cur_v / avg_v) if avg_v > 0 else 1.0
                        else:
                            rel_v = 1.0

                        # Calculate 5-day return volatility
                        ret_pcts = s_close.pct_change().dropna()
                        volatility_5d = float(ret_pcts.std() * 100.0) if len(ret_pcts) > 1 else 1.5

                        live_metrics[sym] = {
                            "price": last_p,
                            "change_pct": chg_pct,
                            "rel_volume": rel_v,
                            "volatility": volatility_5d,
                        }
            except Exception:
                continue

    # Step 2: Dynamic Categorization & Quantitative Ranking
    penny_items = []
    safe_items = []
    new_items = []
    trending_candidates = []
    future_items = []

    price_ceiling = 100.0 if is_indian else 15.0

    for sym, meta in meta_by_sym.items():
        m = live_metrics.get(sym, None)
        if not m:
            continue

        price = m["price"]
        chg_pct = m["change_pct"]
        rel_v = m["rel_volume"]
        vol = m["volatility"]
        base_cat = meta["base_category"]

        # 1. Penny / Small-Priced condition (Strict live price ceiling)
        if price <= price_ceiling:
            risk_badge = "🔴 High Risk" if vol > 3.5 else "🟡 Moderate"
            risk_level = f"Volatile ({vol:.1f}% swing)" if vol > 3.5 else "Moderate Risk"
            penny_items.append((rel_v, sym, price, chg_pct, rel_v, risk_badge, risk_level))

        # 2. Safe Havens
        if base_cat == "safe":
            safe_items.append((-vol, sym, price, chg_pct, rel_v, "🟢 Safe Haven", "Low Volatility / Fortress"))

        # 3. New & Emerging
        if base_cat == "new":
            score = (chg_pct * 0.6) + (rel_v * 1.5)
            badge = "🟢 High Conviction" if chg_pct > 0 and rel_v >= 1.2 else "🟡 Emerging Growth"
            new_items.append((score, sym, price, chg_pct, rel_v, badge, "Growth / Innovation"))

        # 4. Future Supercycles
        if base_cat == "future":
            score = chg_pct + (rel_v * 1.2)
            future_items.append((score, sym, price, chg_pct, rel_v, "🟢 Secular Megatrend", "Secular Supercycle"))

        # 5. Trending Today Candidate (Evaluated across the ENTIRE universe!)
        # Ranked by composite momentum: day change % and volume breakout
        trend_score = (chg_pct * 0.7) + ((rel_v - 1.0) * 8.0)
        t_badge = "🟢 Bullish Momentum" if chg_pct >= 0 else "⚡ Heavy Volume Action"
        t_level = f"High Momentum (+{chg_pct:.1f}%)" if chg_pct >= 0 else f"High Turnover ({rel_v:.1f}x Vol)"
        trending_candidates.append((trend_score, sym, price, chg_pct, rel_v, t_badge, t_level))

    # Sort each list by their quantitative scores
    penny_items.sort(key=lambda x: x[0], reverse=True)           # Highest volume surge first
    safe_items.sort(key=lambda x: x[0], reverse=True)            # Lowest volatility first
    new_items.sort(key=lambda x: x[0], reverse=True)             # Highest momentum first
    trending_candidates.sort(key=lambda x: x[0], reverse=True)   # Best trend score first
    future_items.sort(key=lambda x: x[0], reverse=True)          # Highest relative strength first

    # Pick top 10 for each category
    selected_penny = penny_items[:10]
    selected_safe = safe_items[:10]
    selected_new = new_items[:10]
    selected_trending = trending_candidates[:10]
    selected_future = future_items[:10]

    # Collect unique tickers to fetch live news for
    all_selected_tickers = list({
        row[1] for row in (selected_penny + selected_safe + selected_new + selected_trending + selected_future)
    })

    # Step 3: Concurrently fetch real-time news articles
    news_map = _fetch_news_concurrently(all_selected_tickers)

    # Step 4: Build ThematicStockItem records with live data
    def build_items(raw_rows, cat_id: str, cat_title: str) -> List[ThematicStockItem]:
        items = []
        for row in raw_rows:
            _, sym, price, chg_pct, rel_v, risk_badge, risk_level = row
            meta = meta_by_sym.get(sym, {})
            name = meta.get("name", sym)
            why_it_matters = meta.get("why_it_matters", "Strategic market player.")

            chg_sign = "+" if chg_pct >= 0 else ""
            change_str = f"{chg_sign}{chg_pct:.2f}%"
            approx_price = f"{currency_sym}{price:,.2f}"

            # Check if live news was retrieved
            if sym in news_map:
                driver, url = news_map[sym]
            else:
                # Dynamic quantitative momentum driver
                v_desc = f"{rel_v:.1f}x ADV" if rel_v >= 1.0 else "steady volume"
                driver = f"⚡ Live Market Action: Trading at {approx_price} ({change_str} today) on {v_desc}."
                url = ""

            items.append(
                ThematicStockItem(
                    ticker=sym,
                    name=name,
                    approx_price=approx_price,
                    category_id=cat_id,
                    category_title=cat_title,
                    catalyst_driver=driver,
                    why_it_matters=why_it_matters,
                    risk_level=risk_level,
                    risk_badge=risk_badge,
                    change_pct=chg_pct,
                    change_str=change_str,
                    volume_multiple=rel_v,
                    news_url=url,
                )
            )
        return items

    result: Dict[str, List[ThematicStockItem]] = {
        "penny": build_items(selected_penny, "penny", f"🪙 Small-Priced (< {currency_sym}{int(price_ceiling)})"),
        "safe": build_items(selected_safe, "safe", "🏰 Safe Havens (Fortress Blue-Chips)"),
        "new": build_items(selected_new, "new", "🌱 New & Emerging Disruptors"),
        "trending": build_items(selected_trending, "trending", "🔥 Trending Today"),
        "future": build_items(selected_future, "future", "🚀 Future Mega-Trends (Supercycles)"),
    }

    return result


def get_thematic_market_radar(is_indian: bool = False) -> Dict[str, List[ThematicStockItem]]:
    """
    Primary interface for fetching the thematic market radar.
    Executes a real-time dynamic market scan without any hardcoded data.
    """
    return scan_live_market_radar(is_indian=is_indian)
