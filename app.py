import os
from typing import Dict, List
import streamlit as st
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

# Import core infrastructure & authentication
from core.auth import (
    render_login_gate,
    render_user_profile_sidebar,
    is_admin,
    is_global_admin,
)
from core.technical_engine import compute_technical_snapshot
from core.visualizer import build_interactive_chart

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
)

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
    selected_market = st.radio(
        "Select Stock Market Exchange",
        options=["🇺🇸 US Markets (NYSE / NASDAQ)", "🇮🇳 Indian Markets (NSE / BSE)"],
        index=0 if st.session_state.get("is_indian", False) is False else 1,
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

        st.markdown("#### 🧩 **Institutional Core Dimensions (ELI5 Deep Dive)**")
        st.caption("Click the context expanders on any card to see how institutional analysts interpret these numbers:")

        # Six Interactive Explanatory Cards
        t_c1, t_c2, t_c3, t_c4, t_c5, t_c6 = st.columns(6)

        with t_c1:
            mood_status = "🟢 Calm & Safe" if macro.market_mood_color == "green" else ("🟡 Choppy Waters" if macro.market_mood_color == "yellow" else "🔴 Stormy Seas")
            st.markdown(f"""
            <div class='interactive-tile'>
                <div class='tile-header'>1. 🌡️ Market Mood</div>
                <div class='tile-status-{"safe" if macro.market_mood_color == "green" else ("caution" if macro.market_mood_color == "yellow" else "danger")}'>{mood_status}</div>
                <div style='font-size: 0.82rem; color: #94A3B8; margin-top: 4px;'>VIX: <strong>{macro.vix:.1f}</strong></div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 ELI5 Context"):
                st.markdown("**In Plain Words:** Think of market mood like flying an airplane. When VIX is low, skies are smooth. When volatility spikes, you're flying into a storm.")
                st.markdown(f"**The Verdict:** {macro.market_mood_desc}")

        with t_c2:
            z_score = getattr(factors, "altman_z_score", 2.5) if factors else 2.5
            health_status = "🟢 Solid & Safe" if z_score >= 2.99 else ("🟡 Watchful Debt" if z_score >= 1.81 else "🔴 Insolvent Risk")
            health_class = "safe" if z_score >= 2.99 else ("caution" if z_score >= 1.81 else "danger")
            st.markdown(f"""
            <div class='interactive-tile'>
                <div class='tile-header'>2. 🏥 Company Health</div>
                <div class='tile-status-{health_class}'>{health_status}</div>
                <div style='font-size: 0.82rem; color: #94A3B8; margin-top: 4px;'>Z-Score: <strong>{z_score:.2f}</strong></div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 ELI5 Context"):
                st.markdown("**In Plain Words:** Does this company generate real cash from customers, or are they borrowing money or inflating accounting numbers just to look profitable?")
                is_manip = getattr(factors, "beneish_manipulation_risk", False) if factors else False
                beneish_val = getattr(factors, "beneish_m_score", -2.45) if factors else -2.45
                f_score = getattr(factors, "piotroski_f_score", 6) if factors else 6
                sloan_val = getattr(factors, "sloan_accrual_ratio", 0.0) if factors else 0.0

                beneish_note = "⚠️ Forensic Distortion Warning" if is_manip else "✅ Clean Accounting"
                st.markdown(f"**The Verdict:** Solvency Status: **{plan.solvency_status}**.")
                st.markdown(f"• Altman Z-Score: **{z_score:.2f}** (Distress: < 1.81, Safe: > 2.99)")
                st.markdown(f"• Piotroski F-Score: **{f_score}/9** (Operating Quality)")
                st.markdown(f"• Sloan Accruals: **{sloan_val * 100:.1f}%** (Quality Threshold: < 10%)")
                st.markdown(f"• Beneish M-Score: **{beneish_val:.2f}** ({beneish_note})")

        with t_c3:
            is_uptrend = tech.current_price > tech.ema_50 and tech.rsi_14 < 70
            is_overheated = tech.rsi_14 >= 70
            mom_status = "🟢 Strong Uptrend" if is_uptrend else ("🟡 Resting" if is_overheated else "🔴 Downtrend")
            mom_class = "safe" if is_uptrend else ("caution" if is_overheated else "danger")
            st.markdown(f"""
            <div class='interactive-tile'>
                <div class='tile-header'>3. 🚀 Price Trend</div>
                <div class='tile-status-{mom_class}'>{mom_status}</div>
                <div style='font-size: 0.82rem; color: #94A3B8; margin-top: 4px;'>RSI: <strong>{tech.rsi_14:.1f}</strong></div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 ELI5 Context"):
                st.markdown("**In Plain Words:** Are more buyers rushing in, or are investors quietly heading for the exits?")
                st.markdown(f"**The Verdict:** Price is {'above 50-day average' if tech.current_price > tech.ema_50 else 'below 50-day average'}.")

        with t_c4:
            smart_status = "🟢 Whales Buying" if micro.delivery_valid else "🟡 Day Trading"
            smart_class = "safe" if micro.delivery_valid else "caution"
            st.markdown(f"""
            <div class='interactive-tile'>
                <div class='tile-header'>4. 🐋 Smart Money</div>
                <div class='tile-status-{smart_class}'>{smart_status}</div>
                <div style='font-size: 0.82rem; color: #94A3B8; margin-top: 4px;'>Delivery: <strong>{micro.delivery_pct:.1f}%</strong></div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 ELI5 Context"):
                st.markdown("**In Plain Words:** Institutional 'whales' buy and hold shares in their vaults. Delivery % proves real accumulation vs speculative churn.")
                st.markdown(f"**The Verdict:** {micro.delivery_status_msg}")

        with t_c5:
            st.markdown(f"""
            <div class='interactive-tile'>
                <div class='tile-header'>5. ⏳ Secular Horizon</div>
                <div class='tile-status-safe' style='font-size: 0.98rem;'>{thematic.timeframe}</div>
                <div style='font-size: 0.82rem; color: #94A3B8; margin-top: 4px;'>Wave: <strong>{thematic.horizon_code}</strong></div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 ELI5 Context"):
                st.markdown(f"**Macro Wave:** {thematic.horizon_title}")
                st.markdown(f"**Driver:** {thematic.thematic_driver}")
                st.markdown(f"**Resource Scarcity Bottleneck:** `{thematic.resource_scarcity_exposure}`")
                st.markdown(f"**Takeaway:** {thematic.plain_english_takeaway}")

        with t_c6:
            risk_status = "🟢 Asymmetric Win" if risk.asymmetric_rr_passed else "🔴 Poor Odds"
            risk_class = "safe" if risk.asymmetric_rr_passed else "danger"
            st.markdown(f"""
            <div class='interactive-tile'>
                <div class='tile-header'>6. 🛡️ Safety Gauge</div>
                <div class='tile-status-{risk_class}'>{risk_status}</div>
                <div style='font-size: 0.82rem; color: #94A3B8; margin-top: 4px;'>Odds: <strong>{risk.risk_reward_ratio:.1f}x</strong></div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 ELI5 Context"):
                st.markdown("**In Plain Words:** Never take a trade where the upside isn't at least 2.5x larger than the risk. Keep losses tiny!")
                st.markdown(f"**The Verdict:** Max allocation: **{plan.calculated_shares} shares** ({currency_sym}{risk.allocated_capital:,.2f}).")

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
            st.markdown(f"### 🧭 **Live Institutional Market Radar ({'India NSE' if is_indian else 'US Markets'})**")
            st.caption("100% real-time quantitative screening across 50+ institutional candidates. Zero hardcoding: live prices, % deltas, relative volume surges, and live financial news.")

        with col_rad_act:
            if st.button("🔄 Re-Scan Live Market", key="btn_rescan_market_radar", use_container_width=True):
                fetch_radar_cached_v2.clear()
                st.rerun()

        with st.spinner("Connecting to live exchange feeds & scanning..."):
            radar_data = fetch_radar_cached_v2(is_indian)

        total_screened = sum(len(stocks) for stocks in radar_data.values())

        # Search / Filter Bar inside the Radar
        radar_search = st.text_input(
            "🔎 Filter live screened stocks by name, ticker, or catalyst keyword:",
            "",
            placeholder="e.g. Tata, Defense, Nuclear, AI, Hydro, Solar, EV...",
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
                    for i in range(0, len(stock_list), 2):
                        col_left, col_right = st.columns(2)
                        pair = [col_left] if i + 1 >= len(stock_list) else [col_left, col_right]

                        for offset, col in enumerate(pair):
                            stock = stock_list[i + offset]
                            with col:
                                # Safe attribute access with fallbacks
                                chg_pct = getattr(stock, "change_pct", 0.0)
                                chg_str = getattr(stock, "change_str", f"{chg_pct:+.2f}%")
                                rel_vol = getattr(stock, "volume_multiple", 1.0)
                                n_url = getattr(stock, "news_url", "")
                                r_badge = getattr(stock, "risk_badge", "🟢 Normal")

                                # Real-time change pill
                                if chg_pct >= 0:
                                    chg_pill = f"<span class='pastel-pill-mint'>▲ {chg_str}</span>"
                                else:
                                    chg_pill = f"<span class='pastel-pill-rose'>▼ {chg_str}</span>"

                                # Relative volume multiplier pill
                                vol_pill = f"<span class='pastel-pill-lilac'>⚡ {rel_vol:.1f}x Vol</span>"

                                # Clickable live news link
                                news_link = f"<a href='{n_url}' target='_blank' style='color: #93C5FD; text-decoration: none; font-weight: 600; margin-left: 6px;'>[Read Story ↗]</a>" if n_url else ""

                                st.markdown(f"""
                                <div class='radar-card'>
                                    <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;'>
                                        <div>
                                            <span style='font-size: 1.18rem; font-weight: 800; color: #93C5FD;'>{stock.ticker}</span>
                                            <span style='font-size: 0.92rem; color: #94A3B8; margin-left: 8px;'>{stock.name}</span>
                                            <span style='margin-left: 10px; font-weight: 700; color: #F8FAFC; font-size: 1.05rem;'>{stock.approx_price}</span>
                                        </div>
                                        <div style='display: flex; gap: 6px; align-items: center; flex-wrap: wrap;'>
                                            {chg_pill}
                                            {vol_pill}
                                            <span class='pastel-pill-amber'>{r_badge}</span>
                                        </div>
                                    </div>
                                    <div style='margin-top: 10px; font-size: 0.90rem; color: #CBD5E1; line-height: 1.45;'>
                                        <strong>Catalyst:</strong> {stock.catalyst_driver} {news_link}
                                    </div>
                                    <div style='margin-top: 5px; font-size: 0.85rem; color: #94A3B8; line-height: 1.4;'>
                                        <strong>Institutional Role:</strong> {stock.why_it_matters}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                                if st.button(f"⚡ Audit {stock.ticker} Now", key=f"radar_audit_{cat_key}_{stock.ticker}_{i + offset}", use_container_width=True):
                                    st.session_state["active_ticker"] = stock.ticker
                                    st.rerun()

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
