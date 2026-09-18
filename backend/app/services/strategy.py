from typing import Dict, Any
from app.services.indicators import indicator_service

class StrategyService:
    def evaluate(self, symbol: str, indicator_data: dict = None) -> Dict[str, Any]:
        if indicator_data:
            latest = indicator_data
        else:
            data = indicator_service.get_indicators(symbol)
            if not data or len(data) == 0:
                return None
            latest = data[-1]
        
        # Extract indicators with fallbacks
        sma_20 = latest.get('sma_20')
        sma_50 = latest.get('sma_50')
        rsi_14 = latest.get('rsi_14')
        macd_line = latest.get('macd_line')
        macd_signal = latest.get('macd_signal')
        
        # Check if we have enough data to calculate
        if None in (sma_20, sma_50, rsi_14, macd_line, macd_signal):
            return {
                "symbol": symbol,
                "signal": "HOLD",
                "conditions": {
                    "sma": False,
                    "rsi": False,
                    "macd": False
                },
                "indicators": latest
            }

        # BUY CONDITIONS
        # SMA20 > SMA50 AND RSI14 > 50 AND MACD > Signal
        buy_sma = sma_20 > sma_50
        buy_rsi = rsi_14 > 50
        buy_macd = macd_line > macd_signal
        
        # SELL CONDITIONS
        # SMA20 < SMA50 AND RSI14 < 50 AND MACD < Signal
        sell_sma = sma_20 < sma_50
        sell_rsi = rsi_14 < 50
        sell_macd = macd_line < macd_signal

        signal = "HOLD"
        
        if buy_sma and buy_rsi and buy_macd:
            signal = "BUY"
            conditions = { "sma": True, "rsi": True, "macd": True }
        elif sell_sma and sell_rsi and sell_macd:
            signal = "SELL"
            conditions = { "sma": True, "rsi": True, "macd": True }
        else:
            signal = "HOLD"
            # Return current condition states relative to the closest signal
            # For transparency, we show what is true and what is false for a buy signal if SMA is bullish,
            # or for a sell signal if SMA is bearish.
            conditions = {
                "sma": buy_sma if buy_sma else sell_sma,
                "rsi": buy_rsi if buy_sma else sell_rsi,
                "macd": buy_macd if buy_sma else sell_macd
            }
            
        return {
            "symbol": symbol,
            "signal": signal,
            "conditions": conditions,
            "indicators": latest
        }

strategy_service = StrategyService()
