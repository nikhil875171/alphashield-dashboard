"""
AlphaShield Centralized Multi-Sector & Market-Cap Universe Registry.

Comprehensive stock universe covering both US (NYSE / NASDAQ) and Indian (NSE / BSE) equities,
strictly classified by Market Capitalization Tier (Large-Cap, Mid-Cap, Small-Cap) and
the 17 Standard Institutional Industry Sectors.
"""

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple


@dataclass
class StockEntry:
    """Stock entry record with sector, market cap tier, and strategic thematic anchors."""
    ticker: str
    name: str
    market: Literal["US", "INDIA"]
    market_cap_tier: Literal["Large-Cap", "Mid-Cap", "Small-Cap"]
    sector: str
    sub_sector: str
    plain_english_role: str
    thematic_anchor: str


# =============================================================================
# EXHAUSTIVE MULTI-SECTOR UNIVERSE (US & INDIA)
# =============================================================================

STOCK_UNIVERSE: List[StockEntry] = [
    # -------------------------------------------------------------------------
    # 1. Telecommunications & Networks
    # -------------------------------------------------------------------------
    StockEntry("BHARTIARTL.NS", "Bharti Airtel", "INDIA", "Large-Cap", "Telecommunications & Networks", "Telco Carrier & Enterprise 5G", "Leading Indian telecom duopoly scaling high-ARPU mobile data, enterprise cloud, and rural broadband.", "5G/6G Networks"),
    StockEntry("INDUSTOWER.NS", "Indus Towers", "INDIA", "Large-Cap", "Telecommunications & Networks", "Passive Telecom Towers", "India's largest telecom tower infrastructure provider with over 200,000 nationwide tenancies.", "5G/6G Networks"),
    StockEntry("TATACOMM.NS", "Tata Communications", "INDIA", "Mid-Cap", "Telecommunications & Networks", "Subsea Cables & Global Cloud WAN", "Monopoly in international subsea fiber cables, cloud networking, and enterprise cybersecurity.", "5G/6G Networks"),
    StockEntry("TEJASNET.NS", "Tejas Networks", "INDIA", "Small-Cap", "Telecommunications & Networks", "Optical Transmission & 4G/5G RAN", "Tata-backed domestic optical equipment designer manufacturing indigenous 4G/5G mobile base stations.", "5G/6G Networks"),
    StockEntry("HFCL.NS", "HFCL Limited", "INDIA", "Small-Cap", "Telecommunications & Networks", "Optical Fiber & 5G Routers", "Leading optical fiber cable producer and 5G networking hardware manufacturer exporting globally.", "5G/6G Networks"),
    StockEntry("STLTECH.NS", "Sterlite Technologies", "INDIA", "Small-Cap", "Telecommunications & Networks", "Fiber Preforms & Optical Interconnect", "Vertically integrated optical glass preform manufacturer supplying global telecom network rollouts.", "5G/6G Networks"),
    StockEntry("IDEA.NS", "Vodafone Idea", "INDIA", "Small-Cap", "Telecommunications & Networks", "Wireless Carrier Turnaround", "Sub-₹20 mobile carrier executing 5G network rollout with government equity backing.", "5G/6G Networks"),
    StockEntry("VZ", "Verizon Communications", "US", "Large-Cap", "Telecommunications & Networks", "Nationwide Wireless & Fixed 5G", "Premier US wireless network operator delivering recurring monthly consumer broadband cash flow.", "5G/6G Networks"),
    StockEntry("T", "AT&T Inc.", "US", "Large-Cap", "Telecommunications & Networks", "Fiber-to-the-Home & 5G Carrier", "Leading pure-play telecom operator rapidly growing fiber internet subscriptions and 5G mobility.", "5G/6G Networks"),
    StockEntry("AMT", "American Tower", "US", "Large-Cap", "Telecommunications & Networks", "Cellular Tower REIT", "Global communications real estate tollbooth leasing tower capacity to wireless operators worldwide.", "5G/6G Networks"),
    StockEntry("CIEN", "Ciena Corporation", "US", "Mid-Cap", "Telecommunications & Networks", "Coherent Optical Backhaul Routing", "High-capacity optical routing and switching systems connecting hyperscale AI data center campuses.", "5G/6G Networks"),

    # -------------------------------------------------------------------------
    # 2. Textiles, Technical Fibers & Apparel
    # -------------------------------------------------------------------------
    StockEntry("PAGEIND.NS", "Page Industries (Jockey)", "INDIA", "Large-Cap", "Textiles, Technical Fibers & Apparel", "Premium Innerwear & Athleisure", "Exclusive licensee of Jockey in India commanding dominant pricing power in organized apparel.", "Consumer & Technical Textiles"),
    StockEntry("KPRMILL.NS", "KPR Mill", "INDIA", "Mid-Cap", "Textiles, Technical Fibers & Apparel", "Vertically Integrated Garments & Yarn", "One of India's largest integrated apparel manufacturers with 100% green captive wind energy.", "Consumer & Technical Textiles"),
    StockEntry("GOKEX.NS", "Gokaldas Exports", "INDIA", "Small-Cap", "Textiles, Technical Fibers & Apparel", "Outerwear & Performance Apparel", "Premier garment exporter to top global fashion brands (Nike, Gap, Adidas) expanding in Latin America.", "Consumer & Technical Textiles"),
    StockEntry("ARVIND.NS", "Arvind Ltd", "INDIA", "Small-Cap", "Textiles, Technical Fibers & Apparel", "Technical Textiles & Denim", "Pioneer in technical protective fabrics, industrial filtration media, and premium denim textiles.", "Consumer & Technical Textiles"),
    StockEntry("VTL.NS", "Vardhman Textiles", "INDIA", "Small-Cap", "Textiles, Technical Fibers & Apparel", "Specialty Spun Yarns & Fabrics", "Major cotton and blended yarn exporter commanding low production costs and modern spindle capacity.", "Consumer & Technical Textiles"),
    StockEntry("TRIDENT.NS", "Trident Limited", "INDIA", "Small-Cap", "Textiles, Technical Fibers & Apparel", "Home Textiles & Eco-Friendly Paper", "Integrated terry towel and bed linen manufacturer utilizing wheat-straw agro-waste paper pulp.", "Consumer & Technical Textiles"),
    StockEntry("FILATFASH.NS", "Filatex Fashions", "INDIA", "Small-Cap", "Textiles, Technical Fibers & Apparel", "Socks & Micro-Cap Hosiery", "Sub-rupee micro-cap manufacturing specialized cotton socks and textile fashion accessories.", "Consumer & Technical Textiles"),
    StockEntry("NKE", "Nike Inc.", "US", "Large-Cap", "Textiles, Technical Fibers & Apparel", "Athletic Footwear & Sportswear", "Global leader in athletic apparel and footwear driving high-margin direct-to-consumer digital channels.", "Consumer & Technical Textiles"),
    StockEntry("LULU", "Lululemon Athletica", "US", "Large-Cap", "Textiles, Technical Fibers & Apparel", "Technical Yoga & Athleisure", "Pioneer in proprietary technical fabrics (Luon, Nulu) commanding premium consumer loyalty and margins.", "Consumer & Technical Textiles"),
    StockEntry("RL", "Ralph Lauren Corp", "US", "Mid-Cap", "Textiles, Technical Fibers & Apparel", "Luxury Lifestyle & Formal Apparel", "Global lifestyle brand delivering gross margin expansion through full-price retail selling.", "Consumer & Technical Textiles"),

    # -------------------------------------------------------------------------
    # 3. Automobile & Ancillaries
    # -------------------------------------------------------------------------
    StockEntry("MARUTI.NS", "Maruti Suzuki", "INDIA", "Large-Cap", "Automobile & Ancillaries", "Passenger Vehicle OEM", "Dominates 40%+ of India's passenger vehicle market with unmatched rural dealership reach.", "Mobility & EV Scale-Up"),
    StockEntry("TATAMOTORS.NS", "Tata Motors", "INDIA", "Large-Cap", "Automobile & Ancillaries", "Electric Vehicles & Commercial Trucks", "Pioneer in Indian electric passenger vehicles with 70%+ EV market share and luxury JLR turnaround.", "Mobility & EV Scale-Up"),
    StockEntry("MOTHERSON.NS", "Samvardhana Motherson", "INDIA", "Mid-Cap", "Automobile & Ancillaries", "Wiring Harnesses & Vision Systems", "Global Tier-1 auto supplier providing 3x-5x higher content per vehicle in electric architectures.", "Mobility & EV Scale-Up"),
    StockEntry("SONACOMS.NS", "Sona BLW Precision", "INDIA", "Mid-Cap", "Automobile & Ancillaries", "EV Differential Gears & e-Axles", "Specialized precision forging maker capturing high-margin global EV drivetrain contracts.", "Mobility & EV Scale-Up"),
    StockEntry("SUBROS.NS", "Subros Ltd", "INDIA", "Small-Cap", "Automobile & Ancillaries", "Thermal Loops & Cabin Cooling", "Market leader in automotive air conditioning systems and high-efficiency EV battery chillers.", "Mobility & EV Scale-Up"),
    StockEntry("EXIDEIND.NS", "Exide Industries", "INDIA", "Small-Cap", "Automobile & Ancillaries", "Lithium-Ion Gigafactory & Lead Batteries", "Building India's largest lithium-ion battery cell gigafactory with global technology ties to SVOLT.", "Mobility & EV Scale-Up"),
    StockEntry("TSLA", "Tesla Inc.", "US", "Large-Cap", "Automobile & Ancillaries", "Autonomous EV & Robotics Prime", "World leader in electric vehicles scaling Full Self-Driving neural networks and humanoid robotics.", "Mobility & EV Scale-Up"),
    StockEntry("APTV", "Aptiv PLC", "US", "Mid-Cap", "Automobile & Ancillaries", "High-Voltage Signal Distribution", "Tier-1 architecture provider supplying high-voltage wiring and brain compute modules to global OEMs.", "Mobility & EV Scale-Up"),
    StockEntry("BWA", "BorgWarner", "US", "Mid-Cap", "Automobile & Ancillaries", "e-Propulsion Drivetrains", "Supplier of electric drive motors, power electronics, and high-efficiency hybrid transmissions.", "Mobility & EV Scale-Up"),
    StockEntry("MOD", "Modine Manufacturing", "US", "Small-Cap", "Automobile & Ancillaries", "Thermal Cooling Loops & Chillers", "Engineering advanced liquid cooling solutions for heavy electric vehicles and AI data center chips.", "Mobility & EV Scale-Up"),

    # -------------------------------------------------------------------------
    # 4. Banking & Financial Services
    # -------------------------------------------------------------------------
    StockEntry("HDFCBANK.NS", "HDFC Bank", "INDIA", "Large-Cap", "Banking & Financial Services", "Private Sector Retail Bank", "Fortress banking franchise with conservative underwriting and systemic retail branch presence.", "Financial Infrastructure"),
    StockEntry("ICICIBANK.NS", "ICICI Bank", "INDIA", "Large-Cap", "Banking & Financial Services", "Universal Digital Bank", "Industry-leading return on assets and clean asset quality across digital retail and corporate lending.", "Financial Infrastructure"),
    StockEntry("SBIN.NS", "State Bank of India", "INDIA", "Large-Cap", "Banking & Financial Services", "Public Sector Sovereign Lender", "India's largest financial institution driving national credit expansion with low-cost deposit CASA.", "Financial Infrastructure"),
    StockEntry("BAJFINANCE.NS", "Bajaj Finance", "INDIA", "Large-Cap", "Banking & Financial Services", "Omnichannel Consumer Credit", "Non-bank financial titan commanding unmatched credit cross-selling and high return on equity.", "Financial Infrastructure"),
    StockEntry("CDSL.NS", "Central Depository Services", "INDIA", "Mid-Cap", "Banking & Financial Services", "Securities Depository Monopoly", "Capital markets tollbooth profiting from the secular surge in retail demat accounts and trading.", "Financial Infrastructure"),
    StockEntry("YESBANK.NS", "Yes Bank", "INDIA", "Small-Cap", "Banking & Financial Services", "Turnaround Commercial Bank", "Post-reconstruction private bank recovering through retail deposit growth and clean corporate loans.", "Financial Infrastructure"),
    StockEntry("SOUTHBANK.NS", "South Indian Bank", "INDIA", "Small-Cap", "Banking & Financial Services", "Regional Private Lender", "Kerala-based lender with attractive price-to-book valuation and sustained NPA reduction.", "Financial Infrastructure"),
    StockEntry("JPM", "JPMorgan Chase", "US", "Large-Cap", "Banking & Financial Services", "Global Money Center Bank", "World's premier investment and commercial bank benefiting from high net interest margins and dealmaking.", "Financial Infrastructure"),
    StockEntry("V", "Visa Inc.", "US", "Large-Cap", "Banking & Financial Services", "Global Payments Tollbooth", "Duopoly payments network processing trillions in electronic transactions at 50%+ operating margins.", "Financial Infrastructure"),
    StockEntry("COIN", "Coinbase Global", "US", "Mid-Cap", "Banking & Financial Services", "Regulated Digital Asset Custodian", "Premier US crypto exchange and institutional custodian capturing secular digital asset adoption.", "Financial Infrastructure"),

    # -------------------------------------------------------------------------
    # 5. Energy, Power & Utilities
    # -------------------------------------------------------------------------
    StockEntry("RELIANCE.NS", "Reliance Industries", "INDIA", "Large-Cap", "Energy, Power & Utilities", "Integrated Energy, Petrochemicals & Retail", "India's largest enterprise spanning oil-to-chemicals refining, Jio digital services, and green energy gigafactories.", "Energy Transition & Grid"),
    StockEntry("NTPC.NS", "NTPC Limited", "INDIA", "Large-Cap", "Energy, Power & Utilities", "Thermal & Green Power Utility", "India's largest electricity generator expanding aggressively into utility-scale solar and green hydrogen.", "Energy Transition & Grid"),
    StockEntry("POWERGRID.NS", "Power Grid Corp of India", "INDIA", "Large-Cap", "Energy, Power & Utilities", "Sovereign Transmission Grid", "Near-monopoly in interstate electricity transmission with guaranteed regulated return on equity.", "Energy Transition & Grid"),
    StockEntry("TATAPOWER.NS", "Tata Power", "INDIA", "Mid-Cap", "Energy, Power & Utilities", "Integrated Renewables & EV Charging", "Scaling national EV fast-charging corridors, rooftop solar EPC, and pumped hydro storage.", "Energy Transition & Grid"),
    StockEntry("SUZLON.NS", "Suzlon Energy", "INDIA", "Small-Cap", "Energy, Power & Utilities", "Wind Turbine Generator OEM", "Debt-free market leader in domestic wind turbines powering India's 500 GW clean energy mandate.", "Energy Transition & Grid"),
    StockEntry("IREDA.NS", "IREDA", "INDIA", "Small-Cap", "Energy, Power & Utilities", "Green Infrastructure Financing", "State-owned NBFC underwriting utility-scale solar, wind, and battery storage projects.", "Energy Transition & Grid"),
    StockEntry("RPOWER.NS", "Reliance Power", "INDIA", "Small-Cap", "Energy, Power & Utilities", "Thermal & Solar Power Generation", "Deleveraging power generator operating large-scale thermal assets during peak summer grid demand.", "Energy Transition & Grid"),
    StockEntry("CEG", "Constellation Energy", "US", "Large-Cap", "Energy, Power & Utilities", "Nuclear Fleet Baseload", "Largest US nuclear clean energy operator securing multi-decade power purchase pacts with AI hyperscalers.", "Energy Transition & Grid"),
    StockEntry("VRT", "Vertiv Holdings", "US", "Mid-Cap", "Energy, Power & Utilities", "Liquid Thermal Cooling for GPUs", "Critical thermal management systems and power conditioning equipment required to cool AI data centers.", "Energy Transition & Grid"),
    StockEntry("ETN", "Eaton Corporation", "US", "Mid-Cap", "Energy, Power & Utilities", "Electrical Switchgear & Transformers", "Essential power distribution equipment modernizing aging electrical utility grids and AI sites.", "Energy Transition & Grid"),
    StockEntry("CCJ", "Cameco Corporation", "US", "Mid-Cap", "Energy, Power & Utilities", "Uranium Mining & Nuclear Fuel", "World's leading commercial uranium producer supplying clean nuclear fuel to western power utilities.", "Energy Transition & Grid"),

    # -------------------------------------------------------------------------
    # 6. FMCG (Fast-Moving Consumer Goods)
    # -------------------------------------------------------------------------
    StockEntry("HINDUNILVR.NS", "Hindustan Unilever", "INDIA", "Large-Cap", "FMCG (Fast-Moving Consumer Goods)", "Household & Personal Care", "Essential consumer staples titan reaching 9 out of 10 Indian homes every day across soap and tea.", "Consumer Staples"),
    StockEntry("ITC.NS", "ITC Limited", "INDIA", "Large-Cap", "FMCG (Fast-Moving Consumer Goods)", "Cigarettes, Foods & Agribusiness", "Defensive cash cow with massive pricing power, growing packaged foods, and strong dividend yields.", "Consumer Staples"),
    StockEntry("NESTLEIND.NS", "Nestle India", "INDIA", "Large-Cap", "FMCG (Fast-Moving Consumer Goods)", "Packaged Foods & Nutrition", "High pricing power in infant nutrition, noodles (Maggi), and dairy products with loyal consumer affinity.", "Consumer Staples"),
    StockEntry("BRITANNIA.NS", "Britannia Industries", "INDIA", "Large-Cap", "FMCG (Fast-Moving Consumer Goods)", "Biscuits & Bakery Products", "Defensive snack food leader with deep rural penetration and expanding cheese and dairy footprint.", "Consumer Staples"),
    StockEntry("FCONSUMER.NS", "Future Consumer", "INDIA", "Small-Cap", "FMCG (Fast-Moving Consumer Goods)", "Branded Food & Staples Turnaround", "Former Future Group consumer brand entity navigating corporate balance sheet debt restructuring.", "Consumer Staples"),
    StockEntry("SANWARIA.NS", "Sanwaria Consumer", "INDIA", "Small-Cap", "FMCG (Fast-Moving Consumer Goods)", "Edible Oils & Basmati Rice", "Basmati rice and edible oil processor trading at sub-rupee micro-cap valuations under CIRP.", "Consumer Staples"),
    StockEntry("PG", "Procter & Gamble", "US", "Large-Cap", "FMCG (Fast-Moving Consumer Goods)", "Global Personal & Fabric Care", "Unmatched consumer goods brand moat (Tide, Gillette, Pampers) with 65+ consecutive years of dividend hikes.", "Consumer Staples"),
    StockEntry("KO", "Coca-Cola Company", "US", "Large-Cap", "FMCG (Fast-Moving Consumer Goods)", "Non-Alcoholic Beverages", "Legendary global beverage distribution network with steady pricing power and emerging market growth.", "Consumer Staples"),
    StockEntry("COST", "Costco Wholesale", "US", "Large-Cap", "FMCG (Fast-Moving Consumer Goods)", "Membership Warehouse Grocery", "Membership-based bulk retail moat with 90%+ renewal rates and high inventory turnover velocity.", "Consumer Staples"),

    # -------------------------------------------------------------------------
    # 7. Healthcare & Pharmaceuticals
    # -------------------------------------------------------------------------
    StockEntry("SUNPHARMA.NS", "Sun Pharma", "INDIA", "Large-Cap", "Healthcare & Pharmaceuticals", "Specialty Dermatology & Generics", "India's largest drugmaker with global specialty dermatology leadership (Ilumya, Winlevi).", "Healthcare Innovation"),
    StockEntry("CIPLA.NS", "Cipla Limited", "INDIA", "Large-Cap", "Healthcare & Pharmaceuticals", "Respiratory Inhalers & Anti-Infectives", "Dominates respiratory aerosol therapies and affordable oncology medications across emerging markets.", "Healthcare Innovation"),
    StockEntry("DRREDDY.NS", "Dr. Reddy's Laboratories", "INDIA", "Large-Cap", "Healthcare & Pharmaceuticals", "Biosimilars & Active Ingredients", "Global generic pharmaceutical player with expanding biosimilar pipeline in the US and Europe.", "Healthcare Innovation"),
    StockEntry("SYNCOMF.NS", "Syncom Formulations", "INDIA", "Small-Cap", "Healthcare & Pharmaceuticals", "Generic Injections & Formulations", "Sub-₹25 pharmaceutical formulation manufacturer exporting generic capsules and syrups to 30+ countries.", "Healthcare Innovation"),
    StockEntry("WELCURE.BO", "Welcure Drugs", "INDIA", "Small-Cap", "Healthcare & Pharmaceuticals", "Micro-Cap Pharmaceutical Formulations", "Sub-rupee pharmaceutical enterprise trading on BSE with low float and speculative micro liquidity.", "Healthcare Innovation"),
    StockEntry("LLY", "Eli Lilly and Co", "US", "Large-Cap", "Healthcare & Pharmaceuticals", "GLP-1 Metabolic & Alzheimer's", "Pioneer in Mounjaro and Zepbound transforming metabolic health and obesity therapeutics worldwide.", "Healthcare Innovation"),
    StockEntry("NVO", "Novo Nordisk", "US", "Large-Cap", "Healthcare & Pharmaceuticals", "Ozempic & Wegovy Semaglutide", "Danish pharmaceutical leader revolutionizing type 2 diabetes management and cardiovascular risk reduction.", "Healthcare Innovation"),
    StockEntry("ISRG", "Intuitive Surgical", "US", "Mid-Cap", "Healthcare & Pharmaceuticals", "da Vinci Robotic Surgery", "Monopolistic robotic surgical platform generating high-margin recurring instrument replacement revenues.", "Healthcare Innovation"),

    # -------------------------------------------------------------------------
    # 8. Industrial Products & Capital Goods
    # -------------------------------------------------------------------------
    StockEntry("LT.NS", "Larsen & Toubro", "INDIA", "Large-Cap", "Industrial Products & Capital Goods", "Mega Infrastructure & Defense EPC", "Premier Indian engineering conglomerate executing multi-trillion rupee sovereign bridges, ports, and defense.", "Industrial Capex"),
    StockEntry("BEL.NS", "Bharat Electronics", "INDIA", "Large-Cap", "Industrial Products & Capital Goods", "Defense Radars & Avionics", "State-owned defense electronics champion securing high-margin sovereign missile and radar contracts.", "Industrial Capex"),
    StockEntry("HAL.NS", "Hindustan Aeronautics", "INDIA", "Large-Cap", "Industrial Products & Capital Goods", "Fighter Aircraft & Helicopters", "Monopoly manufacturer of indigenous Tejas fighter aircraft with massive multi-year defense order book.", "Industrial Capex"),
    StockEntry("SEPC.NS", "SEPC Ltd", "INDIA", "Small-Cap", "Industrial Products & Capital Goods", "Water & Metallurgy EPC", "Sub-₹10 engineering contractor building municipal water supply infrastructure and industrial metallurgy plants.", "Industrial Capex"),
    StockEntry("HCC.NS", "Hindustan Construction Co", "INDIA", "Small-Cap", "Industrial Products & Capital Goods", "Tunnels, Hydro Dams & Nuclear Plants", "Iconic infrastructure builder constructing nuclear reactors, trans-Himalayan railway tunnels, and bridges.", "Industrial Capex"),
    StockEntry("CAT", "Caterpillar Inc.", "US", "Large-Cap", "Industrial Products & Capital Goods", "Heavy Construction & Mining Machinery", "Global benchmark in heavy earthmoving excavators, mining trucks, and backup power generators.", "Industrial Capex"),
    StockEntry("GEV", "GE Vernova", "US", "Large-Cap", "Industrial Products & Capital Goods", "Gas Turbines & Grid Electrification", "Supplying gas turbines, wind blades, and grid software to satisfy soaring data center electricity demand.", "Industrial Capex"),
    StockEntry("FLS", "Flowserve Corp", "US", "Mid-Cap", "Industrial Products & Capital Goods", "High-Pressure Industrial Pumps", "Pumps, valves, and mechanical seals engineered for nuclear power plants and chemical refineries.", "Industrial Capex"),
    StockEntry("ERII", "Energy Recovery", "US", "Small-Cap", "Industrial Products & Capital Goods", "Desalination Pressure Exchangers", "Recovers 60% of pumping energy in seawater reverse osmosis desalination plants globally.", "Industrial Capex"),

    # -------------------------------------------------------------------------
    # 9. IT Industry & High-Tech Software
    # -------------------------------------------------------------------------
    StockEntry("TCS.NS", "Tata Consultancy Services", "INDIA", "Large-Cap", "IT Industry & High-Tech Software", "Global IT Consulting & Enterprise AI", "Zero-debt balance sheet, 35%+ ROE, and mission-critical multi-billion global cloud contracts.", "Enterprise Tech & AI"),
    StockEntry("INFY.NS", "Infosys", "INDIA", "Large-Cap", "IT Industry & High-Tech Software", "Digital Services & Cloud Modernization", "High cash generation provider delivering enterprise AI transformation and generative software tools.", "Enterprise Tech & AI"),
    StockEntry("PERSISTENT.NS", "Persistent Systems", "INDIA", "Mid-Cap", "IT Industry & High-Tech Software", "Digital Product Engineering", "High-growth software engineering specialist creating AI models for healthcare and fintech clients.", "Enterprise Tech & AI"),
    StockEntry("TATATECH.NS", "Tata Technologies", "INDIA", "Mid-Cap", "IT Industry & High-Tech Software", "Automotive & Aerospace ER&D", "Pure-play engineering R&D services powering OEM transitions to software-defined autonomous vehicles.", "Enterprise Tech & AI"),
    StockEntry("FCSSOFT.NS", "FCS Software Solutions", "INDIA", "Small-Cap", "IT Industry & High-Tech Software", "Offshore Software & Infrastructure", "Sub-₹5 micro-cap software consulting and enterprise infrastructure management services provider.", "Enterprise Tech & AI"),
    StockEntry("3IINFOLTD.NS", "3i Infotech", "INDIA", "Small-Cap", "IT Industry & High-Tech Software", "Banking & Fintech Software Solutions", "Sub-₹30 digital transformation provider serving public banking and financial services clients.", "Enterprise Tech & AI"),
    StockEntry("NVDA", "NVIDIA Corporation", "US", "Large-Cap", "IT Industry & High-Tech Software", "AI GPUs & CUDA Ecosystem", "Global monopoly in parallel processing silicon powering modern artificial intelligence datacenters.", "Enterprise Tech & AI"),
    StockEntry("MSFT", "Microsoft Corporation", "US", "Large-Cap", "IT Industry & High-Tech Software", "Azure Cloud & Enterprise Copilots", "Cloud infrastructure monopoly combined with Office enterprise software and OpenAI strategic partnership.", "Enterprise Tech & AI"),
    StockEntry("PLTR", "Palantir Technologies", "US", "Large-Cap", "IT Industry & High-Tech Software", "Defense & Enterprise AI Ontology", "Operating system for government intelligence and commercial enterprise AI decision orchestration.", "Enterprise Tech & AI"),
    StockEntry("SOUN", "SoundHound AI", "US", "Small-Cap", "IT Industry & High-Tech Software", "Voice AI & Automotive Interfaces", "Conversational voice AI powering automotive vehicle dashboards and restaurant drive-thrus.", "Enterprise Tech & AI"),

    # -------------------------------------------------------------------------
    # 10. Raw Materials, Metals & Mining
    # -------------------------------------------------------------------------
    StockEntry("TATASTEEL.NS", "Tata Steel", "INDIA", "Large-Cap", "Raw Materials, Metals & Mining", "Integrated Flat Steel & Iron Ore", "Low-cost integrated steelmaker backed by captive iron ore mines and Indian infrastructure demand.", "Materials & Mining"),
    StockEntry("JSWSTEEL.NS", "JSW Steel", "INDIA", "Large-Cap", "Raw Materials, Metals & Mining", "High-Grade Electrical & Construction Steel", "Private steelmaker expanding domestic capacity across high-margin coated and electrical steels.", "Materials & Mining"),
    StockEntry("HINDALCO.NS", "Hindalco Industries", "INDIA", "Large-Cap", "Raw Materials, Metals & Mining", "Aluminum Smelting & Can Recycling", "Global aluminum champion owning Novelis, the world's largest beverage can aluminum recycler.", "Materials & Mining"),
    StockEntry("COALINDIA.NS", "Coal India", "INDIA", "Large-Cap", "Raw Materials, Metals & Mining", "Thermal Coal Mining Monopoly", "Supplies 80%+ of India's domestic coal for electricity generation with double-digit dividend yield.", "Materials & Mining"),
    StockEntry("VIKASPROP.BO", "Vikas Proppant & Granite", "INDIA", "Small-Cap", "Raw Materials, Metals & Mining", "Frac Sand & Granite Exploration", "Sub-rupee mining entity supplying industrial frac sand proppants and architectural granite in Rajasthan.", "Materials & Mining"),
    StockEntry("FCX", "Freeport-McMoRan", "US", "Large-Cap", "Raw Materials, Metals & Mining", "Global Copper Mining", "Primary global pure-play copper miner with Tier-1 low-cost reserves in Grasberg and North America.", "Materials & Mining"),
    StockEntry("MP", "MP Materials", "US", "Small-Cap", "Raw Materials, Metals & Mining", "Rare Earth NdPr Magnets", "Owns Mountain Pass, the premier western rare earth mine providing permanent magnets for EV motors.", "Materials & Mining"),

    # -------------------------------------------------------------------------
    # 11. Logistics, Freight & Maritime
    # -------------------------------------------------------------------------
    StockEntry("ADANIPORTS.NS", "Adani Ports & SEZ", "INDIA", "Large-Cap", "Logistics, Freight & Maritime", "Commercial Seaports & Logistics Parks", "Handles nearly 25% of India's maritime container trade with high operating margins.", "Global Supply Chain"),
    StockEntry("DELHIVERY.NS", "Delhivery", "INDIA", "Mid-Cap", "Logistics, Freight & Maritime", "Automated Express E-Commerce Delivery", "Fully automated express parcel logistics network capturing Indian quick-commerce and online retail.", "Global Supply Chain"),
    StockEntry("CONCOR.NS", "Container Corp of India", "INDIA", "Mid-Cap", "Logistics, Freight & Maritime", "Inland Railway Freight Terminals", "State-backed multimodal logistics operator connecting Indian interior dry ports to coastal gateways.", "Global Supply Chain"),
    StockEntry("UPS", "United Parcel Service", "US", "Large-Cap", "Logistics, Freight & Maritime", "Global Air & Ground Freight", "World's largest package delivery company with automated sorting hubs and healthcare cold chains.", "Global Supply Chain"),

    # -------------------------------------------------------------------------
    # 12. Media & Entertainment
    # -------------------------------------------------------------------------
    StockEntry("SUNTV.NS", "Sun TV Network", "INDIA", "Mid-Cap", "Media & Entertainment", "Regional Television Broadcasting", "Dominates South Indian television entertainment with zero debt and consistent dividend distributions.", "Digital Media"),
    StockEntry("PVRINOX.NS", "PVR INOX", "INDIA", "Mid-Cap", "Media & Entertainment", "Multiplex Theatrical Cinema", "Monopoly cinema exhibitor in organized film exhibition with expanding food and beverage margins.", "Digital Media"),
    StockEntry("ZEEMEDIA.NS", "Zee Media Corp", "INDIA", "Small-Cap", "Media & Entertainment", "News Broadcast Television", "Sub-₹10 broadcasting network operating 14 regional news television channels across India.", "Digital Media"),
    StockEntry("DISHTV.NS", "Dish TV India", "INDIA", "Small-Cap", "Media & Entertainment", "Direct-to-Home Satellite TV", "Sub-₹5 satellite television broadcaster serving rural and suburban television subscribers.", "Digital Media"),
    StockEntry("RADAAN.NS", "Radaan Mediaworks", "INDIA", "Small-Cap", "Media & Entertainment", "Regional Television Content Production", "Sub-₹5 media company producing television serials, web-series, and regional entertainment.", "Digital Media"),
    StockEntry("SHALPRO.BO", "Shalimar Productions", "INDIA", "Small-Cap", "Media & Entertainment", "Media Production & Video Studios", "Sub-rupee micro-cap outfit trading on BSE in the media and video entertainment segment.", "Digital Media"),
    StockEntry("NFLX", "Netflix Inc.", "US", "Large-Cap", "Media & Entertainment", "Global Streaming Entertainment", "Dominant streaming platform expanding operating margins via paid sharing and ad-supported tiers.", "Digital Media"),
    StockEntry("RDDT", "Reddit Inc.", "US", "Mid-Cap", "Media & Entertainment", "Social Discussion & Data Licensing", "Community platform monetizing authentic human discussions through digital ads and LLM data licensing.", "Digital Media"),

    # -------------------------------------------------------------------------
    # 13. Agricultural & Farm Products
    # -------------------------------------------------------------------------
    StockEntry("COROMANDEL.NS", "Coromandel International", "INDIA", "Large-Cap", "Agricultural & Farm Products", "Phosphatic Fertilizers & Ag-Chemicals", "Pioneer in complex fertilizers and crop protection protecting domestic agricultural food security.", "Agricultural Inputs"),
    StockEntry("PIIND.NS", "PI Industries", "INDIA", "Mid-Cap", "Agricultural & Farm Products", "Custom Agrochemical Synthesis", "Leading custom synthesis manufacturer exporting complex patented agricultural chemicals to global innovators.", "Agricultural Inputs"),
    StockEntry("JISLJALEQS.NS", "Jain Irrigation Systems", "INDIA", "Small-Cap", "Agricultural & Farm Products", "Micro-Drip Irrigation Systems", "Pioneer in water-saving precision micro-irrigation systems and PVC piping for Indian farmers.", "Agricultural Inputs"),
    StockEntry("DE", "Deere & Company", "US", "Large-Cap", "Agricultural & Farm Products", "Autonomous Tractors & Precision Farming", "World leader in agricultural machinery integrating AI computer vision sprayers and autonomous tractors.", "Agricultural Inputs"),

    # -------------------------------------------------------------------------
    # 14. Consumer Durables & Electronics
    # -------------------------------------------------------------------------
    StockEntry("HAVELLS.NS", "Havells India", "INDIA", "Large-Cap", "Consumer Durables & Electronics", "Fast Moving Electrical Goods (FMEG)", "Household brand commanding organized market share in switchgears, cables, LED lighting, and fans.", "Consumer Electrification"),
    StockEntry("DIXON.NS", "Dixon Technologies", "INDIA", "Large-Cap", "Consumer Durables & Electronics", "Electronic Manufacturing Services (EMS)", "India's largest domestic contract electronics assembler benefiting from national PLI incentives.", "Consumer Electrification"),
    StockEntry("VOLTAS.NS", "Voltas Ltd", "INDIA", "Mid-Cap", "Consumer Durables & Electronics", "Room Air Conditioners & Commercial HVAC", "Tata Group market leader in residential cooling units expanding market share during severe heatwaves.", "Consumer Electrification"),
    StockEntry("WHR", "Whirlpool Corporation", "US", "Large-Cap", "Consumer Durables & Electronics", "Major Home Appliances", "Global leader in kitchen and laundry appliances expanding high-margin small domestic devices.", "Consumer Electrification"),

    # -------------------------------------------------------------------------
    # 15. Derived Materials & Chemicals
    # -------------------------------------------------------------------------
    StockEntry("PIDILITIND.NS", "Pidilite Industries (Fevicol)", "INDIA", "Large-Cap", "Derived Materials & Chemicals", "Consumer Adhesives & Sealants", "Monopoly in consumer adhesives with iconic Fevicol brand equity and unmatched carpenter distribution.", "Specialty Chemicals"),
    StockEntry("SRF.NS", "SRF Limited", "INDIA", "Mid-Cap", "Derived Materials & Chemicals", "Fluorochemicals & Technical Textiles", "Market leader in clean refrigerants and fluorinated specialty intermediates for pharma and agro.", "Specialty Chemicals"),
    StockEntry("VIKASECO.NS", "Vikas EcoTech", "INDIA", "Small-Cap", "Derived Materials & Chemicals", "Recycled Polymers & Chemical Additives", "Sub-₹5 specialty chemical company formulating eco-friendly organotin heat stabilizers.", "Specialty Chemicals"),
    StockEntry("LIN", "Linde plc", "US", "Large-Cap", "Derived Materials & Chemicals", "Industrial Gases & Cryogenic Hydrogen", "Global industrial gas monopoly supplying atmospheric oxygen, nitrogen, and clean hydrogen infrastructure.", "Specialty Chemicals"),
    StockEntry("ALB", "Albemarle Corporation", "US", "Mid-Cap", "Derived Materials & Chemicals", "Lithium Compounds for EV Cells", "World's premier lithium producer supplying battery-grade lithium hydroxide to automakers.", "Specialty Chemicals"),

    # -------------------------------------------------------------------------
    # 16. Hospitality, Travel & Aviation
    # -------------------------------------------------------------------------
    StockEntry("INDIGO.NS", "InterGlobe Aviation (IndiGo)", "INDIA", "Large-Cap", "Hospitality, Travel & Aviation", "Low-Cost Commercial Airline", "Commands 60%+ of Indian domestic air travel with unmatched on-time performance and young fleet.", "Travel & Mobility"),
    StockEntry("INDHOTEL.NS", "Indian Hotels Co (Taj)", "INDIA", "Mid-Cap", "Hospitality, Travel & Aviation", "Luxury Hospitality & Palaces", "Tata flagship operating iconic Taj luxury palaces and scaling high-margin asset-light Ginger hotels.", "Travel & Mobility"),
    StockEntry("BKNG", "Booking Holdings", "US", "Large-Cap", "Hospitality, Travel & Aviation", "Online Travel Agency (OTA)", "Global travel booking duopoly with high free cash flow conversion and rising hotel bookings.", "Travel & Mobility"),
    StockEntry("JOBY", "Joby Aviation", "US", "Small-Cap", "Hospitality, Travel & Aviation", "Electric Air Taxis (eVTOL)", "Pioneering certified commercial electric aerial ridesharing backed by Toyota and Delta Air Lines.", "Travel & Mobility"),

    # -------------------------------------------------------------------------
    # 17. Apparel & Accessories
    # -------------------------------------------------------------------------
    StockEntry("TITAN.NS", "Titan Company (Tanishq)", "INDIA", "Large-Cap", "Apparel & Accessories", "Organized Jewelry & Watches", "Tata luxury consumer flagship capturing the generational consumer shift to organized hallmarked gold.", "Consumer Lifestyle"),
    StockEntry("KALYANKJIL.NS", "Kalyan Jewellers", "INDIA", "Mid-Cap", "Apparel & Accessories", "Pan-India Retail Jewelry", "Fast-scaling jewelry retailer expanding footprint across North and South India via franchise formats.", "Consumer Lifestyle"),
    StockEntry("TPR", "Tapestry Inc. (Coach)", "US", "Mid-Cap", "Apparel & Accessories", "Accessible Luxury Handbags", "Parent company of Coach and Kate Spade delivering digital margin expansion and premium consumer demand.", "Consumer Lifestyle"),
]


