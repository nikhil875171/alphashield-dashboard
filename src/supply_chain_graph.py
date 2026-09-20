from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import networkx as nx
import plotly.graph_objects as go


@dataclass
class SupplierRippleResult:
    ticker: str
    role: str  # "ANCHOR_OEM", "TIER_1", "TIER_2", "TIER_3"
    case_name: str
    case_description: str
    connected_anchors: List[str]
    upstream_dependencies: List[str]
    downstream_beneficiaries: List[str]
    ripple_explanation: str
    operating_leverage_summary: str


def build_supply_chain_network() -> nx.DiGraph:
    """
    Constructs the master directed multi-tier supply chain network using NetworkX.
    Edges represent directed demand flow: Anchor OEM -> Tier 1 -> Tier 2 -> Tier 3.
    """
    G = nx.DiGraph()

    # --- CASE A: The Automotive & EV Scale-Up ---
    anchors_ev = ["TSLA", "TATAMOTORS.NS", "MARUTI.NS"]
    for a in anchors_ev:
        G.add_node(a, tier="ANCHOR_OEM", label=a, case="EV & Automotive Scale-Up", desc="Automotive OEM assembling finished vehicles")

    # Tier 1
    tier1_ev = [
        ("MOTHERSON.NS", "Samvardhana Motherson", "High-Voltage Wiring Harnesses (3x-5x ICE value)"),
        ("APTV", "Aptiv PLC", "High-Voltage Signal Distribution & Architecture"),
        ("SUBROS.NS", "Subros Ltd", "Thermal Management Loops & EV Chillers"),
    ]
    for sym, name, component in tier1_ev:
        G.add_node(sym, tier="TIER_1", label=f"{sym} ({name})", case="EV & Automotive Scale-Up", desc=component)
        for a in anchors_ev:
            G.add_edge(a, sym, relationship="Supplies Sub-Assemblies to")

    # Tier 2
    tier2_ev = [
        ("SONACOMS.NS", "Sona BLW", "Differential Gears, e-Axles & Starter Motors"),
        ("BWA", "BorgWarner", "Dual-Clutch & Electric Drive Transmission Units"),
    ]
    for sym, name, component in tier2_ev:
        G.add_node(sym, tier="TIER_2", label=f"{sym} ({name})", case="EV & Automotive Scale-Up", desc=component)
        G.add_edge("MOTHERSON.NS", sym, relationship="Procures Precision Modules from")
        G.add_edge("APTV", sym, relationship="Integrates Modules from")

    # Tier 3
    tier3_ev = [
        ("MP", "MP Materials", "NdPr Rare Earth Permanent Magnets for EV Motors"),
        ("JSWSTEEL.NS", "JSW Steel", "Non-Grain Oriented Electrical Steel (CRNO) for Stators"),
    ]
    for sym, name, component in tier3_ev:
        G.add_node(sym, tier="TIER_3", label=f"{sym} ({name})", case="EV & Automotive Scale-Up", desc=component)
        G.add_edge("SONACOMS.NS", sym, relationship="Sources Magnetic/Steel Feedstock from")
        G.add_edge("BWA", sym, relationship="Sources Feedstock from")

    # --- CASE B: The $10B Hyperscale AI Data Center Campus ---
    anchors_ai = ["MSFT", "AMZN", "GOOGL", "META"]
    for a in anchors_ai:
        G.add_node(a, tier="ANCHOR_OEM", label=a, case="Hyperscale AI Datacenter", desc="Cloud Hyperscaler Capex Deployer")

    # Tier 1
    tier1_ai = [
        ("VRT", "Vertiv Holdings", "Coolant Distribution Units (CDUs) & Liquid Cooling"),
        ("MOD", "Modine Manufacturing", "High-Density Liquid Chillers & Air Handlers"),
        ("ETN", "Eaton Corporation", "High-Voltage Switchgear, Transformers & Power Distribution"),
    ]
    for sym, name, component in tier1_ai:
        G.add_node(sym, tier="TIER_1", label=f"{sym} ({name})", case="Hyperscale AI Datacenter", desc=component)
        for a in anchors_ai:
            G.add_edge(a, sym, relationship="Awards Infrastructure Contracts to")

    # Tier 2
    tier2_ai = [
        ("COHR", "Coherent Corp", "800G & 1.6T Silicon Photonics Optical Transceivers"),
        ("CAT", "Caterpillar Inc", "Industrial Mission-Critical Diesel/Gas Backup Gensets"),
    ]
    for sym, name, component in tier2_ai:
        G.add_node(sym, tier="TIER_2", label=f"{sym} ({name})", case="Hyperscale AI Datacenter", desc=component)
        G.add_edge("VRT", sym, relationship="Integrates Hardware with")
        G.add_edge("ETN", sym, relationship="Coordinates Electrical Microgrid with")

    # Tier 3
    tier3_ai = [
        ("NVDA", "NVIDIA Corporation", "Core Parallel Acceleration Silicon & NVLink Interconnect"),
        ("TSM", "TSMC", "Advanced 3nm/2nm Foundries & CoWoS Packaging"),
    ]
    for sym, name, component in tier3_ai:
        G.add_node(sym, tier="TIER_3", label=f"{sym} ({name})", case="Hyperscale AI Datacenter", desc=component)
        G.add_edge("COHR", sym, relationship="Interfaces High-Speed Optical with")
        G.add_edge("NVDA", "TSM", relationship="Manufactures Custom Silicon at")

    # --- CASE C: Municipal Water Desalination Project ---
    anchors_water = ["EPC_MUNICIPAL", "XYL"]
    G.add_node("EPC_MUNICIPAL", tier="ANCHOR_OEM", label="Municipal Water Authority", case="Water Desalination & Treatment", desc="Sovereign Public Works Sponsor")
    G.add_node("XYL", tier="TIER_1", label="Xylem (XYL)", case="Water Desalination & Treatment", desc="Global Water Systems Engineering & Integrator")
    G.add_edge("EPC_MUNICIPAL", "XYL", relationship="Awards Desalination EPC to")

    tier2_water = [
        ("ERII", "Energy Recovery Inc", "Pressure Exchangers (Recovers 60% of pumping energy)"),
        ("FLS", "Flowserve Corp", "High-Pressure Slurry & Brine Injection Pumps"),
    ]
    for sym, name, component in tier2_water:
        G.add_node(sym, tier="TIER_2", label=f"{sym} ({name})", case="Water Desalination & Treatment", desc=component)
        G.add_edge("XYL", sym, relationship="Procures Energy Recovery Technology from")

    tier3_water = [
        ("DD", "DuPont de Nemours", "FilmTec Reverse Osmosis Thin-Film Composite Membranes"),
        ("WELCORP.NS", "Welspun Corp", "High-Pressure Helical Submerged Arc-Welded Ductile Piping"),
    ]
    for sym, name, component in tier3_water:
        G.add_node(sym, tier="TIER_3", label=f"{sym} ({name})", case="Water Desalination & Treatment", desc=component)
        G.add_edge("ERII", sym, relationship="Houses Membranes & High-Pressure Plumbing from")
        G.add_edge("FLS", sym, relationship="Pumps Fluid Through Heavy Piping from")

    return G


