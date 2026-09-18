# TradePilot

## Overview

TradePilot is a sophisticated algorithmic trading and paper-trading platform. It processes historical and real-time market data, calculates advanced technical indicators, and autonomously generates `BUY`/`SELL`/`HOLD` signals based on a rule-driven strategy. 

The system applies strict risk management and dynamic position sizing before routing signals to a simulated execution engine (Paper Trading). Users can track their portfolio, monitor open positions, view realized and unrealized P&L in real-time, and run completely isolated historical backtests to validate strategy performance against historical OHLCV data.

## Features

- **Market Data**: Local CSV sample ingestion and Zerodha Kite Connect Sandbox API integration.
- **Technical Indicators**: Pandas-driven SMA, EMA, RSI (14), and MACD.
- **Rule-based Strategy**: Extensible logic evaluating indicators to generate absolute `BUY`/`SELL`/`HOLD` signals.
- **Risk Management**: Dynamic position sizing based on account equity, Risk %, Stop Loss, and Target parameters. Calculates Risk/Reward before execution.
- **Paper Trading Engine**: A fully isolated simulation engine that manages order lifecycles and fills simulated orders instantly.
- **Portfolio Management**: Real-time tracking of Active Orders, Open Positions, and Trade History with Realized/Unrealized P&L (INR ₹).
- **Historical Backtesting**: A zero-lookahead-bias engine that simulates the live strategy against historical data, calculating Final Equity, Win Rate, Profit Factor, and Maximum Drawdown.
- **Trading Dashboard**: A unified, responsive React frontend (Dark Mode) replacing fragmented tabs with a single-pane-of-glass terminal view. Includes a dedicated Backtesting configuration and visualization panel.

## Architecture

**Live/Paper Trading Pipeline:**
```text
Market Data ↓
Indicators ↓
Strategy ↓
Risk Management ↓
Trade Validation ↓
Paper Execution ↓
Orders / Trades / Positions ↓
P&L
```

**Backtesting Pipeline:**
```text
Historical Data ↓
Backtesting Engine ↓
Strategy (Re-used) ↓
Simulated Chronological Trades ↓
Performance Metrics & Equity Curve
```

## Technology Stack

- **Frontend**: React, TypeScript, Vite, TailwindCSS, Recharts, Lucide Icons.
- **Backend**: Python 3, FastAPI, Pandas, NumPy, SQLAlchemy.
- **Database**: SQLite (Local file-based database).

## Project Structure

```text
TradePilot/
├── backend/                  # Python FastAPI application
│   ├── app/
│   │   ├── routers/          # API endpoints (market, trading, backtest, paper, risk)
│   │   ├── schemas/          # Pydantic validation models
│   │   ├── services/         # Core business logic (strategy, risk, indicators, backtester)
│   │   └── models/           # SQLAlchemy ORM models
│   ├── data/                 # Historical OHLCV sample CSVs
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/       # UI Components (TradingDashboard, Backtesting)
│   │   └── App.tsx           # Main application entry point
│   ├── package.json          # Node dependencies
│   └── vite.config.ts        # Vite configuration
└── README.md
```

## Running Locally

### 1. Backend Setup

Open a terminal and navigate to the backend directory:
```bash
cd backend
```

Create and activate a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Start the FastAPI development server:
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

### 2. Frontend Setup

Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

Start the Vite development server:
```bash
npm run dev
```
The application will be available at `http://localhost:5173`.

## Environment Variables

To configure broker integrations (like Zerodha Sandbox), create a `.env` file in the `backend/` directory based on the provided `.env.example`:

```env
MARKET_DATA_SOURCE=sample
ZERODHA_API_KEY=
ZERODHA_API_SECRET=
ZERODHA_ACCESS_TOKEN=
```
*Note: Do not commit your real `.env` file containing actual credentials.*

## Backtesting

TradePilot includes a rigorous historical backtesting engine. 
- **Sequential Processing**: It iterates through historical OHLCV candles chronologically. 
- **Zero Look-Ahead Bias**: The engine utilizes Pandas `rolling()` functions strictly up to candle `i`, feeding the existing `StrategyService` without peeking into the future.
- **Execution Assumption**: A signal generated at the close of candle `i` executes at the open of candle `i+1`.
- **Conservative Stops**: If a candle breaches both the Stop Loss and the Target simultaneously, the engine pessimistically assumes the Stop Loss was hit first.
- **Metrics**: Outputs Final Equity, Total Return %, Win Rate %, Profit Factor, and Maximum Drawdown alongside an interactive Equity Curve.

## Paper Trading Disclaimer

> **IMPORTANT**: TradePilot's execution engine is strictly a **paper-trading simulation**. It does not place real-money orders, nor does it connect to any live brokerage accounts for execution. The Zerodha integration is used exclusively for fetching market data, not for routing real capital.

## Future Improvements

- Additional algorithmic strategies.
- WebSocket streaming for tick-by-tick real-time data.
- Additional broker market-data integrations.
- Cloud deployment and containerization.
