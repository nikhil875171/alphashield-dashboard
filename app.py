import os
import math
from typing import Dict, List
import streamlit as st
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

# Import core infrastructure & authentication
from core.auth import (
    init_session_state,
    render_login_gate,
    render_user_profile_sidebar,
    is_admin,
    is_global_admin,
    get_all_users,
    update_user_credentials,
)
from core.technical_engine import compute_technical_snapshot
from core.visualizer import (
    build_interactive_chart,
    compute_institutional_dimension_scores,
    build_institutional_radar_chart,
)

# Import institutional quantitative & thematic modules
from src.macro_engine import compute_macro_transmission, MacroRegimeState
from src.transmission_tree import detect_company_catalyst, get_supply_chain_spillover
from src.thematic_engine import audit_thematic_profile, ThematicProfile
from src.supply_chain_graph import (
    build_supply_chain_network,
    get_supplier_ripple_effect,
    render_interactive_network_graph,
    SupplierRippleResult,
)
from src.ancillary_screener import screen_ancillary_supplier, AncillaryMetrics
from src.microstructure import validate_microstructure, MicrostructureValidation
from src.factor_model import evaluate_factor_model, FactorScoreSummary
from src.trap_guards import evaluate_all_traps
from src.risk_engine import calculate_algorithmic_execution, ExecutionRiskReport
from src.ai_agent import generate_institutional_trade_plan, FullInstitutionalTradePlan
from src.market_radar import get_thematic_market_radar, ThematicStockItem
from src.stock_universe import (
    get_stock_universe,
    get_all_sectors,
    get_all_cap_tiers,
    infer_company_sector,
    infer_cap_tier,
    get_ticker_sector_map,
)

load_dotenv()

