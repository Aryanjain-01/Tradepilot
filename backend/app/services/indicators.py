import pandas as pd
import numpy as np
from typing import List, Dict, Any
from app.services.market_data import market_data_service

class IndicatorService:
    def get_indicators(self, symbol: str) -> List[Dict[str, Any]]:
        # Get raw data from the market data service
        raw_data = market_data_service.get_history(symbol)
        if not raw_data:
            return None
        
        # Convert to pandas DataFrame for calculations
        df = pd.DataFrame(raw_data)
        
        # We need the 'close' column to compute these indicators
        if 'close' not in df.columns:
            return None
            
        # 1. SMA 20
        df['sma_20'] = df['close'].rolling(window=20, min_periods=20).mean()
        
        # 2. SMA 50
        df['sma_50'] = df['close'].rolling(window=50, min_periods=50).mean()
        
        # 3. EMA 20
        df['ema_20'] = df['close'].ewm(span=20, adjust=False, min_periods=20).mean()
        
        # 4. RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # 5. MACD (12, 26, 9)
        ema_12 = df['close'].ewm(span=12, adjust=False, min_periods=12).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False, min_periods=26).mean()
        df['macd_line'] = ema_12 - ema_26
        df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False, min_periods=9).mean()
        df['macd_histogram'] = df['macd_line'] - df['macd_signal']
        
        # Replace NaN with None for JSON serialization
        df = df.replace({np.nan: None})
        
        return df.to_dict(orient='records')

indicator_service = IndicatorService()
