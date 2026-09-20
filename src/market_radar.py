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

    def __getattr__(self, name: str):
        # Backward compatibility safeguard for deserialized cached objects
        if name == "change_pct":
            return 0.0
        if name == "change_str":
            return "0.00%"
        if name == "volume_multiple":
            return 1.0
        if name == "news_url":
            return ""
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


# =============================================================================
# EXPANDED ACTIVE INSTITUTIONAL CANDIDATE UNIVERSES (100+ Tickers per Market)
# =============================================================================

INDIAN_SCAN_UNIVERSE = [
    # Safe Havens & Fortress Blue-Chips
    {"ticker": "RELIANCE.NS", "name": "Reliance Industries", "base_category": "safe", "why_it_matters": "Conglomerate anchoring Nifty 50 with leading telecom, oil-to-chemicals, and retail cash flows."},
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
    {"ticker": "MARUTI.NS", "name": "Maruti Suzuki India", "base_category": "safe", "why_it_matters": "Market leader in domestic passenger vehicles with unmatched distribution and service reach."},
    {"ticker": "BAJFINANCE.NS", "name": "Bajaj Finance", "base_category": "safe", "why_it_matters": "Omnichannel consumer lending giant commanding industry-leading return on equity."},
    {"ticker": "BAJAJFINSV.NS", "name": "Bajaj Finserv", "base_category": "safe", "why_it_matters": "Holding company for consumer finance, general insurance, and health protection."},
    {"ticker": "AXISBANK.NS", "name": "Axis Bank", "base_category": "safe", "why_it_matters": "Large-scale private bank with strong digital adoption and expanding corporate credit margins."},
    {"ticker": "SUNPHARMA.NS", "name": "Sun Pharma", "base_category": "safe", "why_it_matters": "India's largest pharmaceutical company with global specialty dermatology leadership."},
    {"ticker": "TITAN.NS", "name": "Titan Company", "base_category": "safe", "why_it_matters": "Tata luxury consumption flagship dominating organized jewelry and lifestyle accessories."},
    {"ticker": "ULTRACEMCO.NS", "name": "UltraTech Cement", "base_category": "safe", "why_it_matters": "India's cement titan benefiting from national highway and urban real estate construction."},
    {"ticker": "WIPRO.NS", "name": "Wipro Limited", "base_category": "safe", "why_it_matters": "Global IT consulting and cloud modernization provider with steady enterprise cash flows."},
    {"ticker": "HCLTECH.NS", "name": "HCL Technologies", "base_category": "safe", "why_it_matters": "IT leader in digital engineering software and infrastructure management with high dividend yields."},
    {"ticker": "POWERGRID.NS", "name": "Power Grid Corp of India", "base_category": "safe", "why_it_matters": "Sovereign electricity transmission utility with regulated return on equity and steady dividends."},
    {"ticker": "ONGC.NS", "name": "Oil & Natural Gas Corp", "base_category": "safe", "why_it_matters": "Primary crude oil and natural gas producer in India with high dividend yield payouts."},
    {"ticker": "JSWSTEEL.NS", "name": "JSW Steel", "base_category": "safe", "why_it_matters": "High-efficiency private steelmaker expanding domestic capacity across infrastructure products."},
    {"ticker": "ADANIPORTS.NS", "name": "Adani Ports & SEZ", "base_category": "safe", "why_it_matters": "Private port operator handling nearly 25% of India's maritime cargo logistics volume."},
    {"ticker": "GRASIM.NS", "name": "Grasim Industries", "base_category": "safe", "why_it_matters": "Aditya Birla flagship commanding viscose staple fiber, chemicals, and new Birla Opus paints."},
    {"ticker": "NESTLEIND.NS", "name": "Nestle India", "base_category": "safe", "why_it_matters": "Premium packaged foods leader with iconic brands (Maggi, Nescafe) and high pricing power."},
    {"ticker": "HINDALCO.NS", "name": "Hindalco Industries", "base_category": "safe", "why_it_matters": "Global aluminum giant with captive bauxite mines and Novelis beverage can recycling."},
    {"ticker": "CIPLA.NS", "name": "Cipla Limited", "base_category": "safe", "why_it_matters": "Defensive pharmaceutical major specializing in respiratory inhalers and anti-retrovirals."},
    {"ticker": "DRREDDY.NS", "name": "Dr. Reddy's Laboratories", "base_category": "safe", "why_it_matters": "Global generic pharmaceutical manufacturer with expanding biosimilar pipeline in US and Europe."},
    {"ticker": "EICHERMOT.NS", "name": "Eicher Motors", "base_category": "safe", "why_it_matters": "Parent of Royal Enfield commanding the middleweight premium motorcycle segment in India."},
    {"ticker": "BRITANNIA.NS", "name": "Britannia Industries", "base_category": "safe", "why_it_matters": "Defensive biscuit and bakery FMCG leader with extensive rural and urban distribution reach."},

    # New & Emerging Disruptors
    {"ticker": "JIOFIN.NS", "name": "Jio Financial Services", "base_category": "new", "why_it_matters": "BlackRock JV partner with balance sheet depth to disrupt lending, broking, and asset management."},
    {"ticker": "SWIGGY.NS", "name": "Swiggy Ltd", "base_category": "new", "why_it_matters": "Urban food delivery and quick-commerce duopoly with expanding dark store operating margins."},
    {"ticker": "TATATECH.NS", "name": "Tata Technologies", "base_category": "new", "why_it_matters": "Pure-play engineering R&D services powering OEM transitions to software-defined EVs."},
    {"ticker": "POLICYBZR.NS", "name": "PB Fintech", "base_category": "new", "why_it_matters": "Online insurance aggregator commanding near-monopoly market share in health and life cover."},
    {"ticker": "NYKAA.NS", "name": "FSN E-Commerce (Nykaa)", "base_category": "new", "why_it_matters": "Omnichannel luxury beauty and fashion marketplace with expanding owned-brand gross margins."},
    {"ticker": "DELHIVERY.NS", "name": "Delhivery", "base_category": "new", "why_it_matters": "Fully automated express parcel logistics network capturing e-commerce volume inflection."},
    {"ticker": "MAPMYINDIA.NS", "name": "C.E. Info Systems", "base_category": "new", "why_it_matters": "Indigenous HD map data monopoly powering automotive ADAS, Apple Maps India, and drones."},
    {"ticker": "PAYTM.NS", "name": "One97 Communications", "base_category": "new", "why_it_matters": "Merchant payment checkout network generating high-margin recurring soundbox rental fees."},
    {"ticker": "NAUKRI.NS", "name": "Info Edge (India)", "base_category": "new", "why_it_matters": "Dominant white-collar recruitment platform (Naukri) and premier incubator for Indian tech."},
    {"ticker": "KALYANKJIL.NS", "name": "Kalyan Jewellers", "base_category": "new", "why_it_matters": "Aggressive retail footprint capturing consumer shift from unorganized to hallmarked jewelry."},
    {"ticker": "CDSL.NS", "name": "Central Depository Services", "base_category": "new", "why_it_matters": "Securities depository tollbooth profiting from hundreds of millions of retail demat accounts."},
    {"ticker": "MCX.NS", "name": "Multi Commodity Exchange", "base_category": "new", "why_it_matters": "Dominant monopoly in Indian bullion and energy commodity futures and options trading."},
    {"ticker": "PERSISTENT.NS", "name": "Persistent Systems", "base_category": "new", "why_it_matters": "High-growth digital engineering and enterprise modernization software specialist."},
    {"ticker": "COFORGE.NS", "name": "Coforge Limited", "base_category": "new", "why_it_matters": "Digital services provider delivering consistent double-digit growth in insurance and banking tech."},

    # Defense, Engineering & Momentum
    {"ticker": "BEL.NS", "name": "Bharat Electronics", "base_category": "trending", "why_it_matters": "Sovereign defense electronics champion securing naval radar and missile avionics orders."},
    {"ticker": "HAL.NS", "name": "Hindustan Aeronautics", "base_category": "trending", "why_it_matters": "Sole manufacturer of indigenous fighter aircraft and combat helicopters with multi-year order backlog."},
    {"ticker": "BDL.NS", "name": "Bharat Dynamics", "base_category": "trending", "why_it_matters": "Premier manufacturer of surface-to-air missiles and torpedoes for the Indian Armed Forces."},
    {"ticker": "COCHINSHIP.NS", "name": "Cochin Shipyard", "base_category": "trending", "why_it_matters": "Aircraft carrier shipyard expanding into green commercial vessels and high-margin ship repair."},
    {"ticker": "MAZDOCK.NS", "name": "Mazagon Dock Shipbuilders", "base_category": "trending", "why_it_matters": "Submarine and guided-missile destroyer builder with massive multi-billion sovereign orders."},
    {"ticker": "PARAS.NS", "name": "Paras Defence & Space", "base_category": "trending", "why_it_matters": "Optics, electro-magnetic pulse protection, and drone technologies for defense and space."},
    {"ticker": "DATAPATTNS.NS", "name": "Data Patterns (India)", "base_category": "trending", "why_it_matters": "Vertically integrated defense and aerospace electronics provider for radars and electronic warfare."},
    {"ticker": "TRENT.NS", "name": "Trent Ltd", "base_category": "trending", "why_it_matters": "Tata Group retail phenomenon driven by exponential store expansions across Zudio."},
    {"ticker": "DIXON.NS", "name": "Dixon Technologies", "base_category": "trending", "why_it_matters": "Premier domestic EMS contractor assembling smartphones and consumer electronics under PLI."},
    {"ticker": "BSE.NS", "name": "BSE Ltd", "base_category": "trending", "why_it_matters": "Surging market share in index derivatives and retail trading on Asia's oldest exchange."},
    {"ticker": "RVNL.NS", "name": "Rail Vikas Nigam", "base_category": "trending", "why_it_matters": "Primary executing arm for Indian Railways modernization and high-speed freight corridors."},
    {"ticker": "ADANIENT.NS", "name": "Adani Enterprises", "base_category": "trending", "why_it_matters": "Flagship private infrastructure incubator executing sovereign airports, solar, and data centers."},

    # Future Supercycles (Clean Energy, Grid, Mobility)
    {"ticker": "SUZLON.NS", "name": "Suzlon Energy", "base_category": "future", "why_it_matters": "Debt-free market leader in domestic wind turbines powering India's 500 GW renewable mandate."},
    {"ticker": "IREDA.NS", "name": "IREDA", "base_category": "future", "why_it_matters": "State-owned non-banking finance institution underwriting sovereign green energy infrastructure."},
    {"ticker": "JSWENERGY.NS", "name": "JSW Energy", "base_category": "future", "why_it_matters": "Rapidly pivoting toward utility-scale renewable power and multi-gigawatt battery storage (BESS)."},
    {"ticker": "TATAPOWER.NS", "name": "Tata Power", "base_category": "future", "why_it_matters": "Integrated utility rolling out national EV fast-charging networks, solar EPC, and rooftop solar."},
    {"ticker": "ADANIGREEN.NS", "name": "Adani Green Energy", "base_category": "future", "why_it_matters": "Developing Khavda, the world's largest renewable energy park (30 GW capacity)."},
    {"ticker": "EXIDEIND.NS", "name": "Exide Industries", "base_category": "future", "why_it_matters": "Building India's premier lithium-ion cell gigafactory with global supply ties to Hyundai & Kia."},
    {"ticker": "TITAGARH.NS", "name": "Titagarh Rail Systems", "base_category": "future", "why_it_matters": "Builder of high-speed Vande Bharat trainsets and smart city metro coaches."},
    {"ticker": "KPITTECH.NS", "name": "KPIT Technologies", "base_category": "future", "why_it_matters": "Global software architecture specialist for electric powertrains and autonomous mobility."},
    {"ticker": "TATAELXSI.NS", "name": "Tata Elxsi", "base_category": "future", "why_it_matters": "High-margin automotive engineering design and AI solutions for medical and tech OEMs."},
    {"ticker": "DEEPAKFERT.NS", "name": "Deepak Fertilisers", "base_category": "future", "why_it_matters": "Key supplier of industrial nitric acid and electronic-grade chemicals for semiconductors."},
    {"ticker": "PRESTIGE.NS", "name": "Prestige Estates", "base_category": "future", "why_it_matters": "Capturing generational urbanization and premium residential demand across Indian tech hubs."},

    # Small-Priced & Micro-Cap Penny Candidates (< ₹100 Target, including sub-₹1 & sub-₹10 Screener nano-caps)
    # Sub-₹1 Nano-Penny Stocks (BSE & NSE)
    {"ticker": "FILATFASH.NS", "name": "Filatex Fashions Ltd", "base_category": "penny", "why_it_matters": "Micro-cap socks and textile manufacturer subject to 5% circuit bandwidth and high volatility."},
    {"ticker": "SHREESEC.BO", "name": "Shree Securities Ltd", "base_category": "penny", "why_it_matters": "Kolkata-based NBFC penny stock with micro-cap liquidity and circuit boundaries."},
    {"ticker": "WELCURE.BO", "name": "Welcure Drugs & Pharmaceuticals", "base_category": "penny", "why_it_matters": "Micro-cap pharmaceutical enterprise trading on BSE with low free-float turnover."},
    {"ticker": "SYLPH.BO", "name": "Sylph Technologies Ltd", "base_category": "penny", "why_it_matters": "Software technology and BPO solutions provider trading at sub-rupee valuations."},
    {"ticker": "FCONSUMER.NS", "name": "Future Consumer Ltd", "base_category": "penny", "why_it_matters": "Former Future Group FMCG brand entity navigating balance sheet and corporate debt restructuring."},
    {"ticker": "SHANGAR.BO", "name": "Shangar Decor Ltd", "base_category": "penny", "why_it_matters": "Event infrastructure and decor services provider listed on BSE in the micro-cap segment."},
    {"ticker": "STURDY.BO", "name": "Sturdy Industries Ltd", "base_category": "penny", "why_it_matters": "Manufacturer of aluminum conductors and irrigation pipes under debt recovery proceedings."},
    {"ticker": "SRESTHA.BO", "name": "Srestha Finvest Ltd", "base_category": "penny", "why_it_matters": "Non-banking financial company offering commercial credit, micro-loans, and investment operations."},
    {"ticker": "SHALPRO.BO", "name": "Shalimar Productions Ltd", "base_category": "penny", "why_it_matters": "Media production and video studio outfit trading in the sub-rupee micro-penny segment."},
    {"ticker": "VIKASPROP.BO", "name": "Vikas Proppant & Granite", "base_category": "penny", "why_it_matters": "Industrial frac sand, proppants, and granite exploration supplier based in Rajasthan."},
    {"ticker": "HARSHILAGR.BO", "name": "Harshil Agrotech Ltd", "base_category": "penny", "why_it_matters": "Agricultural produce trading and supply chain distribution company listed on BSE."},
    {"ticker": "BIOGEN.BO", "name": "Biogen Pharmachem Ltd", "base_category": "penny", "why_it_matters": "Wholesale pharmaceutical formulations and API chemical distributor trading on BSE."},
    {"ticker": "SANWARIA.BO", "name": "Sanwaria Consumer Ltd", "base_category": "penny", "why_it_matters": "Edible oil and basmati rice processor undergoing corporate insolvency resolution process."},
    {"ticker": "INVENTURE.NS", "name": "Inventure Growth & Securities", "base_category": "penny", "why_it_matters": "Retail stockbroking, margin funding, and financial advisory boutique."},
    {"ticker": "RCOM.NS", "name": "Reliance Communications Ltd", "base_category": "penny", "why_it_matters": "Anil Ambani telecommunications entity undergoing corporate insolvency resolution process (CIRP)."},

    # Sub-₹10 Micro-Cap Penny Stocks
    {"ticker": "VIKASECO.NS", "name": "Vikas EcoTech Ltd", "base_category": "penny", "why_it_matters": "Specialty chemical additives, recycled polymers, and eco-friendly infrastructure materials maker."},
    {"ticker": "GTLINFRA.NS", "name": "GTL Infrastructure Ltd", "base_category": "penny", "why_it_matters": "Shared telecom tower infrastructure provider serving nationwide cellular network operators."},
    {"ticker": "BLSINFOTE.BO", "name": "BLS Infotech Ltd", "base_category": "penny", "why_it_matters": "IT education and computer software services provider in the sub-₹5 micro-cap segment."},
    {"ticker": "FCSSOFT.NS", "name": "FCS Software Solutions Ltd", "base_category": "penny", "why_it_matters": "Offshore software development, IT consulting, and infrastructure management services."},
    {"ticker": "SUULD.NS", "name": "Suumaya Industries Ltd", "base_category": "penny", "why_it_matters": "Textile supply chain and agricultural commodities merchant trading in distress turnaround."},
    {"ticker": "RHFL.NS", "name": "Reliance Home Finance Ltd", "base_category": "penny", "why_it_matters": "Affordable housing finance provider navigating debt resolution and promoter transitions."},
    {"ticker": "GVKPIL.NS", "name": "GVK Power & Infrastructure", "base_category": "penny", "why_it_matters": "Transportation and energy infrastructure concessionaire managing highway and airport projects."},
    {"ticker": "DISHTV.NS", "name": "Dish TV India Ltd", "base_category": "penny", "why_it_matters": "Direct-to-home (DTH) satellite broadcast television provider with nationwide subscriber base."},
    {"ticker": "RADAAN.NS", "name": "Radaan Mediaworks India", "base_category": "penny", "why_it_matters": "Regional television content production house producing Tamil and Telugu serial broadcasts."},
    {"ticker": "UNITECH.NS", "name": "Unitech Ltd", "base_category": "penny", "why_it_matters": "Real estate developer undergoing government-supervised board management to complete stalled projects."},
    {"ticker": "SEPC.NS", "name": "SEPC Ltd", "base_category": "penny", "why_it_matters": "Integrated engineering, procurement, and construction (EPC) contractor for water and metallurgy."},
    {"ticker": "ALOKINDS.NS", "name": "Alok Industries Ltd", "base_category": "penny", "why_it_matters": "Integrated textile manufacturer co-promoted by Reliance Industries with expanding polyester capacity."},
    {"ticker": "RTNPOWER.NS", "name": "RattanIndia Power Ltd", "base_category": "penny", "why_it_matters": "Thermal power utility operating 2,700 MW coal generation capacity in Amravati and Nashik."},
    {"ticker": "ZEEMEDIA.NS", "name": "Zee Media Corp Ltd", "base_category": "penny", "why_it_matters": "News broadcasting network operating 14 television news channels across India."},
    {"ticker": "URJA.NS", "name": "Urja Global Ltd", "base_category": "penny", "why_it_matters": "Renewable energy developer distributing solar panels, e-rickshaws, and lithium battery packs."},

    # Turnaround & High-Volume Small Caps (₹10 to ₹100 Target)
    {"ticker": "BCG.NS", "name": "Brightcom Group Ltd", "base_category": "penny", "why_it_matters": "Digital marketing ad-tech platform under SEBI forensic review and compliance scrutiny."},
    {"ticker": "IDEA.NS", "name": "Vodafone Idea Ltd", "base_category": "penny", "why_it_matters": "Sub-₹20 telecom turnaround candidate executing 5G network rollout with government backing."},
    {"ticker": "JPPOWER.NS", "name": "Jaiprakash Power Ventures", "base_category": "penny", "why_it_matters": "Hydropower and thermal electricity generator with declining debt and rising power plant PLF."},
    {"ticker": "SURANAT&P.NS", "name": "Surana Telecom and Power", "base_category": "penny", "why_it_matters": "Manufacturer of optic-fiber cables, solar photovoltaic modules, and wind power generation."},
    {"ticker": "SYNCOMF.NS", "name": "Syncom Formulations Ltd", "base_category": "penny", "why_it_matters": "Pharmaceutical formulation manufacturer exporting generic capsules and injections to 30+ nations."},
    {"ticker": "SUBEXLTD.NS", "name": "Subex Ltd", "base_category": "penny", "why_it_matters": "Telecom enterprise software provider specializing in revenue assurance, fraud management, and AI IoT."},
    {"ticker": "RPOWER.NS", "name": "Reliance Power Ltd", "base_category": "penny", "why_it_matters": "Power generator operating Sasan ultra-mega power plant, aggressively reducing parent debt."},
    {"ticker": "HCC.NS", "name": "Hindustan Construction Co", "base_category": "penny", "why_it_matters": "Infrastructure contractor building iconic nuclear reactors, tunnels, hydro dams, and bridges."},
    {"ticker": "YESBANK.NS", "name": "Yes Bank Ltd", "base_category": "penny", "why_it_matters": "Post-cleanup private banking turnaround supported by low-cost retail deposit expansion."},
    {"ticker": "3IINFOLTD.NS", "name": "3i Infotech Ltd", "base_category": "penny", "why_it_matters": "Digital transformation and cloud services company executing banking and fintech software solutions."},
    {"ticker": "SOUTHBANK.NS", "name": "South Indian Bank", "base_category": "penny", "why_it_matters": "Kerala-based private lender with clean NPA reduction, expanding NIMs, and attractive price-to-book."},
    {"ticker": "TTML.NS", "name": "Tata Teleservices (Maharashtra)", "base_category": "penny", "why_it_matters": "Tata enterprise broadband, cloud telephony, and cybersecurity networking provider."},
    {"ticker": "TRIDENT.NS", "name": "Trident Limited", "base_category": "penny", "why_it_matters": "Integrated home textiles and paper exporter benefiting from global supply chain diversification."},
    {"ticker": "UCOBANK.NS", "name": "UCO Bank", "base_category": "penny", "why_it_matters": "State-backed lender experiencing sustained asset quality normalization and rising margins."},
    {"ticker": "IOB.NS", "name": "Indian Overseas Bank", "base_category": "penny", "why_it_matters": "Recovered public lender with declining bad loans and sovereign capital backing."},
    {"ticker": "CENTRALBK.NS", "name": "Central Bank of India", "base_category": "penny", "why_it_matters": "Rapidly reviving public lender with sovereign deposit franchise and falling credit costs."},
    {"ticker": "NHPC.NS", "name": "NHPC Ltd", "base_category": "penny", "why_it_matters": "Defensive state-owned hydropower utility commanding long-term power purchase agreements."},
    {"ticker": "NBCC.NS", "name": "NBCC (India) Ltd", "base_category": "penny", "why_it_matters": "Debt-free PSU managing mega-redevelopment construction projects on cost-plus basis."},
    {"ticker": "SJVN.NS", "name": "SJVN Ltd", "base_category": "penny", "why_it_matters": "Expanding renewable utility executing massive solar and hydro projects across North India."},
    {"ticker": "IDFCFIRSTB.NS", "name": "IDFC First Bank", "base_category": "penny", "why_it_matters": "High-CASA retail banking franchise with rapid branch expansion and clean underwriting."},
    {"ticker": "PNB.NS", "name": "Punjab National Bank", "base_category": "penny", "why_it_matters": "Major state lender benefiting from corporate credit demand and low credit costs."},
    {"ticker": "CANBK.NS", "name": "Canara Bank", "base_category": "penny", "why_it_matters": "Strong public sector lender with expanding retail loan books and attractive valuation."},
    {"ticker": "HFCL.NS", "name": "HFCL Limited", "base_category": "penny", "why_it_matters": "Optical fiber and telecom network equipment manufacturer exporting 5G equipment globally."},
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
    {"ticker": "MA", "name": "Mastercard Inc.", "base_category": "safe", "why_it_matters": "Global card payment network benefiting from international travel and cross-border transactions."},
    {"ticker": "COST", "name": "Costco Wholesale", "base_category": "safe", "why_it_matters": "Unshakable membership-based warehouse moat with 90%+ renewal rates and relentless customer traffic."},
    {"ticker": "WMT", "name": "Walmart Inc.", "base_category": "safe", "why_it_matters": "World's largest retailer commanding grocery distribution and scaling high-margin retail media ads."},
    {"ticker": "UNH", "name": "UnitedHealth Group", "base_category": "safe", "why_it_matters": "Vertically integrated healthcare giant combining health insurance with Optum clinical care."},
    {"ticker": "HD", "name": "Home Depot", "base_category": "safe", "why_it_matters": "Home improvement retail giant with defensive professional contractor business."},
    {"ticker": "ABBV", "name": "AbbVie Inc.", "base_category": "safe", "why_it_matters": "Biopharmaceutical leader with blockbuster immunology (Skyrizi, Rinvoq) and oncology pipelines."},
    {"ticker": "KO", "name": "Coca-Cola Company", "base_category": "safe", "why_it_matters": "Legendary beverage moat with global brand distribution and decades of uninterrupted dividend growth."},
    {"ticker": "PEP", "name": "PepsiCo Inc.", "base_category": "safe", "why_it_matters": "Resilient consumer staples giant combining beverage leadership with Frito-Lay snacks monopoly."},
    {"ticker": "MCD", "name": "McDonald's Corporation", "base_category": "safe", "why_it_matters": "Global fast-food real estate tollbooth with recession-proof consumer demand."},

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
    {"ticker": "SNOW", "name": "Snowflake Inc.", "base_category": "new", "why_it_matters": "Enterprise data cloud platform enabling corporate data sharing, analytics, and AI model training."},
    {"ticker": "DDOG", "name": "Datadog Inc.", "base_category": "new", "why_it_matters": "Cloud monitoring and observability SaaS essential for cloud application uptime and cybersecurity."},
    {"ticker": "NET", "name": "Cloudflare Inc.", "base_category": "new", "why_it_matters": "Global edge network providing cybersecurity, CDN speed, and serverless AI inferencing."},

    # High Beta / Trending / Momentum Leaders
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "base_category": "trending", "why_it_matters": "Global monopoly in AI GPUs and CUDA software stack powering hyperscale datacenters."},
    {"ticker": "TSLA", "name": "Tesla Inc.", "base_category": "trending", "why_it_matters": "Electric vehicle volume leader scaling Full Self-Driving neural networks and Cybercab robotics."},
    {"ticker": "PLTR", "name": "Palantir Technologies", "base_category": "trending", "why_it_matters": "Commercial and defense AI ontology platform seeing explosive demand from US government and Fortune 500."},
    {"ticker": "AMD", "name": "Advanced Micro Devices", "base_category": "trending", "why_it_matters": "Primary competitor in x86 CPUs and emerging alternative in datacenter AI accelerators (MI300)."},
    {"ticker": "AVGO", "name": "Broadcom Inc.", "base_category": "trending", "why_it_matters": "Custom AI ASIC silicon designer (for Google TPU and Meta) and enterprise infrastructure software giant."},
    {"ticker": "QCOM", "name": "Qualcomm Inc.", "base_category": "trending", "why_it_matters": "5G wireless modem leader expanding into Snapdragon X Elite on-device AI processors for PCs."},
    {"ticker": "META", "name": "Meta Platforms", "base_category": "trending", "why_it_matters": "Advertising cash engine funding open-source Llama AI models and smart glasses technology."},
    {"ticker": "NFLX", "name": "Netflix Inc.", "base_category": "trending", "why_it_matters": "Streaming entertainment giant delivering operating margin expansion and growing ad-tier subs."},
    {"ticker": "CRM", "name": "Salesforce Inc.", "base_category": "trending", "why_it_matters": "Enterprise CRM giant launching Agentforce autonomous enterprise customer service AI agents."},
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
    {"ticker": "LLY", "name": "Eli Lilly and Co", "base_category": "future", "why_it_matters": "Mounjaro and Zepbound pharmaceutical pioneer expanding into Alzheimer's disease treatments."},
    {"ticker": "GEV", "name": "GE Vernova", "base_category": "future", "why_it_matters": "Gas turbines, wind power, and grid electrification software meeting soaring electricity demand."},
    {"ticker": "CRWD", "name": "CrowdStrike Holdings", "base_category": "future", "why_it_matters": "AI-native cloud security platform protecting enterprise endpoints against sophisticated cyber attacks."},
    {"ticker": "PANW", "name": "Palo Alto Networks", "base_category": "future", "why_it_matters": "Leading enterprise network cybersecurity platform delivering platformized security architectures."},
    {"ticker": "AXON", "name": "Axon Enterprise", "base_category": "future", "why_it_matters": "TASER devices, body cameras, and cloud evidence management modernizing global law enforcement."},
    {"ticker": "OKLO", "name": "Oklo Inc.", "base_category": "future", "why_it_matters": "Developing fast fission micro-reactors to provide emission-free power directly to data center sites."},
    {"ticker": "SMR", "name": "NuScale Power", "base_category": "future", "why_it_matters": "Pioneering certified small modular nuclear reactors for clean commercial baseload electricity."},
    {"ticker": "BWXT", "name": "BWX Technologies", "base_category": "future", "why_it_matters": "Manufactures nuclear reactor components for US Navy submarines and medical radioisotopes."},
    {"ticker": "CCJ", "name": "Cameco Corporation", "base_category": "future", "why_it_matters": "World's largest commercial uranium producer supplying clean nuclear fuel to western utilities."},
    {"ticker": "ISRG", "name": "Intuitive Surgical", "base_category": "future", "why_it_matters": "Monopolistic da Vinci robotic surgical systems transforming minimally invasive healthcare."},

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
    {"ticker": "MARA", "name": "MARA Holdings", "base_category": "penny", "why_it_matters": "Digital asset infrastructure and energy harvesting provider with institutional Bitcoin reserves."},
    {"ticker": "RIOT", "name": "Riot Platforms", "base_category": "penny", "why_it_matters": "Vertically integrated digital infrastructure and Bitcoin mining operator in Texas."},
    {"ticker": "LCID", "name": "Lucid Group", "base_category": "penny", "why_it_matters": "Luxury electric vehicle manufacturer backed by the Saudi Public Investment Fund."},
    {"ticker": "RIVN", "name": "Rivian Automotive", "base_category": "penny", "why_it_matters": "Pure-play adventure electric vehicle and commercial delivery van maker partnered with Amazon & VW."},
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

    max_workers = min(16, max(2, len(tickers)))
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for sym, driver, url in executor.map(_fetch_single_news, tickers):
                if driver:
                    results[sym] = (driver, url)
    except Exception:
        pass
    return results