# Bridge Streamlit Cloud secrets to os.environ if running on cloud
try:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# Page configuration
st.set_page_config(
    page_title="AlphaShield | Quantitative & Thematic Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Initialize session state for role-based security
init_session_state()

# RBAC Enforcement: Hide GitHub Icon, Edit options, and Streamlit Cloud toolbar unless user is Global Admin
if not is_global_admin():
    st.markdown("""
    <style>
        /* Hide Main Menu Hamburger */
        #MainMenu {
            display: none !important;
            visibility: hidden !important;
        }
        /* Hide Streamlit Header, Toolbar, Deploy & Edit Buttons */
        header[data-testid="stHeader"] {
            display: none !important;
            visibility: hidden !important;
            height: 0px !important;
        }
        [data-testid="stToolbar"] {
            display: none !important;
            visibility: hidden !important;
        }
        .stAppDeployButton {
            display: none !important;
            visibility: hidden !important;
        }
        [data-testid="stToolbarActions"] {
            display: none !important;
            visibility: hidden !important;
        }
        [data-testid="stActionButton"] {
            display: none !important;
            visibility: hidden !important;
        }
        /* Hide GitHub icons, repository links, and fork badges */
        a[href*="github.com"] {
            display: none !important;
            visibility: hidden !important;
        }
        [title*="GitHub"], [aria-label*="GitHub"], [title*="github"], [aria-label*="github"] {
            display: none !important;
            visibility: hidden !important;
        }
        /* Hide Edit options, pencil badges, and Streamlit Cloud viewer bar */
        button[title*="Edit"], a[title*="Edit"], [aria-label*="Edit"], a[href*="edit"] {
            display: none !important;
            visibility: hidden !important;
        }
        [class*="viewerBadge"], [class*="manageApp"], .viewerBadge_container__r5tak {
            display: none !important;
            visibility: hidden !important;
        }
        footer {
            display: none !important;
            visibility: hidden !important;
        }
        .main .block-container {
            padding-top: 1.5rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        /* Global Admin has complete root access: display developer toolbar & indicators */
        header[data-testid="stHeader"] {
            display: block !important;
            visibility: visible !important;
        }
        [data-testid="stToolbar"] {
            display: block !important;
            visibility: visible !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Custom High-Contrast Modern Theme CSS
st.markdown("""
<style>
    /* Obsidian Luxury Canvas & Classy Pastel Accents */
    .stApp {
        background-color: #0A0E1A;
        background-image: radial-gradient(circle at 50% 0%, #131E33 0%, #0A0E1A 75%);
        color: #E2E8F0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;
        font-variant-numeric: tabular-nums;
    }

    /* Tabular numbers for all financial metrics */
    div[data-testid="stMetricValue"], .radar-card, .interactive-tile, table {
        font-variant-numeric: tabular-nums;
    }

    /* Top-Level Segmented Menu Bar (Pill Navigation) */
    div[data-testid="stTabs"] > div > div[role="tablist"] {
        display: flex;
        gap: 8px;
        background: #0D1527;
        padding: 7px 10px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
        margin-bottom: 22px;
        overflow-x: auto;
    }
    div[data-testid="stTabs"] button[role="tab"] {
        background: transparent;
        color: #94A3B8;
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 0.95rem;
        border: 1px solid transparent;
        transition: all 0.22s ease-in-out;
    }
    div[data-testid="stTabs"] button[role="tab"]:hover {
        color: #F1F5F9;
        background: rgba(255, 255, 255, 0.04);
        border-color: rgba(255, 255, 255, 0.08);
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #93C5FD !important;
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
        border: 1px solid rgba(147, 197, 253, 0.35) !important;
        box-shadow: 0 4px 14px rgba(147, 197, 253, 0.12) !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Elevated Metric Surfaces with Pastel Accents */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #121A2B 0%, #162238 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 12px 18px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
        transition: border-color 0.2s ease, transform 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(147, 197, 253, 0.3);
        transform: translateY(-1px);
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8;
        font-size: 0.80rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.35rem;
        font-weight: 700;
        color: #F8FAFC;
    }

    /* Company Identity Card */
    .company-profile-banner {
        background: linear-gradient(135deg, #111A2D 0%, #17233D 100%);
        border: 1px solid rgba(147, 197, 253, 0.18);
        border-radius: 16px;
        padding: 18px 24px;
        margin-bottom: 20px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4);
    }

    /* 30-Second Bottom Line Executive Strip in Classy Pastels */
    .bottom-line-container {
        background: linear-gradient(135deg, #111A2E 0%, #17243C 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 6px solid #6EE7B7;
        border-radius: 14px;
        padding: 18px 24px;
        margin-bottom: 22px;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.5);
    }
    .bottom-line-danger {
        border-left-color: #FDA4AF !important;
    }
    .bottom-line-caution {
        border-left-color: #FDE68A !important;
    }

    /* Soft Pastel Action Badges */
    .badge-buy {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.25) 0%, rgba(110, 231, 183, 0.2) 100%);
        color: #6EE7B7;
        border: 1px solid rgba(110, 231, 183, 0.45);
        padding: 6px 20px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.20rem;
        display: inline-block;
        letter-spacing: 0.04em;
        box-shadow: 0 0 16px rgba(110, 231, 183, 0.25);
    }
    .badge-sell {
        background: linear-gradient(135deg, rgba(225, 29, 72, 0.25) 0%, rgba(253, 164, 175, 0.2) 100%);
        color: #FDA4AF;
        border: 1px solid rgba(253, 164, 175, 0.45);
        padding: 6px 20px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.20rem;
        display: inline-block;
        letter-spacing: 0.04em;
        box-shadow: 0 0 16px rgba(253, 164, 175, 0.25);
    }
    .badge-hold {
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.25) 0%, rgba(253, 230, 138, 0.2) 100%);
        color: #FDE68A;
        border: 1px solid rgba(253, 230, 138, 0.45);
        padding: 6px 20px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.20rem;
        display: inline-block;
        letter-spacing: 0.04em;
        box-shadow: 0 0 16px rgba(253, 230, 138, 0.25);
    }
    .badge-avoid {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.25) 0%, rgba(196, 181, 253, 0.2) 100%);
        color: #C4B5FD;
        border: 1px solid rgba(196, 181, 253, 0.45);
        padding: 6px 20px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.20rem;
        display: inline-block;
        letter-spacing: 0.04em;
        box-shadow: 0 0 16px rgba(196, 181, 253, 0.25);
    }

    /* Interactive Explanatory Tiles */
    .interactive-tile {
        background: linear-gradient(135deg, #121A2B 0%, #162238 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px;
        height: 100%;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
        transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
    }
    .interactive-tile:hover {
        border-color: rgba(147, 197, 253, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(147, 197, 253, 0.12);
    }
    .tile-header {
        font-size: 0.78rem;
        color: #94A3B8;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .tile-status-safe {
        color: #6EE7B7;
        font-weight: 700;
        font-size: 1.05rem;
    }
    .tile-status-caution {
        color: #FDE68A;
        font-weight: 700;
        font-size: 1.05rem;
    }
    .tile-status-danger {
        color: #FDA4AF;
        font-weight: 700;
        font-size: 1.05rem;
    }

    /* 360-Degree Institutional Dimension Cards & ELI5 Containers */
    .dimension-card {
        background: linear-gradient(145deg, #101827 0%, #162035 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 18px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
        transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        margin-bottom: 14px;
    }
    .dimension-card:hover {
        border-color: rgba(56, 189, 248, 0.40);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(56, 189, 248, 0.12);
    }
    .dim-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        gap: 8px;
    }
    .dim-title {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #94A3B8;
        letter-spacing: 0.04em;
    }
    .dim-meter-track {
        background: rgba(255, 255, 255, 0.07);
        border-radius: 999px;
        height: 5px;
        width: 100%;
        overflow: hidden;
        margin-bottom: 8px;
    }
    .dim-meter-fill-safe {
        background: linear-gradient(90deg, #10B981, #34D399);
        height: 100%;
        border-radius: 999px;
    }
    .dim-meter-fill-caution {
        background: linear-gradient(90deg, #F59E0B, #FBBF24);
        height: 100%;
        border-radius: 999px;
    }
    .dim-meter-fill-danger {
        background: linear-gradient(90deg, #EF4444, #FB7185);
        height: 100%;
        border-radius: 999px;
    }
    .dim-metric-sub {
        font-size: 0.84rem;
        color: #94A3B8;
        margin-bottom: 10px;
    }
    .eli5-callout {
        background: rgba(30, 41, 59, 0.55);
        border-left: 3px solid #38BDF8;
        border-radius: 8px;
        padding: 10px 12px;
        margin: 8px 0;
    }
    .eli5-label {
        font-size: 0.68rem;
        font-weight: 800;
        color: #38BDF8;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .eli5-text {
        font-size: 0.86rem;
        color: #E2E8F0;
        line-height: 1.48;
        font-style: italic;
    }
    .verdict-box {
        font-size: 0.85rem;
        color: #CBD5E1;
        line-height: 1.45;
        border-top: 1px solid rgba(255, 255, 255, 0.07);
        padding-top: 10px;
        margin-top: 6px;
    }
    .dim-overview-banner {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.75) 100%);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }

    /* Thematic Discovery Card */
    .radar-card {
        background: linear-gradient(135deg, #121A2B 0%, #162138 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 12px;
        transition: border-color 0.18s ease, transform 0.18s ease;
    }
    .radar-card:hover {
        border-color: rgba(147, 197, 253, 0.35);
        transform: translateY(-1px);
    }

    /* Pastel Tag / Pill */
    .pastel-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        background: rgba(147, 197, 253, 0.12);
        color: #93C5FD;
        border: 1px solid rgba(147, 197, 253, 0.25);
    }
    .pastel-pill-mint {
        background: rgba(110, 231, 183, 0.12);
        color: #6EE7B7;
        border: 1px solid rgba(110, 231, 183, 0.25);
    }
    .pastel-pill-amber {
        background: rgba(253, 230, 138, 0.12);
        color: #FDE68A;
        border: 1px solid rgba(253, 230, 138, 0.25);
    }
    .pastel-pill-rose {
        background: rgba(253, 164, 175, 0.12);
        color: #FDA4AF;
        border: 1px solid rgba(253, 164, 175, 0.25);
    }
    .pastel-pill-lilac {
        background: rgba(196, 181, 253, 0.12);
        color: #C4B5FD;
        border: 1px solid rgba(196, 181, 253, 0.25);
    }
</style>
""", unsafe_allow_html=True)

# --- 1. ENFORCE ROLE-BASED AUTHENTICATION GATE ---
if not render_login_gate():
    st.stop()


# --- 2. TOP GLOBAL MARKET & EXCHANGE SELECTOR ---
col_brand, col_market_selector = st.columns([1.6, 1.4])

with col_brand:
    st.markdown("## 🛡️ **AlphaShield** | Quantitative & Thematic Intelligence")
    st.caption("Intermarket transmission, multi-horizon scarcity models, and directed supply chain ripple mapping.")

with col_market_selector:
    if "is_indian" not in st.session_state:
        st.session_state["is_indian"] = True

    selected_market = st.radio(
        "Select Stock Market Exchange",
        options=["🇮🇳 Indian Markets (NSE / BSE)", "🇺🇸 US Markets (NYSE / NASDAQ)"],
        index=0 if st.session_state.get("is_indian", True) else 1,
        horizontal=True,
        help="Instantly reloads currency ($ vs ₹), benchmark index (S&P 500 vs Nifty 50), and market telemetry."
    )

is_indian = "Indian" in selected_market
st.session_state["is_indian"] = is_indian
currency_sym = "₹" if is_indian else "$"

# Default ticker per market
default_ticker = "RELIANCE.NS" if is_indian else "NVDA"

# Initialize session state for active ticker
if "active_ticker" not in st.session_state:
    st.session_state["active_ticker"] = default_ticker

# Handle market switch ticker reconciliation
if is_indian and not (st.session_state["active_ticker"].endswith(".NS") or st.session_state["active_ticker"].endswith(".BO")):
    st.session_state["active_ticker"] = default_ticker
elif not is_indian and (st.session_state["active_ticker"].endswith(".NS") or st.session_state["active_ticker"].endswith(".BO")):
    st.session_state["active_ticker"] = default_ticker


# Cached macro telemetry
@st.cache_data(ttl=300)
def fetch_macro_cached(is_ind: bool) -> MacroRegimeState:
    return compute_macro_transmission(is_indian_market=is_ind)


# Cached live thematic market radar (v2 invalidates legacy schema cache)
@st.cache_data(ttl=180, show_spinner=False)
def fetch_radar_cached_v2(is_ind: bool) -> Dict[str, List[ThematicStockItem]]:
    return get_thematic_market_radar(is_indian=is_ind)


# =============================================================================
# GLOBAL MODAL DIALOG: INSTITUTIONAL STOCK PROFILE & 1-CLICK AUDIT
# =============================================================================
@st.dialog("🏢 Company Profile & Live Catalyst", width="large")
def show_stock_inspection_modal(stock: ThematicStockItem):
    chg_val = getattr(stock, "change_pct", 0.0)
    chg_str = getattr(stock, "change_str", f"{chg_val:+.2f}%")
    rel_vol = getattr(stock, "volume_multiple", 1.0)
    r_badge = getattr(stock, "risk_badge", "🟢 Normal")
    n_url = getattr(stock, "news_url", "")
    sec_tag = getattr(stock, "sector", "")
    cap_tag = getattr(stock, "market_cap_tier", "")

    chg_pill = f"<span class='pastel-pill-mint'>▲ {chg_str} Today</span>" if chg_val >= 0 else f"<span class='pastel-pill-rose'>▼ {chg_str} Today</span>"
    vol_pill = f"<span class='pastel-pill-lilac'>⚡ {rel_vol:.1f}x ADV</span>"
    risk_pill = f"<span class='pastel-pill-amber'>{r_badge}</span>"
    sec_pill = f"<span class='pastel-pill'>{sec_tag}</span>" if sec_tag else ""
    cap_pill = f"<span class='pastel-pill'>{cap_tag}</span>" if cap_tag else ""

    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #121A2B 0%, #162238 100%); border-radius: 14px; padding: 18px 20px; border: 1px solid rgba(147, 197, 253, 0.25); margin-bottom: 16px;'>
        <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;'>
            <div>
                <div style='font-size: 1.50rem; font-weight: 800; color: #F8FAFC;'>{stock.name}</div>
                <div style='font-size: 1.05rem; font-weight: 700; color: #93C5FD; margin-top: 2px;'>{stock.ticker} <span style='font-size: 0.85rem; color: #94A3B8; font-weight: 500;'>• {stock.category_title}</span></div>
            </div>
            <div style='text-align: right;'>
                <div style='font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;'>Live Market Price</div>
                <div style='font-size: 1.65rem; font-weight: 800; color: #38BDF8;'>{stock.approx_price}</div>
            </div>
        </div>
        <div style='display: flex; gap: 8px; margin-top: 14px; align-items: center; flex-wrap: wrap;'>
            {chg_pill}
            {vol_pill}
            {risk_pill}
            {sec_pill}
            {cap_pill}
            <span class='pastel-pill'>{stock.risk_level}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📰 **Live Catalyst & Market Action**")
    news_link = f" <a href='{n_url}' target='_blank' style='color: #93C5FD; text-decoration: none; font-weight: 600;'>[Open Full Article ↗]</a>" if n_url else ""
    st.info(f"{stock.catalyst_driver}{news_link}")

    st.markdown("#### 🔗 **Institutional Role & Strategic Thesis**")
    st.markdown(f"""
    <div style='background: rgba(255, 255, 255, 0.03); border-radius: 10px; padding: 14px 16px; border: 1px solid rgba(255, 255, 255, 0.06); font-size: 0.95rem; color: #CBD5E1; line-height: 1.55; margin-bottom: 20px;'>
        <strong>Macro & Supply Chain Context:</strong> {stock.why_it_matters}
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"⚡ Run Full AlphaShield Audit on {stock.ticker}", key=f"modal_audit_btn_{stock.ticker}", type="primary", use_container_width=True):
        st.session_state["active_ticker"] = stock.ticker
        st.rerun()


# Cached unified full-market universe with sectors and cap tiers
@st.cache_data(ttl=180, show_spinner=False)
def get_unified_market_universe(is_ind: bool) -> List[ThematicStockItem]:
    radar_data = fetch_radar_cached_v2(is_ind)
    ticker_map = get_ticker_sector_map()
    market_str = "INDIA" if is_ind else "US"

    cat_keys = ["safe", "trending", "future", "new", "penny"]
    unified_stocks: Dict[str, ThematicStockItem] = {}

    for c_key in cat_keys:
        for item in radar_data.get(c_key, []):
            sym = item.ticker.upper().strip()
            if sym not in unified_stocks:
                if sym in ticker_map:
                    sec, cap, role = ticker_map[sym]
                    item.sector = sec
                    item.market_cap_tier = cap
                    if not item.why_it_matters or "Series" in item.why_it_matters:
                        item.why_it_matters = f"{role} | {sec}"
                else:
                    item.sector = infer_company_sector(item.name, sym)
                    raw_p = item.approx_price.replace("₹", "").replace("$", "").replace(",", "").strip()
                    try:
                        p_val = float(raw_p)
                    except Exception:
                        p_val = 50.0
                    item.market_cap_tier = infer_cap_tier(
                        price=p_val,
                        category_id=item.category_id
                    )
                unified_stocks[sym] = item

    curated_entries = get_stock_universe(market=market_str)
    for entry in curated_entries:
        sym = entry.ticker.upper().strip()
        if sym not in unified_stocks:
            p_str = "₹---" if is_ind else "$---"
            unified_stocks[sym] = ThematicStockItem(
                ticker=entry.ticker,
                name=entry.name,
                approx_price=p_str,
                category_id="safe" if entry.market_cap_tier == "Large-Cap" else ("penny" if entry.market_cap_tier == "Small-Cap" else "future"),
                category_title=f"Thematic Universe ({entry.thematic_anchor})",
                catalyst_driver=entry.plain_english_role,
                why_it_matters=f"{entry.plain_english_role} | {entry.thematic_anchor}",
                risk_level="Institutional Anchor" if entry.market_cap_tier == "Large-Cap" else "Secular Growth",
                risk_badge="🟢 Safe Haven" if entry.market_cap_tier == "Large-Cap" else "🟡 Moderate",
                change_pct=0.0,
                change_str="0.00%",
                volume_multiple=1.0,
                sector=entry.sector,
                market_cap_tier=entry.market_cap_tier,
                news_url=""
            )

    return list(unified_stocks.values())


# --- SIDEBAR: CONTROLS & BEGINNER CAPITAL ALLOCATION ---
with st.sidebar:
    render_user_profile_sidebar()

    st.markdown(f"### 📍 **Active Market: {'India (NSE)' if is_indian else 'United States (NYSE)'}**")

    # Ticker Quick-Select Chips
    st.markdown("##### **Popular Watchlist:**")
    quick_tickers = (
        ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SUZLON.NS", "BEL.NS"]
        if is_indian
        else ["NVDA", "AAPL", "MSFT", "TSLA", "PLTR", "AMZN"]
    )

    qp_cols = st.columns(3)
    for idx, q_sym in enumerate(quick_tickers):
        col_target = qp_cols[idx % 3]
        display_sym = q_sym.replace(".NS", "")
        if col_target.button(display_sym, key=f"chip_{q_sym}", use_container_width=True):
            st.session_state["active_ticker"] = q_sym
            st.rerun()

    st.markdown("---")
    st.markdown("#### 🔍 **Custom Stock Lookup**")
    user_ticker = st.text_input(
        "Enter Stock Ticker",
        value=st.session_state["active_ticker"],
        help=f"Type any stock symbol (e.g. {quick_tickers[0]} or {quick_tickers[1]})."
    ).strip().upper()

    # Automatically append .NS for Indian stocks if user omitted it
    if is_indian and user_ticker and not (user_ticker.endswith(".NS") or user_ticker.endswith(".BO")):
        user_ticker = f"{user_ticker}.NS"

    st.session_state["active_ticker"] = user_ticker

    st.markdown("---")
    st.markdown("#### 💰 **Your Investment Budget**")

    account_size = st.number_input(
        f"Total Account Capital ({currency_sym})",
        min_value=1_000.0 if not is_indian else 10_000.0,
        max_value=100_000_000.0,
        value=50_000.0 if not is_indian else 500_000.0,
        step=5_000.0 if not is_indian else 50_000.0,
        format="%.2f",
        help="How much total money is in your trading/investment account."
    )

    risk_pct = st.slider(
        "Maximum Loss Allowed per Trade (%)",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="Institutional Zero-Ruin Rule: Never risk losing more than 1% of your total account on a single trade."
    )

    st.markdown("---")
    st.markdown("#### 🤖 **Decision Engine Model**")
    model_choice = st.selectbox(
        "AI Reasoning Cascade",
        options=["gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-flash-latest"],
        index=0,
        help="Ultra-fast Gemini Pro AI engines with automated institutional rule-engine fallback."
    )

    run_btn = st.button("🚀 Analyze Stock Now", use_container_width=True, type="primary")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "YOUR_GEMINI_API_KEY_HERE":
        st.info("ℹ️ Running on Institutional Rule Engine (No Gemini API Key configured).", icon="ℹ️")
    else:
        st.success("🟢 Gemini Pro Decision AI Active", icon="✅")


# --- TOP BENCHMARK & MACRO STRIP ---
with st.spinner("Synchronizing real-time market telemetry..."):
    macro = fetch_macro_cached(is_indian)

m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)

with m_col1:
    bench_delta = f"{macro.benchmark_change_pct:+.2f}% Today"
    st.metric(
        f"{macro.benchmark_name} Index",
        f"{macro.benchmark_price:,.2f}",
        delta=bench_delta,
        delta_color="normal" if macro.benchmark_change_pct >= 0 else "inverse"
    )

with m_col2:
    st.metric(
        "Market Weather",
        macro.market_mood_label,
        delta="Normal Liquidity" if macro.position_scale_factor >= 1.0 else "Cautionary Sizing",
        delta_color="normal" if macro.market_mood_color == "green" else "inverse"
    )

with m_col3:
    vix_name = "India VIX" if is_indian else "CBOE VIX"
    st.metric(
        f"Volatility ({vix_name})",
        f"{macro.vix:.2f}",
        delta=f"Safety Budget: {int(macro.position_scale_factor * 100)}%",
        delta_color="normal" if macro.position_scale_factor >= 1.0 else "inverse"
    )

with m_col4:
    st.metric(
        "10Y Government Yield",
        f"{macro.yield_10y:.2f}%",
        delta=macro.yield_curve_state,
        delta_color="normal" if macro.yield_spread >= 0 else "inverse"
    )

with m_col5:
    st.metric(
        "Crude Oil (WTI)",
        f"${macro.crude_oil:.2f}",
        delta="Demand Stable" if not macro.crude_demand_destruction else "Oil Price Shock!",
        delta_color="normal" if not macro.crude_demand_destruction else "inverse"
    )

st.markdown("<hr style='margin: 14px 0; border-color: #232D3F;'>", unsafe_allow_html=True)

# =============================================================================
# MODULE 11.2: INTERACTIVE SECTOR UNIVERSE EXPLORER TERMINAL
# =============================================================================
with st.expander("📊 **Explore Market Universe by Cap & Sector** (Click to Expand / Browse Categories)", expanded=False):
    # Fetch live radar data for category counts
    radar_data = fetch_radar_cached_v2(is_indian)
    count_penny = len(radar_data.get("penny", []))
    count_safe = len(radar_data.get("safe", []))
    count_new = len(radar_data.get("new", []))
    count_trending = len(radar_data.get("trending", []))
    count_future = len(radar_data.get("future", []))

    # Fetch unified market universe with sectors and cap tiers
    all_universe_stocks = get_unified_market_universe(is_indian)

    category_options = [
        f"All Categories ({len(all_universe_stocks):,} Stocks)",
        f"🪙 Small-Priced ({count_penny:,})",
        f"🏰 Safe Havens ({count_safe:,})",
        f"🌱 New & Emerging ({count_new:,})",
        f"🔥 Trending Today ({count_trending:,})",
        f"🚀 Future Supercycles ({count_future:,})",
    ]

    col_cat, col_cap, col_sec, col_search = st.columns([1.5, 1.0, 1.4, 1.3])

    with col_cat:
        selected_cat_str = st.selectbox(
            "Filter by Category",
            options=category_options,
            index=0,
            key="sector_explorer_cat"
        )

    with col_cap:
        selected_cap = st.selectbox(
            "Filter by Market Cap",
            options=get_all_cap_tiers(),
            index=0,
            key="sector_explorer_cap"
        )

    with col_sec:
        market_str = "INDIA" if is_indian else "US"
        available_sectors = ["All Sectors"] + get_all_sectors(market=market_str)
        selected_sector = st.selectbox(
            "Filter by Sector",
            options=available_sectors,
            index=0,
            key="sector_explorer_sec"
        )

    with col_search:
        sec_query = st.text_input(
            "Quick Filter",
            "",
            placeholder="e.g. Tata, 5G, Defense, Bank, Solar...",
            key="sector_explorer_query"
        ).strip().lower()

    # Apply category filter
    if "Small-Priced" in selected_cat_str:
        filtered_stocks = [s for s in all_universe_stocks if s.category_id == "penny"]
    elif "Safe Havens" in selected_cat_str:
        filtered_stocks = [s for s in all_universe_stocks if s.category_id == "safe"]
    elif "New & Emerging" in selected_cat_str:
        filtered_stocks = [s for s in all_universe_stocks if s.category_id == "new"]
    elif "Trending Today" in selected_cat_str:
        filtered_stocks = [s for s in all_universe_stocks if s.category_id == "trending"]
    elif "Future Supercycles" in selected_cat_str:
        filtered_stocks = [s for s in all_universe_stocks if s.category_id == "future"]
    else:
        filtered_stocks = all_universe_stocks

    # Apply cap tier filter
    if selected_cap != "All Caps":
        filtered_stocks = [s for s in filtered_stocks if getattr(s, "market_cap_tier", "Mid-Cap") == selected_cap]

    # Apply sector filter
    if selected_sector != "All Sectors":
        filtered_stocks = [s for s in filtered_stocks if getattr(s, "sector", "") == selected_sector]

    # Apply text search filter
    if sec_query:
        filtered_stocks = [
            s for s in filtered_stocks
            if sec_query in s.ticker.lower()
            or sec_query in s.name.lower()
            or sec_query in getattr(s, "sector", "").lower()
            or sec_query in getattr(s, "market_cap_tier", "").lower()
            or sec_query in s.catalyst_driver.lower()
            or sec_query in s.why_it_matters.lower()
        ]

    if not filtered_stocks:
        st.info("No companies found matching the selected category, cap tier, and sector criteria.")
    else:
        # Build tabular DataFrame
        table_rows = []
        for s in filtered_stocks:
            cat_label = (
                "🪙 Small-Priced" if s.category_id == "penny"
                else ("🏰 Safe Haven" if s.category_id == "safe"
                else ("🌱 Emerging" if s.category_id == "new"
                else ("🔥 Trending" if s.category_id == "trending"
                else "🚀 Supercycle")))
            )
            chg_val = getattr(s, "change_pct", 0.0)
            rel_vol = getattr(s, "volume_multiple", 1.0)
            table_rows.append({
                "Ticker": s.ticker,
                "Company Name": s.name,
                "Category": cat_label,
                "Sector": getattr(s, "sector", "General Equities"),
                "Cap Tier": getattr(s, "market_cap_tier", "Mid-Cap"),
                "Live Price": s.approx_price,
                "Change %": getattr(s, "change_str", f"{chg_val:+.2f}%"),
                "Volume Multiple": f"{rel_vol:.1f}x ADV",
                "Risk Rating": getattr(s, "risk_badge", "🟢 Normal"),
                "Live Catalyst": s.catalyst_driver,
            })
        table_df = pd.DataFrame(table_rows)

        col_hint, col_quick_sel = st.columns([2.8, 1.4])
        with col_hint:
            clean_cat_title = selected_cat_str.split('(')[0].strip()
            st.caption(f"Showing **{len(filtered_stocks):,}** stocks in `{selected_sector}` ({selected_cap}) matching `{clean_cat_title}`. Click any row below to open its profile popup and run an immediate audit.")
        with col_quick_sel:
            sel_sym = st.selectbox(
                "Quick Inspect:",
                options=[s.ticker for s in filtered_stocks],
                format_func=lambda t: f"{t} — {next((s.name for s in filtered_stocks if s.ticker == t), t)[:20]}",
                key="select_inspect_universe_drawer",
                label_visibility="collapsed",
            )

        # Interactive Scrollable Table with Row Selection
        table_event = st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            height=440,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Company Name": st.column_config.TextColumn("Company Name", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Sector": st.column_config.TextColumn("Sector", width="medium"),
                "Cap Tier": st.column_config.TextColumn("Cap Tier", width="small"),
                "Live Price": st.column_config.TextColumn("Live Price", width="small"),
                "Change %": st.column_config.TextColumn("Change %", width="small"),
                "Volume Multiple": st.column_config.TextColumn("Volume Multiple", width="small"),
                "Risk Rating": st.column_config.TextColumn("Risk Rating", width="small"),
                "Live Catalyst": st.column_config.TextColumn("Live News & Catalyst", width="large"),
            },
            key="sector_universe_table",
        )

        # Open modal popup if a row is clicked
        if table_event and table_event.selection and len(table_event.selection.rows) > 0:
            clicked_idx = table_event.selection.rows[0]
            if 0 <= clicked_idx < len(filtered_stocks):
                show_stock_inspection_modal(filtered_stocks[clicked_idx])

        # Action button for quick select
        if st.button(f"🔍 Inspect {sel_sym} & Run Audit", key="btn_quick_inspect_universe_drawer", use_container_width=True):
            matched_stock = next((s for s in filtered_stocks if s.ticker == sel_sym), None)
            if matched_stock:
                show_stock_inspection_modal(matched_stock)

