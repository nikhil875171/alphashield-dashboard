from typing import Dict, List, Optional


# Institutional Supply Chain & Sectoral Transmission Trees
TRANSMISSION_GRAPHS = {
    "AI_DATACENTER": {
        "title": "AI Datacenter & Semiconductor Supercycle",
        "description": "Massive capital expenditure wave into generative AI training & inference infrastructure.",
        "upstream_positive": [
            "GPU & Custom ASIC Designers (NVIDIA, Broadcom, AMD)",
            "Advanced Foundries & Lithography (TSMC, ASML)",
            "High-Bandwidth Memory - HBM (SK Hynix, Micron)",
        ],
        "midstream_positive": [
            "Server ODMs & System Integrators (Foxconn, Supermicro, Quanta)",
            "Optical Transceivers & 800G/1.6T Silicon Photonics (Coherent, Lumentum)",
            "Outsourced Semiconductor Assembly & Test - OSAT (ASE, Amkor)",
        ],
        "downstream_positive": [
            "Nuclear & Small Modular Reactor (SMR) Utilities (Constellation, Vistra, NuScale)",
            "Copper Grid & High-Voltage Transmission (Eaton, Schneider, Prysmian)",
            "Industrial HVAC & Liquid Immersion Cooling (Vertiv, Modine)",
            "Hyperscale Datacenter REITs (Equinix, Digital Realty)",
        ],
        "negative_spillovers": [
            "Commodity Enterprise HDD Storage (Replaced by enterprise NVMe SSDs)",
            "Legacy Enterprise On-Premise Hardware (Budget cannibalization)",
        ],
        "typical_tickers": ["NVDA", "TSM", "AVGO", "VRT", "CEG", "ANET", "TCS.NS", "INFY.NS"]
    },
    "EV_BATTERY": {
        "title": "Electric Vehicle & Energy Transition Ecosystem",
        "description": "Global electrification of mobility, cell chemistry innovation, and high-voltage grid integration.",
        "upstream_positive": [
            "Critical Mineral Miners: Lithium, Nickel, Cobalt, Synthetic Graphite (Albemarle, SQM)",
            "Rare Earth Magnet Producers for Traction Motors",
        ],
        "midstream_positive": [
            "Tier-1 Battery Cell Manufacturers (CATL, LG Energy, Panasonic)",
            "Cathode & Anode Active Material Chemists",
            "Battery Management System (BMS) Microcontrollers",
        ],
        "downstream_positive": [
            "DC Fast-Charging Infrastructure & Energy Storage Systems",
            "High-Voltage Wiring Harnesses & Silicon Carbide (SiC) Power Inverters (Wolfspeed, STMicro)",
        ],
        "negative_spillovers": [
            "Legacy Internal Combustion Engine (ICE) Powertrain & Catalytic Converter Suppliers",
            "Exhaust System Fabricators & Transmission Gear Machiners",
        ],
        "typical_tickers": ["TSLA", "TATAMOTORS.NS", "RIVN", "ALB", "ON", "EXIDEIND.NS"]
    },
    "AVIATION_TOURISM": {
        "title": "Aviation, Aerospace & Experiential Tourism Recovery",
        "description": "Global passenger yield expansion, fleet renewals, and discretionary hospitality tailwinds.",
        "upstream_positive": [
            "Aerospace Engine & Airframe MRO Facilities (GE Aerospace, Safran, MTU Aero)",
            "Avionics & Structural Composite Forgers (Hexcel, Howmet Aerospace)",
        ],
        "midstream_positive": [
            "Commercial Jetliner OEMs & Duopolies (Boeing, Airbus)",
            "Airport Ground Handling & In-Flight Catering Logistics",
        ],
        "downstream_positive": [
            "Online Travel Agencies - OTAs (Booking Holdings, MakeMyTrip)",
            "Luxury & Business Hotel REITs (Marriott, Indian Hotels - INDHOTEL.NS)",
            "Duty-Free & Airport Concession Operators",
        ],
        "negative_spillovers": [
            "Budget Rail Operators on Shorter Direct Corridors",
            "Commercial Video Conferencing Tools (Replaced by in-person dealmaking)",
        ],
        "typical_tickers": ["INDIGO.NS", "INDHOTEL.NS", "BA", "AIR.PA", "BKNG", "MMYT"]
    },
    "REAL_ESTATE_INFRA": {
        "title": "Real Estate, Industrial & Infrastructure Capex Boom",
        "description": "Sovereign infrastructure spend, residential housing demand, and manufacturing reshoring.",
        "upstream_positive": [
            "Cement & Clinker Grinders (UltraTech Cement, Holcim)",
            "Primary Steel & TMT Rebar Mills (Tata Steel, JSW Steel, Nucor)",
            "PVC Resins, Conduit Pipes & Industrial Cables (Polycab, Astral)",
        ],
        "midstream_positive": [
            "Heavy EPC & Construction Contractors (Larsen & Toubro - LT.NS, Caterpillar)",
            "Earthmoving, Cranes & Pre-Cast Concrete Engineering",
        ],
        "downstream_positive": [
            "Housing Finance & Mortgage Lenders (HDFC, Bajaj Housing)",
            "Architectural Decorative Paints (Asian Paints, Berger Paints)",
            "Vitrified Tiles, Bathware & Sanitary Fittings (Kajaria, Cera)",
        ],
        "negative_spillovers": [
            "High-Leverage Developers with Speculative Undeveloped Land Banks",
            "Unorganized Regional Subcontractors without Working Capital",
        ],
        "typical_tickers": ["LT.NS", "ULTRACEMCO.NS", "TATASTEEL.NS", "ASIANPAINT.NS", "POLYCAB.NS", "CAT"]
    },
    "DEFENSE_GEOPOLITICS": {
        "title": "Defense Modernization & Geopolitical Flashpoints",
        "description": "Escalating regional conflicts, NATO recapitalization, and chokepoint shipping diversion.",
        "upstream_positive": [
            "Specialty Titanium Alloys & Advanced Composites",
            "Radar, Electronic Warfare & Sensor Micro-optics",
            "Solid Rocket Propellant & Munitions Chemical Synthesizers",
        ],
        "midstream_positive": [
            "Defense Prime Contractors & Shipbuilders (Lockheed Martin, RTX, General Dynamics, HAL.NS, BEL.NS)",
            "Autonomous Drone & Loitering Munition Developers",
        ],
        "downstream_positive": [
            "Spot Container & Tanker Shipping Operators (Suez/Hormuz diversion Cape routing: Frontline, Maersk)",
            "War Risk Marine Insurers",
        ],
        "negative_spillovers": [
            "Commercial Air Freight routing through contested air corridors",
            "Just-In-Time Automotive Plants dependent on single-source maritime lanes",
        ],
        "typical_tickers": ["HAL.NS", "BEL.NS", "LMT", "RTX", "FRO", "ZIM"]
    }
}