# =============================================================================
# UNIVERSE QUERY & FILTER UTILITIES
# =============================================================================

def get_all_sectors(market: Optional[str] = None) -> List[str]:
    """Returns sorted unique list of all 17 sectors, optionally filtered by market."""
    entries = STOCK_UNIVERSE if not market else [e for e in STOCK_UNIVERSE if e.market.upper() == market.upper()]
    return sorted(list({e.sector for e in entries}))


def get_all_cap_tiers() -> List[str]:
    """Returns standardized market capitalization tiers."""
    return ["All Caps", "Large-Cap", "Mid-Cap", "Small-Cap"]


def get_stock_universe(
    market: Optional[str] = None,
    cap_tier: Optional[str] = None,
    sector: Optional[str] = None,
) -> List[StockEntry]:
    """
    Filters the stock universe by market, capitalization tier, and sector.
    """
    results = STOCK_UNIVERSE

    if market:
        results = [e for e in results if e.market.upper() == market.upper()]

    if cap_tier and cap_tier != "All Caps":
        results = [e for e in results if e.market_cap_tier.lower() == cap_tier.lower()]

    if sector and sector != "All Sectors":
        results = [e for e in results if e.sector.lower() == sector.lower()]

    return results


def search_stock_universe(
    query: Optional[str] = None,
    market: Optional[str] = None,
    market_cap_tier: Optional[str] = None,
    sector: Optional[str] = None,
) -> List[StockEntry]:
    """
    Full-text search across ticker, company name, sector, sub-sector, and role,
    with optional filtering by market, cap tier, and sector.
    """
    results = get_stock_universe(market=market, cap_tier=market_cap_tier, sector=sector)

    if not query or not query.strip():
        return results

    q = query.strip().lower()
    return [
        e for e in results
        if q in e.ticker.lower()
        or q in e.name.lower()
        or q in e.sector.lower()
        or q in e.sub_sector.lower()
        or q in e.plain_english_role.lower()
        or q in e.thematic_anchor.lower()
    ]


