import os
import pandas as pd
from typing import Dict, Any, List

class MarketDataService:
    def __init__(self):
        self.data: Dict[str, pd.DataFrame] = {}
        self.load_data()

    def load_data(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        data_dir = os.path.join(base_dir, 'data')
        
        if not os.path.exists(data_dir):
            print(f"Data directory {data_dir} not found.")
            return

        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                symbol = filename.replace('.csv', '')
                filepath = os.path.join(data_dir, filename)
                try:
                    df = pd.read_csv(filepath)
                    # Validate required columns
                    required_columns = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
                    if required_columns.issubset(df.columns):
                        self.data[symbol] = df
                    else:
                        print(f"File {filename} missing required columns.")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    def get_latest(self, symbol: str) -> Dict[str, Any]:
        if symbol not in self.data:
            return None
        
        df = self.data[symbol]
        latest_record = df.iloc[-1].to_dict()
        return latest_record

    def get_history(self, symbol: str) -> List[Dict[str, Any]]:
        if symbol not in self.data:
            return None
        
        df = self.data[symbol]
        return df.to_dict(orient='records')

market_data_service = MarketDataService()