def get_supply_chain_spillover(catalyst_keyword: str) -> Dict[str, List[str]]:
    """
    Returns positive and negative ticker/industry dependencies for a given catalyst theme.
    """
    kw = catalyst_keyword.upper().strip()

    # Search for match in graph keys or titles
    matched_graph = None
    for key, data in TRANSMISSION_GRAPHS.items():
        if key in kw or any(word in data["title"].upper() for word in kw.split()):
            matched_graph = data
            break

    if not matched_graph:
        # Default to AI / Tech or Infrastructure based on common queries
        if any(term in kw for term in ["CHIP", "TECH", "SEMICONDUCTOR", "SOFTWARE", "AI", "CLOUD"]):
            matched_graph = TRANSMISSION_GRAPHS["AI_DATACENTER"]
        elif any(term in kw for term in ["AUTO", "BATTERY", "LITHIUM", "CAR", "VEHICLE"]):
            matched_graph = TRANSMISSION_GRAPHS["EV_BATTERY"]
        elif any(term in kw for term in ["WAR", "ARMY", "MISSILE", "DEFENSE", "WEAPON"]):
            matched_graph = TRANSMISSION_GRAPHS["DEFENSE_GEOPOLITICS"]
        elif any(term in kw for term in ["FLIGHT", "TRAVEL", "AIRLINE", "HOTEL"]):
            matched_graph = TRANSMISSION_GRAPHS["AVIATION_TOURISM"]
        else:
            matched_graph = TRANSMISSION_GRAPHS["REAL_ESTATE_INFRA"]

    return {
        "theme": [matched_graph["title"]],
        "description": [matched_graph["description"]],
        "upstream_positive": matched_graph["upstream_positive"],
        "midstream_positive": matched_graph["midstream_positive"],
        "downstream_positive": matched_graph["downstream_positive"],
        "negative_spillovers": matched_graph["negative_spillovers"],
    }


def detect_company_catalyst(symbol: str, sector: str = "", industry: str = "") -> str:
    """
    Detects which macro transmission graph applies best to a specific ticker.
    """
    sym = symbol.upper()
    sec = sector.upper()
    ind = industry.upper()

    # Check direct ticker mappings
    for key, data in TRANSMISSION_GRAPHS.items():
        if any(sym.startswith(t.split(".")[0]) for t in data["typical_tickers"]):
            return key

    # Sector keyword matching
    if any(k in sec or k in ind for k in ["TECHNOLOGY", "SEMICONDUCTOR", "SOFTWARE", "ELECTRONIC"]):
        return "AI_DATACENTER"
    if any(k in sec or k in ind for k in ["AUTO", "VEHICLE", "BATTERY"]):
        return "EV_BATTERY"
    if any(k in sec or k in ind for k in ["AEROSPACE", "DEFENSE"]):
        return "DEFENSE_GEOPOLITICS"
    if any(k in sec or k in ind for k in ["AIRLINE", "HOTEL", "LEISURE", "TRAVEL"]):
        return "AVIATION_TOURISM"
    if any(k in sec or k in ind for k in ["CONSTRUCTION", "REAL ESTATE", "BUILDING", "BASIC MATERIALS", "STEEL"]):
        return "REAL_ESTATE_INFRA"

    return "REAL_ESTATE_INFRA"

