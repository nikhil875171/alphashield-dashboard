import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Any, Optional
from core.schemas import AlphaShieldRecommendation, TechnicalSnapshot


def build_interactive_chart(
    df: pd.DataFrame,
    tech: TechnicalSnapshot,
    rec: Any,
    currency_symbol: Optional[str] = None
) -> go.Figure:
    """
    Constructs an institutional 3-tier Plotly chart:
    1. Main Candlesticks with EMA 20/50/200, VWAP, and Trade Level Overlays (Entry, Stop, Targets)
    2. Volume Bars with 20-day ADV trendline
    3. RSI(14) with Overbought (70) and Oversold (30) bands
    """
    # Create 3 subplots with custom height ratios
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.65, 0.18, 0.17],
        subplot_titles=(
            f"{tech.symbol} — Institutional Multi-Factor Technical Architecture",
            "Volume Microstructure & 20-Day ADV",
            "RSI (14-Period) Momentum"
        )
    )

    # 1. Candlestick Trace with Classy Pastel Palette
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
            increasing_line_color="#34D399",  # Soft Pastel Mint Emerald
            decreasing_line_color="#FB7185",  # Soft Pastel Coral Rose
        ),
        row=1,
        col=1
    )

    # 2. Moving Average Overlays in Sophisticated Pastels
    if "EMA_20" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["EMA_20"], mode="lines", name="20 EMA", line=dict(color="#38BDF8", width=1.5)),
            row=1, col=1
        )
    if "EMA_50" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["EMA_50"], mode="lines", name="50 EMA", line=dict(color="#FBBF24", width=1.5)),
            row=1, col=1
        )
    if "EMA_200" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["EMA_200"], mode="lines", name="200 EMA", line=dict(color="#C084FC", width=1.8)),
            row=1, col=1
        )
    if "VWAP" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["VWAP"], mode="lines", name="VWAP", line=dict(color="#B0BEC5", width=1.0, dash="dot")),
            row=1, col=1
        )

    # Auto-detect currency symbol if not explicitly provided
    if not currency_symbol:
        currency_symbol = "₹" if (tech.symbol.endswith(".NS") or tech.symbol.endswith(".BO")) else "$"

    # Support both AlphaShieldRecommendation and InstitutionalTradePlan schemas safely
    stop_loss = getattr(rec, "algorithmic_stop_loss", None)
    if stop_loss is None:
        stop_loss = getattr(rec, "hard_stop_loss", None)

    entry_range = getattr(rec, "entry_price_range", None)
    if entry_range is None:
        entry_range = getattr(rec, "recommended_entry_range", None)

    target_ladder = getattr(rec, "target_ladder", None)
    if target_ladder is None:
        target_ladder = getattr(rec, "target_price_ladder", None)
    if target_ladder is None:
        target_ladder = []

    # 3. Horizontal Trade Level Annotations
    # Hard Stop Loss & Shaded Invalidation Zone in Soft Coral
    if stop_loss is not None and stop_loss > 0:
        fig.add_hline(
            y=stop_loss,
            line_dash="dash",
            line_color="#FB7185",
            line_width=1.8,
            annotation_text=f"Hard Stop: {currency_symbol}{stop_loss}",
            annotation_position="bottom right",
            annotation_font_color="#FDA4AF",
            row=1, col=1
        )
        fig.add_hrect(
            y0=stop_loss * 0.96,
            y1=stop_loss,
            fillcolor="rgba(251, 113, 133, 0.12)",
            line_width=0,
            row=1, col=1
        )

    # Entry Range in Soft Pastel Blue
    if entry_range and len(entry_range) >= 2 and entry_range[0] > 0 and entry_range[1] > 0:
        entry_low, entry_high = entry_range[0], entry_range[1]
        fig.add_hrect(
            y0=entry_low,
            y1=entry_high,
            fillcolor="rgba(96, 165, 250, 0.14)",
            line_width=1,
            line_dash="dot",
            line_color="#60A5FA",
            annotation_text=f"Entry Zone ({currency_symbol}{entry_low} - {currency_symbol}{entry_high})",
            annotation_position="top left",
            annotation_font_color="#93C5FD",
            row=1, col=1
        )

    # Target Price Ladder & Shaded Profit Accumulation Band in Pastel Mint
    if target_ladder and len(target_ladder) >= 1 and target_ladder[0] > 0:
        t_min = target_ladder[0]
        t_max = target_ladder[-1] if len(target_ladder) > 1 else target_ladder[0] * 1.05
        fig.add_hrect(
            y0=t_min,
            y1=t_max,
            fillcolor="rgba(52, 211, 153, 0.10)",
            line_width=0,
            row=1, col=1
        )

    target_colors = ["#A7F3D0", "#6EE7B7", "#34D399"]
    for idx, target in enumerate(target_ladder[:3]):
        if target is not None and target > 0:
            color = target_colors[idx % len(target_colors)]
            fig.add_hline(
                y=target,
                line_dash="dashdot",
                line_color=color,
                line_width=1.5,
                annotation_text=f"Target {idx + 1}: {currency_symbol}{target}",
                annotation_position="top right",
                annotation_font_color=color,
                row=1, col=1
            )

    # 4. Volume Bar Subplot with Soft Pastel Tints
    vol_colors = ["#34D399" if c >= o else "#FB7185" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=vol_colors,
            opacity=0.65
        ),
        row=2,
        col=1
    )
    if "VOL_SMA_20" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["VOL_SMA_20"],
                mode="lines",
                name="20 ADV",
                line=dict(color="#FDE68A", width=1.5)
            ),
            row=2,
            col=1
        )

    # 5. RSI Subplot with Pastel Lilac
    if "RSI_14" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["RSI_14"],
                mode="lines",
                name="RSI (14)",
                line=dict(color="#C4B5FD", width=1.5)
            ),
            row=3,
            col=1
        )
        # 70 Overbought line
        fig.add_hline(y=70, line_dash="dash", line_color="#FB7185", line_width=1, row=3, col=1)
        # 30 Oversold line
        fig.add_hline(y=30, line_dash="dash", line_color="#34D399", line_width=1, row=3, col=1)

    # Dark Obsidian / Slate Institutional Theme Styling
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0A0E1A",
        plot_bgcolor="#111827",
        font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", color="#CBD5E1", size=11),
        xaxis_rangeslider_visible=False,
        height=720,
        margin=dict(l=40, r=60, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )

    # Update axes styling
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.06)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.06)")
    fig.update_yaxes(title_text=f"Price ({currency_symbol})", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[10, 90], row=3, col=1)

    return fig


