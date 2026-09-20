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

