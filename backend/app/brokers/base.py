from abc import ABC, abstractmethod
from typing import Dict, Any, List

class MarketDataProvider(ABC):
    @abstractmethod
    def get_ltp(self, symbol: str) -> Dict[str, Any]:
        """Get Latest Traded Price"""
        pass

    @abstractmethod
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get full quote data"""
        pass

    @abstractmethod
    def get_ohlc(self, symbol: str) -> Dict[str, Any]:
        """Get Open High Low Close data"""
        pass

    @abstractmethod
    def get_historical_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Get historical OHLCV data"""
        pass