def get_supplier_ripple_effect(ticker: str) -> SupplierRippleResult:
    """
    Identifies the target company's position in the global supply chain, its anchor OEM drivers,
    and operating leverage multiplier.
    """
    G = build_supply_chain_network()
    sym = ticker.upper().strip()

    if sym in G.nodes:
        node_data = G.nodes[sym]
        tier = node_data.get("tier", "TIER_1")
        case_name = node_data.get("case", "Global Secular Transmission")
        desc = node_data.get("desc", "Component Manufacturer")

        # Find upstream parents (who drives demand to this company)
        pred = list(G.predecessors(sym))
        # Find downstream successors (who receives components from this company)
        succ = list(G.successors(sym))

        anchors = [p for p in pred if G.nodes[p].get("tier") == "ANCHOR_OEM"] or pred

        if tier == "ANCHOR_OEM":
            leverage_text = "Anchor OEM commanding direct pricing power and deploying mega-capex budgets."
            ripple = f"When {sym} expands its production volume, orders cascade immediately down to Tier-1, Tier-2, and Tier-3 suppliers."
        elif tier == "TIER_1":
            leverage_text = "High Operating Leverage: Fixed assembly plants mean revenue growth expands operating margins by 1.8x - 2.5x."
            ripple = f"Directly contracted by {', '.join(anchors[:2])}. An order ramp of 500k units creates massive unutilized capacity fill."
        elif tier == "TIER_2":
            leverage_text = "Maximum Margin Expansion: Specialized precision manufacturing enjoys 2.2x - 3.2x operating leverage."
            ripple = f"Essential precision tier contracted by Tier-1 integrators. High barrier to entry protects pricing power."
        else:
            leverage_text = "Commodity/Feedstock Tier: High volume absorption, sensitive to input material pricing."
            ripple = f"Critical chemical, metallurgical, or silicon foundation without which assembly stops completely."

        return SupplierRippleResult(
            ticker=sym,
            role=tier,
            case_name=case_name,
            case_description=desc,
            connected_anchors=anchors if anchors else ["Broad Global OEMs"],
            upstream_dependencies=pred,
            downstream_beneficiaries=succ,
            ripple_explanation=ripple,
            operating_leverage_summary=leverage_text,
        )

    # Heuristic fallback for tickers not in the pre-programmed 4 cases
    return SupplierRippleResult(
        ticker=sym,
        role="TIER_1",
        case_name="Global Industrial & Technology Value Chain",
        case_description="Direct product and service supplier to enterprise end-markets.",
        connected_anchors=["Global Industry Leaders"],
        upstream_dependencies=["Enterprise Customer Capex"],
        downstream_beneficiaries=["Component & Raw Material Feedstock"],
        ripple_explanation=f"Participates in industrial supply chain transmission, benefiting from enterprise spending cycles.",
        operating_leverage_summary="Moderate Operating Leverage (1.4x): Scales margins with broader economic activity.",
    )


