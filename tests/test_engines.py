"""Institutional Test Suite for AlphaShield Dashboard Quantitative Engines."""
import sys
import os

# Ensure UTF-8 output for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from core.schemas import (
    AlphaShieldRecommendation,
    MacroSnapshot,
    FundamentalAudit,
    TechnicalSnapshot,
    SentimentSnapshot,
    InstitutionalSnapshot,
    RiskAllocation,
)
from core.macro_engine import get_macro_snapshot
from core.fundamental_engine import audit_fundamental_health, calculate_altman_z_score, calculate_piotroski_f_score
from core.technical_engine import compute_technical_snapshot
from core.sentiment_engine import fetch_sentiment_analysis, _analyze_headline_sentiment
from core.institutional_engine import audit_institutional_positioning
from core.risk_manager import calculate_risk_parameters
from core.gemini_advisor import evaluate_alpha_shield
from core.visualizer import build_interactive_chart
import pandas as pd


def test_macro_engine():
    print("[*] Testing Macro Engine...")
    macro = get_macro_snapshot(is_indian_market=True)
    assert isinstance(macro, MacroSnapshot)
    assert macro.vix > 0
    assert macro.macro_regime in ["DEFENSIVE", "NEUTRAL", "EXPANSION"]
    print(f"    [+] Macro Regime: {macro.macro_regime}, VIX: {macro.vix}, Yield Spread: {macro.yield_spread_10y_2y}%")


def test_sentiment_lexicon():
    print("[*] Testing Sentiment Lexicon...")
    bull_score = _analyze_headline_sentiment("Reliance reports record profit growth and dividend surge")
    bear_score = _analyze_headline_sentiment("Company faces fraud investigation, default lawsuit and loss")
    assert bull_score > 0
    assert bear_score < 0
    print(f"    [+] Bull score: {bull_score}, Bear score: {bear_score}")


def test_technical_engine():
    print("[*] Testing Technical Engine with RELIANCE.NS...")
    tech, df = compute_technical_snapshot("RELIANCE.NS", period="6mo", interval="1d")
    assert isinstance(tech, TechnicalSnapshot)
    assert not df.empty
    assert "EMA_20" in df.columns
    assert "RSI_14" in df.columns
    assert "ATR_14" in df.columns
    assert tech.current_price > 0
    assert tech.dynamic_stop_1_5x < tech.current_price
    print(f"    [+] Price: ₹{tech.current_price}, RSI: {tech.rsi_14}, ATR: ₹{tech.atr_14}, 20-EMA: ₹{tech.ema_20}")
    return tech, df


def test_risk_manager(tech: TechnicalSnapshot):
    print("[*] Testing Zero-Ruin Risk Manager...")
    account_size = 1_000_000.0  # ₹10 Lakhs
    target = tech.current_price + (3.0 * (tech.current_price - tech.dynamic_stop_1_5x))

    risk = calculate_risk_parameters(
        account_size=account_size,
        current_price=tech.current_price,
        atr=tech.atr_14,
        target_price=target,
        risk_pct=1.5,
        atr_multiplier=1.8,
        volatility_kill_switch=False
    )
    assert isinstance(risk, RiskAllocation)
    assert risk.risk_capital_amount == 15_000.0
    assert risk.position_size_shares > 0
    assert risk.risk_reward_ratio_1 >= 2.5
    assert risk.asymmetric_rr_passed is True
    print(f"    [+] Risk Capital: ₹{risk.risk_capital_amount}, Shares: {risk.position_size_shares}, R:R: {risk.risk_reward_ratio_1}:1")
    return risk


def test_fundamental_engine():
    print("[*] Testing Fundamental Solvency Engine with RELIANCE.NS...")
    fund = audit_fundamental_health("RELIANCE.NS")
    assert isinstance(fund, FundamentalAudit)
    print(f"    [+] Altman Zone: {fund.altman_zone} (Score: {fund.altman_z_score}), Piotroski: {fund.piotroski_grade} ({fund.piotroski_f_score}/9)")
    return fund


def test_advisor_and_chart(tech, df, fund, risk):
    print("[*] Testing Gemini Advisor Schema & Decision Engine...")
    macro = get_macro_snapshot(is_indian_market=True)
    sent = fetch_sentiment_analysis("RELIANCE.NS", rsi=tech.rsi_14)
    inst = audit_institutional_positioning("RELIANCE.NS")

    rec = evaluate_alpha_shield(tech, fund, macro, sent, inst, risk)
    assert isinstance(rec, AlphaShieldRecommendation)
    assert rec.action in ["BUY", "SELL", "HOLD", "AVOID"]
    assert 0.0 <= rec.conviction_score <= 1.0
    assert len(rec.recommended_entry_range) == 2
    assert len(rec.target_price_ladder) >= 2
    assert len(rec.primary_kill_switches) >= 1
    print(f"    [+] Decision Action: [{rec.action}], Conviction: {rec.conviction_score * 100:.1f}%, Stop: ₹{rec.hard_stop_loss}")

    print("[*] Testing Plotly Visualizer...")
    fig = build_interactive_chart(df, tech, rec)
    assert fig is not None
    print(f"    [+] Plotly Figure built successfully with {len(fig.data)} traces!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RUNNING ALPHASHIELD INSTITUTIONAL TEST SUITE")
    print("=" * 60)
    test_macro_engine()
    test_sentiment_lexicon()
    tech, df = test_technical_engine()
    risk = test_risk_manager(tech)
    fund = test_fundamental_engine()
    test_advisor_and_chart(tech, df, fund, risk)
    print("=" * 60)
    print("ALL INSTITUTIONAL QUANT ENGINES PASSED VERIFICATION!")
    print("=" * 60 + "\n")
