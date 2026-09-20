from typing import Optional
import yfinance as yf
from core.schemas import InstitutionalSnapshot


def audit_institutional_positioning(symbol: str) -> InstitutionalSnapshot:
    """Ingests smart money metrics: institutional holding %, insider ownership, and short interest."""
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}

    inst_pct = info.get("heldPercentInstitutions")
    if inst_pct is not None:
        inst_pct = round(float(inst_pct) * 100.0, 2)

    insider_pct = info.get("heldPercentInsiders")
    if insider_pct is not None:
        insider_pct = round(float(insider_pct) * 100.0, 2)

    short_float = info.get("shortPercentOfFloat")
    if short_float is not None:
        short_float = round(float(short_float) * 100.0, 2)

    signals = []
    if inst_pct is not None:
        if inst_pct > 60.0:
            signals.append(f"Heavy Institutional Backing ({inst_pct}% held).")
        elif inst_pct < 15.0:
            signals.append(f"Low Institutional Coverage ({inst_pct}% held) - retail driven.")

    if short_float is not None and short_float > 10.0:
        signals.append(f"High Short Interest ({short_float}% of float) - watch for squeeze volatility.")

    if insider_pct is not None and insider_pct > 25.0:
        signals.append(f"High Insider/Promoter Ownership ({insider_pct}% held) - aligned management.")

    summary = " | ".join(signals) if signals else "Neutral institutional footprint."

    return InstitutionalSnapshot(
        institutional_ownership_pct=inst_pct,
        insider_ownership_pct=insider_pct,
        short_float_pct=short_float,
        institutional_signal=summary,
    )

