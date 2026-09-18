from fastapi import APIRouter, HTTPException
from app.services.indicators import indicator_service

router = APIRouter(
    prefix="/api/indicators",
    tags=["indicators"],
)

@router.get("/{symbol}")
def get_historical_indicators(symbol: str):
    data = indicator_service.get_indicators(symbol.upper())
    if data is None:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    return data
