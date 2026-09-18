from fastapi import APIRouter, HTTPException
from app.services.strategy import strategy_service

router = APIRouter(
    prefix="/api/strategy",
    tags=["strategy"],
)

@router.get("/{symbol}")
def get_strategy_signal(symbol: str):
    data = strategy_service.evaluate(symbol.upper())
    if data is None:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    return data
