from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


ThematicHorizonType = Literal["1_YEAR", "3_YEARS", "5_YEARS", "10_YEARS", "20_YEARS"]
ScarcityType = Literal["WATER", "CLEAN_AIR", "ORE_DEPLETION", "POWER_GRID", "NONE"]


@dataclass
class ThematicHorizonDefinition:
    horizon_code: ThematicHorizonType
    title: str
    timeframe: str
    macro_catalyst: str
    anchor_beneficiaries: List[str]
    ancillary_beneficiaries: List[str]
    negative_spillovers: List[str] = field(default_factory=list)
    resource_scarcity: ScarcityType = "NONE"


@dataclass
class ThematicProfile:
    ticker: str
    horizon_code: ThematicHorizonType
    horizon_title: str
    thematic_driver: str
    role_in_theme: Literal["ANCHOR_OEM", "HIGH_LEVERAGE_ANCILLARY", "ECOSYSTEM_PARTICIPANT"]
    resource_scarcity_exposure: ScarcityType
    plain_english_takeaway: str
    timeframe: str = "Next 3 Years"


THEMATIC_HORIZONS: Dict[ThematicHorizonType, ThematicHorizonDefinition] = {
    "1_YEAR": ThematicHorizonDefinition(
        horizon_code="1_YEAR",
        title="Edge Hardware Deployment & Munitions Replenishment",
        timeframe="Next 1 Year",
        macro_catalyst="Monetary easing cycles; generative AI transitions from centralized cloud training to local on-device (edge) inference; global defense inventory replenishment.",
        anchor_beneficiaries=["TSM", "ASX", "MU", "LMT", "RHM.DE", "BEL.NS", "HAL.NS", "AAPL", "QCOM"],
        ancillary_beneficiaries=["ENTG", "KLAC", "6920.T", "HWM", "KAYNES.NS"],
        resource_scarcity="ORE_DEPLETION",
    ),
    "3_YEARS": ThematicHorizonDefinition(
        horizon_code="3_YEARS",
        title="The Power Wall, Grid Capex & Metabolic Health",
        timeframe="Next 3 Years",
        macro_catalyst="Electrical grids in industrial nations reach saturation from data centers and EV charging; commercial scaling of GLP-1 anti-obesity therapeutics.",
        anchor_beneficiaries=["ETN", "SU.PA", "ENR.DE", "ABBN.SW", "LLY", "NVO", "VRT", "MOD", "PWR"],
        ancillary_beneficiaries=["JSWSTEEL.NS", "5401.T", "PRY.MI", "NEX.PA", "WST", "GXI.DE", "LONN.SW"],
        negative_spillovers=["High-calorie snack food and packaged confectionery", "Conventional bariatric surgical equipment"],
        resource_scarcity="POWER_GRID",
    ),
    "5_YEARS": ThematicHorizonDefinition(
        horizon_code="5_YEARS",
        title="Commercial Autonomy, Nuclear Baseload & Solid-State Chemistry",
        timeframe="Next 5 Years",
        macro_catalyst="Fossil fuel plant retirements collide with continuous 24/7 uptime requirements for automation; initial commercial rollout of Level 4 autonomous vehicle fleets.",
        anchor_beneficiaries=["CEG", "CCJ", "BWXT", "GOOGL", "TSLA", "TATAMOTORS.NS", "MARUTI.NS"],
        ancillary_beneficiaries=["5631.T", "LEU", "CW", "ALB", "QS", "COHR", "LAZR", "SONACOMS.NS", "MOTHERSON.NS"],
        resource_scarcity="POWER_GRID",
    ),
    "10_YEARS": ThematicHorizonDefinition(
        horizon_code="10_YEARS",
        title="The Scarcity Era: Water, Topsoil & Humanoid Robotics",
        timeframe="Next 10 Years",
        macro_catalyst="Depletion of global freshwater aquifers (Ogallala, Indo-Gangetic basin); manufacturing working-age labor deficits resolved via bipedal humanoid robots.",
        anchor_beneficiaries=["6954.T", "6506.T", "005380.KS", "VIE.PA", "XYL"],
        ancillary_beneficiaries=["6324.T", "6268.T", "MOG.A", "ERII", "FLS", "SUN.SW", "LNN", "JISLJALEQS.NS", "WELCORP.NS"],
        resource_scarcity="WATER",
    ),
    "20_YEARS": ThematicHorizonDefinition(
        horizon_code="20_YEARS",
        title="Planetary Systems: Air Remediation, Longevity & Space Logistics",
        timeframe="Next 20 Years",
        macro_catalyst="Point-source and direct atmospheric carbon/particulate capture mandates; clinical senolytic cellular rejuvenation therapies; low-Earth orbit industrialization.",
        anchor_beneficiaries=["LIN", "AI.PA", "RKLB", "SPACEX", "VRTX", "CRSP"],
        ancillary_beneficiaries=["ZEOCHEM", "BAS.DE", "GTLS", "SRT.DE", "DHR", "BA.L", "MCHP", "LUNR"],
        resource_scarcity="CLEAN_AIR",
    ),
}


