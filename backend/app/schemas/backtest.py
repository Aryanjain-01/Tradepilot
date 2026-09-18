from pydantic import BaseModel
from typing import List, Optional

class BacktestRequest(BaseModel):
    symbol: str
    initial_capital: float = 100000.0
    risk_percentage: float = 1.0
    stop_loss_percentage: float = 2.0
    target_percentage: float = 4.0

class BacktestTrade(BaseModel):
    trade_id: str
    symbol: str
    side: str
    quantity: int
    entry_timestamp: str
    entry_price: float
    exit_timestamp: str
    exit_price: float
    stop_loss: float
    target: float
    exit_reason: str
    gross_pnl: float
    net_pnl: float
    return_percentage: float
    strategy_reason: str

class EquityPoint(BaseModel):
    timestamp: str
    equity: float

class BacktestResponse(BaseModel):
    symbol: str
    initial_capital: float
    final_equity: float
    total_pnl: float
    return_percentage: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    trades: List[BacktestTrade]
    equity_curve: List[EquityPoint]
