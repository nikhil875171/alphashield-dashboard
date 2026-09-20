import os
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

# Import institutional quantitative modules
from src.macro_engine import compute_macro_transmission, MacroRegimeState
from src.transmission_tree import detect_company_catalyst, get_supply_chain_spillover
from src.microstructure import validate_microstructure, MicrostructureValidation
from src.factor_model import evaluate_factor_model, FactorScoreSummary
from src.trap_guards import evaluate_all_traps
from src.risk_engine import calculate_algorithmic_execution, ExecutionRiskReport
from src.ai_agent import generate_institutional_trade_plan, InstitutionalTradePlan

load_dotenv()

# Bridge Streamlit Cloud secrets to os.environ if running on cloud
try:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# Page configuration
st.set_page_config(
    page_title="AlphaShield | Institutional Quantitative Engine",
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
        font-size: 0.80rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.30rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    /* Action Badges */
    .badge-buy {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%);
        color: white;
        padding: 8px 22px;
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
        padding: 8px 22px;
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
        padding: 8px 22px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.25rem;
        display: inline-block;
        letter-spacing: 0.05em;
    }
    .badge-avoid {
        background: linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%);
        color: white;
        padding: 8px 22px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 1.25rem;
        display: inline-block;
        letter-spacing: 0.05em;
        box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
    }
    .spillover-box {
        background-color: #151B26;
        border: 1px solid #232D3F;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .spillover-title {
        color: #38BDF8;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 6px;
    }
    .trap-card {
        background-color: #151B26;
        border: 1px solid #232D3F;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. ENFORCE ROLE-BASED AUTHENTICATION GATE ---
if not render_login_gate():
    st.stop()

# Cached macro telemetry
@st.cache_data(ttl=300)
def fetch_macro_cached(is_indian: bool) -> MacroRegimeState:
    return compute_macro_transmission(is_indian_market=is_indian)


# --- SIDEBAR: CONTROLS & PARAMETERS ---
with st.sidebar:
    # Render user profile & Sign out button
    render_user_profile_sidebar()

    st.markdown("### 🛡️ **Execution Parameters**")
    st.caption("Institutional Quantitative Risk Gates")

    ticker_input = st.text_input(
        "Asset Ticker (NSE or Global)",
        value="RELIANCE.NS",
        help="Use .NS for Indian National Stock Exchange (e.g. RELIANCE.NS, TCS.NS, INFY.NS) or standard US tickers (e.g. NVDA, AAPL, MSFT)."
    ).strip().upper()

    st.markdown("---")
    st.markdown("#### 💼 **Capital Allocation**")

    account_size = st.number_input(
        "Total Portfolio Equity (₹ / $)",
        min_value=10_000.0,
        max_value=1_000_000_000.0,
        value=1_000_000.0,
        step=50_000.0,
        format="%.2f",
    )

    risk_pct = st.slider(
        "Max Equity at Risk per Trade (%)",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="Institutional Zero-Ruin rule mandates maximum 1.0% capital risk per trade.",
    )

    atr_multiplier = st.slider(
        "Dynamic ATR Hard Stop Multiplier",
        min_value=1.4,
        max_value=2.6,
        value=1.8,
        step=0.1,
        help="Algorithmic hard stop distance: Entry - (Multiplier * ATR). Dynamically scaled by VIX regime.",
    )

    target_rr = st.slider(
        "Asymmetric Target R:R Ratio",
        min_value=2.0,
        max_value=4.0,
        value=2.5,
        step=0.1,
        help="Mathematical gate: Trades projecting below this target ratio are gated as AVOID.",
    )

    st.markdown("---")
    st.markdown("#### 🤖 **AI Decision Engine**")
    model_choice = st.selectbox(
        "Gemini Model",
        options=["gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3.6-flash"],
        index=0,
        help="Ultra-fast production Gemini models with automated multi-tier fallback cascade."
    )

    run_btn = st.button("🚀 Run Institutional Audit", use_container_width=True, type="primary")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "YOUR_GEMINI_API_KEY_HERE":
        st.warning("⚠️ **GEMINI_API_KEY** not configured. Running on Institutional Rule Engine.", icon="⚠️")
    else:
        st.success("🟢 Gemini Decision Engine Active", icon="✅")


# --- HEADER: CROSS-ASSET MACRO TRANSMISSION RIBBON ---
is_indian = ticker_input.endswith(".NS") or ticker_input.endswith(".BO")
with st.spinner("Synchronizing Cross-Asset Macro Transmission Feeds..."):
    macro = fetch_macro_cached(is_indian)

# Macro ribbon display (6 clean cards)
m1, m2, m3, m4, m5, m6 = st.columns(6)

with m1:
    st.metric(
        "Macro Regime",
        macro.regime_label,
        delta=f"Liquidity: {macro.liquidity_bias:+.1f}",
        delta_color="normal" if macro.regime_label == "EXPANSION" else "inverse"
    )

with m2:
    vix_label = "India VIX" if is_indian else "CBOE VIX"
    scale_label = f"Scale: {int(macro.position_scale_factor * 100)}%"
    st.metric(
        vix_label,
        f"{macro.vix:.2f}",
        delta=scale_label,
        delta_color="normal" if macro.position_scale_factor >= 1.0 else "inverse"
    )

with m3:
    st.metric(
        "10Y-2Y Yield Spread",
        f"{macro.yield_spread:+.2f}%",
        delta=macro.yield_curve_state,
        delta_color="inverse" if macro.yield_spread < 0 else "normal"
    )

with m4:
    dxy_delta = f"{macro.dxy_20d_roc:+.1f}% 20d"
    st.metric(
        "Dollar Index (DXY)",
        f"{macro.dxy:.2f}",
        delta=dxy_delta,
        delta_color="inverse" if macro.dxy_20d_roc > 2.0 else "normal"
    )

with m5:
    st.metric(
        "Crude Oil (WTI)",
        f"${macro.crude_oil:.2f}",
        delta="Demand Shock" if macro.crude_demand_destruction else "Normal Range",
        delta_color="inverse" if macro.crude_demand_destruction else "normal"
    )

with m6:
    st.metric(
        "Dr. Copper / Gold",
        f"{macro.copper_gold_ratio:.4f}",
        delta=macro.industrial_momentum,
        delta_color="normal" if "Expansionary" in macro.industrial_momentum else "inverse"
    )

st.markdown("<hr style='margin: 12px 0; border-color: #232D3F;'>", unsafe_allow_html=True)


# --- MAIN PIPELINE EXECUTION ---
def execute_institutional_pipeline():
    with st.spinner(f"Auditing Multi-Factor Telemetry & Order Flow for {ticker_input}..."):
        try:
            # 1. Technical Microstructure & OHLCV
            tech, df = compute_technical_snapshot(ticker_input, period="1y", interval="1d")
            if df.empty:
                st.error(f"Failed to fetch historical market data for {ticker_input}. Please verify the ticker symbol.")
                return None, None, None, None, None, None, None, None

            # 2. Company Info & Metadata
            try:
                t = yf.Ticker(ticker_input)
                info = t.info or {}
            except Exception:
                info = {}

            # 3. Solvency Sieve & 4-Pillar Factor Model
            factors = evaluate_factor_model(ticker_input, df, info=info)

            # 4. Microstructure & Order Flow Validation
            micro = validate_microstructure(ticker_input, df, info=info)

            # 5. Heuristic Trap Guards
            traps = evaluate_all_traps(df, info=info)

            # 6. Sectoral Spillover Tree
            sector_val = info.get("sector", "")
            ind_val = info.get("industry", "")
            cat_key = detect_company_catalyst(ticker_input, sector=sector_val, industry=ind_val)
            spillovers = get_supply_chain_spillover(cat_key)

            # 7. Algorithmic Risk & Capital Preservation Engine
            # Check Global Admin Emergency Cash Lock
            cash_defense = st.session_state.get("emergency_cash_lock", False)

            # Dynamic target projection: resistance or ATR multiplier
            stop_dist = max(tech.atr_14 * atr_multiplier, tech.current_price * 0.015)
            proj_target = round(tech.current_price + (target_rr * stop_dist), 2)

            risk = calculate_algorithmic_execution(
                portfolio_equity=account_size,
                current_price=tech.current_price,
                atr=tech.atr_14,
                macro=macro,
                resistance_target=proj_target,
                user_risk_pct=risk_pct,
            )

            # Handle Global Admin emergency cash defense
            if cash_defense:
                risk.calculated_shares = 0
                risk.allocated_capital = 0.0
                risk.execution_verdict = "REJECT_EMERGENCY_CASH_LOCK"
                risk.risk_guardrail_notes.append("Emergency Cash Defense ENGAGED by Global Administrator.")

            # 8. Gemini Pro Structured Decision Engine
            trade_plan = generate_institutional_trade_plan(
                ticker=ticker_input,
                macro=macro,
                micro=micro,
                factors=factors,
                traps=traps,
                spillovers=spillovers,
                risk=risk,
                model_name=model_choice,
            )

            # Override action if emergency cash lock engaged
            if cash_defense:
                trade_plan.action = "AVOID"
                trade_plan.calculated_shares = 0

            return tech, df, factors, micro, traps, spillovers, risk, trade_plan

        except Exception as err:
            st.error(f"Pipeline Execution Anomaly: {err}")
            return None, None, None, None, None, None, None, None


tech, df, factors, micro, traps, spillovers, risk, plan = execute_institutional_pipeline()

if tech and df is not None and plan:
    # --- TOP ROW: PRIMARY EXECUTION MANDATE CARD (THE GLANCE) ---
    col_badge, col_conviction, col_rr, col_size, col_loss = st.columns([1.5, 1.2, 1.2, 1.6, 1.6])

    with col_badge:
        st.markdown(f"### **{plan.ticker}**")
        if plan.action == "BUY":
            badge_html = "<div class='badge-buy'>BUY MANDATE</div>"
        elif plan.action == "SELL":
            badge_html = "<div class='badge-sell'>SHORT / EXIT</div>"
        elif plan.action == "HOLD":
            badge_html = "<div class='badge-hold'>HOLD / WAIT</div>"
        else:
            badge_html = "<div class='badge-avoid'>AVOID (HIGH RISK)</div>"
        st.markdown(badge_html, unsafe_allow_html=True)

    with col_conviction:
        st.metric(
            "Conviction Score",
            f"{plan.conviction_score * 100:.0f}%",
            delta=f"Regime: {plan.macro_regime}"
        )

    with col_rr:
        st.metric(
            "Risk / Reward",
            f"{risk.risk_reward_ratio:.2f}:1",
            delta="Asymmetric Pass" if risk.asymmetric_rr_passed else "Below 2.5x Gate",
            delta_color="normal" if risk.asymmetric_rr_passed else "inverse"
        )

    with col_size:
        st.metric(
            "Calculated Position",
            f"{plan.calculated_shares:,} Shares",
            delta=f"₹/{risk.allocated_capital:,.0f} ({risk.portfolio_allocation_pct:.1f}% Equity)"
        )

    with col_loss:
        st.metric(
            "Max Capital at Risk",
            f"₹/{risk.max_equity_at_risk:,.2f}",
            delta=f"Hard Stop: ₹{plan.algorithmic_stop_loss}"
        )

    # Prominent Capital Sieve / Warning Banner if active
    if factors.sieve_verdict != "PASS":
        st.error(
            f"🚨 **Zero-Ruin Capital Preservation Sieve Active ({factors.sieve_verdict})**: "
            f"{'; '.join(factors.sieve_rejection_reasons)}. Capital allocation blocked.",
            icon="🛡️"
        )
    elif st.session_state.get("emergency_cash_lock", False):
        st.error("🚨 **Emergency Cash Defense ENGAGED by Global Administrator**: All long trades restricted to 100% cash.", icon="🔒")
    elif len(traps) > 0:
        st.warning(f"⚠️ **Structural Heuristic Trap Alert**: {traps[0]}", icon="🪤")

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # --- CENTRAL PLOTLY INTERACTIVE CHART ---
    fig = build_interactive_chart(df, tech, plan)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})

    # --- BOTTOM SECTION: INSTITUTIONAL DEEP-DIVE TABS ---
    tab_titles = [
        "🧠 Trade Plan & Kill-Switches",
        "🔗 Supply Chain & Spillover Tree",
        "⚖️ Solvency Sieve & Factor Grades",
        "🌊 Microstructure & Options Flow",
        "🪤 Heuristic Trap Detectors",
    ]

    if is_global_admin():
        tab_titles.append("👑 Global Governance (nikhil875171)")
    elif is_admin():
        tab_titles.append("🛡️ Admin Operational Telemetry")

    tabs = st.tabs(tab_titles)

    # TAB 1: TRADE PLAN & KILL SWITCHES
    with tabs[0]:
        c1, c2 = st.columns([1.4, 1.0])
        with c1:
            st.markdown("#### **Executive Quantitative Thesis & Decision Rationale**")
            st.info(
                f"**Macro State:** {plan.macro_regime} | "
                f"**Solvency Sieve:** {factors.sieve_verdict} | "
                f"**Composite Alpha Score:** {factors.composite_factor_score}/100"
            )

            # Factor pillars overview
            p_cols = st.columns(4)
            p_cols[0].metric("Value Pillar", f"{factors.factor_grades.get('Value', 50):.0f}/100")
            p_cols[1].metric("Quality Pillar", f"{factors.factor_grades.get('Quality', 50):.0f}/100")
            p_cols[2].metric("Momentum Pillar", f"{factors.factor_grades.get('Momentum', 50):.0f}/100")
            p_cols[3].metric("Microstructure", f"{factors.factor_grades.get('Microstructure', 50):.0f}/100")

            st.markdown("##### **Institutional Synthesis & Rationale:**")
            for warning in plan.detected_traps_or_warnings:
                if "No active" in warning:
                    st.success(f"✅ {warning}")
                else:
                    st.warning(f"⚠️ {warning}")

        with c2:
            st.markdown("#### **🚨 Execution Kill-Switches**")
            st.caption("Immediate algorithmic invalidation triggers:")
            for ks in plan.execution_kill_switches:
                st.markdown(f"- 🔴 `{ks}`")

            st.markdown("---")
            st.markdown("#### **🎯 Execution Price Levels**")
            st.markdown(f"**Recommended Entry Zone:** ₹{plan.entry_price_range[0]} – ₹{plan.entry_price_range[1]}")
            st.markdown(f"**Algorithmic Hard Stop:** ₹{plan.algorithmic_stop_loss} *(Per-share risk: ₹{risk.per_share_risk:.2f})*")
            
            target_str = " | ".join([f"T{i+1}: ₹{t}" for i, t in enumerate(plan.target_ladder)])
            st.markdown(f"**Target Price Ladder:** {target_str}")
            st.markdown(f"**Risk/Reward Ratio:** **{risk.risk_reward_ratio:.2f}:1** (Gate: >= 2.5:1)")

    # TAB 2: SUPPLY CHAIN & SECTORAL SPILLOVER TREE
    with tabs[1]:
        theme_title = spillovers.get("theme", ["Sector Transmission"])[0]
        theme_desc = spillovers.get("description", ["Supply chain spillover analysis"])[0]

        st.markdown(f"### 🔗 **{theme_title}**")
        st.caption(theme_desc)

        sc1, sc2, sc3 = st.columns(3)

        with sc1:
            st.markdown("<div class='spillover-box'><div class='spillover-title'>🔺 Upstream Positive Beneficiaries</div>", unsafe_allow_html=True)
            for item in spillovers.get("upstream_positive", []):
                st.markdown(f"• **{item}**")
            st.markdown("</div>", unsafe_allow_html=True)

        with sc2:
            st.markdown("<div class='spillover-box'><div class='spillover-title'>🔻 Midstream & Downstream Drivers</div>", unsafe_allow_html=True)
            for item in spillovers.get("midstream_positive", []) + spillovers.get("downstream_positive", []):
                st.markdown(f"• **{item}**")
            st.markdown("</div>", unsafe_allow_html=True)

        with sc3:
            st.markdown("<div class='spillover-box'><div class='spillover-title'>⚠️ Negative Spillovers & Budget Cannibalization</div>", unsafe_allow_html=True)
            for item in spillovers.get("negative_spillovers", []):
                st.markdown(f"• **{item}**")
            st.markdown("</div>", unsafe_allow_html=True)

    # TAB 3: SOLVENCY SIEVE & FACTOR GRADES
    with tabs[2]:
        st.markdown("#### **Zero-Ruin Capital Preservation Sieve Audit**")

        f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
        with f_col1:
            z_score = factors.altman_z_score
            st.metric(
                "Altman Z-Score",
                f"{z_score:.2f}",
                delta="Safe Zone" if z_score >= 2.99 else ("Grey Zone" if z_score >= 1.81 else "Distress (< 1.81)"),
                delta_color="normal" if z_score >= 1.81 else "inverse"
            )

        with f_col2:
            f_score = factors.piotroski_f_score
            st.metric(
                "Piotroski F-Score",
                f"{f_score}/9",
                delta="Strong" if f_score >= 7 else ("Moderate" if f_score >= 4 else "Failing (<= 3)"),
                delta_color="normal" if f_score >= 4 else "inverse"
            )

        with f_col3:
            sloan_ratio = factors.sloan_accrual_ratio
            st.metric(
                "Sloan Accrual Ratio",
                f"{sloan_ratio * 100:.1f}%",
                delta="Aggressive Accruals" if sloan_ratio > 0.10 else "High Quality Cash Flow",
                delta_color="inverse" if sloan_ratio > 0.10 else "normal"
            )

        with f_col4:
            roe_val = factors.solvency_audit.get("ROE (%)", 0.0)
            st.metric("Return on Equity", f"{roe_val:.1f}%")

        with f_col5:
            de_val = factors.solvency_audit.get("Debt-to-Equity", 0.0)
            st.metric("Debt-to-Equity", f"{de_val:.2f}x")

        st.markdown("---")
        st.markdown("#### **Four-Pillar Factor Architecture**")

        pg_col1, pg_col2 = st.columns(2)
        with pg_col1:
            st.write(f"**Value Pillar Score:** {factors.factor_grades.get('Value', 50.0):.1f} / 100")
            st.progress(int(factors.factor_grades.get('Value', 50.0)))

            st.write(f"**Quality Pillar Score:** {factors.factor_grades.get('Quality', 50.0):.1f} / 100")
            st.progress(int(factors.factor_grades.get('Quality', 50.0)))

        with pg_col2:
            st.write(f"**Momentum Pillar Score:** {factors.factor_grades.get('Momentum', 50.0):.1f} / 100")
            st.progress(int(factors.factor_grades.get('Momentum', 50.0)))

            st.write(f"**Microstructure Pillar Score:** {factors.factor_grades.get('Microstructure', 50.0):.1f} / 100")
            st.progress(int(factors.factor_grades.get('Microstructure', 50.0)))

    # TAB 4: MICROSTRUCTURE & OPTIONS FLOW
    with tabs[3]:
        st.markdown("#### **Institutional Microstructure & Order Flow Verification**")

        u1, u2, u3, u4 = st.columns(4)
        with u1:
            st.metric(
                "Delivery Percentage",
                f"{micro.delivery_pct:.1f}%",
                delta="Institutional Validation Pass" if micro.delivery_valid else "Below Institutional Threshold",
                delta_color="normal" if micro.delivery_valid else "inverse"
            )

        with u2:
            st.metric(
                "FII / DII Confluence",
                "Confluent Inflow" if micro.institutional_confluence else "Divergent Flow",
                delta="Institutional Sponsorship" if micro.institutional_confluence else "Cautious",
                delta_color="normal" if micro.institutional_confluence else "inverse"
            )

        with u3:
            pcr_str = f"{micro.put_call_ratio:.2f}"
            st.metric(
                "Put-Call Ratio (PCR)",
                pcr_str,
                delta=micro.pcr_regime
            )

        with u4:
            st.metric(
                "Estimated Slippage Impact",
                f"{micro.estimated_bid_ask_spread_pct:.2f}%",
                delta="High Liquidity" if micro.liquidity_passed else "Illiquid / High Spread",
                delta_color="normal" if micro.liquidity_passed else "inverse"
            )

        st.markdown("##### **Options Skew & Strike Geometry:**")
        sk1, sk2, sk3 = st.columns(3)
        sk1.write(f"**Max Pain Strike:** ₹{micro.max_pain_strike if micro.max_pain_strike else 'N/A'}")
        sk2.write(f"**Major Call Resistance Wall:** ₹{micro.call_resistance_wall if micro.call_resistance_wall else 'N/A'}")
        sk3.write(f"**Major Put Support Floor:** ₹{micro.put_support_wall if micro.put_support_wall else 'N/A'}")

        if micro.microstructure_warnings:
            st.markdown("##### **Microstructure Alerts:**")
            for w in micro.microstructure_warnings:
                st.warning(w)

    # TAB 5: HEURISTIC TRAP DETECTORS
    with tabs[4]:
        st.markdown("#### **Quantitative Heuristic Trap Diagnostics**")
        st.caption("Active monitoring for market failure modes, fake breakouts, and narrative traps.")

        t_col1, t_col2 = st.columns(2)

        with t_col1:
            st.markdown("<div class='trap-card'>", unsafe_allow_html=True)
            st.markdown("##### **1. Exhaustion Trap**")
            st.caption("Detects 3-day rallies into overhead resistance on fading volume or RSI > 75.")
            exh_detected = any("EXHAUSTION TRAP" in t for t in traps)
            if exh_detected:
                st.error("🚨 **TRAP DETECTED**: Volume divergence indicates institutional buying has dried up.")
            else:
                st.success("✅ **CLEAN**: Volume expansion validates price trend.")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='trap-card'>", unsafe_allow_html=True)
            st.markdown("##### **2. Priced-in Rumor Trap**")
            st.caption("Flags > 20% price surges in the 20 days prior to expected earnings/catalysts.")
            rumor_detected = any("PRICED-IN RUMOR" in t for t in traps)
            if rumor_detected:
                st.error("🚨 **TRAP DETECTED**: High probability of 'sell-the-news' profit taking.")
            else:
                st.success("✅ **CLEAN**: Asset trading within balanced momentum bounds.")
            st.markdown("</div>", unsafe_allow_html=True)

        with t_col2:
            st.markdown("<div class='trap-card'>", unsafe_allow_html=True)
            st.markdown("##### **3. Cyclical Value Trap**")
            st.caption("Prevents classifying cyclical commodity/materials producers as 'cheap' at cyclical peak earnings.")
            cyc_detected = any("CYCLICAL VALUE TRAP" in t for t in traps)
            if cyc_detected:
                st.error("🚨 **TRAP DETECTED**: Trailing P/E reflects peak-cycle earnings rather than true margin discount.")
            else:
                st.success("✅ **CLEAN**: Valuation not distorted by cyclical peak anomaly.")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='trap-card'>", unsafe_allow_html=True)
            st.markdown("##### **4. Geopolitical Overreaction**")
            st.caption("Distinguishes between transitory headline fear and structural supply chokepoint disruptions.")
            geo_detected = any("GEOPOLITICAL OVERREACTION" in t for t in traps)
            if geo_detected:
                st.info("ℹ️ **POTENTIAL V-BOTTOM**: Transitory headline dip may offer favorable mean-reverting entry.")
            else:
                st.success("✅ **CLEAN**: No abnormal headline overreaction distortion.")
            st.markdown("</div>", unsafe_allow_html=True)

    # TAB 6: GOVERNANCE & PRIVILEGED CONTROLS (RBAC ENFORCED)
    if is_global_admin():
        with tabs[5]:
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
                st.write(f"**Default Model Cascade:** `gemini-flash-lite-latest` ➔ `gemini-3.1-flash-lite` ➔ `gemini-flash-latest`")

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
        with tabs[5]:
            st.markdown("### 🛡️ **Administrator Operational Telemetry**")
            st.info("Logged in as Administrator (`nkk_admin`). Standard operations active.")
            a_col1, a_col2 = st.columns(2)
            with a_col1:
                st.metric("System Health", "ONLINE", delta="All Quantitative Engines Operational")
                st.metric("Active Model", model_choice)
            with a_col2:
                st.metric("Session Mode", "Authenticated Admin")
                st.caption("Note: Root policy changes and emergency kill-switches are strictly restricted to Global Administrator (nikhil875171).")

st.markdown("<div style='margin-top: 40px; text-align: center; color: #64748B; font-size: 0.8rem;'>AlphaShield Institutional Quantitative Engine | Capital Preservation & Decision Support Architecture</div>", unsafe_allow_html=True)