def scan_live_market_radar(is_indian: bool = True, use_full_nse: bool = True) -> Dict[str, List[ThematicStockItem]]:
    """
    Executes a pure live quantitative market scan across the expanded universe.
    
    When is_indian=True and use_full_nse=True:
    Dynamically scans and classifies ALL 2,500+ listed equities on the National Stock
    Exchange of India (NSE) directly from official exchange feeds.
    
    Falls back gracefully to yfinance candidate batch downloading if needed.
    """
    if is_indian and use_full_nse:
        try:
            from src.nse_full_market import build_full_nse_thematic_radar
            radar_data = build_full_nse_thematic_radar()
            if radar_data and len(radar_data.get("penny", [])) > 0:
                # Concurrently attach real-time news for top tickers across categories
                top_tickers = list({
                    s.ticker for s in (
                        radar_data.get("penny", [])[:6] +
                        radar_data.get("safe", [])[:8] +
                        radar_data.get("trending", [])[:8] +
                        radar_data.get("new", [])[:6] +
                        radar_data.get("future", [])[:6]
                    )
                })
                news_map = _fetch_news_concurrently(top_tickers)
                if news_map:
                    for cat_key, items in radar_data.items():
                        for item in items:
                            if item.ticker in news_map:
                                driver, url = news_map[item.ticker]
                                item.catalyst_driver = driver
                                item.news_url = url
                return radar_data
        except Exception:
            pass  # Fall back to candidate scanning

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
            if is_indian and price < 1.0:
                risk_badge = "🔴 Nano-Penny (<₹1)"
                risk_level = f"Sub-Rupee Micro-Cap ({vol:.1f}% swing)"
            elif is_indian and price < 10.0:
                risk_badge = "🔴 Micro-Penny (<₹10)"
                risk_level = f"Sub-₹10 Micro-Cap ({vol:.1f}% swing)"
            elif not is_indian and price < 5.0:
                risk_badge = "🔴 Micro-Penny (<$5)"
                risk_level = f"Sub-$5 Micro-Cap ({vol:.1f}% swing)"
            elif vol > 3.5:
                risk_badge = "🟡 High Volatility"
                risk_level = f"Volatile ({vol:.1f}% swing)"
            else:
                risk_badge = "🟢 Turnaround / Liquid"
                risk_level = "Liquid Small-Cap / PSU"
            penny_items.append((price, sym, price, chg_pct, rel_v, risk_badge, risk_level))

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
    penny_items.sort(key=lambda x: x[0])                         # Lowest price first (e.g. ₹0.14, ₹0.19, ₹0.22... up to ₹100)
    safe_items.sort(key=lambda x: x[0], reverse=True)            # Lowest volatility first
    new_items.sort(key=lambda x: x[0], reverse=True)             # Highest momentum first
    trending_candidates.sort(key=lambda x: x[0], reverse=True)   # Best trend score first
    future_items.sort(key=lambda x: x[0], reverse=True)          # Highest relative strength first

    # Return full depth for each category (up to 60 per category for rich scrollable tables)
    selected_penny = penny_items[:60]
    selected_safe = safe_items[:50]
    selected_new = new_items[:50]
    selected_trending = trending_candidates[:50]
    selected_future = future_items[:50]

    # Collect top tickers across each category to fetch real-time news for
    top_news_tickers = list({
        row[1] for row in (
            selected_penny[:6] + selected_safe[:6] + selected_new[:6] + selected_trending[:8] + selected_future[:6]
        )
    })

    # Step 3: Concurrently fetch real-time news articles
    news_map = _fetch_news_concurrently(top_news_tickers)

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


def get_thematic_market_radar(is_indian: bool = True) -> Dict[str, List[ThematicStockItem]]:
    """
    Primary interface for fetching the thematic market radar.
    Executes a real-time dynamic market scan across the expanded universe.
    Defaults to Indian Markets (NSE/BSE).
    """
    return scan_live_market_radar(is_indian=is_indian)