def infer_company_sector(name: str, ticker: str = "") -> str:
    """
    Infers one of the 17 standardized Master Spec sectors from company name & ticker keywords.
    """
    text = f"{name} {ticker}".upper()

    if any(k in text for k in ["TELECOM", "COMMUNICATION", "BROADBAND", "OPTICAL", "FIBER", "TOWER", "NETWORK", "5G", "6G"]):
        return "Telecommunications & Networks"
    if any(k in text for k in ["TEXTILE", "SPINNING", "MILLS", "FABRIC", "YARN", "WEAVING", "COTTON", "SILK", "SYNTHETIC", "GARMENT", "DENIM"]):
        return "Textiles, Technical Fibers & Apparel"
    if any(k in text for k in ["BANK", "FINANC", "CAPITAL", "INVEST", "HOLDING", "INSUR", "LEASING", "SECURIT", "BROK"]):
        return "Banking & Financial Services"
    if any(k in text for k in ["AUTO", "MOTOR", "TYRE", "TIRE", "WHEEL", "BEARING", "BRAKE", "ENGINE", "AXLE", "TRANSMISSION"]):
        return "Automobile & Ancillaries"
    if any(k in text for k in ["PHARMA", "HEALTH", "DRUG", "BIO", "MEDIC", "LABORAT", "HOSPITAL", "CLINIC", "LIFE SCIENCE"]):
        return "Healthcare & Pharmaceuticals"
    if any(k in text for k in ["POWER", "ENERGY", "SOLAR", "WIND", "HYDRO", "ELECTRIC", "GRID", "GAS", "PETRO", "RENEWABLE"]):
        return "Energy, Power & Utilities"
    if any(k in text for k in ["SOFTWARE", "INFOTECH", "TECH", "DIGITAL", "SYSTEMS", "COMPUT", "CYBER", "CLOUD", "AI"]):
        return "IT Industry & High-Tech Software"
    if any(k in text for k in ["FOOD", "FMCG", "BEVERAGE", "DAIRY", "BREWER", "DISTILL", "SUGAR", "CONSUMER", "TEA", "COFFEE", "SNACK", "FLOUR"]):
        return "FMCG (Fast-Moving Consumer Goods)"
    if any(k in text for k in ["STEEL", "IRON", "MINING", "METAL", "ALUMIN", "ZINC", "COPPER", "MINERAL", "ORES", "FOUNDRY"]):
        return "Raw Materials, Metals & Mining"
    if any(k in text for k in ["LOGISTIC", "TRANSPORT", "CARRIER", "SHIPPING", "PORT", "FREIGHT", "EXPRESS", "DELIVER", "RAIL"]):
        return "Logistics, Freight & Maritime"
    if any(k in text for k in ["CHEM", "POLY", "PLASTIC", "FERT", "PEST", "CARBON", "RESIN", "PIGMENT", "COATING"]):
        return "Derived Materials & Chemicals"
    if any(k in text for k in ["AGRO", "AGRI", "CROP", "SEED", "TRACTOR", "IRRIGATION"]):
        return "Agricultural & Farm Products"
    if any(k in text for k in ["HOTEL", "RESORT", "TRAVEL", "AIRLINE", "AVIATION", "TOUR", "HOSPITALITY", "RESTAURANT"]):
        return "Hospitality, Travel & Aviation"
    if any(k in text for k in ["MEDIA", "ENTERTAIN", "FILM", "CINEMA", "BROADCAST", "PUBLISH", "TV", "RADIO"]):
        return "Media & Entertainment"
    if any(k in text for k in ["JEWEL", "WATCH", "FOOTWEAR", "RETAIL", "APPAREL", "FASHION", "LIFESTYLE", "LUXURY"]):
        return "Apparel & Accessories"
    if any(k in text for k in ["ELECTRONIC", "APPLIANCE", "AIRCON", "REFRIG", "LAMP", "LIGHT", "GADGET", "DISPLAY"]):
        return "Consumer Durables & Electronics"

    return "Industrial Products & Capital Goods"


def infer_cap_tier(price: float, turnover: float = 0.0, category_id: str = "") -> str:
    """
    Infers standardized market capitalization tier (Large-Cap, Mid-Cap, Small-Cap).
    """
    if category_id == "penny" or price < 100.0:
        return "Small-Cap"
    if category_id == "safe" or (price >= 500.0 and turnover >= 500.0):
        return "Large-Cap"
    return "Mid-Cap"


def get_ticker_sector_map() -> Dict[str, Tuple[str, str, str]]:
    """
    Returns a fast lookup dictionary mapping ticker -> (sector, market_cap_tier, plain_english_role).
    """
    return {
        entry.ticker: (entry.sector, entry.market_cap_tier, entry.plain_english_role)
        for entry in STOCK_UNIVERSE
    }
