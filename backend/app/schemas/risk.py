from pydantic import BaseModel, Field
from typing import Literal

class RiskRequest(BaseModel):
    capital: float = Field(..., gt=0, description="Total capital available")
    risk_percentage: float = Field(..., gt=0, description="Risk percentage (e.g. 1.0 for 1%)")
    entry_price: float = Field(..., gt=0, description="Entry price of the trade")
    stop_loss: float = Field(..., gt=0, description="Stop loss price")
    target: float = Field(..., gt=0, description="Target price")
    direction: Literal["LONG", "SHORT"] = Field(..., description="Trade direction")

class RiskResponse(BaseModel):
    maximum_risk: float
    risk_per_share: float
    position_size: int
    potential_loss: float
    potential_profit: float
    risk_reward_ratio: str
