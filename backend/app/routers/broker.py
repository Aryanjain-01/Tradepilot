import os
from fastapi import APIRouter
from app.brokers.zerodha_sandbox import zerodha_provider

router = APIRouter(
    prefix="/api/broker",
    tags=["broker"],
)

@router.get("/status")
def get_broker_status():
    source = os.getenv("MARKET_DATA_SOURCE", "sample")
    
    if source == "zerodha_sandbox":
        provider_status = zerodha_provider.get_status()
        return {
            "source": "zerodha_sandbox",
            "provider_status": provider_status
        }
    else:
        return {
            "source": "sample",
            "provider_status": {"status": "ok", "message": "Using local sample data"}
        }

@router.get("/zerodha/ltp/{symbol}")
def get_zerodha_ltp(symbol: str):
    return zerodha_provider.get_ltp(symbol)

@router.get("/zerodha/quote/{symbol}")
def get_zerodha_quote(symbol: str):
    return zerodha_provider.get_quote(symbol)

@router.get("/zerodha/ohlc/{symbol}")
def get_zerodha_ohlc(symbol: str):
    return zerodha_provider.get_ohlc(symbol)

@router.get("/zerodha/history/{symbol}")
def get_zerodha_history(symbol: str):
    return zerodha_provider.get_historical_data(symbol)
