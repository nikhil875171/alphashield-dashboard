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
    page_title="AlphaShield | Beginner-Friendly Stock Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Contrast Modern Theme CSS
st.markdown("""
<style>
    /* Dark background styling */
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Top Global Switcher */
    .market-switch-banner {
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 12px 20px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #151B26;
        border: 1px solid #232D3F;
        border-radius: 10px;
        padding: 12px 16px;
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
        font-size: 1.35rem;
        font-weight: 700;
        color: #F8FAFC;
    }

    /* 30-Second Bottom Line Strip */
    .bottom-line-container {
        background: linear-gradient(135deg, #131A2A 0%, #1A2234 100%);
        border: 1px solid #2D3A4F;
        border-left: 6px solid #10B981;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.4);
    }
    .bottom-line-danger {
        border-left-color: #EF4444 !important;
    }
    .bottom-line-caution {
        border-left-color: #F59E0B !important;
    }

    /* Action Badges */
    .badge-buy {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%);
        color: white;
        padding: 8px 24px;
        border-radius: 24px;
        font-weight: 800;
        font-size: 1.35rem;
        display: inline-block;
        letter-spacing: 0.05em;
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.45);
    }
    .badge-sell {
        background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%);
        color: white;
        padding: 8px 24px;
        border-radius: 24px;
        font-weight: 800;
        font-size: 1.35rem;
        display: inline-block;
        letter-spacing: 0.05em;
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.45);
    }
    .badge-hold {
        background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%);
        color: white;
        padding: 8px 24px;
        border-radius: 24px;
        font-weight: 800;
        font-size: 1.35rem;
        display: inline-block;
        letter-spacing: 0.05em;
        box-shadow: 0 0 16px rgba(245, 158, 11, 0.4);
    }
    .badge-avoid {
        background: linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%);
        color: white;
        padding: 8px 24px;
        border-radius: 24px;
        font-weight: 800;
        font-size: 1.35rem;
        display: inline-block;
        letter-spacing: 0.05em;
        box-shadow: 0 0 16px rgba(139, 92, 246, 0.4);
    }

    /* Interactive Explanatory Tiles */
    .interactive-tile {
        background-color: #151B26;
        border: 1px solid #232D3F;
        border-radius: 12px;
        padding: 16px;
        height: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.25);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .interactive-tile:hover {
        border-color: #38BDF8;
        transform: translateY(-2px);
    }
    .tile-header {
        font-size: 0.85rem;
        color: #94A3B8;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .tile-status-safe {
        color: #10B981;
        font-weight: 700;
        font-size: 1.15rem;
    }
    .tile-status-caution {
        color: #F59E0B;
        font-weight: 700;
        font-size: 1.15rem;
    }
    .tile-status-danger {
        color: #EF4444;
        font-weight: 700;
        font-size: 1.15rem;
    }

    /* Thematic Discovery Card */
    .radar-card {
        background-color: #151B26;
        border: 1px solid #232D3F;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .radar-card:hover {
        border-color: #38BDF8;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. ENFORCE ROLE-BASED AUTHENTICATION GATE ---
if not render_login_gate():
    st.stop()


# --- 2. TOP GLOBAL MARKET & EXCHANGE SELECTOR ---
# We provide a clean, prominent segmented control at the top of the interface
col_brand, col_market_selector = st.columns([1.6, 1.4])

with col_brand:
    st.markdown("## 🛡️ **AlphaShield** | Intelligent Stock Decision Engine")
    st.caption("Simplified institutional quantitative intelligence for beginner & modern investors.")

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


# --- SIDEBAR: CONTROLS & BEGINNER CAPITAL ALLOCATION ---
with st.sidebar:
    render_user_profile_sidebar()

    st.markdown(f"### 📍 **Active Market: {'India (NSE)' if is_indian else 'United States (NYSE)'}**")

    # Ticker Quick-Select Chips
    st.markdown("##### **Popular Watchlist:**")
    quick_tickers = (
        ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "ZOMATO.NS"]
        if is_indian
        else ["NVDA", "AAPL", "MSFT", "TSLA", "PLTR", "AMZN"]
    )
    
    # Render quick pick buttons in 3 columns
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
        help="Golden Rule of Investing: Never risk losing more than 1% of your total account on a single bad stock."
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
        st.info("ℹ️ Running on Institutional Rule Engine (No Gemini API Key found).", icon="ℹ️")
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
    with st.spinner(f"Auditing company health and market signals for {ticker}..."):
        try:
            # 1. Technical Data
            tech, df = compute_technical_snapshot(ticker, period="1y", interval="1d")
            if df.empty:
                st.error(f"Could not retrieve stock data for '{ticker}'. Please verify the symbol.")
                return None, None, None, None, None, None, None, None

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

            # 6. Sector Spillovers
            sec = info.get("sector", "")
            ind = info.get("industry", "")
            cat_key = detect_company_catalyst(ticker, sector=sec, industry=ind)
            spill = get_supply_chain_spillover(cat_key)

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

            # 8. AI Decision Plan
            trade_plan = generate_institutional_trade_plan(
                ticker=ticker,
                macro=macro,
                micro=micro,
                factors=factors,
                traps=traps,
                spillovers=spill,
                risk=risk,
                model_name=model_choice,
            )

            if cash_defense:
                trade_plan.action = "AVOID"
                trade_plan.calculated_shares = 0

            return tech, df, factors, micro, traps, spill, risk, trade_plan

        except Exception as e:
            st.error(f"Analysis encountered an unexpected issue: {e}")
            return None, None, None, None, None, None, None, None


tech, df, factors, micro, traps, spill, risk, plan = run_full_audit(ticker_to_run)


if tech and df is not None and plan:
    # --- 3. THE 30-SECOND "BOTTOM LINE" SUMMARY STRIP ---
    # Determine summary theme
    if plan.action == "BUY":
        box_class = "bottom-line-container"
        badge_html = "<span class='badge-buy'>🟢 BUY RECOMMENDATION</span>"
        action_headline = "A favorable setup with high reward and protected risk."
        why_text = f"The company passed our strict financial safety sieve with strong operational health ({factors.piotroski_f_score}/9) and active institutional buying. Projected upside is more than {risk.risk_reward_ratio:.1f}x your downside risk."
    elif plan.action == "HOLD":
        box_class = "bottom-line-container bottom-line-caution"
        badge_html = "<span class='badge-hold'>🟡 HOLD / WAIT FOR DIP</span>"
        action_headline = "Good company, but not the ideal moment to enter."
        why_text = "The price is currently consolidating or resting near resistance. Beginners should wait for a slight pullback into the safe entry zone before buying."
    elif plan.action == "SELL":
        box_class = "bottom-line-container bottom-line-danger"
        badge_html = "<span class='badge-sell'>🔴 EXIT / TAKE PROFIT</span>"
        action_headline = "Momentum is breaking down or targets have been reached."
        why_text = "Technical indicators show sellers taking control. Protect your profits or cut your losses."
    else:
        box_class = "bottom-line-container bottom-line-danger"
        badge_html = "<span class='badge-avoid'>🔴 AVOID (HIGH RISK)</span>"
        action_headline = "High risk of capital loss detected. Do not invest now."
        if factors.sieve_verdict != "PASS":
            why_text = f"Capital Preservation Alert: {factors.sieve_rejection_reasons[0] if factors.sieve_rejection_reasons else 'Weak balance sheet'}. The company failed our solvency checks."
        elif len(traps) > 0:
            why_text = f"Market Trap Detected: {traps[0]}. High probability of a sharp pullback or rumor sell-off."
        else:
            why_text = "The trade does not provide enough reward to justify risking your capital. Stay safe in cash."

    risk_rule_text = f"If the price falls below **{currency_sym}{plan.algorithmic_stop_loss}**, sell immediately. This strictly caps your total loss to **{currency_sym}{risk.max_equity_at_risk:,.2f}** (exactly {risk.risk_pct:.1f}% of your budget)."

    st.markdown(f"""
    <div class='{box_class}'>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
            <div>
                {badge_html}
                <span style='margin-left: 14px; font-size: 1.25rem; font-weight: 700; color: #F8FAFC;'>{plan.ticker} — {action_headline}</span>
            </div>
            <div style='font-size: 0.95rem; color: #94A3B8; font-weight: 600;'>
                Conviction: <strong style='color: #F8FAFC;'>{plan.conviction_score * 100:.0f}%</strong>
            </div>
        </div>
        <div style='font-size: 1.02rem; line-height: 1.55; color: #CBD5E1; margin-bottom: 10px;'>
            <strong>💡 Why:</strong> {why_text}
        </div>
        <div style='font-size: 1.02rem; line-height: 1.55; color: #FCA5A5;'>
            <strong>⚠️ The #1 Risk to Watch:</strong> {risk_rule_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


    # --- 4. FIVE INTERACTIVE EXPLANATORY TILES (CARDS) ---
    t_c1, t_c2, t_c3, t_c4, t_c5 = st.columns(5)

    # TILE 1: MARKET MOOD
    with t_c1:
        mood_status = "🟢 Calm & Supportive" if macro.market_mood_color == "green" else ("🟡 Choppy Waters" if macro.market_mood_color == "yellow" else "🔴 Stormy Seas")
        st.markdown(f"""
        <div class='interactive-tile'>
            <div class='tile-header'>1. 🌡️ Market Mood</div>
            <div class='tile-status-{"safe" if macro.market_mood_color == "green" else ("caution" if macro.market_mood_color == "yellow" else "danger")}'>{mood_status}</div>
            <div style='font-size: 0.85rem; color: #94A3B8; margin-top: 4px;'>VIX Volatility: <strong>{macro.vix:.1f}</strong></div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Explain Like I'm 5"):
            st.markdown("**In Plain Words:** Think of market mood like flying an airplane. When the VIX is low, skies are clear and smooth. When volatility spikes above 20, you're flying into a storm.")
            st.markdown("**Why It Matters:** When the overall market is stormy, even great companies get dragged down. In calm markets, your trades are much more likely to succeed.")
            st.markdown(f"**The Verdict:** {macro.market_mood_desc}")

    # TILE 2: COMPANY HEALTH
    with t_c2:
        z_score = factors.altman_z_score
        health_status = "🟢 Solid & Safe" if z_score >= 2.99 else ("🟡 Watchful Debt" if z_score >= 1.81 else "🔴 Bankruptcy Hazard")
        health_class = "safe" if z_score >= 2.99 else ("caution" if z_score >= 1.81 else "danger")
        st.markdown(f"""
        <div class='interactive-tile'>
            <div class='tile-header'>2. 🏥 Company Health</div>
            <div class='tile-status-{health_class}'>{health_status}</div>
            <div style='font-size: 0.85rem; color: #94A3B8; margin-top: 4px;'>Safety Score: <strong>{z_score:.2f}</strong> (Min 1.81)</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Explain Like I'm 5"):
            st.markdown("**In Plain Words:** Does this company generate real cash from real customers, or are they borrowing money just to survive and using tricky accounting?")
            st.markdown("**Why It Matters:** Companies with high debt or fake accounting numbers can crash unexpectedly. Our system checks their balance sheet to make sure your money is safe.")
            st.markdown(f"**The Verdict:** Piotroski Business Health: **{factors.piotroski_f_score}/9**. {'Financials are sound and resilient.' if factors.sieve_verdict == 'PASS' else factors.sieve_rejection_reasons[0]}")

    # TILE 3: PRICE MOMENTUM
    with t_c3:
        is_uptrend = tech.current_price > tech.ema_50 and tech.rsi_14 < 70
        is_overheated = tech.rsi_14 >= 70
        mom_status = "🟢 Strong Uptrend" if is_uptrend else ("🟡 Resting / Pullback" if is_overheated else "🔴 Slipping Downward")
        mom_class = "safe" if is_uptrend else ("caution" if is_overheated else "danger")
        st.markdown(f"""
        <div class='interactive-tile'>
            <div class='tile-header'>3. 🚀 Price Momentum</div>
            <div class='tile-status-{mom_class}'>{mom_status}</div>
            <div style='font-size: 0.85rem; color: #94A3B8; margin-top: 4px;'>Buyer Meter (RSI): <strong>{tech.rsi_14:.1f}</strong></div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Explain Like I'm 5"):
            st.markdown("**In Plain Words:** Are more buyers rushing in to buy, or are investors quietly heading for the exits?")
            st.markdown("**Why It Matters:** It's much easier to make money swimming with the current than against it. We avoid buying when buyers are exhausted (RSI > 75) or when price is falling below trend lines.")
            st.markdown(f"**The Verdict:** Current price ({currency_sym}{tech.current_price}) is {'above its 50-day average trend' if tech.current_price > tech.ema_50 else 'below its 50-day average trend'}.")

    # TILE 4: SMART MONEY FLOW
    with t_c4:
        smart_status = "🟢 Whales Buying" if micro.delivery_valid else "🟡 Mixed / Day Trading"
        smart_class = "safe" if micro.delivery_valid else "caution"
        st.markdown(f"""
        <div class='interactive-tile'>
            <div class='tile-header'>4. 🐋 Smart Money Flow</div>
            <div class='tile-status-{smart_class}'>{smart_status}</div>
            <div style='font-size: 0.85rem; color: #94A3B8; margin-top: 4px;'>Real Delivery: <strong>{micro.delivery_pct:.1f}%</strong></div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Explain Like I'm 5"):
            st.markdown("**In Plain Words:** Everyday retail traders don't move markets—massive investment banks and mutual funds ('whales') do. Delivery percentage shows if they are quietly filling their vaults or just day-trading.")
            st.markdown("**Why It Matters:** Riding on the coattails of giant institutional buyers gives you the strongest tailwind. When they buy, prices tend to stay supported.")
            st.markdown(f"**The Verdict:** {micro.delivery_status_msg}")

    # TILE 5: SAFETY & RISK GAUGE
    with t_c5:
        risk_status = "🟢 Asymmetric Win" if risk.asymmetric_rr_passed else "🔴 Poor Odds"
        risk_class = "safe" if risk.asymmetric_rr_passed else "danger"
        st.markdown(f"""
        <div class='interactive-tile'>
            <div class='tile-header'>5. 🛡️ Safety & Risk Gauge</div>
            <div class='tile-status-{risk_class}'>{risk_status}</div>
            <div style='font-size: 0.85rem; color: #94A3B8; margin-top: 4px;'>Reward / Risk: <strong>{risk.risk_reward_ratio:.2f}x</strong></div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Explain Like I'm 5"):
            st.markdown("**In Plain Words:** If you risk $1 of downside, can you make at least $2.50 of upside? Professional investors never take a trade where the upside isn't at least 2.5x larger than the risk.")
            st.markdown("**Why It Matters:** The #1 secret to surviving the stock market is never losing a big chunk of your money. By enforcing a 2.5x ratio, you can be wrong half the time and still come out ahead!")
            st.markdown(f"**The Verdict:** Max safe investment size for your account is **{plan.calculated_shares} shares** ({currency_sym}{risk.allocated_capital:,.2f}).")

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # --- 5. INTERACTIVE 3-TIER CHART ---
    st.markdown("### 📈 **Interactive Technical Chart with Safety Overlays**")
    st.caption("Visualizing the entry zone (blue), safety stop-loss (red dashed), and profit targets (green).")
    
    fig = build_interactive_chart(df, tech, plan, currency_symbol=currency_sym)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})

    # --- 6. STRUCTURED DEEP-DIVE TABS ---
    tab_names = [
        "🧭 Thematic Market Radar",
        "📖 Step-by-Step Action Plan",
        "🔗 Who Benefits? (Supply Chain)",
        "🪤 Beginner Traps Checked",
    ]

    if is_global_admin():
        tab_names.append("👑 Global Governance (nikhil875171)")
    elif is_admin():
        tab_names.append("🛡️ Admin Operational Telemetry")

    tabs = st.tabs(tab_names)

    # TAB 1: THEMATIC MARKET RADAR (Penny, Safe, New, Trending, Future)
    with tabs[0]:
        st.markdown(f"### 🧭 **Curated Stock Discovery Radar ({'India NSE' if is_indian else 'US Markets'})**")
        st.caption("Discover hand-picked companies categorized by investment style, world leader policies, and news catalysts. Click any stock to analyze it immediately!")

        radar_data = get_thematic_market_radar(is_indian)
        
        r_tabs = st.tabs([
            "🪙 Small-Priced (< $10 / < ₹100)",
            "🏰 Safe Havens (Blue-Chips)",
            "🌱 New & Emerging Stocks",
            "🔥 Trending Today",
            "🚀 Future Mega-Trends (Supercycles)",
        ])

        categories = ["penny", "safe", "new", "trending", "future"]

        for c_idx, cat_key in enumerate(categories):
            with r_tabs[c_idx]:
                stock_list = radar_data.get(cat_key, [])
                for stock in stock_list:
                    st.markdown(f"""
                    <div class='radar-card'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <span style='font-size: 1.15rem; font-weight: 700; color: #38BDF8;'>{stock.ticker}</span>
                                <span style='font-size: 0.95rem; color: #94A3B8; margin-left: 8px;'>{stock.name}</span>
                                <span style='margin-left: 12px; font-weight: 600; color: #F8FAFC;'>{stock.approx_price}</span>
                            </div>
                            <div>
                                <span style='font-size: 0.85rem; font-weight: 600; padding: 4px 10px; border-radius: 12px; background: rgba(255,255,255,0.08);'>{stock.risk_badge}</span>
                            </div>
                        </div>
                        <div style='margin-top: 8px; font-size: 0.92rem; color: #CBD5E1;'>
                            <strong>Catalyst:</strong> {stock.catalyst_driver}
                        </div>
                        <div style='margin-top: 4px; font-size: 0.88rem; color: #94A3B8;'>
                            <strong>Why it matters:</strong> {stock.why_it_matters}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 1-Click Action to audit this stock
                    if st.button(f"⚡ Audit {stock.ticker} Now", key=f"radar_audit_{stock.ticker}"):
                        st.session_state["active_ticker"] = stock.ticker
                        st.rerun()

    # TAB 2: STEP-BY-STEP ACTION PLAN
    with tabs[1]:
        st.markdown("### 📖 **Beginner's Step-by-Step Execution Checklist**")
        st.caption(f"Exact guidelines for trading {plan.ticker} safely with minimal stress:")

        ap_col1, ap_col2 = st.columns([1.2, 1.0])

        with ap_col1:
            st.markdown("#### **Execution Checklist**")
            st.markdown(f"""
            1. **Step 1: Check the Safe Entry Window**
               - Recommended Buy Zone: **{currency_sym}{plan.entry_price_range[0]} – {currency_sym}{plan.entry_price_range[1]}**
               - *Do not chase the price if it has already skyrocketed above the upper entry price.*

            2. **Step 2: Place Your Safety Stop-Loss Order**
               - Hard Stop-Loss Price: **{currency_sym}{plan.algorithmic_stop_loss}**
               - *Set this immediately in your broker terminal after buying. Never move your stop-loss down.*

            3. **Step 3: Taking Profits (The Ladder)**
               - Target 1: **{currency_sym}{plan.target_ladder[0] if len(plan.target_ladder) > 0 else 'N/A'}** *(Sell 1/3 to lock in profits)*
               - Target 2: **{currency_sym}{plan.target_ladder[1] if len(plan.target_ladder) > 1 else 'N/A'}** *(Sell 1/3 and move stop to breakeven)*
               - Target 3: **{currency_sym}{plan.target_ladder[2] if len(plan.target_ladder) > 2 else 'N/A'}** *(Let the last 1/3 run for maximum gain)*

            4. **Step 4: Position Sizing**
               - Buy no more than **{plan.calculated_shares:,} shares** (Total: {currency_sym}{risk.allocated_capital:,.2f}).
            """)

        with ap_col2:
            st.markdown("#### **🚨 Emergency Kill-Switches**")
            st.caption("Immediate triggers that tell you: *'Exit now and protect your capital'*: ")
            for ks in plan.execution_kill_switches:
                st.markdown(f"- 🔴 `{ks}`")

    # TAB 3: WHO BENEFITS? (SUPPLY CHAIN TRANSMISSION)
    with tabs[2]:
        theme_name = spill.get("theme", ["Sector Transmission"])[0]
        theme_desc = spill.get("description", ["Supply chain overview"])[0]

        st.markdown(f"### 🔗 **Who Makes Money When {theme_name} Booms?**")
        st.caption(theme_desc)

        sc1, sc2, sc3 = st.columns(3)

        with sc1:
            st.markdown("#### 🔺 Upstream Suppliers")
            st.caption("Companies that supply the raw materials and parts first:")
            for u in spill.get("upstream_positive", []):
                st.markdown(f"• **{u}**")

        with sc2:
            st.markdown("#### 🔻 Downstream Beneficiaries")
            st.caption("Companies that package, distribute, and sell to end users:")
            for d in spill.get("midstream_positive", []) + spill.get("downstream_positive", []):
                st.markdown(f"• **{d}**")

        with sc3:
            st.markdown("#### ⚠️ Who Loses Out? (Disrupted)")
            st.caption("Old legacy businesses getting disrupted by this shift:")
            for n in spill.get("negative_spillovers", []):
                st.markdown(f"• **{n}**")

    # TAB 4: BEGINNER TRAPS CHECKED
    with tabs[3]:
        st.markdown("### 🪤 **Common Stock Market Traps Checked**")
        st.caption("Our automated guardrails check for amateur mistakes before you put your money at risk:")

        tr1, tr2 = st.columns(2)

        with tr1:
            exh = any("EXHAUSTION" in t for t in traps)
            st.markdown(f"""
            <div class='radar-card'>
                <div style='font-size: 1.05rem; font-weight: 700; color: {"#EF4444" if exh else "#10B981"};'>
                    {"🚨 TRAP ALERT: Exhaustion FOMO" if exh else "✅ SAFE: No Exhaustion Trap"}
                </div>
                <div style='font-size: 0.90rem; color: #94A3B8; margin-top: 4px;'>
                    <strong>What it means:</strong> Did you show up too late to the party? Buying after a 3-day rally when trading volume has dried up often leads to immediate losses.
                </div>
            </div>
            """, unsafe_allow_html=True)

            rumor = any("PRICED-IN" in t for t in traps)
            st.markdown(f"""
            <div class='radar-card'>
                <div style='font-size: 1.05rem; font-weight: 700; color: {"#EF4444" if rumor else "#10B981"};'>
                    {"🚨 TRAP ALERT: Priced-in Rumor" if rumor else "✅ SAFE: Balanced Price Action"}
                </div>
                <div style='font-size: 0.90rem; color: #94A3B8; margin-top: 4px;'>
                    <strong>What it means:</strong> 'Buy the rumor, sell the news'. If a stock already rallied +20% right before an announcement, professionals will dump their shares on beginners.
                </div>
            </div>
            """, unsafe_allow_html=True)

        with tr2:
            cyc = any("CYCLICAL" in t for t in traps)
            st.markdown(f"""
            <div class='radar-card'>
                <div style='font-size: 1.05rem; font-weight: 700; color: {"#EF4444" if cyc else "#10B981"};'>
                    {"🚨 TRAP ALERT: Cheap Value Illusion" if cyc else "✅ SAFE: True Valuation"}
                </div>
                <div style='font-size: 0.90rem; color: #94A3B8; margin-top: 4px;'>
                    <strong>What it means:</strong> Commodity, metal, and oil companies look artificially 'cheap' right when commodity prices hit peak profit margins before collapsing.
                </div>
            </div>
            """, unsafe_allow_html=True)

            geo = any("GEOPOLITICAL" in t for t in traps)
            st.markdown(f"""
            <div class='radar-card'>
                <div style='font-size: 1.05rem; font-weight: 700; color: {"#38BDF8" if geo else "#10B981"};'>
                    {"ℹ️ V-BOTTOM OPPORTUNITY: Headline Overreaction" if geo else "✅ SAFE: Normal Price Action"}
                </div>
                <div style='font-size: 0.90rem; color: #94A3B8; margin-top: 4px;'>
                    <strong>What it means:</strong> Transitory geopolitical panic headlines often create temporary discounts in fundamentally great companies.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # TAB 5: GLOBAL GOVERNANCE (RESTRICTED RBAC)
    if is_global_admin():
        with tabs[4]:
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
        with tabs[4]:
            st.markdown("### 🛡️ **Administrator Operational Telemetry**")
            st.info("Logged in as Administrator (`nkk_admin`). Standard operations active.")
            a_col1, a_col2 = st.columns(2)
            with a_col1:
                st.metric("System Health", "ONLINE", delta="All Quantitative Engines Operational")
                st.metric("Active Model", model_choice)
            with a_col2:
                st.metric("Session Mode", "Authenticated Admin")
                st.caption("Note: Root policy overrides and emergency cash locks are strictly restricted to Global Administrator (nikhil875171).")

st.markdown("<div style='margin-top: 40px; text-align: center; color: #64748B; font-size: 0.8rem;'>AlphaShield Intelligent Stock Decision Engine | Designed for Clarity, Safety, and Capital Preservation</div>", unsafe_allow_html=True)