def audit_thematic_profile(symbol: str, sector: str = "", industry: str = "") -> ThematicProfile:
    """
    Evaluates which secular growth horizon and physical resource constraint a given equity participates in.
    """
    sym = symbol.upper().strip()
    sec = sector.upper().strip()
    ind = industry.upper().strip()

    # Direct ticker matching
    for code, h in THEMATIC_HORIZONS.items():
        clean_anchors = [t.split(".")[0] for t in h.anchor_beneficiaries]
        clean_ancillaries = [t.split(".")[0] for t in h.ancillary_beneficiaries]
        sym_base = sym.split(".")[0]

        if sym in h.anchor_beneficiaries or sym_base in clean_anchors:
            return ThematicProfile(
                ticker=symbol,
                horizon_code=code,
                horizon_title=h.title,
                thematic_driver=h.macro_catalyst[:100] + "...",
                role_in_theme="ANCHOR_OEM",
                resource_scarcity_exposure=h.resource_scarcity,
                plain_english_takeaway=f"Direct primary beneficiary of the {h.timeframe} secular wave: {h.title}.",
                timeframe=h.timeframe,
            )

        if sym in h.ancillary_beneficiaries or sym_base in clean_ancillaries:
            return ThematicProfile(
                ticker=symbol,
                horizon_code=code,
                horizon_title=h.title,
                thematic_driver=h.macro_catalyst[:100] + "...",
                role_in_theme="HIGH_LEVERAGE_ANCILLARY",
                resource_scarcity_exposure=h.resource_scarcity,
                plain_english_takeaway=f"High-operating-leverage supplier benefiting from the {h.timeframe} secular surge in {h.title}.",
                timeframe=h.timeframe,
            )

    # Sector / Industry heuristics if not explicitly listed
    if any(k in sec or k in ind for k in ["UTILITY", "POWER", "ELECTRICAL", "ENERGY"]):
        return ThematicProfile(
            ticker=symbol,
            horizon_code="3_YEARS",
            horizon_title=THEMATIC_HORIZONS["3_YEARS"].title,
            thematic_driver="Data center power demand and grid infrastructure upgrade supercycle.",
            role_in_theme="ECOSYSTEM_PARTICIPANT",
            resource_scarcity_exposure="POWER_GRID",
            plain_english_takeaway="Benefits from the multi-year grid upgrade and energy infrastructure buildout.",
            timeframe=THEMATIC_HORIZONS["3_YEARS"].timeframe,
        )

    if any(k in sec or k in ind for k in ["SEMICONDUCTOR", "CHIP", "DEFENSE", "AEROSPACE"]):
        return ThematicProfile(
            ticker=symbol,
            horizon_code="1_YEAR",
            horizon_title=THEMATIC_HORIZONS["1_YEAR"].title,
            thematic_driver="Hardware edge-AI deployment and global defense replenishment cycles.",
            role_in_theme="ECOSYSTEM_PARTICIPANT",
            resource_scarcity_exposure="ORE_DEPLETION",
            plain_english_takeaway="Poised to benefit from the immediate 1-year surge in hardware inference and sovereign defense contracts.",
            timeframe=THEMATIC_HORIZONS["1_YEAR"].timeframe,
        )

    if any(k in sec or k in ind for k in ["WATER", "AGRICULTURE", "MACHINERY", "ROBOT"]):
        return ThematicProfile(
            ticker=symbol,
            horizon_code="10_YEARS",
            horizon_title=THEMATIC_HORIZONS["10_YEARS"].title,
            thematic_driver="Global freshwater scarcity and manufacturing automation.",
            role_in_theme="ECOSYSTEM_PARTICIPANT",
            resource_scarcity_exposure="WATER",
            plain_english_takeaway="Positioned to capture value as water infrastructure and robotics become essential over the next decade.",
            timeframe=THEMATIC_HORIZONS["10_YEARS"].timeframe,
        )

    # Default fallback: Horizon 2 (Power Wall & Digital Infrastructure)
    return ThematicProfile(
        ticker=symbol,
        horizon_code="3_YEARS",
        horizon_title=THEMATIC_HORIZONS["3_YEARS"].title,
        thematic_driver="General industrial modernization, electrification, and enterprise digitization.",
        role_in_theme="ECOSYSTEM_PARTICIPANT",
        resource_scarcity_exposure="POWER_GRID",
        plain_english_takeaway="Riding ongoing macro investments in digital transformation and energy efficiency.",
        timeframe=THEMATIC_HORIZONS["3_YEARS"].timeframe,
    )
