import math
from fastapi import HTTPException
from app.schemas.risk import RiskRequest, RiskResponse

class RiskManagerService:
    def calculate(self, req: RiskRequest) -> RiskResponse:
        # Validate logic
        if req.direction == "LONG":
            if not (req.stop_loss < req.entry_price < req.target):
                raise HTTPException(status_code=400, detail="Invalid LONG setup: Must have Stop Loss < Entry Price < Target")
        else: # SHORT
            if not (req.target < req.entry_price < req.stop_loss):
                raise HTTPException(status_code=400, detail="Invalid SHORT setup: Must have Target < Entry Price < Stop Loss")

        max_risk = req.capital * (req.risk_percentage / 100.0)
        risk_per_share = abs(req.entry_price - req.stop_loss)
        
        if risk_per_share == 0:
            raise HTTPException(status_code=400, detail="Risk per share cannot be zero (Entry equals Stop Loss)")
            
        position_size = math.floor(max_risk / risk_per_share)
        
        potential_loss = position_size * risk_per_share
        potential_profit = position_size * abs(req.target - req.entry_price)
        
        # Risk Reward Ratio
        # Reward / Risk
        reward_per_share = abs(req.target - req.entry_price)
        rr_ratio_val = reward_per_share / risk_per_share
        # Format as 1:X, where X is rounded to 2 decimal places if needed, but normally just rounded to standard
        # However, to handle e.g. 1:3 cleanly:
        rr_ratio = f"1:{round(rr_ratio_val, 2)}"
        
        # If position_size is 0, we can still output 0 for profit/loss but math works out automatically
        
        return RiskResponse(
            maximum_risk=round(max_risk, 2),
            risk_per_share=round(risk_per_share, 2),
            position_size=position_size,
            potential_loss=round(potential_loss, 2),
            potential_profit=round(potential_profit, 2),
            risk_reward_ratio=rr_ratio
        )

risk_manager_service = RiskManagerService()
