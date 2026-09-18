from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class OrderRequest(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(..., gt=0)
    order_type: Literal["LIMIT", "MARKET"]
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None

class OrderResponse(BaseModel):
    order_id: str
    symbol: str
    side: str
    quantity: int
    requested_price: float
    filled_price: Optional[float]
    status: str
    
    class Config:
        from_attributes = True

class PositionResponse(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: int
    entry_price: float
    current_price: float
    stop_loss: Optional[float]
    target: Optional[float]
    unrealized_pnl: float
    status: str
    opened_at: datetime
    
    class Config:
        from_attributes = True

class AccountResponse(BaseModel):
    initial_capital: float
    available_cash: float
    used_capital: float
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    equity: float

    class Config:
        from_attributes = True

class MarketPriceUpdate(BaseModel):
    symbol: str
    price: float = Field(..., gt=0)

class TradeResponse(BaseModel):
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: int
    entry_price: float
    exit_price: float
    realized_pnl: float
    opened_at: datetime
    closed_at: datetime
    
    class Config:
        from_attributes = True
