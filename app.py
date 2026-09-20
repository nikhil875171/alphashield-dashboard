import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Import core analytical modules
from core.schemas import AlphaShieldRecommendation
from core.macro_engine import get_macro_snapshot
from core.fundamental_engine import audit_fundamental_health
from core.technical_engine import compute_technical_snapshot
from core.sentiment_engine import fetch_sentiment_analysis
from core.institutional_engine import audit_institutional_positioning
from core.risk_manager import calculate_risk_parameters
from core.gemini_advisor import evaluate_alpha_shield
from core.visualizer import build_interactive_chart
from core.auth import (
    render_login_gate,
    render_user_profile_sidebar,
    is_admin,
    is_global_admin,
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
    page_title="AlphaShield | Institutional Multi-Factor Alpha",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Institutional Dark Theme CSS
st.markdown("""
<style>
    /* Dark background styling */
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #151B26;
        border: 1px solid #232D3F;
        border-radius: 8px;
        padding: 10px 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.35rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    /* Action Badges */
    .badge-buy {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%);
        color: white;
        padding: 6px 18px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.25rem;
        display: inline-block;
        letter-spacing: 0.05em;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
    }
    .badge-sell {
        background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%);
        color: white;
        padding: 6px 18px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.25rem;
        display: inline-block;
        letter-spacing: 0.05em;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
    }
    .badge-hold {
        background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%);
        color: white;
        padding: 6px 18px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.25rem;
        display: inline-block;
        letter-spacing: 0.05em;
    }
    .badge-avoid {
        background: linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%);
        color: white;
        padding: 6px 18px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.25rem;
        display: inline-block;
        letter-spacing: 0.05em;
        box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
    }
    /* Accordion Customization */
    .streamlit-expanderHeader {
        background-color: #151B26;
        border-radius: 6px;
        font-weight: 600;
        color: #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. ENFORCE ROLE-BASED AUTHENTICATION GATE ---
if not render_login_gate():
    st.stop()

# Cached macro telemetry
@st.cache_data(ttl=300)
def fetch_macro_cached(is_indian: bool):
    return get_macro_snapshot(is_indian_market=is_indian)


# --- SIDEBAR: CONTROLS & PARAMETERS ---
with st.sidebar:
    # Render user profile & Sign out button
    render_user_profile_sidebar()

    st.markdown("### 🛡️ **AlphaShield Controls**")
    st.caption("Institutional Quantitative Parameters")


    ticker_input = st.text_input(
        "Asset Ticker (NSE or Global)",
        value="RELIANCE.NS",
        help="Use .NS for Indian National Stock Exchange (e.g. RELIANCE.NS, TCS.NS, INFY.NS) or standard symbols for US (e.g. NVDA, AAPL)."
    ).strip().upper()

    st.markdown("---")
    st.markdown("#### 💼 **Capital Allocation & Risk**")

    account_size = st.number_input(
        "Total Account Capital (₹ / $)",
        min_value=10_000.0,
        max_value=1_000_000_000.0,
        value=1_000_000.0,
        step=50_000.0,
        format="%.2f",
    )

    risk_pct = st.slider(
        "Max Risk Capital per Trade (%)",
        min_value=0.5,
        max_value=2.5,
        value=1.5,
        step=0.1,
        help="Institutional Zero-Ruin rule mandates maximum 1.0% to 2.0% risk per trade.",
    )

    atr_multiplier = st.slider(
        "Dynamic ATR Stop Multiplier",
        min_value=1.2,
        max_value=3.0,
        value=1.8,
        step=0.1,
        help="Distance for algorithmic hard stop-loss: Entry - (Multiplier * ATR).",
    )

    target_rr = st.slider(
        "Minimum Required R:R Ratio",
        min_value=2.0,
        max_value=4.0,
        value=2.5,
        step=0.1,
        help="Asymmetric gate: Trades below this target ratio are automatically flagged as AVOID.",
    )

    st.markdown("---")
    st.markdown("#### 🤖 **AI Decision Engine**")
    model_choice = st.selectbox(
        "Gemini Model",
        options=["gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3.6-flash"],
        index=0,
        help="Ultra-fast, zero-throttling production Gemini models with multi-tier fallback."
    )




    run_btn = st.button("🚀 Run Multi-Factor Audit", use_container_width=True, type="primary")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "YOUR_GEMINI_API_KEY_HERE":
        st.warning("⚠️ **GEMINI_API_KEY** not set in `.env`. Running on Algorithmic Rule Engine.", icon="⚠️")
    else:
        st.success("🟢 Gemini Pro Engine Active", icon="✅")

# --- HEADER: MACRO TELEMETRY TICKER RIBBON ---
is_indian = ticker_input.endswith(".NS") or ticker_input.endswith(".BO")
with st.spinner("Synchronizing Macro & Geopolitical Telemetry..."):
    macro = fetch_macro_cached(is_indian)

# Macro ribbon metrics
m1, m2, m3, m4, m5, m6 = st.columns(6)
with m1:
    regime_color = "#10B981" if macro.macro_regime == "EXPANSION" else ("#EF4444" if macro.macro_regime == "DEFENSIVE" else "#F59E0B")
    st.metric(
        "Macro Regime",
        macro.macro_regime,
        delta="Stress High" if macro.volatility_kill_switch_active else "Stable",
        delta_color="inverse" if macro.volatility_kill_switch_active else "normal"
    )
with m2:
    st.metric(
        "10Y-2Y Yield Spread",
        f"{macro.yield_spread_10y_2y:.2f}%",
        delta="Inverted" if macro.yield_spread_10y_2y < 0 else "Normal",
        delta_color="inverse" if macro.yield_spread_10y_2y < 0 else "normal"
    )
with m3:
    vix_label = "India VIX" if is_indian else "CBOE VIX"
    st.metric(
        vix_label,
        f"{macro.vix:.2f}",
        delta="Kill-Switch Alert" if macro.volatility_kill_switch_active else "Controlled",
        delta_color="inverse" if macro.volatility_kill_switch_active else "normal"
    )
with m4:
    st.metric("Dollar Index (DXY)", f"{macro.dxy:.2f}")
with m5:
    st.metric("Crude Oil (WTI)", f"${macro.crude_oil:.2f}")
with m6:
    st.metric("Gold (Comex)", f"${macro.gold:.2f}")

st.markdown("<hr style='margin: 12px 0; border-color: #232D3F;'>", unsafe_allow_html=True)


# --- MAIN COMPUTATION PIPELINE ---
def execute_pipeline():
    with st.spinner(f"Ingesting Multi-Factor Telemetry for {ticker_input}..."):
        try:
            # 1. Technical Microstructure
            tech, df = compute_technical_snapshot(ticker_input, period="1y", interval="1d")

            # 2. Fundamental Solvency Sieve
            fund = audit_fundamental_health(ticker_input)

            # 3. Sentiment & Euphoria Sieve
            sent = fetch_sentiment_analysis(ticker_input, rsi=tech.rsi_14)

            # 4. Smart Money / Institutional
            inst = audit_institutional_positioning(ticker_input)

            # 5. Zero-Ruin Risk Calculations (Target 1 based on Asymmetric Target)
            # Default projected target = current price + (target_rr * stop_distance)
            stop_distance = max(tech.atr_14 * atr_multiplier, tech.current_price * 0.015)
            projected_target = round(tech.current_price + (target_rr * stop_distance), 2)

            risk = calculate_risk_parameters(
                account_size=account_size,
                current_price=tech.current_price,
                atr=tech.atr_14,
                target_price=projected_target,
                risk_pct=risk_pct,
                atr_multiplier=atr_multiplier,
                volatility_kill_switch=macro.volatility_kill_switch_active,
            )

            # 6. Gemini Pro Structured Reasoning
            rec = evaluate_alpha_shield(tech, fund, macro, sent, inst, risk, model_name=model_choice)

            return tech, df, fund, sent, inst, risk, rec

        except Exception as err:
            st.error(f"Execution Error: {err}")
            return None, None, None, None, None, None, None


tech, df, fund, sent, inst, risk, rec = execute_pipeline()

if tech and df is not None and rec:
    # --- TOP ROW: AI ACTION MANDATE CARD ---
    col_badge, col_conviction, col_rr, col_size, col_loss = st.columns([1.5, 1.2, 1.2, 1.6, 1.6])

    with col_badge:
        st.markdown(f"### **{rec.ticker}**")
        if rec.action == "BUY":
            badge_html = f"<div class='badge-buy'>BUY MANDATE</div>"
        elif rec.action == "SELL":
            badge_html = f"<div class='badge-sell'>SHORT / EXIT</div>"
        elif rec.action == "HOLD":
            badge_html = f"<div class='badge-hold'>HOLD / WAIT</div>"
        else:
            badge_html = f"<div class='badge-avoid'>AVOID (HIGH RISK)</div>"
        st.markdown(badge_html, unsafe_allow_html=True)

    with col_conviction:
        st.metric("Conviction Score", f"{rec.conviction_score * 100:.0f}%", delta=rec.risk_regime)

    with col_rr:
        st.metric(
            "Risk / Reward",
            f"{risk.risk_reward_ratio_1}:1",
            delta="Asymmetric Pass" if risk.asymmetric_rr_passed else "Below 2.5x Gate",
            delta_color="normal" if risk.asymmetric_rr_passed else "inverse"
        )

    with col_size:
        st.metric(
            "Max Position Sizing",
            f"{risk.position_size_shares:,} Shares",
            delta=f"₹/{risk.total_allocated_capital:,.0f} ({risk.portfolio_allocation_pct}%)"
        )

    with col_loss:
        st.metric(
            "Max Downside at Risk",
            f"₹/{risk.risk_capital_amount:,.2f}",
            delta=f"Capped at {risk.risk_pct_selected}%"
        )

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # --- CENTRAL PLOTLY INTERACTIVE CHART ---
    fig = build_interactive_chart(df, tech, rec)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})

    # --- BOTTOM SECTION: FACTOR SIEVE ACCORDIONS & GOVERNANCE ---
    tab_titles = [
        "🧠 Multi-Factor Thesis & Kill-Switches",
        "⚖️ Fundamental Solvency (Altman & Piotroski)",
        "📊 Technical Microstructure & Volatility",
        "👥 Crowdsourced Sentiment & Smart Money",
    ]

    if is_global_admin():
        tab_titles.append("👑 Global Governance (nikhil875171 Only)")
    elif is_admin():
        tab_titles.append("🛡️ Admin Operational Telemetry")

    tabs = st.tabs(tab_titles)
    t1, t2, t3, t4 = tabs[0], tabs[1], tabs[2], tabs[3]

    with t1:
        c_thesis, c_kill = st.columns([1.5, 1.0])
        with c_thesis:
            st.markdown("#### **Executive Multi-Factor Rationale**")
            for factor, rationale in rec.multi_factor_thesis.items():
                st.markdown(f"**• {factor}:** {rationale}")

        with c_kill:
            st.markdown("#### **🚨 Primary Kill-Switches**")
            st.caption("Immediate thesis invalidation triggers:")
            for ks in rec.primary_kill_switches:
                st.markdown(f"- 🔴 `{ks}`")

            st.markdown("---")
            st.markdown(f"**Recommended Entry Zone:** ₹{rec.recommended_entry_range[0]} – ₹{rec.recommended_entry_range[1]}")
            st.markdown(f"**Hard Stop-Loss:** ₹{rec.hard_stop_loss}")
            st.markdown(f"**Target Price Ladder:** {', '.join([f'₹{t}' for t in rec.target_price_ladder])}")

    with t2:
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            z_val = f"{fund.altman_z_score:.2f}" if fund.altman_z_score is not None else "N/A"
            st.metric("Altman Z-Score (Solvency)", z_val, delta=fund.altman_zone, delta_color="normal" if "Safe" in fund.altman_zone else "inverse")
        with f2:
            f_val = f"{fund.piotroski_f_score}/9" if fund.piotroski_f_score is not None else "N/A"
            st.metric("Piotroski F-Score", f_val, delta=fund.piotroski_grade, delta_color="normal" if "Strong" in fund.piotroski_grade else "inverse")
        with f3:
            de_val = f"{fund.debt_to_equity}x" if fund.debt_to_equity is not None else "N/A"
            st.metric("Debt to Equity", de_val)
        with f4:
            roe_val = f"{fund.roe}%" if fund.roe is not None else "N/A"
            st.metric("Return on Equity (ROE)", roe_val)

        if fund.audit_notes:
            st.markdown("##### **Fundamental Audit Findings:**")
            for note in fund.audit_notes:
                st.info(note)

    with t3:
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.metric("RSI (14-Day)", f"{tech.rsi_14:.2f}", delta="Overbought" if tech.rsi_14 > 70 else ("Oversold" if tech.rsi_14 < 30 else "Balanced"))
        with p2:
            st.metric("ATR (14-Day Volatility)", f"₹{tech.atr_14:.2f}", delta=f"{((tech.atr_14 / tech.current_price) * 100):.2f}% of price")
        with p3:
            st.metric("Volume Surge vs ADV", f"{tech.volume_surge_ratio:.2f}x", delta="Above Average" if tech.volume_surge_ratio > 1.0 else "Normal")
        with p4:
            st.metric("Estimated Bid-Ask Slippage", f"{tech.estimated_spread_impact_pct:.2f}%")

        st.markdown("##### **Moving Average Architecture:**")
        ma_col1, ma_col2, ma_col3, ma_col4 = st.columns(4)
        ma_col1.write(f"**20 EMA:** ₹{tech.ema_20}")
        ma_col2.write(f"**50 EMA:** ₹{tech.ema_50}")
        ma_col3.write(f"**200 EMA:** ₹{tech.ema_200}")
        ma_col4.write(f"**VWAP:** ₹{tech.vwap}")

    with t4:
        s1, s2 = st.columns([1, 1])
        with s1:
            st.markdown("#### **Crowdsourced & News Sentiment**")
            st.metric("Sentiment Score", f"{sent.sentiment_score:+.2f}", delta=sent.sentiment_label)
            if sent.retail_euphoria_flag:
                st.error("🚨 **Retail Euphoria Warning:** Crowd sentiment is excessively bullish while technical indicators reflect extreme overbought conditions. High risk of contrarian pullback!")
            else:
                st.success("✅ No Retail Euphoria Divergence detected.")

            st.markdown("##### **Recent Curated Headlines:**")
            for news in sent.recent_news[:4]:
                st.markdown(f"- [{news['title']}]({news['link']}) *({news['source']} — {news['sentiment']})*")

        with s2:
            st.markdown("#### **Smart Money & Institutional Positioning**")
            st.metric("Institutional Holding", f"{inst.institutional_ownership_pct}%" if inst.institutional_ownership_pct else "N/A")
            st.metric("Insider / Promoter Ownership", f"{inst.insider_ownership_pct}%" if inst.insider_ownership_pct else "N/A")
            st.metric("Short Float Interest", f"{inst.short_float_pct}%" if inst.short_float_pct else "N/A")
            st.info(f"**Positioning Signal:** {inst.institutional_signal}")

    # --- 5th TAB: GOVERNANCE & PRIVILEGED CONTROLS ---
    if is_global_admin():
        with tabs[4]:
            st.markdown("### 👑 **Global Governance & Root Authority**")
            st.success("🔐 **Authenticated as Global Administrator (`nikhil875171`).** Complete root governance active.", icon="👑")

            gov_col1, gov_col2 = st.columns([1, 1])
            with gov_col1:
                st.markdown("#### 🚨 **Fund Risk Overrides**")
                cash_lock = st.toggle("Force Fund-Wide 100% Cash Defense", value=st.session_state.get("emergency_cash_lock", False))
                st.session_state["emergency_cash_lock"] = cash_lock
                if cash_lock:
                    st.error("⚠️ Emergency Cash Defense ENGAGED: All trades overridden to AVOID.", icon="🚨")
                else:
                    st.info("System operating under normal quantitative risk governance.")

                st.markdown("#### 🔑 **Root API Telemetry**")
                api_k = os.getenv("GEMINI_API_KEY", "")
                masked_k = (api_k[:7] + "..." + api_k[-4:]) if len(api_k) > 12 else "Not Configured"
                st.write(f"**Gemini API Key:** `{masked_k}`")
                st.write(f"**Default Model Cascade:** `gemini-flash-lite-latest` ➔ `gemini-3.1-flash-lite`")

            with gov_col2:
                st.markdown("#### 👥 **Authorized Personnel Registry**")
                st.markdown("""
                | Identity | Assigned Role | Permissions |
                | :--- | :--- | :--- |
                | `nikhil875171` | **Global Administrator** | Complete Root & Governance Rights |
                | `nkk_admin` | **System Administrator** | Operational Telemetry & Monitoring |
                | `nkk_user` | **Standard Analyst** | Asset Analysis & Chart Access |
                """)

    elif is_admin():
        with tabs[4]:
            st.markdown("### 🛡️ **Administrator Operational Telemetry**")
            st.info("Logged in as Administrator (`nkk_admin`). Standard operations active.")
            a_col1, a_col2 = st.columns(2)
            with a_col1:
                st.metric("System Health", "ONLINE", delta="All Engines Operational")
                st.metric("Active Model", model_choice)
            with a_col2:
                st.metric("Session Mode", "Authenticated Admin")
                st.caption("Note: Root policy changes and emergency kill-switches are restricted to Global Administrator (nikhil875171).")

st.markdown("<div style='margin-top: 40px; text-align: center; color: #64748B; font-size: 0.8rem;'>AlphaShield Institutional Capital Preservation System | For Educational & Quantitative Decision-Support Only</div>", unsafe_allow_html=True)


