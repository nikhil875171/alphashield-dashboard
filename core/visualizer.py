import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.schemas import AlphaShieldRecommendation, TechnicalSnapshot


def build_interactive_chart(
    df: pd.DataFrame,
    tech: TechnicalSnapshot,
    rec: AlphaShieldRecommendation
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

    # 1. Candlestick Trace
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
            increasing_line_color="#00E676",  # Bright Green
            decreasing_line_color="#FF1744",  # Neon Red
        ),
        row=1,
        col=1
    )

    # 2. Moving Average Overlays
    if "EMA_20" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["EMA_20"], mode="lines", name="20 EMA", line=dict(color="#29B6F6", width=1.5)),
            row=1, col=1
        )
    if "EMA_50" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["EMA_50"], mode="lines", name="50 EMA", line=dict(color="#FFA726", width=1.5)),
            row=1, col=1
        )
    if "EMA_200" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["EMA_200"], mode="lines", name="200 EMA", line=dict(color="#AB47BC", width=2.0)),
            row=1, col=1
        )
    if "VWAP" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["VWAP"], mode="lines", name="VWAP", line=dict(color="#B0BEC5", width=1.0, dash="dot")),
            row=1, col=1
        )

    # 3. Horizontal Trade Level Annotations
    # Hard Stop Loss
    fig.add_hline(
        y=rec.hard_stop_loss,
        line_dash="dash",
        line_color="#FF1744",
        line_width=2,
        annotation_text=f"Hard Stop: ₹{rec.hard_stop_loss}",
        annotation_position="bottom right",
        annotation_font_color="#FF1744",
        row=1, col=1
    )

    # Entry Range (Midpoint or upper/lower)
    entry_low, entry_high = rec.recommended_entry_range
    fig.add_hrect(
        y0=entry_low,
        y1=entry_high,
        fillcolor="rgba(33, 150, 243, 0.15)",
        line_width=1,
        line_dash="dot",
        line_color="#2196F3",
        annotation_text=f"Entry Zone (₹{entry_low} - ₹{entry_high})",
        annotation_position="top left",
        row=1, col=1
    )

    # Target Price Ladder
    target_colors = ["#69F0AE", "#00E676", "#00C853"]
    for idx, target in enumerate(rec.target_price_ladder[:3]):
        color = target_colors[idx % len(target_colors)]
        fig.add_hline(
            y=target,
            line_dash="dashdot",
            line_color=color,
            line_width=1.5,
            annotation_text=f"Target {idx + 1}: ₹{target}",
            annotation_position="top right",
            annotation_font_color=color,
            row=1, col=1
        )

    # 4. Volume Bar Subplot
    vol_colors = ["#00E676" if c >= o else "#FF1744" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=vol_colors,
            opacity=0.75
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
                line=dict(color="#FFD54F", width=1.5)
            ),
            row=2,
            col=1
        )

    # 5. RSI Subplot
    if "RSI_14" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["RSI_14"],
                mode="lines",
                name="RSI (14)",
                line=dict(color="#E040FB", width=1.5)
            ),
            row=3,
            col=1
        )
        # 70 Overbought line
        fig.add_hline(y=70, line_dash="dash", line_color="#FF5252", line_width=1, row=3, col=1)
        # 30 Oversold line
        fig.add_hline(y=30, line_dash="dash", line_color="#69F0AE", line_width=1, row=3, col=1)

    # Dark Institutional Theme Styling
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0E1117",
        plot_bgcolor="#131722",
        font=dict(family="Consolas, monospace, sans-serif", color="#E0E0E0", size=11),
        xaxis_rangeslider_visible=False,
        height=750,
        margin=dict(l=40, r=60, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )

    # Update axes styling
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.06)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.06)")
    fig.update_yaxes(title_text="Price (₹/$)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[10, 90], row=3, col=1)

    return fig

