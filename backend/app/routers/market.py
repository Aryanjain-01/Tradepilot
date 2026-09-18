from fastapi import APIRouter, HTTPException
from app.services.market_data import market_data_service

router = APIRouter(
    prefix="/api/market",
    tags=["market"],
)

@router.get("/{symbol}")
def get_latest_market_data(symbol: str):
    data = market_data_service.get_latest(symbol.upper())
    if data is None:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    return {
        "symbol": symbol.upper(),
        "latest": data
    }

@router.get("/{symbol}/history")
def get_historical_market_data(symbol: str):
    data = market_data_service.get_history(symbol.upper())
    if data is None:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    return data