def compute_institutional_dimension_scores(
    macro: Any,
    factors: Any,
    tech: Any,
    micro: Any,
    thematic: Any,
    risk: Any,
) -> dict:
    """
    Computes normalized institutional health scores (0-100) and statuses for the 6 core pillars:
    1. Market Mood (Volatility / Macro Regime)
    2. Company Health (Forensic Accounting & Solvency)
    3. Price Trend (EMA Alignment & RSI Momentum)
    4. Smart Money (Microstructure Delivery Accumulation)
    5. Secular Horizon (Wave Potential & Scarcity Tailwind)
    6. Safety Gauge (Asymmetric Risk-Reward & Capital Protection)
    """
    import math

    # 1. Market Mood
    vix = getattr(macro, "vix", 15.0) if macro else 15.0
    mood_color = getattr(macro, "market_mood_color", "green") if macro else "green"
    if mood_color == "green":
        mood_score = 95 if vix < 13.0 else (88 if vix < 16.0 else 80)
        mood_status = "🟢 Calm & Safe"
        mood_class = "safe"
    elif mood_color == "yellow":
        mood_score = 65 if vix < 22.0 else 55
        mood_status = "🟡 Choppy Waters"
        mood_class = "caution"
    else:
        mood_score = 35 if vix < 30.0 else 20
        mood_status = "🔴 Stormy Seas"
        mood_class = "danger"

    # 2. Company Health
    z_score = getattr(factors, "altman_z_score", 2.5) if factors else 2.5
    f_score = getattr(factors, "piotroski_f_score", 6) if factors else 6
    is_manip = getattr(factors, "beneish_manipulation_risk", False) if factors else False
    sloan_val = getattr(factors, "sloan_accrual_ratio", 0.0) if factors else 0.0

    if z_score >= 2.99:
        base_health = 88
        health_status = "🟢 Solid & Safe"
        health_class = "safe"
    elif z_score >= 1.81:
        base_health = 65
        health_status = "🟡 Watchful Debt"
        health_class = "caution"
    else:
        base_health = 30
        health_status = "🔴 Insolvent Risk"
        health_class = "danger"

    if f_score >= 7:
        base_health += 7
    elif f_score <= 4:
        base_health -= 10

    if is_manip:
        base_health = min(base_health, 35)
        health_status = "🔴 Forensic Risk"
        health_class = "danger"
    elif abs(sloan_val) > 0.10:
        base_health -= 6

    health_score = max(15, min(98, base_health))

    # 3. Price Trend
    price = getattr(tech, "current_price", 100.0) if tech else 100.0
    ema_20 = getattr(tech, "ema_20", price) if tech else price
    ema_50 = getattr(tech, "ema_50", price) if tech else price
    ema_200 = getattr(tech, "ema_200", price) if tech else price
    rsi = getattr(tech, "rsi_14", 50.0) if tech else 50.0

    if price > ema_50 and price > ema_200:
        base_trend = 86
    elif price > ema_50:
        base_trend = 72
    elif price > ema_200:
        base_trend = 52
    else:
        base_trend = 28

    if 45 <= rsi <= 65:
        base_trend += 8
    elif rsi >= 70:
        base_trend -= 12  # Overheated
    elif rsi < 35:
        base_trend -= 10  # Breakdown / Oversold

    trend_score = max(15, min(95, base_trend))
    is_uptrend = price > ema_50 and rsi < 70
    is_overheated = rsi >= 70
    trend_status = "🟢 Strong Uptrend" if is_uptrend else ("🟡 Resting" if is_overheated else "🔴 Downtrend")
    trend_class = "safe" if is_uptrend else ("caution" if is_overheated else "danger")

    # 4. Smart Money
    deliv_valid = getattr(micro, "delivery_valid", True) if micro else True
    deliv_pct = getattr(micro, "delivery_pct", 40.0) if micro else 40.0
    if deliv_valid:
        if deliv_pct >= 55.0:
            deliv_score = 94
        elif deliv_pct >= 45.0:
            deliv_score = 84
        elif deliv_pct >= 35.0:
            deliv_score = 72
        else:
            deliv_score = 65
        money_status = "🟢 Whales Buying"
        money_class = "safe"
    else:
        deliv_score = 38
        money_status = "🟡 Day Trading"
        money_class = "caution"
    money_score = max(20, min(98, deliv_score))

    # 5. Secular Horizon
    horizon_code = getattr(thematic, "horizon_code", "3_YEARS") if thematic else "3_YEARS"
    if horizon_code in ["20_YEARS", "10_YEARS"]:
        sec_score = 92
    elif horizon_code == "5_YEARS":
        sec_score = 84
    elif horizon_code == "3_YEARS":
        sec_score = 76
    else:
        sec_score = 65
    sec_status = getattr(thematic, "timeframe", "Next 3 Years") if thematic else "Next 3 Years"
    sec_class = "safe"

    # 6. Safety Gauge
    asym_pass = getattr(risk, "asymmetric_rr_passed", False) if risk else False
    rr = getattr(risk, "risk_reward_ratio", 0.0) if risk else 0.0
    if rr is None or math.isnan(rr) or rr <= 0:
        rr_clean = 0.0
        safety_score = 20
        safety_status = "🔴 Poor Odds"
        safety_class = "danger"
    elif asym_pass:
        rr_clean = float(rr)
        safety_score = min(96, max(75, int(rr_clean * 28)))
        safety_status = "🟢 Asymmetric Win"
        safety_class = "safe"
    else:
        rr_clean = float(rr)
        safety_score = max(25, min(60, int(rr_clean * 20)))
        safety_status = "🔴 Poor Odds"
        safety_class = "danger"

    return {
        "Market Mood": {
            "score": mood_score,
            "status": mood_status,
            "class": mood_class,
            "metric": f"VIX: {vix:.1f}",
            "axis_label": "Market Mood",
        },
        "Company Health": {
            "score": health_score,
            "status": health_status,
            "class": health_class,
            "metric": f"Z-Score: {z_score:.2f}",
            "axis_label": "Balance Sheet",
        },
        "Price Trend": {
            "score": trend_score,
            "status": trend_status,
            "class": trend_class,
            "metric": f"RSI: {rsi:.1f}",
            "axis_label": "Price Trend",
        },
        "Smart Money": {
            "score": money_score,
            "status": money_status,
            "class": money_class,
            "metric": f"Delivery: {deliv_pct:.1f}%",
            "axis_label": "Smart Money",
        },
        "Secular Horizon": {
            "score": sec_score,
            "status": sec_status,
            "class": sec_class,
            "metric": f"Wave: {horizon_code}",
            "axis_label": "Secular Wave",
        },
        "Safety Gauge": {
            "score": safety_score,
            "status": safety_status,
            "class": safety_class,
            "metric": f"Odds: {rr_clean:.1f}x" if rr_clean > 0 else "Odds: Gate Active",
            "axis_label": "Capital Safety",
        },
    }