def render_interactive_network_graph(highlight_ticker: Optional[str] = None) -> go.Figure:
    """
    Renders an interactive Plotly node-link network visualization of the supply chain.
    """
    G = build_supply_chain_network()
    # Compute spring layout positions
    pos = nx.spring_layout(G, k=0.6, iterations=40, seed=42)

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.0, color="rgba(148, 163, 184, 0.4)"),
        hoverinfo="none",
        mode="lines"
    )

    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []

    tier_colors = {
        "ANCHOR_OEM": "#38BDF8",  # Sky Blue
        "TIER_1": "#10B981",      # Emerald Green
        "TIER_2": "#F59E0B",      # Amber Yellow
        "TIER_3": "#E040FB",      # Purple Magenta
    }

    target_sym = highlight_ticker.upper().strip() if highlight_ticker else ""

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        data = G.nodes[node]
        tier = data.get("tier", "TIER_1")
        case = data.get("case", "")
        desc = data.get("desc", "")

        is_target = (node == target_sym or node.startswith(target_sym.split(".")[0]))
        color = "#FF1744" if is_target else tier_colors.get(tier, "#94A3B8")
        size = 24 if is_target else (18 if tier == "ANCHOR_OEM" else 14)

        node_color.append(color)
        node_size.append(size)
        node_text.append(f"<b>{node}</b><br>Role: {tier}<br>Theme: {case}<br>Details: {desc}")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=[n for n in G.nodes()],
        textposition="top center",
        hovertext=node_text,
        textfont=dict(size=10, color="#CBD5E1"),
        marker=dict(
            color=node_color,
            size=node_size,
            line=dict(width=2, color="#0F172A")
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text="<b>Interactive Multi-Tier Supply Chain Ripple Graph</b><br><sup>Anchor OEMs (Blue) → Tier-1 Sub-Assemblies (Green) → Tier-2 Precision Modules (Yellow) → Tier-3 Feedstock (Purple)</sup>",
                font=dict(size=13, color="#F8FAFC")
            ),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=20, r=20, t=50),
            paper_bgcolor="#0E1117",
            plot_bgcolor="#131722",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=500
        )
    )

    return fig
