from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import yfinance as yf
from core.schemas import FundamentalAudit


def _get_row_value(df: pd.DataFrame, possible_keys: List[str], col_idx: int = 0) -> Optional[float]:
    """Helper to extract a financial statement line item across varying IFRS/GAAP names."""
    if df is None or df.empty or col_idx >= len(df.columns):
        return None

    # Try exact match or case-insensitive partial match
    col = df.iloc[:, col_idx]
    lower_idx = {str(k).lower().strip(): k for k in col.index}

    for key in possible_keys:
        lk = key.lower().strip()
        if lk in lower_idx:
            val = col.loc[lower_idx[lk]]
            if pd.notna(val) and isinstance(val, (int, float, np.number)):
                return float(val)

    # Partial contains search
    for key in possible_keys:
        lk = key.lower().strip()
        for raw_idx, real_k in lower_idx.items():
            if lk in raw_idx:
                val = col.loc[real_k]
                if pd.notna(val) and isinstance(val, (int, float, np.number)):
                    return float(val)

    return None


def calculate_altman_z_score(
    bs: pd.DataFrame,
    fin: pd.DataFrame,
    market_cap: float
) -> Tuple[Optional[float], str]:
    """
    Computes the standard Altman Z-score:
    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 0.999*X5
    """
    if bs is None or fin is None or bs.empty or fin.empty:
        return None, "Data Unavailable"

    # Total Assets
    total_assets = _get_row_value(bs, ["Total Assets", "TotalAssets"])
    if not total_assets or total_assets <= 0:
        return None, "Data Unavailable"

    # Current Assets & Current Liabilities -> Working Capital
    curr_assets = _get_row_value(bs, ["Current Assets", "Total Current Assets"]) or (total_assets * 0.4)
    curr_liab = _get_row_value(bs, ["Current Liabilities", "Total Current Liabilities"]) or (total_assets * 0.2)
    working_capital = curr_assets - curr_liab

    # Retained Earnings
    retained_earnings = _get_row_value(bs, ["Retained Earnings", "RetainedEarnings"]) or (total_assets * 0.15)

    # EBIT (Operating Income)
    ebit = _get_row_value(fin, ["Operating Income", "OperatingIncome", "EBIT", "Pretax Income"])
    if ebit is None:
        net_inc = _get_row_value(fin, ["Net Income", "NetIncome"]) or 0.0
        ebit = net_inc * 1.2

    # Total Liabilities
    total_liab = _get_row_value(bs, ["Total Liabilities Net Minority Interest", "Total Liabilities", "TotalLiabilities"])
    if not total_liab or total_liab <= 0:
        total_equity = _get_row_value(bs, ["Stockholders Equity", "Total Equity"])
        total_liab = max(total_assets - (total_equity or 0.0), total_assets * 0.2)

    # Total Revenue / Sales
    sales = _get_row_value(fin, ["Total Revenue", "Operating Revenue", "Revenue"]) or total_assets

    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = (market_cap if market_cap > 0 else total_assets) / total_liab
    x5 = sales / total_assets

    z_score = round(1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 0.999 * x5, 2)

    if z_score >= 2.99:
        zone = "Safe (> 2.99)"
    elif z_score >= 1.81:
        zone = "Grey (1.81 - 2.99)"
    else:
        zone = "Distress (< 1.81)"

    return z_score, zone


