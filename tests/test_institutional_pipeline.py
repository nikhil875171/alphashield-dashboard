import sys
import os

# Ensure UTF-8 console output for Windows PowerShell
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from src.macro_engine import compute_macro_transmission, MacroRegimeState
from src.transmission_tree import get_supply_chain_spillover, detect_company_catalyst
from src.microstructure import validate_microstructure, MicrostructureValidation
from src.factor_model import evaluate_factor_model, FactorScoreSummary
from src.trap_guards import evaluate_all_traps, is_exhaustion_trap, is_priced_in_rumor
from src.risk_engine import calculate_algorithmic_execution, ExecutionRiskReport
from src.ai_agent import generate_institutional_trade_plan, InstitutionalTradePlan


def test_full_pipeline():
    symbol = "RELIANCE.NS"
    print("\n" + "=" * 65)
    print(f"RUNNING ALPHASHIELD V2 INSTITUTIONAL TEST: {symbol}")
    print("=" * 65)

    # 1. Macro Transmission
    print("[1/7] Testing Macro Transmission Engine...")
    macro = compute_macro_transmission(is_indian_market=True)
    assert isinstance(macro, MacroRegimeState)
    assert macro.vix > 0
    print(f"      [+] Regime: {macro.regime_label} (VIX: {macro.vix}, Spread: {macro.yield_spread}%, Scale: {macro.position_scale_factor}x)")

    # 2. Transmission Tree
    print("[2/7] Testing Supply Chain Transmission Tree...")
    catalyst_key = detect_company_catalyst(symbol, sector="Energy", industry="Refining")
    spillovers = get_supply_chain_spillover(catalyst_key)
    assert "upstream_positive" in spillovers
    assert len(spillovers["upstream_positive"]) > 0
    print(f"      [+] Catalyst Theme: {spillovers.get('theme', ['N/A'])[0]}")

    # Dummy OHLCV data for technical checks
    from core.technical_engine import compute_technical_snapshot
    tech, df = compute_technical_snapshot(symbol, period="6mo", interval="1d")

    # 3. Microstructure
    print("[3/7] Testing Microstructure & Order Flow Validator...")
    micro = validate_microstructure(symbol, df)
    assert isinstance(micro, MicrostructureValidation)
    print(f"      [+] Delivery Est: {micro.delivery_pct}% | PCR: {micro.put_call_ratio} | Max Pain: ₹{micro.max_pain_strike}")

    # 4. Factor Model & Quality Sieve
    print("[4/7] Testing Multi-Factor Scoring & Quality Sieve...")
    factors = evaluate_factor_model(symbol, df)
    assert isinstance(factors, FactorScoreSummary)
    print(f"      [+] Sieve Verdict: {factors.sieve_verdict} (Altman Z: {factors.altman_z_score}, Piotroski: {factors.piotroski_f_score}/9, Sloan Accruals: {factors.sloan_accrual_ratio * 100:.2f}%)")
    print(f"      [+] Factor Grades: {factors.factor_grades}")

    # 5. Trap Guards
    print("[5/7] Testing Heuristic Trap Guardrails...")
    traps = evaluate_all_traps(df)
    print(f"      [+] Traps Detected: {traps if traps else 'Clean Setup (0 traps)'}")

    # 6. Risk Engine
    print("[6/7] Testing Algorithmic Risk & Sizing Engine...")
    portfolio_equity = 1_000_000.0  # ₹10 Lakhs
    risk = calculate_algorithmic_execution(
        portfolio_equity=portfolio_equity,
        current_price=tech.current_price,
        atr=tech.atr_14,
        macro=macro,
        user_risk_pct=1.0,
    )
    assert isinstance(risk, ExecutionRiskReport)
    assert risk.max_equity_at_risk == 10_000.0  # Exactly 1.0%
    print(f"      [+] Stop Loss: ₹{risk.algorithmic_stop_loss} | Shares: {risk.calculated_shares} (Allocated: ₹{risk.allocated_capital:,.2f}) | R:R: {risk.risk_reward_ratio}:1")

    # 7. Gemini AI Agent
    print("[7/7] Testing Gemini Pro Structured Decision Pipeline...")
    plan = generate_institutional_trade_plan(
        ticker=symbol,
        macro=macro,
        micro=micro,
        factors=factors,
        traps=traps,
        spillovers=spillovers,
        risk=risk,
    )
    assert isinstance(plan, InstitutionalTradePlan)
    assert plan.action in ["BUY", "SELL", "HOLD", "AVOID"]
    assert 0.0 <= plan.conviction_score <= 1.0
    print(f"      [+] Mandate: [{plan.action}] with {plan.conviction_score * 100:.0f}% Conviction")
    print(f"      [+] Entry Range: ₹{plan.entry_price_range[0]} - ₹{plan.entry_price_range[1]}")
    print(f"      [+] Target Ladder: {plan.target_ladder}")
    print(f"      [+] Kill-Switches: {len(plan.execution_kill_switches)} configured")

    print("=" * 65)
    print("ALL 7 INSTITUTIONAL MODULES VERIFIED WITH ZERO ERRORS!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    test_full_pipeline()
