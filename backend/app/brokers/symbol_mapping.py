# Maps frontend symbols to Zerodha Exchange:TradingSymbol formats
SYMBOL_MAP = {
    "NIFTY": "NSE:NIFTY 50",
    "RELIANCE": "NSE:RELIANCE",
    "TCS": "NSE:TCS",
    "INFY": "NSE:INFY"
}

def get_zerodha_symbol(symbol: str) -> str:
    """Returns the Kite formatted symbol, or raises ValueError if unsupported."""
    if symbol not in SYMBOL_MAP:
        raise ValueError(f"Symbol {symbol} not supported for Zerodha Sandbox integration.")
    return SYMBOL_MAP[symbol]
