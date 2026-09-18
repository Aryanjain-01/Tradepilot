import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_random_walk_data(symbol, start_price, days=365):
    dates = pd.date_range(end=datetime.today(), periods=days, freq='D')
    
    # Generate random walk for close price
    returns = np.random.normal(0, 0.02, days)
    price_path = start_price * np.exp(np.cumsum(returns))
    
    # Generate O, H, L relative to C
    open_prices = price_path * np.random.uniform(0.99, 1.01, days)
    high_prices = np.maximum(open_prices, price_path) * np.random.uniform(1.0, 1.02, days)
    low_prices = np.minimum(open_prices, price_path) * np.random.uniform(0.98, 1.0, days)
    volumes = np.random.randint(100000, 5000000, size=days)
    
    df = pd.DataFrame({
        'timestamp': dates.strftime('%Y-%m-%d'),
        'open': np.round(open_prices, 2),
        'high': np.round(high_prices, 2),
        'low': np.round(low_prices, 2),
        'close': np.round(price_path, 2),
        'volume': volumes
    })
    return df

if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    os.makedirs(DATA_DIR, exist_ok=True)
    
    symbols = {
        'NIFTY': 25000,
        'RELIANCE': 3000,
        'TCS': 4200,
        'INFY': 1900
    }
    
    for symbol, start_price in symbols.items():
        df = generate_random_walk_data(symbol, start_price, 500)
        filepath = os.path.join(DATA_DIR, f"{symbol}.csv")
        df.to_csv(filepath, index=False)
        print(f"Generated {filepath} with {len(df)} rows.")
