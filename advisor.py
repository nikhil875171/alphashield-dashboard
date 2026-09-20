import argparse
import os
import sys
from typing import List, Literal

# Ensure UTF-8 output for Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
import pandas as pd
from pydantic import BaseModel, Field
import yfinance as yf

# Load environment variables from .env
load_dotenv()


# 1. Pydantic Schema for Structured Recommendation
class TradeRecommendation(BaseModel):
    ticker: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence_score: float = Field(
        description="Confidence between 0.0 (low) and 1.0 (high)"
    )
    time_horizon: Literal["INTRADAY", "SWING (1-2 WEEKS)", "POSITIONAL (1-3 MONTHS)"]
    entry_price_range: str = Field(description="Recommended entry price range in INR")
    stop_loss: float = Field(description="Strict stop-loss price level in INR")
    target_price: float = Field(description="Realistic target exit price in INR")
    risk_reward_ratio: str = Field(description="e.g. 1:2 or 1:3")
    technical_catalysts: List[str] = Field(
        description="Key technical indicator signals driving the recommendation"
    )
    key_risks: List[str] = Field(
        description="Key risk factors, resistances, or bearish indicators"
    )
    summary_verdict: str = Field(
        description="2-3 sentence executive summary for the trader"
    )


# 2. Market Data Retrieval & Indicator Computation
def fetch_market_data(symbol: str) -> dict:
    """Fetches historical price data and computes key technical indicators."""
    print(f"[*] Fetching historical market data for {symbol}...")
    stock = yf.Ticker(symbol)
    df = stock.history(period="6mo")

    if df.empty or len(df) < 50:
        raise ValueError(
            f"Insufficient historical data found for '{symbol}'. "
            "For Indian stocks, ensure the '.NS' (NSE) or '.BO' (BSE) suffix is included."
        )

    # Calculate 20-day, 50-day, and 200-day (if data permits) Moving Averages
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

    # Calculate 14-day Relative Strength Index (RSI)
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss.replace(0, 0.0001))
    df["RSI_14"] = 100 - (100 / (1 + rs))

    # MACD (12, 26, 9)
    exp1 = df["Close"].ewm(span=12, adjust=False).mean()
    exp2 = df["Close"].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    df["MACD"] = macd
    df["MACD_SIGNAL"] = signal

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    high_period = df["High"].max()
    low_period = df["Low"].min()
    avg_vol_20d = int(df["Volume"].tail(20).mean())

    return {
        "symbol": symbol,
        "current_price": round(float(latest["Close"]), 2),
        "previous_close": round(float(prev["Close"]), 2),
        "daily_change_pct": round(
            float((latest["Close"] - prev["Close"]) / prev["Close"] * 100), 2
        ),
        "sma_20": round(float(latest["SMA_20"]), 2),
        "sma_50": round(float(latest["SMA_50"]), 2),
        "ema_20": round(float(latest["EMA_20"]), 2),
        "rsi_14": round(float(latest["RSI_14"]), 2),
        "macd": round(float(latest["MACD"]), 2),
        "macd_signal": round(float(latest["MACD_SIGNAL"]), 2),
        "period_high": round(float(high_period), 2),
        "period_low": round(float(low_period), 2),
        "volume": int(latest["Volume"]),
        "avg_volume_20d": avg_vol_20d,
        "volume_ratio": round(float(latest["Volume"]) / max(avg_vol_20d, 1), 2),
    }


# 3. Gemini Advisory Engine
def get_gemini_recommendation(data: dict) -> TradeRecommendation:
    """Sends structured market data to Gemini and returns a validated recommendation."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        print("\n[!] Error: GEMINI_API_KEY is not set.")
        print("    Please create a .env file and add your key: GEMINI_API_KEY=\"your_key\"")
        print("    You can get a free key from: https://aistudio.google.com/")
        sys.exit(1)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an experienced Chartered Market Technician (CMT) and quantitative swing trader.
    Analyze the technical setup below for {data['symbol']} and formulate a disciplined trading plan.

    Market Snapshot:
    - Symbol: {data['symbol']}
    - Current Price: ₹{data['current_price']} (Day change: {data['daily_change_pct']}%)
    - 20-Day SMA: ₹{data['sma_20']} | 20-Day EMA: ₹{data['ema_20']}
    - 50-Day SMA: ₹{data['sma_50']}
    - 14-Day RSI: {data['rsi_14']}
    - MACD Line: {data['macd']} (Signal Line: {data['macd_signal']})
    - 6-Month Range: Low ₹{data['period_low']} — High ₹{data['period_high']}
    - Today's Volume: {data['volume']:,} (vs 20-day avg: {data['avg_volume_20d']:,}, Ratio: {data['volume_ratio']}x)

    Technical Rules & Risk Policy:
    1. If RSI > 70, flag overbought condition; if RSI < 30, flag oversold bounce potential.
    2. Price above 20 and 50 SMA with positive MACD indicates bullish momentum.
    3. Price below 20 and 50 SMA indicates bearish momentum or correction.
    4. For BUY suggestions, enforce a minimum 1:2 Risk-to-Reward ratio.
    5. If price action is choppy or conflicting, recommend HOLD.
    6. Always provide sensible stop-loss based on support levels or moving averages.
    """

    print("[*] Generating recommendation with Gemini AI...")
    models_to_try = ["gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3.6-flash"]
    for current_model in models_to_try:
        try:
            response = client.models.generate_content(
                model=current_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=TradeRecommendation.model_json_schema(),
                    temperature=0.2,
                ),
            )
            return TradeRecommendation.model_validate_json(response.text)
        except Exception as e:
            continue

    raise RuntimeError("All Gemini models encountered transient rate limits. Please retry in a few moments.")





# 4. Formatted Terminal Dashboard
def display_report(metrics: dict, rec: TradeRecommendation):
    border = "=" * 65
    print("\n" + border)
    print(f"         AI TRADING ADVISORY REPORT: {rec.ticker}")
    print(border)
    print(f" Current Price:  ₹{metrics['current_price']} ({metrics['daily_change_pct']}%)")
    print(f" 20 SMA / 50 SMA: ₹{metrics['sma_20']} / ₹{metrics['sma_50']}")
    print(f" RSI (14):       {metrics['rsi_14']} | Volume Ratio: {metrics['volume_ratio']}x")
    print("-" * 65)
    print(f" ACTION:         [{rec.action}]")
    print(f" Confidence:     {rec.confidence_score * 100:.1f}%")
    print(f" Horizon:        {rec.time_horizon}")
    print(f" Entry Range:    {rec.entry_price_range}")
    print(f" Target Price:   ₹{rec.target_price}")
    print(f" Stop Loss:      ₹{rec.stop_loss}")
    print(f" Risk / Reward:  {rec.risk_reward_ratio}")
    print("-" * 65)
    print(" Technical Catalysts:")
    for item in rec.technical_catalysts:
        print(f"   [+] {item}")
    print("\n Key Risk Factors:")
    for item in rec.key_risks:
        print(f"   [-] {item}")
    print("-" * 65)
    print(f" Verdict: {rec.summary_verdict}")
    print(border)
    print(" Disclaimer: For educational & decision-support only. Not SEBI registered.")
    print(border + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="AI Stock Trading Advisor using Python & Gemini Pro"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="RELIANCE.NS",
        help="Stock ticker symbol (e.g. RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS)",
    )
    args = parser.parse_args()

    try:
        metrics = fetch_market_data(args.symbol)
        rec = get_gemini_recommendation(metrics)
        display_report(metrics, rec)
    except Exception as e:
        print(f"[!] Execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

