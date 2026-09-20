# 🛡️ AlphaShield Dashboard

Institutional-grade Market Intelligence, Multi-Factor Alpha, and Capital Preservation web application built with **Streamlit**, **Plotly**, and **Google Gemini AI**.

---

## Features

- **Macroeconomic & Geopolitical Regime**: Ingests real-time 10Y-2Y yield curve spreads, VIX / India VIX, Dollar Index (DXY), Crude Oil, Gold, and financial RSS headlines.
- **Fundamental Health & Solvency Sieve**: Programmatic calculation of **Altman Z-Score** (bankruptcy risk) and **Piotroski F-Score** (0-9 solvency audit).
- **Technical Momentum & Microstructure**: EMA 20/50/200, RSI(14), MACD(12, 26, 9), VWAP, and ATR(14) volatility.
- **Crowdsourced Sentiment & Retail Euphoria Check**: Contrarian caution flag if sentiment is euphoric while technical indicators reflect extreme overbought conditions.
- **Smart Money Tracking**: Institutional ownership %, insider/promoter holdings, and short float interest.
- **Zero-Ruin Risk Management**:
  - Dynamic ATR stop-loss (1.5x - 2.0x ATR)
  - Fixed fractional position sizing (1.0% - 2.0% risk cap per trade)
  - Asymmetric R:R validation (minimum 1:2.5 required)
  - Automatic Volatility Kill-Switch
- **Gemini AI Decision Engine**: Powered by Google GenAI with strict Pydantic schemas.

---

## Local Setup

1. **Clone repository & enter directory**:
   ```bash
   git clone https://github.com/<your-username>/<your-repo-name>.git
   cd <your-repo-name>
   ```

2. **Create and activate virtual environment**:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure API Key**:
   Create a `.env` file from `.env.example`:
   ```env
   GEMINI_API_KEY="your_api_key_here"
   ```

5. **Launch Application**:
   ```powershell
   streamlit run app.py
   ```

---

## Deployment on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/) with your GitHub account.
3. Select your repository, branch `main`, and main file `app.py`.
4. Under **Advanced Settings** -> **Secrets**, paste:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key"
   ```
5. Click **Deploy!**

