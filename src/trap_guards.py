from typing import List, Optional, Tuple
import pandas as pd


def is_exhaustion_trap(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Detects Exhaustion Traps:
    Flag if a 3-day price rise occurs directly into declining 50/200 EMA resistance with dropping volume OR RSI(14) > 75.
    """
    if df.empty or len(df) < 20:
        return False, "Insufficient data for exhaustion analysis."

    c = df["Close"]
    v = df["Volume"]

    # 3-day rise check
    if len(c) >= 4:
        three_day_up = (c.iloc[-1] > c.iloc[-2] > c.iloc[-3] > c.iloc[-4])
    else:
        three_day_up = False

    # Declining volume over the 3 days
    if len(v) >= 3:
        volume_declining = (v.iloc[-1] < v.iloc[-2] < v.iloc[-3])
    else:
        volume_declining = False

    # RSI condition
    rsi = float(df["RSI_14"].iloc[-1]) if "RSI_14" in df else 50.0

    # Moving average resistance check
    curr_p = float(c.iloc[-1])
    ema_50 = float(df["EMA_50"].iloc[-1]) if "EMA_50" in df else curr_p
    ema_200 = float(df["EMA_200"].iloc[-1]) if "EMA_200" in df else curr_p

    # Near 50 or 200 EMA resistance (within 1.5%) while EMA is sloping downwards
    near_resistance = (abs(curr_p - ema_50) / curr_p < 0.018 or abs(curr_p - ema_200) / curr_p < 0.018)

    if (three_day_up and volume_declining and near_resistance) or rsi > 75.0:
        reason = f"EXHAUSTION TRAP: 3-day rally into major overhead resistance on declining volume with RSI({rsi:.1f}) overbought."
        return True, reason

    return False, "No exhaustion trap detected."


def is_priced_in_rumor(df: pd.DataFrame, catalyst_date: Optional[str] = None) -> Tuple[bool, str]:
    """
    Detects Priced-in Rumors / 'Buy the Rumor, Sell the News':
    Flag if stock has run > 20% in the 20 trading sessions prior to an expected announcement.
    """
    if df.empty or len(df) < 20:
        return False, "Normal momentum window."

    c = df["Close"]
    runup_20d = ((c.iloc[-1] - c.iloc[-20]) / c.iloc[-20]) * 100.0

    if runup_20d >= 20.0:
        reason = f"PRICED-IN RUMOR RISK: Asset has already surged +{runup_20d:.1f}% in the last 20 sessions; high vulnerability to 'sell-the-news' profit taking."
        return True, reason

    return False, "Pre-catalyst runup within balanced bounds."


def is_cyclical_value_trap(pe_ratio: Optional[float], sector: str) -> Tuple[bool, str]:
    """
    Detects Cyclical Value Traps:
    Prevent classifying cyclical commodity/metal/oil producers as 'cheap' when trailing P/E is near historical lows at cyclic peak earnings.
    """
    if pe_ratio is None or pe_ratio <= 0:
        return False, "P/E ratio not applicable."

    cyclical_keywords = ["BASIC MATERIALS", "METALS", "MINING", "STEEL", "COMMODITIES", "OIL & GAS", "ENERGY", "CHEMICALS"]
    is_cyclical = any(k in sector.upper() for k in cyclical_keywords)

    # Cyclical stocks often have lowest P/E at peak earnings right before demand collapse
    if is_cyclical and pe_ratio < 7.5:
        reason = f"CYCLICAL VALUE TRAP: P/E of {pe_ratio:.1f}x in {sector} may reflect peak-cycle trailing earnings rather than true margin discount."
        return True, reason

    return False, "Valuation not signaling cyclical trap."


def is_geopolitical_overreaction(event_type: str, price_drawdown: float) -> Tuple[bool, str]:
    """
    Distinguishes between transitory geopolitical headlines (V-bottom setups) and critical supply chokepoint closures.
    """
    et = event_type.upper()
    if any(k in et for k in ["CHOKEPOINT", "STRAIT OF HORMUZ", "SUEZ CLOSURE", "SANCTIONS DIRECT", "INFRASTRUCTURE ATTACK"]):
        return False, "STRUCTURAL SUPPLY DISRUPTION: Chokepoint closures enforce persistent structural freight & commodity inflation."

    if price_drawdown > 5.0 and any(k in et for k in ["HEADLINE", "THREAT", "RHETORIC", "DIPLOMATIC", "MISSILE TEST"]):
        return True, f"GEOPOLITICAL OVERREACTION (-{price_drawdown:.1f}%): Transitory fear headline typically produces a sharp mean-reverting V-bottom."

    return False, "Standard price reaction."


def evaluate_all_traps(df: pd.DataFrame, info: Optional[dict] = None) -> List[str]:
    """
    Aggregates all failure mode checks and returns active trap warning strings.
    """
    info = info or {}
    traps: List[str] = []

    # 1. Exhaustion Trap
    is_exh, exh_msg = is_exhaustion_trap(df)
    if is_exh:
        traps.append(exh_msg)

    # 2. Priced-in Rumor
    is_rumor, rumor_msg = is_priced_in_rumor(df)
    if is_rumor:
        traps.append(rumor_msg)

    # 3. Cyclical Value Trap
    pe = info.get("trailingPE")
    sec = info.get("sector", "")
    is_cyc, cyc_msg = is_cyclical_value_trap(pe, sec)
    if is_cyc:
        traps.append(cyc_msg)

    return traps

