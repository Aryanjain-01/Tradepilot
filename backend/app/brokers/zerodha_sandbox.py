import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from fastapi import HTTPException
from kiteconnect import KiteConnect

from app.brokers.base import MarketDataProvider
from app.brokers.symbol_mapping import get_zerodha_symbol

# Load env variables safely
load_dotenv()

class ZerodhaSandboxProvider(MarketDataProvider):
    def __init__(self):
        self.api_key = os.getenv("ZERODHA_API_KEY")
        self.api_secret = os.getenv("ZERODHA_API_SECRET")
        self.access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
        
        if not self.api_key or not self.access_token:
            # We don't fail on init, we fail when endpoints are accessed if misconfigured
            self.kite = None
        else:
            # Initialize with sandbox root URL
            self.kite = KiteConnect(api_key=self.api_key)
            self.kite.set_access_token(self.access_token)
            # KiteConnect supports overriding the root API URL for sandbox environments
            # Default is https://api.kite.trade, we overwrite for sandbox
            self.kite.root = "https://sandbox.kite.trade"
            self.kite.login_url = "https://sandbox.kite.trade/connect/login"
            self.kite.session_expiry_hook = None

    def _ensure_initialized(self):
        if not self.kite:
            raise HTTPException(
                status_code=503, 
                detail="Zerodha credentials missing or invalid. Please check your .env configuration."
            )

    def _safe_execute(self, func, *args, **kwargs):
        self._ensure_initialized()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Mask API secrets and exact stack traces from reaching frontend
            # We log internally, but raise a safe HTTP exception
            print(f"Zerodha API Error: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail=f"Error communicating with Zerodha Sandbox. Ensure your Access Token is valid and Sandbox is online."
            )

    def get_status(self) -> Dict[str, Any]:
        """Simple health check for the broker"""
        if not self.kite:
            return {"status": "error", "message": "Credentials missing"}
        
        # Optionally test profile fetch if needed, but a simple OK is fine for now
        return {"status": "ok", "message": "Zerodha Sandbox configured"}

    def get_ltp(self, symbol: str) -> Dict[str, Any]:
        kite_symbol = get_zerodha_symbol(symbol.upper())
        # dict mapping instrument to ltp
        res = self._safe_execute(self.kite.ltp, [kite_symbol])
        
        if kite_symbol not in res:
            raise HTTPException(status_code=404, detail="LTP data not found for symbol")
            
        return {
            "symbol": symbol.upper(),
            "ltp": res[kite_symbol]["last_price"]
        }

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        kite_symbol = get_zerodha_symbol(symbol.upper())
        res = self._safe_execute(self.kite.quote, [kite_symbol])
        
        if kite_symbol not in res:
            raise HTTPException(status_code=404, detail="Quote data not found for symbol")
            
        return res[kite_symbol]

    def get_ohlc(self, symbol: str) -> Dict[str, Any]:
        kite_symbol = get_zerodha_symbol(symbol.upper())
        res = self._safe_execute(self.kite.ohlc, [kite_symbol])
        
        if kite_symbol not in res:
            raise HTTPException(status_code=404, detail="OHLC data not found for symbol")
            
        return res[kite_symbol]

    def get_historical_data(self, symbol: str) -> List[Dict[str, Any]]:
        # In this sandbox version without DB sync, we just mock the historical call structure
        # A real historical call requires instrument_token resolution and date ranges.
        # Since this is Step 6A (Data integration) and the user wants to avoid breaking the app,
        # we can throw 501 or return a mock list. Let's return a safe failure if hit directly.
        raise HTTPException(
            status_code=501, 
            detail="Historical data pull from Sandbox not implemented in Step 6A. Use Sample Data."
        )

zerodha_provider = ZerodhaSandboxProvider()