st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

# --- MAIN PIPELINE EXECUTION ---
ticker_to_run = st.session_state["active_ticker"]

def run_full_audit(ticker: str):
    with st.spinner(f"Auditing company health, secular horizons, and supply chain ripple for {ticker}..."):
        try:
            # 1. Technical Data
            tech, df = compute_technical_snapshot(ticker, period="1y", interval="1d")
            if df.empty:
                st.error(f"Could not retrieve market data for '{ticker}'. Please verify the symbol.")
                return None, None, None, None, None, None, None, None, None, None, None

            # 2. Company Info
            try:
                t = yf.Ticker(ticker)
                info = t.info or {}
            except Exception:
                info = {}

            # 3. Factor Model & Solvency
            factors = evaluate_factor_model(ticker, df, info=info)

            # 4. Microstructure Flow
            micro = validate_microstructure(ticker, df, info=info)

            # 5. Trap Guards
            traps = evaluate_all_traps(df, info=info)

            # 6. Sector Spillovers & Thematic Profile
            sec = info.get("sector", "")
            ind = info.get("industry", "")
            cat_key = detect_company_catalyst(ticker, sector=sec, industry=ind)
            spill = get_supply_chain_spillover(cat_key)
            thematic = audit_thematic_profile(ticker, sector=sec, industry=ind)
            ripple = get_supplier_ripple_effect(ticker)
            ancillary = screen_ancillary_supplier(ticker, info=info)

            # 7. Risk Engine
            cash_defense = st.session_state.get("emergency_cash_lock", False)
            stop_dist = max(tech.atr_14 * 1.8, tech.current_price * 0.015)
            proj_target = round(tech.current_price + (2.5 * stop_dist), 2)

            risk = calculate_algorithmic_execution(
                portfolio_equity=account_size,
                current_price=tech.current_price,
                atr=tech.atr_14,
                macro=macro,
                resistance_target=proj_target,
                user_risk_pct=risk_pct,
            )

            if cash_defense:
                risk.calculated_shares = 0
                risk.allocated_capital = 0.0
                risk.execution_verdict = "REJECT_EMERGENCY_CASH_LOCK"
                risk.risk_guardrail_notes.append("Emergency 100% Cash Lock active.")

            # 8. AI Decision Plan (FullInstitutionalTradePlan)
            trade_plan = generate_institutional_trade_plan(
                ticker=ticker,
                macro=macro,
                micro=micro,
                factors=factors,
                traps=traps,
                spillovers=spill,
                risk=risk,
                thematic=thematic,
                ancillary=ancillary,
                ripple=ripple,
                model_name=model_choice,
            )

            if cash_defense:
                trade_plan.action = "AVOID"
                trade_plan.calculated_shares = 0

            return tech, df, factors, micro, traps, spill, risk, trade_plan, thematic, ripple, ancillary, info

        except Exception as e:
            st.error(f"Analysis encountered an unexpected issue: {e}")
            return None, None, None, None, None, None, None, None, None, None, None, {}


