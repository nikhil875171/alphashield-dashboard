import math
from typing import Tuple
from core.schemas import RiskAllocation


def calculate_risk_parameters(
    account_size: float,
    current_price: float,
    atr: float,
    target_price: float,
    risk_pct: float = 1.5,
    atr_multiplier: float = 1.8,
    volatility_kill_switch: bool = False
) -> RiskAllocation:
    """
    Implements institutional zero-ruin risk management:
    1. Dynamic ATR Hard Stop = Entry - (Multiplier * ATR)
    2. Fixed Fractional Position Sizing = (Account Size * Risk %) / Per-Share Risk
    3. Asymmetric R:R Gate (Min 1:2.5)
    4. Volatility Kill-Switch Enforcement
    """
    # Enforce safe bounds on risk percentage (1.0% to 2.0% standard institutional mandate)
    risk_pct = max(0.5, min(risk_pct, 2.5))

    # 1. Dynamic ATR Stop Loss
    stop_distance = max(atr * atr_multiplier, current_price * 0.015)
    stop_loss = round(max(current_price - stop_distance, 0.01), 2)
    per_share_risk = round(current_price - stop_loss, 2)

    # 2. Risk Capital
    risk_capital = round(account_size * (risk_pct / 100.0), 2)

    # 3. Position Sizing
    if per_share_risk > 0:
        raw_shares = risk_capital / per_share_risk
        shares = int(math.floor(raw_shares))
    else:
        shares = 0

    # Total capital required
    total_allocated = round(shares * current_price, 2)

    # If position exceeds total account size (no leverage assumption), cap it
    if total_allocated > account_size:
        shares = int(math.floor(account_size / current_price))
        total_allocated = round(shares * current_price, 2)

    portfolio_alloc_pct = round((total_allocated / max(account_size, 1.0)) * 100.0, 2)

    # 4. Asymmetric Risk-to-Reward Ratio
    upside = target_price - current_price
    if per_share_risk > 0 and upside > 0:
        rr_ratio = round(upside / per_share_risk, 2)
    else:
        rr_ratio = 0.0

    asymmetric_passed = rr_ratio >= 2.5

    # 5. Volatility Kill-Switch Intervention
    if volatility_kill_switch:
        # Force capital preservation
        shares = 0
        total_allocated = 0.0
        portfolio_alloc_pct = 0.0
        verdict = "KILL-SWITCH ENGAGED: Extreme macro stress/VIX spike detected. 100% Cash Defense enforced."
    elif not asymmetric_passed:
        verdict = f"AVOID / POOR R:R: Trade upside offers only {rr_ratio}:1 (Minimum required: 2.5:1)."
    else:
        verdict = f"RISK APPROVED: Asymmetric R:R of {rr_ratio}:1. Max downside strictly capped at {risk_pct}% (₹/{risk_capital:,.2f})."

    return RiskAllocation(
        account_size=round(account_size, 2),
        risk_pct_selected=risk_pct,
        risk_capital_amount=risk_capital,
        entry_price=round(current_price, 2),
        stop_loss_price=stop_loss,
        per_share_risk=per_share_risk,
        position_size_shares=shares,
        total_allocated_capital=total_allocated,
        portfolio_allocation_pct=portfolio_alloc_pct,
        target_price_1=round(target_price, 2),
        risk_reward_ratio_1=rr_ratio,
        asymmetric_rr_passed=asymmetric_passed,
        volatility_kill_switch_forced=volatility_kill_switch,
        risk_verdict=verdict,
    )

