from dataclasses import dataclass
import math
from typing import Optional, Tuple
from src.macro_engine import MacroRegimeState


@dataclass
class ExecutionRiskReport:
    """Institutional algorithmic risk execution and sizing report."""
    portfolio_equity: float
    risk_pct: float
    max_equity_at_risk: float
    entry_price: float
    algorithmic_stop_loss: float
    per_share_risk: float
    calculated_shares: int
    allocated_capital: float
    portfolio_allocation_pct: float
    target_ladder: list[float]
    risk_reward_ratio: float
    asymmetric_rr_passed: bool
    vix_scale_factor: float
    execution_verdict: str
    risk_guardrail_notes: list[str]

    @property
    def risk_reward_ratio_1(self) -> float:
        return self.risk_reward_ratio

    @property
    def position_size_shares(self) -> int:
        return self.calculated_shares

    @property
    def total_allocated_capital(self) -> float:
        return self.allocated_capital

    @property
    def risk_capital_amount(self) -> float:
        return self.max_equity_at_risk

    @property
    def risk_pct_selected(self) -> float:
        return self.risk_pct


def calculate_algorithmic_execution(
    portfolio_equity: float,
    current_price: float,
    atr: float,
    macro: Optional[MacroRegimeState] = None,
    resistance_target: Optional[float] = None,
    user_risk_pct: float = 1.0,
) -> ExecutionRiskReport:
    """
    Executes pure mathematical capital preservation:
    1. Dynamic ATR Hard Stop = Entry - (2.0 * ATR_14) [Tightened if VIX elevated]
    2. Fixed Fractional Position Sizing = (Portfolio Equity * 0.01) / Per-Share Risk
    3. Macro VIX Scaling:
       - VIX < 20: 100% sizing
       - 20 <= VIX <= 25: Tighten ATR to 1.6x
       - 25 < VIX <= 32: Automatically halve sizing (-50%)
       - VIX > 32: Volatility Halt (0 shares)
    4. Asymmetric R:R Gate (Min 2.5:1 required)
    """
    notes: list[str] = []
    equity_risk_pct = max(0.5, min(user_risk_pct, 1.5))  # strictly bounded

    # 1. Determine ATR multiple based on macro regime
    vix_val = macro.vix if macro else 14.50
    if vix_val > 32.0:
        atr_multiplier = 2.0
        vix_scale = 0.0
        notes.append("VOLATILITY HALT: Systemic VIX spike > 32 restricts all long risk.")
    elif vix_val > 25.0:
        atr_multiplier = 2.0
        vix_scale = 0.50
        notes.append("High Volatility Sizing Cut: Position size reduced by 50% per macro policy.")
    elif vix_val >= 20.0:
        atr_multiplier = 1.6  # tighten stop in choppy conditions
        vix_scale = 0.85
        notes.append("Moderate Volatility: ATR stop tightened to 1.6x to prevent deep whipsaws.")
    else:
        atr_multiplier = 2.0
        vix_scale = 1.0

    # 2. Hard Stop Loss calculation
    stop_distance = max(atr * atr_multiplier, current_price * 0.015)
    hard_stop = round(max(current_price - stop_distance, 0.01), 2)
    per_share_risk = round(current_price - hard_stop, 2)

    # 3. Maximum capital at risk (1.0% of portfolio equity)
    max_risk_amount = round(portfolio_equity * (equity_risk_pct / 100.0), 2)

    # 4. Fixed Fractional Share Sizing
    if per_share_risk > 0 and vix_scale > 0:
        raw_shares = (max_risk_amount / per_share_risk) * vix_scale
        shares = int(math.floor(raw_shares))
    else:
        shares = 0

    allocated_cap = round(shares * current_price, 2)

    # Cap allocated capital so it never exceeds 20% of total portfolio on a single position
    max_position_cap = portfolio_equity * 0.20
    if allocated_cap > max_position_cap and current_price > 0:
        shares = int(math.floor(max_position_cap / current_price))
        allocated_cap = round(shares * current_price, 2)
        notes.append(f"Position Concentration Cap: Sizing capped at 20% portfolio equity limit (₹/{max_position_cap:,.0f}).")

    alloc_pct = round((allocated_cap / max(portfolio_equity, 1.0)) * 100.0, 2)

    # 5. Target Ladder & Asymmetric R:R Gate (Min 2.5:1)
    if resistance_target and resistance_target > current_price:
        t1 = round(resistance_target, 2)
    else:
        # Default projected asymmetric targets
        t1 = round(current_price + (2.5 * per_share_risk), 2)

    t2 = round(t1 + (1.5 * atr), 2)
    t3 = round(t2 + (2.0 * atr), 2)
    target_ladder = [t1, t2, t3]

    upside = t1 - current_price
    rr_ratio = round(upside / max(per_share_risk, 0.01), 2)
    asymmetric_passed = rr_ratio >= 2.50

    # Verdict synthesis
    if vix_scale == 0.0:
        verdict = "VOLATILITY HALT: All new entries restricted."
    elif not asymmetric_passed:
        verdict = f"AVOID / POOR R:R: Upside yields {rr_ratio}:1 (Below 2.5:1 institutional hurdle)."
        notes.append("Asymmetric Gate Failed: Trade does not offer required 2.5x upside reward per unit of risk.")
    else:
        verdict = f"APPROVED: Asymmetric setup of {rr_ratio}:1. Strict stop at ₹{hard_stop}."

    return ExecutionRiskReport(
        portfolio_equity=portfolio_equity,
        risk_pct=equity_risk_pct,
        max_equity_at_risk=max_risk_amount,
        entry_price=round(current_price, 2),
        algorithmic_stop_loss=hard_stop,
        per_share_risk=per_share_risk,
        calculated_shares=shares,
        allocated_capital=allocated_cap,
        portfolio_allocation_pct=alloc_pct,
        target_ladder=target_ladder,
        risk_reward_ratio=rr_ratio,
        asymmetric_rr_passed=asymmetric_passed,
        vix_scale_factor=vix_scale,
        execution_verdict=verdict,
        risk_guardrail_notes=notes,
    )
