from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class PipelineRequest(BaseModel):
    symbol: str
    risk_percentage: Optional[float] = Field(1.0, gt=0, description="Risk percentage (e.g. 1.0 for 1%)")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss absolute price")
    target: Optional[float] = Field(None, gt=0, description="Target absolute price")

class PipelineResponse(BaseModel):
    symbol: str
    status: str # "FILLED", "NO_TRADE", "REJECTED"
    current_price: Optional[float] = None
    signal: Optional[str] = None # "BUY", "SELL", "HOLD"
    strategy_reason: Optional[str] = None
    reason: Optional[str] = None
    risk: Optional[Dict[str, Any]] = None
    execution: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, Any]] = None