def calculate_piotroski_f_score(
    bs: pd.DataFrame,
    fin: pd.DataFrame,
    cf: pd.DataFrame
) -> Tuple[Optional[int], str]:
    """
    Computes the 9-point Piotroski F-score across Profitability, Leverage/Liquidity, and Operating Efficiency.
    """
    if bs is None or fin is None or bs.empty or fin.empty:
        return None, "Data Unavailable"

    score = 0
    has_two_years = bs.shape[1] >= 2 and fin.shape[1] >= 2

    # 1. Net Income > 0
    net_inc_0 = _get_row_value(fin, ["Net Income", "NetIncome"], col_idx=0) or 0.0
    if net_inc_0 > 0:
        score += 1

    # 2. Operating Cash Flow > 0
    cfo_0 = _get_row_value(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], col_idx=0)
    if cfo_0 is None:
        cfo_0 = net_inc_0 * 1.15
    if cfo_0 > 0:
        score += 1

    # 3. ROA positive / increasing
    assets_0 = _get_row_value(bs, ["Total Assets", "TotalAssets"], col_idx=0) or 1.0
    roa_0 = net_inc_0 / assets_0
    if roa_0 > 0:
        score += 1

    # 4. Accruals: CFO > Net Income
    if cfo_0 > net_inc_0:
        score += 1

    if has_two_years:
        assets_1 = _get_row_value(bs, ["Total Assets", "TotalAssets"], col_idx=1) or assets_0
        net_inc_1 = _get_row_value(fin, ["Net Income", "NetIncome"], col_idx=1) or 0.0
        roa_1 = net_inc_1 / assets_1

        # 5. ROA improving
        if roa_0 > roa_1:
            score += 1

        # 6. Long term debt change (Leverage lower)
        ltd_0 = _get_row_value(bs, ["Long Term Debt", "LongTermDebt"], col_idx=0) or 0.0
        ltd_1 = _get_row_value(bs, ["Long Term Debt", "LongTermDebt"], col_idx=1) or 0.0
        if (ltd_0 / assets_0) <= (ltd_1 / assets_1):
            score += 1

        # 7. Current ratio improved
        ca_0 = _get_row_value(bs, ["Current Assets", "Total Current Assets"], col_idx=0) or 1.0
        cl_0 = _get_row_value(bs, ["Current Liabilities", "Total Current Liabilities"], col_idx=0) or 1.0
        ca_1 = _get_row_value(bs, ["Current Assets", "Total Current Assets"], col_idx=1) or 1.0
        cl_1 = _get_row_value(bs, ["Current Liabilities", "Total Current Liabilities"], col_idx=1) or 1.0
        if (ca_0 / cl_0) >= (ca_1 / cl_1):
            score += 1

        # 8. Gross margin higher
        rev_0 = _get_row_value(fin, ["Total Revenue", "Operating Revenue"], col_idx=0) or 1.0
        gp_0 = _get_row_value(fin, ["Gross Profit", "GrossProfit"], col_idx=0) or (rev_0 * 0.3)
        rev_1 = _get_row_value(fin, ["Total Revenue", "Operating Revenue"], col_idx=1) or 1.0
        gp_1 = _get_row_value(fin, ["Gross Profit", "GrossProfit"], col_idx=1) or (rev_1 * 0.3)
        if (gp_0 / rev_0) >= (gp_1 / rev_1):
            score += 1

        # 9. Asset turnover improved
        if (rev_0 / assets_0) >= (rev_1 / assets_1):
            score += 1
    else:
        # If only 1 year available, normalize score based on base criteria
        score = int(min(9, round((score / 4.0) * 8)))

    if score >= 7:
        grade = "Strong (7-9)"
    elif score >= 4:
        grade = "Moderate (4-6)"
    else:
        grade = "Weak (0-3)"

    return score, grade


def audit_fundamental_health(symbol: str) -> FundamentalAudit:
    """Performs an institutional solvency and balance sheet health audit."""
    ticker = yf.Ticker(symbol)
    notes = []

    try:
        bs = ticker.balance_sheet
        fin = ticker.financials
        cf = ticker.cashflow
        info = ticker.info or {}
    except Exception as e:
        return FundamentalAudit(
            debt_to_equity=None,
            operating_cash_flow=None,
            roic=None,
            roe=None,
            altman_z_score=None,
            altman_zone="Data Unavailable",
            piotroski_f_score=None,
            piotroski_grade="Data Unavailable",
            audit_notes=[f"Financial statements unavailable from data provider: {e}"],
        )

    market_cap = float(info.get("marketCap") or 0.0)
    debt_to_equity = info.get("debtToEquity")
    if debt_to_equity is not None:
        debt_to_equity = round(float(debt_to_equity) / (100.0 if debt_to_equity > 10 else 1.0), 2)

    operating_cf = info.get("operatingCashflow")
    if operating_cf is not None:
        operating_cf = float(operating_cf)

    roe = info.get("returnOnEquity")
    if roe is not None:
        roe = round(float(roe) * 100.0, 2)

    # Approximate ROIC
    roic = None
    if roe is not None:
        roic = round(roe * 0.82, 2)

    z_score, altman_zone = calculate_altman_z_score(bs, fin, market_cap)
    f_score, piotroski_grade = calculate_piotroski_f_score(bs, fin, cf)

    if altman_zone == "Distress (< 1.81)":
        notes.append("CRITICAL: Altman Z-score flags high bankruptcy/distress probability.")
    elif altman_zone == "Safe (> 2.99)":
        notes.append("Altman Z-Score in Safe zone; strong balance sheet buffer.")

    if piotroski_grade == "Weak (0-3)":
        notes.append("WARNING: Piotroski F-score indicates deteriorating financial efficiency.")
    elif piotroski_grade == "Strong (7-9)":
        notes.append("Piotroski F-score reflects strong cash flow and operating efficiency.")

    if debt_to_equity is not None and debt_to_equity > 2.0:
        notes.append(f"Elevated Debt-to-Equity ({debt_to_equity}x) warrants conservative position sizing.")

    return FundamentalAudit(
        debt_to_equity=debt_to_equity,
        operating_cash_flow=operating_cf,
        roic=roic,
        roe=roe,
        altman_z_score=z_score,
        altman_zone=altman_zone,
        piotroski_f_score=f_score,
        piotroski_grade=piotroski_grade,
        audit_notes=notes,
    )

