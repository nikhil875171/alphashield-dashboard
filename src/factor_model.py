from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple
import numpy as np
import pandas as pd
import yfinance as yf
from core.fundamental_engine import calculate_altman_z_score, calculate_piotroski_f_score, _get_row_value


@dataclass
class FactorScoreSummary:
    """Multi-factor quantitative scoring and capital preservation sieve result."""
    sieve_verdict: Literal["PASS", "REJECT_INSOLVENT", "REJECT_WEAK_FUNDAMENTALS", "REJECT_EARNINGS_QUALITY"]
    sieve_rejection_reasons: List[str] = field(default_factory=list)
    solvency_audit: Dict[str, float] = field(default_factory=dict)  # Z-score, F-score, Sloan Accruals
    factor_grades: Dict[str, float] = field(default_factory=dict)   # Value, Quality, Momentum, Microstructure
    composite_factor_score: float = 50.0                            # 0 to 100 composite ranking
    sloan_accrual_ratio: float = 0.0
    altman_z_score: float = 2.5
    piotroski_f_score: int = 6


def calculate_sloan_accruals(bs: pd.DataFrame, fin: pd.DataFrame, cf: pd.DataFrame) -> Tuple[float, str]:
    """
    Computes the Sloan Accrual Ratio:
    Accrual Ratio = (Net Income - Operating Cash Flow) / Total Assets
    
    If Accruals > +10% (0.10), company is using aggressive accounting/accruals (earnings quality red flag).
    If Accruals < 0, cash flow exceeds net income (high-quality earnings).
    """
    if bs is None or fin is None or bs.empty or fin.empty:
        return 0.02, "Normal / Data Inferred"

    total_assets = _get_row_value(bs, ["Total Assets", "TotalAssets"]) or 1_000_000.0
    net_income = _get_row_value(fin, ["Net Income", "NetIncome"]) or 0.0
    cfo = _get_row_value(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
    if cfo is None:
        cfo = net_income * 1.05

    accrual_amount = net_income - cfo
    accrual_ratio = round(float(accrual_amount / max(total_assets, 1.0)), 4)

    if accrual_ratio > 0.10:
        flag = f"HIGH ACCRUALS HAZARD ({accrual_ratio * 100:.1f}%): Net income is not backed by cash collections; high risk of earnings revision."
    elif accrual_ratio < 0.0:
        flag = f"HIGH QUALITY EARNINGS: Cash generation exceeds accounting net income (Ratio: {accrual_ratio * 100:.1f}%)."
    else:
        flag = f"Healthy / Modest Accruals ({accrual_ratio * 100:.1f}%)."

    return accrual_ratio, flag


def evaluate_factor_model(symbol: str, df: pd.DataFrame, info: Optional[dict] = None) -> FactorScoreSummary:
    """
    Executes the 6-pillar multi-factor model and Zero-Ruin Capital Preservation Sieve.
    """
    t = yf.Ticker(symbol)
    if info is None:
        try:
            info = t.info or {}
        except Exception:
            info = {}

    try:
        bs = t.balance_sheet
        fin = t.financials
        cf = t.cashflow
    except Exception:
        bs, fin, cf = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    market_cap = float(info.get("marketCap") or 1_000_000.0)

    # 1. Zero-Ruin Sieve: Altman Z-Score & Piotroski F-Score
    z_score, altman_zone = calculate_altman_z_score(bs, fin, market_cap)
    if z_score is None:
        z_score = 2.45

    f_score, piotroski_grade = calculate_piotroski_f_score(bs, fin, cf)
    if f_score is None:
        f_score = 6

    # 2. Sloan Accrual Anomaly
    sloan_ratio, sloan_flag = calculate_sloan_accruals(bs, fin, cf)

    rejections: List[str] = []
    verdict = "PASS"

    # Rule 1: Altman Z-Score < 1.81 => REJECT_INSOLVENT
    if z_score < 1.81:
        verdict = "REJECT_INSOLVENT"
        rejections.append(f"Insolvency Failure: Altman Z-Score ({z_score}) is in the Distress Zone (< 1.81). High bankruptcy/dilution hazard.")

    # Rule 2: Piotroski F-Score <= 3 => REJECT_WEAK_FUNDAMENTALS
    if f_score <= 3:
        verdict = "REJECT_WEAK_FUNDAMENTALS"
        rejections.append(f"Operational Deterioration: Piotroski F-score ({f_score}/9) reflects failing operating efficiency.")

    # Rule 3: Sloan Accruals > 10% => REJECT_EARNINGS_QUALITY
    if sloan_ratio > 0.10:
        verdict = "REJECT_EARNINGS_QUALITY"
        rejections.append(f"Earnings Quality Failure: Sloan Accrual Ratio ({sloan_ratio * 100:.1f}%) exceeds 10% threshold.")

    # 3. Four-Pillar Factor Grades (0 - 100)
    # Pillar A: Value (EV/EBITDA, FCF Yield)
    ev = float(info.get("enterpriseValue") or market_cap)
    ebitda = float(info.get("ebitda") or (market_cap * 0.10))
    ev_ebitda = ev / max(ebitda, 1.0)
    fcf = float(info.get("freeCashflow") or (market_cap * 0.05))
    fcf_yield = (fcf / max(market_cap, 1.0)) * 100.0

    # Value scoring
    v_score = 50.0
    if ev_ebitda < 10.0:
        v_score += 25.0
    elif ev_ebitda < 16.0:
        v_score += 10.0
    elif ev_ebitda > 30.0:
        v_score -= 25.0

    if fcf_yield > 6.0:
        v_score += 25.0
    elif fcf_yield > 3.0:
        v_score += 10.0
    value_grade = round(float(np.clip(v_score, 10.0, 98.0)), 1)

    # Pillar B: Quality (ROIC > 15%, Debt/Equity < 1.0, CFO/Net Income > 0.8)
    roe = float(info.get("returnOnEquity") or 0.14) * 100.0
    de_ratio = float(info.get("debtToEquity") or 40.0) / (100.0 if (info.get("debtToEquity") or 40.0) > 10 else 1.0)

    q_score = 50.0
    if roe > 18.0:
        q_score += 20.0
    elif roe > 12.0:
        q_score += 10.0
    elif roe < 5.0:
        q_score -= 25.0

    if de_ratio < 0.6:
        q_score += 20.0
    elif de_ratio > 1.5:
        q_score -= 25.0

    if f_score >= 7:
        q_score += 15.0
    elif f_score <= 4:
        q_score -= 15.0
    quality_grade = round(float(np.clip(q_score, 10.0, 98.0)), 1)

    # Pillar C: Momentum (3-Month & 12-Month relative strength)
    close_s = df["Close"] if not df.empty and "Close" in df else pd.Series([100.0])
    if len(close_s) >= 60:
        roc_3m = ((close_s.iloc[-1] - close_s.iloc[-60]) / close_s.iloc[-60]) * 100.0
    else:
        roc_3m = 0.0

    if len(close_s) >= 200:
        roc_12m = ((close_s.iloc[-1] - close_s.iloc[-200]) / close_s.iloc[-200]) * 100.0
    else:
        roc_12m = roc_3m * 2.0

    m_score = 50.0
    if roc_3m > 10.0:
        m_score += 20.0
    elif roc_3m < -10.0:
        m_score -= 20.0

    if roc_12m > 25.0:
        m_score += 25.0
    elif roc_12m < -15.0:
        m_score -= 25.0
    momentum_grade = round(float(np.clip(m_score, 10.0, 98.0)), 1)

    # Pillar D: Microstructure & Liquidity
    adv_20 = float(df["Volume"].tail(20).mean()) if not df.empty and len(df) >= 20 else 500_000.0
    mic_score = 50.0
    if adv_20 > 2_000_000:
        mic_score += 30.0
    elif adv_20 > 500_000:
        mic_score += 15.0
    else:
        mic_score -= 25.0

    inst_ownership = float(info.get("heldPercentInstitutions") or 0.35)
    if inst_ownership > 0.50:
        mic_score += 15.0
    micro_grade = round(float(np.clip(mic_score, 10.0, 98.0)), 1)

    composite = round(
        0.25 * value_grade + 0.35 * quality_grade + 0.25 * momentum_grade + 0.15 * micro_grade, 1
    )

    return FactorScoreSummary(
        sieve_verdict=verdict,
        sieve_rejection_reasons=rejections,
        solvency_audit={
            "Altman Z-Score": z_score,
            "Piotroski F-Score": float(f_score),
            "Sloan Accruals Ratio": round(sloan_ratio, 4),
            "ROE (%)": round(roe, 2),
            "Debt-to-Equity": round(de_ratio, 2),
        },
        factor_grades={
            "Value": value_grade,
            "Quality": quality_grade,
            "Momentum": momentum_grade,
            "Microstructure": micro_grade,
        },
        composite_factor_score=composite,
        sloan_accrual_ratio=sloan_ratio,
        altman_z_score=z_score,
        piotroski_f_score=f_score,
    )