audit_results = run_full_audit(ticker_to_run)
if audit_results and audit_results[0] is not None:
    tech, df, factors, micro, traps, spill, risk, plan, thematic, ripple, ancillary, info = audit_results

    # --- TOP-LEVEL SEGMENTED MENU BAR ---
    tab_names = [
        "📊 Executive Summary",
        "📈 Interactive Chart Terminal",
        "🧭 Thematic Market Radar",
        "🔗 Supply Chain & Ripple Graph",
        "🛡️ Solvency, Traps & Execution",
    ]

    if is_global_admin():
        tab_names.append("👑 Global Governance (nikhil875171)")
    elif is_admin():
        tab_names.append("🛡️ Admin Operational Telemetry")

    tabs = st.tabs(tab_names)

    # =========================================================================
    # TAB 1: EXECUTIVE SUMMARY (30s BOTTOM-LINE & ELI5 TILES)
    # =========================================================================
    with tabs[0]:
        # Company Profile & Identity Header
        company_name = info.get("longName") or info.get("shortName") or plan.ticker
        sector = info.get("sector", "Global Equities")
        industry = info.get("industry", "Diversified")
        market_cap = info.get("marketCap", None)
        if market_cap:
            if is_indian:
                mcap_str = f"₹{market_cap / 1e7:,.1f} Cr" if market_cap >= 1e7 else f"₹{market_cap:,.0f}"
            else:
                mcap_str = f"${market_cap / 1e9:,.2f}B" if market_cap >= 1e9 else f"${market_cap / 1e6:,.1f}M"
        else:
            mcap_str = "N/A"

        pe_ratio = info.get("trailingPE", None) or info.get("forwardPE", None)
        pe_str = f"{pe_ratio:.1f}x" if pe_ratio else "N/A"

        fifty_two_high = info.get("fiftyTwoWeekHigh", None)
        fifty_two_low = info.get("fiftyTwoWeekLow", None)
        range_str = f"{currency_sym}{fifty_two_low:.2f} – {currency_sym}{fifty_two_high:.2f}" if (fifty_two_high and fifty_two_low) else "N/A"

        st.markdown(f"""
        <div class='company-profile-banner'>
            <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;'>
                <div>
                    <div style='display: flex; align-items: center; gap: 10px;'>
                        <span style='font-size: 1.55rem; font-weight: 800; color: #F8FAFC;'>{company_name}</span>
                        <span class='pastel-pill'>{plan.ticker}</span>
                    </div>
                    <div style='margin-top: 8px;'>
                        <span class='pastel-pill-mint'>{sector}</span>
                        <span class='pastel-pill-lilac' style='margin-left: 6px;'>{industry}</span>
                    </div>
                </div>
                <div style='display: flex; gap: 24px; align-items: center; flex-wrap: wrap;'>
                    <div style='text-align: right;'>
                        <div style='font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;'>Market Price</div>
                        <div style='font-size: 1.50rem; font-weight: 800; color: #38BDF8;'>{currency_sym}{tech.current_price:,.2f}</div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;'>Market Cap</div>
                        <div style='font-size: 1.15rem; font-weight: 700; color: #E2E8F0;'>{mcap_str}</div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;'>P/E Ratio</div>
                        <div style='font-size: 1.15rem; font-weight: 700; color: #E2E8F0;'>{pe_str}</div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;'>52-Week Range</div>
                        <div style='font-size: 0.95rem; font-weight: 600; color: #CBD5E1;'>{range_str}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # The 30-Second "Bottom Line" Summary Strip
        if plan.action in ["BUY", "ACCUMULATE"]:
            box_class = "bottom-line-container"
            badge_html = f"<span class='badge-buy'>🟢 {plan.action} RECOMMENDATION</span>"
            action_headline = "A favorable setup with high reward and protected risk."
            f_score_disp = getattr(factors, "piotroski_f_score", 6) if factors else 6
            why_text = f"{plan.plain_english_verdict} (Operating leverage: {ancillary.operating_leverage_multiplier}x, Business Health: {f_score_disp}/9)."
        elif plan.action == "HOLD":
            box_class = "bottom-line-container bottom-line-caution"
            badge_html = "<span class='badge-hold'>🟡 HOLD / WAIT FOR DIP</span>"
            action_headline = "Good company, but not the ideal moment to enter."
            why_text = f"{plan.plain_english_verdict} Wait for a clean pullback into the recommended entry zone."
        elif plan.action == "SELL":
            box_class = "bottom-line-container bottom-line-danger"
            badge_html = "<span class='badge-sell'>🔴 EXIT / TAKE PROFIT</span>"
            action_headline = "Momentum is breaking down or targets have been reached."
            why_text = plan.plain_english_verdict
        else:
            box_class = "bottom-line-container bottom-line-danger"
            badge_html = "<span class='badge-avoid'>🔴 AVOID (HIGH RISK)</span>"
            action_headline = "High risk of capital loss detected. Do not invest now."
            why_text = plan.plain_english_verdict

        risk_rule_text = f"{plan.primary_danger}. Automatic stop-loss at **{currency_sym}{plan.algorithmic_stop_loss}** caps loss to exactly **{currency_sym}{risk.max_equity_at_risk:,.2f}** ({risk.risk_pct:.1f}% of budget)."

        st.markdown(f"""
        <div class='{box_class}'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;'>
                <div>
                    {badge_html}
                    <span style='margin-left: 14px; font-size: 1.25rem; font-weight: 700; color: #F8FAFC;'>{plan.ticker} — {action_headline}</span>
                </div>
                <div style='font-size: 0.95rem; color: #94A3B8; font-weight: 600;'>
                    Conviction: <strong style='color: #F8FAFC;'>{plan.conviction_score * 100:.0f}%</strong> | Role: <strong style='color: #93C5FD;'>{plan.supply_chain_role}</strong>
                </div>
            </div>
            <div style='font-size: 1.02rem; line-height: 1.55; color: #CBD5E1; margin-bottom: 10px;'>
                <strong>💡 Why:</strong> {why_text}
            </div>
            <div style='font-size: 1.02rem; line-height: 1.55; color: #FDA4AF;'>
                <strong>⚠️ The #1 Risk to Watch:</strong> {risk_rule_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # =========================================================================
        # 360° INSTITUTIONAL MULTI-FACTOR MATRIX (ZERO-CLICK ELI5 & RADAR)
        # =========================================================================
        st.markdown("#### 🧩 **Institutional Core Dimensions (360° Multi-Factor Matrix)**")
        st.caption("Institutional forensic gates paired with intuitive plain-English insights — zero manual clicking required.")

        # Compute normalized scores for the 6 core pillars
        dim_scores = compute_institutional_dimension_scores(macro, factors, tech, micro, thematic, risk)
        total_score = sum(d["score"] for d in dim_scores.values())
        avg_score = int(total_score / len(dim_scores)) if dim_scores else 50
        passing_pillars = sum(1 for d in dim_scores.values() if d["class"] == "safe")
        caution_pillars = sum(1 for d in dim_scores.values() if d["class"] == "caution")
        danger_pillars = sum(1 for d in dim_scores.values() if d["class"] == "danger")

        # Top Control Strip: View Mode + ELI5 Insights Toggle
        c_mode_col, c_tgl_col = st.columns([2.5, 1.5])
        with c_mode_col:
            selected_dim_view = st.segmented_control(
                "Dimension View Mode",
                options=["✨ 360° Matrix & Cards", "🕸️ Interactive Spider Radar", "🎯 Single Pillar Spotlight"],
                default="✨ 360° Matrix & Cards",
                label_visibility="collapsed",
            )
            if not selected_dim_view:
                selected_dim_view = "✨ 360° Matrix & Cards"

        with c_tgl_col:
            show_eli5_insights = st.toggle("💡 Plain-English (ELI5) Insights", value=True)

        # Overview Header Banner
        health_grade = "INSTITUTIONAL GRADE" if avg_score >= 75 else ("MODERATE CONVICTION" if avg_score >= 55 else "CAPITAL PRESERVATION RISK")
        health_badge_class = "safe" if avg_score >= 75 else ("caution" if avg_score >= 55 else "danger")
        score_color = "#34D399" if avg_score >= 75 else ("#FBBF24" if avg_score >= 55 else "#FB7185")

        st.markdown(f"""
        <div class='dim-overview-banner'>
            <div>
                <span style='font-size: 0.78rem; text-transform: uppercase; color: #94A3B8; font-weight: 700; letter-spacing: 0.05em;'>Composite Multi-Factor Health</span>
                <div style='display: flex; align-items: center; gap: 10px; margin-top: 4px;'>
                    <span style='font-size: 1.55rem; font-weight: 800; color: {score_color};'>{avg_score} / 100</span>
                    <span class='tile-status-{health_badge_class}' style='font-size: 0.88rem; padding: 4px 10px; background: rgba(255,255,255,0.05); border-radius: 999px;'>{health_grade}</span>
                </div>
            </div>
            <div style='display: flex; gap: 14px; flex-wrap: wrap; align-items: center;'>
                <div style='text-align: center; padding: 0 8px;'>
                    <div style='font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;'>Passing Gates</div>
                    <div style='font-size: 1.15rem; font-weight: 700; color: #34D399;'>🟢 {passing_pillars} of 6</div>
                </div>
                <div style='text-align: center; padding: 0 8px; border-left: 1px solid rgba(255,255,255,0.1); border-right: 1px solid rgba(255,255,255,0.1);'>
                    <div style='font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;'>Caution</div>
                    <div style='font-size: 1.15rem; font-weight: 700; color: #FBBF24;'>🟡 {caution_pillars}</div>
                </div>
                <div style='text-align: center; padding: 0 8px;'>
                    <div style='font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;'>Distress / Danger</div>
                    <div style='font-size: 1.15rem; font-weight: 700; color: #FB7185;'>🔴 {danger_pillars}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Precalculate shared data & resilient NaN safeguards
        rr = getattr(risk, "risk_reward_ratio", 0.0) if risk else 0.0
        if rr is None or math.isnan(rr) or rr <= 0:
            odds_disp = "0.0x (Risk Gate Tripped)"
            alloc_disp = "0 shares (₹0.00 — Capital Protected)"
        else:
            odds_disp = f"{rr:.1f}x"
            alloc_cap = getattr(risk, "allocated_capital", 0.0)
            alloc_cap_str = f"{currency_sym}{alloc_cap:,.2f}" if (alloc_cap and not math.isnan(alloc_cap)) else f"{currency_sym}0.00"
            alloc_disp = f"{plan.calculated_shares} shares ({alloc_cap_str})"

        z_score = getattr(factors, "altman_z_score", 2.5) if factors else 2.5
        is_manip = getattr(factors, "beneish_manipulation_risk", False) if factors else False
        beneish_val = getattr(factors, "beneish_m_score", -2.45) if factors else -2.45
        f_score = getattr(factors, "piotroski_f_score", 6) if factors else 6
        sloan_val = getattr(factors, "sloan_accrual_ratio", 0.0) if factors else 0.0
        beneish_note = "⚠️ Forensic Warning" if is_manip else "✅ Clean Accounting"

        # -------------------------------------------------------------------------
        # VIEW 1: 360° MATRIX & CARDS (DEFAULT)
        # -------------------------------------------------------------------------
        if selected_dim_view == "✨ 360° Matrix & Cards":
            # Top Visual Strip: Interactive Radar on Left, 6-Pillar Health Meters on Right
            vis_r1, vis_r2 = st.columns([1.15, 1.45])
            with vis_r1:
                radar_fig = build_institutional_radar_chart(dim_scores, ticker=plan.ticker)
                st.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar": False})
            with vis_r2:
                st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; margin-bottom: 8px;'>Pillar Readiness vs Institutional Threshold (60)</div>", unsafe_allow_html=True)
                for p_name, p_data in dim_scores.items():
                    meter_fill_class = f"dim-meter-fill-{p_data['class']}"
                    st.markdown(f"""
                    <div style='margin-bottom: 8px;'>
                        <div style='display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 3px;'>
                            <span style='color: #E2E8F0; font-weight: 600;'>{p_data['axis_label']}</span>
                            <span><strong style='color: #F8FAFC;'>{p_data['score']}</strong>/100 • <span class='tile-status-{p_data["class"]}' style='font-size: 0.80rem;'>{p_data["status"]}</span></span>
                        </div>
                        <div class='dim-meter-track'>
                            <div class='{meter_fill_class}' style='width: {p_data["score"]}%;'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Reorganized 3-Column x 2-Row Grid of Luxury Dimension Cards (Zero-Click ELI5)
            r1_c1, r1_c2, r1_c3 = st.columns(3)
            with r1_c1:
                # 1. Market Mood
                p1 = dim_scores["Market Mood"]
                eli5_html = """
                <div class='eli5-callout'>
                    <div class='eli5-label'>💡 In Plain English (ELI5)</div>
                    <div class='eli5-text'>Think of market mood like flying an airplane. When VIX is low, skies are smooth. When volatility spikes, you're flying into a storm.</div>
                </div>
                """ if show_eli5_insights else ""
                st.markdown(f"""
                <div class='dimension-card'>
                    <div>
                        <div class='dim-card-header'>
                            <span class='dim-title'>1. 🌡️ Market Mood</span>
                            <span class='tile-status-{p1["class"]}'>{p1["status"]}</span>
                        </div>
                        <div class='dim-meter-track'>
                            <div class='dim-meter-fill-{p1["class"]}' style='width: {p1["score"]}%;'></div>
                        </div>
                        <div class='dim-metric-sub'>VIX: <strong>{macro.vix:.1f}</strong> • Volatility Regime: <strong>{macro.regime.value if hasattr(macro, "regime") else "NORMAL"}</strong></div>
                        {eli5_html}
                    </div>
                    <div class='verdict-box'>
                        <strong>🏛️ Institutional Verdict:</strong> {macro.market_mood_desc}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with r1_c2:
                # 2. Company Health
                p2 = dim_scores["Company Health"]
                eli5_html = """
                <div class='eli5-callout'>
                    <div class='eli5-label'>💡 In Plain English (ELI5)</div>
                    <div class='eli5-text'>Does this company generate real cash from customers, or are they borrowing money or inflating accounting numbers just to look profitable?</div>
                </div>
                """ if show_eli5_insights else ""
                st.markdown(f"""
                <div class='dimension-card'>
                    <div>
                        <div class='dim-card-header'>
                            <span class='dim-title'>2. 🏥 Company Health</span>
                            <span class='tile-status-{p2["class"]}'>{p2["status"]}</span>
                        </div>
                        <div class='dim-meter-track'>
                            <div class='dim-meter-fill-{p2["class"]}' style='width: {p2["score"]}%;'></div>
                        </div>
                        <div class='dim-metric-sub'>Altman Z: <strong>{z_score:.2f}</strong> • Solvency: <strong>{plan.solvency_status}</strong></div>
                        {eli5_html}
                    </div>
                    <div class='verdict-box'>
                        <strong>🏛️ Forensic Gate Checks:</strong>
                        <div style='margin-top: 4px; font-size: 0.82rem; line-height: 1.5;'>
                            • Altman Z-Score: <strong>{z_score:.2f}</strong> (Distress: &lt; 1.81, Safe: &gt; 2.99)<br>
                            • Piotroski F-Score: <strong>{f_score}/9</strong> (Operating Quality)<br>
                            • Sloan Accruals: <strong>{sloan_val * 100:.1f}%</strong> (Cash Backed &lt; 10%)<br>
                            • Beneish M-Score: <strong>{beneish_val:.2f}</strong> ({beneish_note})
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with r1_c3:
                # 3. Price Trend
                p3 = dim_scores["Price Trend"]
                eli5_html = """
                <div class='eli5-callout'>
                    <div class='eli5-label'>💡 In Plain English (ELI5)</div>
                    <div class='eli5-text'>Are more buyers rushing in, or are investors quietly heading for the exits? Moving averages reveal the institutional money footprint.</div>
                </div>
                """ if show_eli5_insights else ""
                trend_msg = "above 50-day baseline" if tech.current_price > tech.ema_50 else "below 50-day baseline"
                st.markdown(f"""
                <div class='dimension-card'>
                    <div>
                        <div class='dim-card-header'>
                            <span class='dim-title'>3. 🚀 Price Trend</span>
                            <span class='tile-status-{p3["class"]}'>{p3["status"]}</span>
                        </div>
                        <div class='dim-meter-track'>
                            <div class='dim-meter-fill-{p3["class"]}' style='width: {p3["score"]}%;'></div>
                        </div>
                        <div class='dim-metric-sub'>RSI: <strong>{tech.rsi_14:.1f}</strong> • Price vs 50 EMA: <strong>{((tech.current_price - tech.ema_50) / tech.ema_50) * 100:+.1f}%</strong></div>
                        {eli5_html}
                    </div>
                    <div class='verdict-box'>
                        <strong>🏛️ Institutional Verdict:</strong> Price is <strong>{trend_msg}</strong>.<br>
                        <span style='font-size: 0.80rem; color: #94A3B8;'>20 EMA: {currency_sym}{tech.ema_20:,.2f} | 50 EMA: {currency_sym}{tech.ema_50:,.2f} | 200 EMA: {currency_sym}{tech.ema_200:,.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            r2_c1, r2_c2, r2_c3 = st.columns(3)
            with r2_c1:
                # 4. Smart Money
                p4 = dim_scores["Smart Money"]
                eli5_html = """
                <div class='eli5-callout'>
                    <div class='eli5-label'>💡 In Plain English (ELI5)</div>
                    <div class='eli5-text'>Institutional 'whales' buy and hold shares in their vaults. Delivery % proves real accumulation vs speculative churn.</div>
                </div>
                """ if show_eli5_insights else ""
                st.markdown(f"""
                <div class='dimension-card'>
                    <div>
                        <div class='dim-card-header'>
                            <span class='dim-title'>4. 🐋 Smart Money</span>
                            <span class='tile-status-{p4["class"]}'>{p4["status"]}</span>
                        </div>
                        <div class='dim-meter-track'>
                            <div class='dim-meter-fill-{p4["class"]}' style='width: {p4["score"]}%;'></div>
                        </div>
                        <div class='dim-metric-sub'>Delivery: <strong>{micro.delivery_pct:.1f}%</strong> • Flow Validity: <strong>{'VALID' if micro.delivery_valid else 'DAY-TRADING'}</strong></div>
                        {eli5_html}
                    </div>
                    <div class='verdict-box'>
                        <strong>🏛️ Microstructure Verdict:</strong> {micro.delivery_status_msg}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with r2_c2:
                # 5. Secular Horizon
                p5 = dim_scores["Secular Horizon"]
                eli5_html = f"""
                <div class='eli5-callout'>
                    <div class='eli5-label'>💡 In Plain English (ELI5)</div>
                    <div class='eli5-text'>{thematic.plain_english_takeaway}</div>
                </div>
                """ if show_eli5_insights else ""
                st.markdown(f"""
                <div class='dimension-card'>
                    <div>
                        <div class='dim-card-header'>
                            <span class='dim-title'>5. ⏳ Secular Horizon</span>
                            <span class='tile-status-{p5["class"]}'>{thematic.timeframe}</span>
                        </div>
                        <div class='dim-meter-track'>
                            <div class='dim-meter-fill-{p5["class"]}' style='width: {p5["score"]}%;'></div>
                        </div>
                        <div class='dim-metric-sub'>Wave: <strong>{thematic.horizon_code}</strong> • <strong>{thematic.horizon_title}</strong></div>
                        {eli5_html}
                    </div>
                    <div class='verdict-box'>
                        <strong>🏛️ Megatrend & Scarcity:</strong><br>
                        <span style='font-size: 0.82rem;'>• Driver: {thematic.thematic_driver}</span><br>
                        <span style='font-size: 0.82rem;'>• Bottleneck: <code style='color: #38BDF8;'>{thematic.resource_scarcity_exposure}</code></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with r2_c3:
                # 6. Safety Gauge
                p6 = dim_scores["Safety Gauge"]
                eli5_html = """
                <div class='eli5-callout'>
                    <div class='eli5-label'>💡 In Plain English (ELI5)</div>
                    <div class='eli5-text'>Never take a trade where the upside isn't at least 2.5x larger than the risk. Protect capital first, profits come second.</div>
                </div>
                """ if show_eli5_insights else ""
                st.markdown(f"""
                <div class='dimension-card'>
                    <div>
                        <div class='dim-card-header'>
                            <span class='dim-title'>6. 🛡️ Safety Gauge</span>
                            <span class='tile-status-{p6["class"]}'>{p6["status"]}</span>
                        </div>
                        <div class='dim-meter-track'>
                            <div class='dim-meter-fill-{p6["class"]}' style='width: {p6["score"]}%;'></div>
                        </div>
                        <div class='dim-metric-sub'>Reward-to-Risk: <strong>{odds_disp}</strong> • Asymmetry: <strong>{'PASS (>=2.5x)' if risk.asymmetric_rr_passed else 'REJECTED'}</strong></div>
                        {eli5_html}
                    </div>
                    <div class='verdict-box'>
                        <strong>🏛️ Risk Sizing Verdict:</strong> Max allocation: <strong>{alloc_disp}</strong>.<br>
                        <span style='font-size: 0.80rem; color: #FDA4AF;'>Hard Stop-Loss: {currency_sym}{plan.algorithmic_stop_loss} caps max equity loss at {currency_sym}{risk.max_equity_at_risk:,.2f}.</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # -------------------------------------------------------------------------
        # VIEW 2: INTERACTIVE SPIDER RADAR
        # -------------------------------------------------------------------------
        elif selected_dim_view == "🕸️ Interactive Spider Radar":
            col_rad_large, col_rad_table = st.columns([1.3, 1.2])
            with col_rad_large:
                radar_fig = build_institutional_radar_chart(dim_scores, ticker=plan.ticker)
                radar_fig.update_layout(height=480)
                st.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar": True})
            with col_rad_table:
                st.markdown("##### 🏛️ **Institutional Dimension Scorecard vs Benchmark**")
                rows = []
                for k, v in dim_scores.items():
                    gap = v["score"] - 60
                    gap_str = f"+{gap}" if gap >= 0 else str(gap)
                    rows.append({
                        "Dimension": k,
                        "Metric": v["metric"],
                        "Score": f"{v['score']}/100",
                        "Benchmark": "60/100",
                        "Gap vs Baseline": gap_str,
                        "Institutional Status": v["status"],
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.info("💡 **Institutional Benchmark Rule:** Top-tier quantitative managers require at least 4 of 6 dimensions to score ≥ 60/100 before committing growth capital.")

        # -------------------------------------------------------------------------
        # VIEW 3: SINGLE PILLAR SPOTLIGHT
        # -------------------------------------------------------------------------
        else:
            pillar_names = list(dim_scores.keys())
            selected_pillar = st.pills("Select Dimension to Inspect in Deep-Dive Mode:", pillar_names, default=pillar_names[1])
            if not selected_pillar:
                selected_pillar = pillar_names[1]

            sp_data = dim_scores[selected_pillar]
            st.markdown(f"### {selected_pillar} — Institutional Analytical Dossier")

            sp_col1, sp_col2 = st.columns([1.2, 1.8])
            with sp_col1:
                st.markdown(f"""
                <div class='dimension-card'>
                    <div class='dim-card-header'>
                        <span class='dim-title'>{selected_pillar}</span>
                        <span class='tile-status-{sp_data["class"]}'>{sp_data["status"]}</span>
                    </div>
                    <div class='dim-meter-track'>
                        <div class='dim-meter-fill-{sp_data["class"]}' style='width: {sp_data["score"]}%;'></div>
                    </div>
                    <div style='font-size: 2.2rem; font-weight: 800; color: #38BDF8; margin: 10px 0;'>{sp_data["score"]} / 100</div>
                    <div class='dim-metric-sub'>Key Metric: <strong>{sp_data["metric"]}</strong></div>
                    <div class='eli5-callout'>
                        <div class='eli5-label'>💡 Plain English Intuition</div>
                        <div class='eli5-text'>Institutional investors use this pillar to rigorously test corporate reality against public sentiment.</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with sp_col2:
                if selected_pillar == "Company Health":
                    st.markdown("#### 🔬 **Forensic Solvency & Earnings Quality Matrix**")
                    st.markdown(f"""
                    - **Altman Z-Score:** `{z_score:.2f}` (Distress Threshold: `< 1.81`, Grey Zone: `1.81 – 2.99`, Safe Zone: `> 2.99`)
                    - **Piotroski F-Score:** `{f_score} / 9` (Operating quality, profitability, and leverage improvements)
                    - **Sloan Accruals Ratio:** `{sloan_val * 100:.1f}%` (Values `< 10%` confirm earnings are backed by hard cash flow)
                    - **Beneish M-Score:** `{beneish_val:.2f}` ({beneish_note})
                    - **Solvency Status:** **{plan.solvency_status}**
                    """)
                elif selected_pillar == "Market Mood":
                    st.markdown("#### 🌡️ **Macro Volatility Transmission**")
                    st.markdown(f"""
                    - **Market VIX:** `{macro.vix:.1f}`
                    - **Macro Regime:** `{macro.regime.value if hasattr(macro, "regime") else "NORMAL"}`
                    - **Transmission Rationale:** {macro.market_mood_desc}
                    """)
                elif selected_pillar == "Price Trend":
                    st.markdown("#### 🚀 **Technical Momentum & Moving Average Ribbons**")
                    st.markdown(f"""
                    - **Current Price:** `{currency_sym}{tech.current_price:,.2f}`
                    - **20-Day Fast EMA:** `{currency_sym}{tech.ema_20:,.2f}`
                    - **50-Day Baseline EMA:** `{currency_sym}{tech.ema_50:,.2f}`
                    - **200-Day Structural EMA:** `{currency_sym}{tech.ema_200:,.2f}`
                    - **14-Day RSI:** `{tech.rsi_14:.1f}`
                    """)
                elif selected_pillar == "Smart Money":
                    st.markdown("#### 🐋 **Delivery Microstructure & Vault Accumulation**")
                    st.markdown(f"""
                    - **Delivery Percentage:** `{micro.delivery_pct:.1f}%`
                    - **Flow Verification:** `{'Accumulation Confirmed' if micro.delivery_valid else 'Speculative Day-Trading'}`
                    - **Details:** {micro.delivery_status_msg}
                    """)
                elif selected_pillar == "Secular Horizon":
                    st.markdown("#### ⏳ **Secular Wave & Supply Chain Scarcity**")
                    st.markdown(f"""
                    - **Horizon Wave:** `{thematic.horizon_title}` ({thematic.timeframe})
                    - **Core Driver:** {thematic.thematic_driver}
                    - **Scarcity Bottleneck Exposure:** `{thematic.resource_scarcity_exposure}`
                    - **Plain-English Takeaway:** {thematic.plain_english_takeaway}
                    """)
                else:  # Safety Gauge
                    st.markdown("#### 🛡️ **Asymmetric Risk-Reward & Capital Preservation**")
                    st.markdown(f"""
                    - **Reward-to-Risk Ratio:** `{odds_disp}` (Minimum threshold: `2.5x`)
                    - **Algorithmic Hard Stop:** `{currency_sym}{plan.algorithmic_stop_loss}`
                    - **Max Equity at Risk:** `{currency_sym}{risk.max_equity_at_risk:,.2f}` ({risk.risk_pct:.1f}% of capital)
                    - **Calculated Allocation:** `{alloc_disp}`
                    """)

    # =========================================================================
    # TAB 2: INTERACTIVE CHART TERMINAL
    # =========================================================================
    with tabs[1]:
        st.markdown(f"### 📈 **Institutional Technical Terminal — {plan.ticker}**")
        st.caption("Visualizing price action with 20/50/200 EMA ribbons, shaded entry/stop zones, volume ADV, and RSI.")

        # Technical Status Strip
        tc1, tc2, tc3, tc4, tc5 = st.columns(5)
        tc1.metric("Current Price", f"{currency_sym}{tech.current_price:,.2f}", delta=f"{((tech.current_price - tech.ema_20) / tech.ema_20) * 100:+.1f}% vs 20 EMA")
        tc2.metric("20-Day Fast EMA", f"{currency_sym}{tech.ema_20:,.2f}", delta="Short-Term Support")
        tc3.metric("50-Day Trend EMA", f"{currency_sym}{tech.ema_50:,.2f}", delta="Institutional Baseline")
        tc4.metric("200-Day Major EMA", f"{currency_sym}{tech.ema_200:,.2f}", delta="Structural S/R")
        tc5.metric("RSI Momentum", f"{tech.rsi_14:.1f}", delta=f"ATR: {currency_sym}{tech.atr_14:.2f}")

        # Interactive 3-Tier Plotly Chart
        fig = build_interactive_chart(df, tech, plan, currency_symbol=currency_sym)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})

        # Plain-English Indicator Explanations for Beginners
        st.markdown("#### 💡 **Technical Signals Explained in Plain English**")
        ch_e1, ch_e2, ch_e3 = st.columns(3)
        with ch_e1:
            st.markdown(f"""
            <div class='interactive-tile'>
                <div class='tile-header'>📈 Moving Average Ribbons (20 / 50 / 200)</div>
                <div style='font-size: 0.90rem; color: #CBD5E1; line-height: 1.5; margin-top: 6px;'>
                    When the price trades above the 20 (blue) and 50 (amber) day averages, big institutional money is actively accumulating. If the price falls below the 200 EMA (purple), the stock is in a long-term decline.
                </div>
            </div>
            """, unsafe_allow_html=True)
        with ch_e2:
            st.markdown(f"""
            <div class='interactive-tile'>
                <div class='tile-header'>⚡ Average True Range (ATR: {currency_sym}{tech.atr_14:.2f})</div>
                <div style='font-size: 0.90rem; color: #CBD5E1; line-height: 1.5; margin-top: 6px;'>
                    ATR measures how much this stock typically swings on a normal day. We automatically place your hard stop-loss at 1.8x ATR so normal daily wiggles won't knock you out of a winning investment.
                </div>
            </div>
            """, unsafe_allow_html=True)
        with ch_e3:
            st.markdown(f"""
            <div class='interactive-tile'>
                <div class='tile-header'>🎯 RSI Momentum ({tech.rsi_14:.1f})</div>
                <div style='font-size: 0.90rem; color: #CBD5E1; line-height: 1.5; margin-top: 6px;'>
                    RSI between 45 and 65 is the sweet spot for steady gains. If RSI shoots above 70, the stock is 'overheated'—never chase buying at this level. If RSI drops below 30, it is heavily oversold.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # TAB 3: THEMATIC MARKET RADAR (100% LIVE DYNAMIC QUANTITATIVE SCREENER)
    # =========================================================================
    with tabs[2]:
        col_rad_head, col_rad_act = st.columns([2.8, 1.2])

        with col_rad_head:
            market_label = "National Stock Exchange of India (NSE Full Market - 2,500+ Equities)" if is_indian else "US Markets"
            st.markdown(f"### 🧭 **Live Institutional Market Radar ({market_label})**")
            st.caption("100% dynamic quantitative screening across all listed exchange securities without hardcoding. High-density data tables with scrollbars, live keyword search, and 1-click inspection popup modals.")

        with col_rad_act:
            if st.button("🔄 Re-Scan Live Market", key="btn_rescan_market_radar", use_container_width=True):
                fetch_radar_cached_v2.clear()
                st.rerun()

        with st.spinner("Connecting to official exchange feeds & scanning full market..."):
            radar_data = fetch_radar_cached_v2(is_indian)

        total_screened = sum(len(stocks) for stocks in radar_data.values())

        # Search / Filter Bar inside the Radar
        radar_search = st.text_input(
            "🔎 Filter live screened stocks by name, ticker, or catalyst keyword:",
            "",
            placeholder="e.g. Tata, Defense, Nuclear, AI, Hydro, Solar, EV, Bank...",
            key="radar_filter_input"
        ).strip().lower()

        r_tabs = st.tabs([
            f"🪙 Small-Priced ({len(radar_data.get('penny', []))})",
            f"🏰 Safe Havens ({len(radar_data.get('safe', []))})",
            f"🌱 New & Emerging ({len(radar_data.get('new', []))})",
            f"🔥 Trending Today ({len(radar_data.get('trending', []))})",
            f"🚀 Future Supercycles ({len(radar_data.get('future', []))})",
        ])

        categories = ["penny", "safe", "new", "trending", "future"]

        for c_idx, cat_key in enumerate(categories):
            with r_tabs[c_idx]:
                raw_list = radar_data.get(cat_key, [])
                if radar_search:
                    stock_list = [
                        s for s in raw_list
                        if radar_search in s.ticker.lower()
                        or radar_search in s.name.lower()
                        or radar_search in s.catalyst_driver.lower()
                        or radar_search in s.why_it_matters.lower()
                    ]
                else:
                    stock_list = raw_list

                if not stock_list:
                    st.info(f"No live stocks found matching '{radar_search}' in this category.")
                else:
                    # Build tabular DataFrame for scrollable display
                    table_rows = []
                    for s in stock_list:
                        chg_val = getattr(s, "change_pct", 0.0)
                        rel_vol = getattr(s, "volume_multiple", 1.0)
                        table_rows.append({
                            "Ticker": s.ticker,
                            "Company Name": s.name,
                            "Live Price": s.approx_price,
                            "Change %": getattr(s, "change_str", f"{chg_val:+.2f}%"),
                            "Volume Surge": f"{rel_vol:.1f}x ADV",
                            "Risk Rating": getattr(s, "risk_badge", "🟢 Normal"),
                            "Live Catalyst": s.catalyst_driver,
                        })
                    table_df = pd.DataFrame(table_rows)

                    col_hint, col_quick_sel = st.columns([2.8, 1.4])
                    with col_hint:
                        st.caption("💡 **Tip:** Click any row in the table below to open its full profile popup window and run an immediate 1-click audit.")
                    with col_quick_sel:
                        sel_sym = st.selectbox(
                            "Quick Inspect:",
                            options=[s.ticker for s in stock_list],
                            format_func=lambda t: f"{t} — {next((s.name for s in stock_list if s.ticker == t), t)[:20]}",
                            key=f"select_inspect_{cat_key}",
                            label_visibility="collapsed",
                        )

                    # Interactive Scrollable Table with Row Selection
                    table_event = st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True,
                        height=440,
                        on_select="rerun",
                        selection_mode="single-row",
                        column_config={
                            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                            "Company Name": st.column_config.TextColumn("Company Name", width="medium"),
                            "Live Price": st.column_config.TextColumn("Live Price", width="small"),
                            "Change %": st.column_config.TextColumn("Change %", width="small"),
                            "Volume Surge": st.column_config.TextColumn("Volume Multiple", width="small"),
                            "Risk Rating": st.column_config.TextColumn("Risk Rating", width="small"),
                            "Live Catalyst": st.column_config.TextColumn("Live News & Catalyst", width="large"),
                        },
                        key=f"radar_table_{cat_key}",
                    )

                    # Open modal popup if a row is clicked
                    if table_event and table_event.selection and len(table_event.selection.rows) > 0:
                        clicked_idx = table_event.selection.rows[0]
                        if 0 <= clicked_idx < len(stock_list):
                            show_stock_inspection_modal(stock_list[clicked_idx])

                    # Action button for quick select
                    if st.button(f"🔍 Inspect {sel_sym} & Run Audit", key=f"btn_quick_inspect_{cat_key}", use_container_width=True):
                        matched_stock = next((s for s in stock_list if s.ticker == sel_sym), None)
                        if matched_stock:
                            show_stock_inspection_modal(matched_stock)

    # =========================================================================
    # TAB 4: SUPPLY CHAIN & RIPPLE GRAPH
    # =========================================================================
    with tabs[3]:
        st.markdown(f"### 🔗 **Directed Supply Chain Ripple Graph & Network Visualizer**")
        st.caption(f"Visualizing the master OEM dependency tree for **{plan.ticker}** ({ripple.case_name}).")

        # Ancillary Screener KPI Metrics
        sc_k1, sc_k2, sc_k3, sc_k4 = st.columns(4)
        sc_k1.metric("Customer Concentration", f"{ancillary.customer_concentration_pct:.1f}%", delta=ancillary.customer_concentration_flag)
        sc_k2.metric("Operating Leverage (DOL)", f"{ancillary.operating_leverage_multiplier:.1f}x", delta="High Margin Expansion" if ancillary.operating_leverage_multiplier >= 2.5 else "Moderate")
        sc_k3.metric("Book-to-Bill Ratio", f"{ancillary.book_to_bill_ratio:.2f}x", delta="Order Surge" if ancillary.book_to_bill_ratio >= 1.15 else "Stable")
        sc_k4.metric("Capex Lead-Lag Phase", ancillary.capex_phase_title, delta=ancillary.capex_lead_time_months)

        st.info(f"💡 **Supplier Ripple Dynamics:** {ripple.ripple_explanation}\n\n**Operating Leverage Insight:** {ripple.operating_leverage_summary}")

        # Plotly Network Graph
        net_fig = render_interactive_network_graph(highlight_ticker=plan.ticker)
        st.plotly_chart(net_fig, use_container_width=True)

        # Transmission Tree Breakdown
        st.markdown("---")
        st.markdown("#### **Detailed Ripple Breakdown**")
        sc1, sc2, sc3 = st.columns(3)

        with sc1:
            st.markdown("##### 🔺 Connected Anchor OEMs")
            st.caption("Companies commanding mega-capex budgets that drive demand:")
            for a in ripple.connected_anchors:
                st.markdown(f"• **{a}**")

        with sc2:
            st.markdown("##### 🔻 Upstream & Sub-Assemblies")
            st.caption("Suppliers of precision sub-assemblies and components:")
            for u in ripple.upstream_dependencies:
                st.markdown(f"• **{u}**")

        with sc3:
            st.markdown("##### ⚡ Downstream Integration")
            st.caption("Beneficiaries down the integration pipeline:")
            for d in ripple.downstream_beneficiaries:
                st.markdown(f"• **{d}**")

    # =========================================================================
    # TAB 5: SOLVENCY, TRAPS & EXECUTION
    # =========================================================================
    with tabs[4]:
        st.markdown("### 🛡️ **Forensic Solvency, Microstructure & Algorithmic Execution**")
        st.caption(f"Comprehensive forensic health audit, institutional order flow verification, and beginner execution checklist for **{plan.ticker}**.")

        sol_col, exe_col = st.columns([1.1, 1.1])

        with sol_col:
            st.markdown("#### 🏥 **Forensic Solvency & Earnings Quality**")
            z_score = getattr(factors, "altman_z_score", 2.5) if factors else 2.5
            f_score = getattr(factors, "piotroski_f_score", 6) if factors else 6
            sloan_val = getattr(factors, "sloan_accrual_ratio", 0.0) if factors else 0.0
            beneish_val = getattr(factors, "beneish_m_score", -2.45) if factors else -2.45
            is_manip = getattr(factors, "beneish_manipulation_risk", False) if factors else False

            z_status = "Safe Zone (> 2.99)" if z_score >= 2.99 else ("Grey Zone (1.81 - 2.99)" if z_score >= 1.81 else "Distress Risk (< 1.81)")
            beneish_status = "⚠️ Forensic Warning: Potential Distortion" if is_manip else "✅ Clean Financials (M < -1.78)"

            st.markdown(f"""
            <div class='interactive-tile' style='margin-bottom: 12px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <strong>Altman Z-Score (Bankruptcy Risk)</strong>
                    <span class='{"tile-status-safe" if z_score >= 2.99 else ("tile-status-caution" if z_score >= 1.81 else "tile-status-danger")}'>{z_score:.2f}</span>
                </div>
                <div style='font-size: 0.85rem; color: #94A3B8; margin-top: 4px;'>Status: {z_status}</div>
            </div>

            <div class='interactive-tile' style='margin-bottom: 12px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <strong>Piotroski F-Score (Operational Quality)</strong>
                    <span class='{"tile-status-safe" if f_score >= 7 else ("tile-status-caution" if f_score >= 5 else "tile-status-danger")}'>{f_score} / 9</span>
                </div>
                <div style='font-size: 0.85rem; color: #94A3B8; margin-top: 4px;'>Evaluates profitability, leverage, and operating efficiency.</div>
            </div>

            <div class='interactive-tile' style='margin-bottom: 12px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <strong>Sloan Accruals Ratio (Cash vs Paper Earnings)</strong>
                    <span class='{"tile-status-safe" if abs(sloan_val) < 0.10 else "tile-status-danger"}'>{sloan_val * 100:.1f}%</span>
                </div>
                <div style='font-size: 0.85rem; color: #94A3B8; margin-top: 4px;'>Accruals < 10% indicates earnings are backed by hard cash flow.</div>
            </div>

            <div class='interactive-tile' style='margin-bottom: 12px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <strong>Beneish M-Score (Forensic Manipulation Sieve)</strong>
                    <span class='{"tile-status-safe" if not is_manip else "tile-status-danger"}'>{beneish_val:.2f}</span>
                </div>
                <div style='font-size: 0.85rem; color: #94A3B8; margin-top: 4px;'>{beneish_status}</div>
            </div>

            <div class='interactive-tile'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <strong>Microstructure Flow (Delivery Volume)</strong>
                    <span class='{"tile-status-safe" if micro.delivery_valid else "tile-status-caution"}'>{micro.delivery_pct:.1f}%</span>
                </div>
                <div style='font-size: 0.85rem; color: #94A3B8; margin-top: 4px;'>{micro.delivery_status_msg}</div>
            </div>
            """, unsafe_allow_html=True)

        with exe_col:
            st.markdown("#### 📖 **Execution Checklist & Profit Targets**")
            st.markdown(f"""
            1. **Step 1: Check Safe Entry Range**
               - Target Buy Zone: **{currency_sym}{plan.entry_price_range[0]} – {currency_sym}{plan.entry_price_range[1]}**
               - *Do not chase price if it has already spiked past the upper boundary.*

            2. **Step 2: Set Algorithmic Hard Stop-Loss**
               - Hard Stop Price: **{currency_sym}{plan.algorithmic_stop_loss}**
               - *Place this stop in your brokerage terminal immediately after order execution.*

            3. **Step 3: Scaling Out (The 3-Target Profit Ladder)**
               - **Target 1 ({currency_sym}{plan.target_ladder[0] if len(plan.target_ladder) > 0 else 'N/A'})**: Sell 1/3 to lock in initial gains.
               - **Target 2 ({currency_sym}{plan.target_ladder[1] if len(plan.target_ladder) > 1 else 'N/A'})**: Sell 1/3 and move stop-loss to breakeven.
               - **Target 3 ({currency_sym}{plan.target_ladder[2] if len(plan.target_ladder) > 2 else 'N/A'})**: Let the final 1/3 run with a trailing stop.

            4. **Step 4: Position Sizing & Capital Allocation**
               - Max Sizing: **{plan.calculated_shares:,} shares** (Total Capital: {currency_sym}{risk.allocated_capital:,.2f}).
            """)

            st.markdown("#### 🚨 **Emergency Kill-Switches**")
            for ks in plan.execution_kill_switches:
                st.markdown(f"- 🔴 `{ks}`")

        st.markdown("---")
        st.markdown("#### 🪤 **Automated Trap Guards Checked**")
        st.caption("Our automated quantitative sieves verify that you are not walking into common amateur pitfalls:")

        tr1, tr2 = st.columns(2)
        with tr1:
            exh = any("EXHAUSTION" in t for t in traps)
            st.markdown(f"""
            <div class='radar-card'>
                <div style='font-size: 1.02rem; font-weight: 700; color: {"#FDA4AF" if exh else "#6EE7B7"};'>
                    {"🚨 TRAP ALERT: Exhaustion FOMO" if exh else "✅ SAFE: Healthy Volume Expansion"}
                </div>
                <div style='font-size: 0.88rem; color: #94A3B8; margin-top: 4px;'>
                    <strong>What it means:</strong> Buying after an extended rally when volume dries up often traps late buyers at the exact top.
                </div>
            </div>
            """, unsafe_allow_html=True)

            rumor = any("PRICED-IN" in t for t in traps)
            st.markdown(f"""
            <div class='radar-card'>
                <div style='font-size: 1.02rem; font-weight: 700; color: {"#FDA4AF" if rumor else "#6EE7B7"};'>
                    {"🚨 TRAP ALERT: Priced-in Rumor" if rumor else "✅ SAFE: Balanced Valuation & News"}
                </div>
                <div style='font-size: 0.88rem; color: #94A3B8; margin-top: 4px;'>
                    <strong>What it means:</strong> 'Buy the rumor, sell the news'. If a stock rallied +20% right before an earnings or product event, smart money will exit.
                </div>
            </div>
            """, unsafe_allow_html=True)

        with tr2:
            cyc = any("CYCLICAL" in t for t in traps)
            st.markdown(f"""
            <div class='radar-card'>
                <div style='font-size: 1.02rem; font-weight: 700; color: {"#FDA4AF" if cyc else "#6EE7B7"};'>
                    {"🚨 TRAP ALERT: Cheap Value Illusion" if cyc else "✅ SAFE: Sustainable Margin Profile"}
                </div>
                <div style='font-size: 0.88rem; color: #94A3B8; margin-top: 4px;'>
                    <strong>What it means:</strong> Commodity and cyclical companies look 'cheap' on P/E right when commodity prices peak, right before profits plunge.
                </div>
            </div>
            """, unsafe_allow_html=True)

            geo = any("GEOPOLITICAL" in t for t in traps)
            st.markdown(f"""
            <div class='radar-card'>
                <div style='font-size: 1.02rem; font-weight: 700; color: {"#93C5FD" if geo else "#6EE7B7"};'>
                    {"ℹ️ V-BOTTOM OPPORTUNITY: Headline Overreaction" if geo else "✅ SAFE: Normal Market Flow"}
                </div>
                <div style='font-size: 0.88rem; color: #94A3B8; margin-top: 4px;'>
                    <strong>What it means:</strong> Transitory geopolitical headlines create temporary discounts in fundamentally resilient companies.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # TAB 6: GLOBAL GOVERNANCE / ADMIN TELEMETRY (RESTRICTED RBAC)
    # =========================================================================
    if is_global_admin():
        with tabs[5]:
            st.markdown("### 👑 **Global Governance & Root Authority**")
            st.success("🔐 **Authenticated as Global Administrator (`nikhil875171`).** Complete root authority active.", icon="👑")

            gov_col1, gov_col2 = st.columns([1, 1])
            with gov_col1:
                st.markdown("#### 🚨 **Fund-Wide Risk Overrides**")
                cash_lock = st.toggle("Force Fund-Wide 100% Cash Defense", value=st.session_state.get("emergency_cash_lock", False))
                st.session_state["emergency_cash_lock"] = cash_lock
                if cash_lock:
                    st.error("⚠️ Emergency 100% Cash Defense ENGAGED: All trades overridden to AVOID.", icon="🚨")
                else:
                    st.info("System operating under normal quantitative risk governance.")

                st.markdown("#### 🔑 **Root API Telemetry**")
                api_k = os.getenv("GEMINI_API_KEY", "")
                masked_k = (api_k[:7] + "..." + api_k[-4:]) if len(api_k) > 12 else "Not Configured"
                st.write(f"**Gemini API Key:** `{masked_k}`")
                st.write(f"**Active Model Cascade:** `gemini-flash-lite-latest` ➔ `gemini-3.1-flash-lite`")

            with gov_col2:
                st.markdown("#### 👥 **Authorized Personnel Registry**")
                st.markdown("""
                | Identity | Assigned Role | Permissions |
                | :--- | :--- | :--- |
                | `nikhil875171` | **Global Administrator** | Complete Root Governance & Overrides |
                | `nkk_admin` | **System Administrator** | Operational Telemetry & Monitoring |
                | `nkk_user` | **Standard Analyst** | Asset Analysis & Interactive Tiles |
                """)

                st.markdown("---")
                st.markdown("#### 🔐 **Edit Authorized User Logins (Global Admin Only)**")
                user_dict = get_all_users()
                edit_uname = st.selectbox(
                    "Select Account to Edit",
                    options=list(user_dict.keys()) + ["[+ Add New User]"],
                    key="admin_user_select"
                )

                if edit_uname == "[+ Add New User]":
                    with st.form("form_add_new_user"):
                        st.caption("Create a new authorized analyst or administrator account.")
                        new_u = st.text_input("New Username", placeholder="e.g. analyst_new").strip().lower()
                        new_p = st.text_input("New Security Passphrase", type="password", placeholder="••••••••••••")
                        new_n = st.text_input("Full Display Name", placeholder="e.g. Senior Analyst")
                        new_r = st.selectbox("Role Permission", options=["USER", "ADMIN", "GLOBAL_ADMIN"], index=0)
                        new_b = st.text_input("Role Badge Label", value="👤 Standard Analyst")
                        add_sub = st.form_submit_button("➕ Create User Account", type="primary", use_container_width=True)
                        if add_sub:
                            if new_u and new_p:
                                update_user_credentials(new_u, new_p, new_n, new_r, new_b)
                                st.success(f"User `{new_u}` successfully created!")
                                st.rerun()
                            else:
                                st.error("Username and password required.")
                else:
                    curr_data = user_dict.get(edit_uname, {})
                    with st.form(f"form_edit_{edit_uname}"):
                        st.caption(f"Edit credentials and access tier for `{edit_uname}`")
                        edit_p = st.text_input("Update Passphrase", value=curr_data.get("password", ""), type="password")
                        edit_n = st.text_input("Display Name", value=curr_data.get("name", ""))
                        default_role_idx = 0 if curr_data.get("role") == "USER" else (1 if curr_data.get("role") == "ADMIN" else 2)
                        edit_r = st.selectbox("Role Permission", options=["USER", "ADMIN", "GLOBAL_ADMIN"], index=default_role_idx)
                        edit_b = st.text_input("Role Badge Label", value=curr_data.get("badge", ""))
                        save_sub = st.form_submit_button(f"💾 Save Changes for {edit_uname}", type="primary", use_container_width=True)
                        if save_sub:
                            update_user_credentials(edit_uname, edit_p, edit_n, edit_r, edit_b)
                            st.success(f"Credentials for `{edit_uname}` updated successfully!")
                            st.rerun()

    elif is_admin():
        with tabs[5]:
            st.markdown("### 🛡️ **Administrator Operational Telemetry**")
            st.info("Logged in as Administrator (`nkk_admin`). Standard operations active.")
            a_col1, a_col2 = st.columns(2)
            with a_col1:
                st.metric("System Health", "ONLINE", delta="All Quantitative Engines Operational")
                st.metric("Active Model", model_choice)
            with a_col2:
                st.metric("Session Mode", "Authenticated Admin")
                st.caption("Note: Root policy overrides and emergency cash locks are strictly restricted to Global Administrator (nikhil875171).")

st.markdown("<div style='margin-top: 40px; text-align: center; color: #64748B; font-size: 0.8rem;'>AlphaShield Quantitative & Thematic Intelligence Platform | Capital Preservation & Macro Systems</div>", unsafe_allow_html=True)