def build_institutional_radar_chart(
    dimension_scores: dict,
    ticker: str = "ASSET",
) -> go.Figure:
    """
    Constructs an institutional 6-axis Plotly Polar Radar Chart displaying
    the company's posture across all 6 core dimensions vs the institutional benchmark (60/100).
    """
    categories = [data["axis_label"] for data in dimension_scores.values()]
    scores = [data["score"] for data in dimension_scores.values()]
    metrics = [data["metric"] for data in dimension_scores.values()]
    statuses = [data["status"] for data in dimension_scores.values()]

    # Close polygon loop
    cat_loop = categories + [categories[0]]
    scores_loop = scores + [scores[0]]
    benchmark_loop = [60] * len(cat_loop)

    hover_texts = [
        f"<b>{c}</b><br>Score: <b>{s}/100</b><br>Status: {st}<br>Metric: {m}"
        for c, s, st, m in zip(categories, scores, statuses, metrics)
    ]
    hover_texts_loop = hover_texts + [hover_texts[0]]

    fig = go.Figure()

    # 1. Institutional Minimum Standard Benchmark (60/100)
    fig.add_trace(
        go.Scatterpolar(
            r=benchmark_loop,
            theta=cat_loop,
            mode="lines",
            line=dict(color="rgba(148, 163, 184, 0.45)", width=1.5, dash="dash"),
            name="Institutional Benchmark (60)",
            hoverinfo="skip",
        )
    )

    # 2. Company Institutional Score Polygon
    avg_score = sum(scores) / len(scores) if scores else 50
    poly_color = "#34D399" if avg_score >= 70 else ("#38BDF8" if avg_score >= 50 else "#FB7185")
    fill_rgba = (
        "rgba(52, 211, 153, 0.22)"
        if avg_score >= 70
        else ("rgba(56, 189, 248, 0.22)" if avg_score >= 50 else "rgba(251, 113, 133, 0.22)")
    )

    fig.add_trace(
        go.Scatterpolar(
            r=scores_loop,
            theta=cat_loop,
            fill="toself",
            fillcolor=fill_rgba,
            mode="lines+markers",
            line=dict(color=poly_color, width=2.5),
            marker=dict(color=poly_color, size=7, symbol="diamond"),
            name=f"{ticker} ({avg_score:.0f}/100)",
            text=hover_texts_loop,
            hoverinfo="text",
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                ticktext=["20", "40", "60", "80", "100"],
                tickfont=dict(size=8, color="#64748B"),
                gridcolor="rgba(255, 255, 255, 0.07)",
                linecolor="rgba(255, 255, 255, 0.10)",
                showline=False,
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#CBD5E1", family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"),
                gridcolor="rgba(255, 255, 255, 0.08)",
                linecolor="rgba(255, 255, 255, 0.12)",
                direction="clockwise",
            ),
            bgcolor="rgba(15, 23, 42, 0.65)",
        ),
        margin=dict(l=35, r=35, t=30, b=30),
        height=350,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.16,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#94A3B8"),
        ),
    )

    return fig

