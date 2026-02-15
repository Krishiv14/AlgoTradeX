"""Generate sample OHLCV data for demonstration"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Stock, OHLCVData

def generate_stock_data(symbol, name, start_price=100, days=1250):
    """Generate realistic stock price data"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Random walk with trend
    returns = np.random.randn(days) * 0.02 + 0.0003  # Daily volatility + slight upward trend
    prices = start_price * (1 + returns).cumprod()
    
    data = []
    for i, date in enumerate(dates):
        price = prices[i]
        volatility = price * 0.02
        
        high = price + abs(np.random.randn() * volatility)
        low = price - abs(np.random.randn() * volatility)
        open_price = price + np.random.randn() * volatility * 0.5
        close = price
        volume = int(np.random.uniform(1000000, 5000000))
        
        data.append({
            'time': date,
            'open': round(float(open_price), 2),
            'high': round(float(high), 2),
            'low': round(float(low), 2),
            'close': round(float(close), 2),
            'volume': volume
        })
    
    return pd.DataFrame(data)

# Sample stocks with realistic starting prices
stocks_data = [
    ("RELIANCE.NS", "Reliance Industries", 2400),
    ("TCS.NS", "Tata Consultancy Services", 3500),
    ("HDFCBANK.NS", "HDFC Bank", 1600),
    ("INFY.NS", "Infosys", 1400),
    ("ICICIBANK.NS", "ICICI Bank", 900),
]

print("🚀 Generating sample data for demonstration...")
print(f"Creating data for {len(stocks_data)} stocks")

db = SessionLocal()

for symbol, name, start_price in stocks_data:
    print(f"\n📊 Creating {symbol} ({name})...")
    
    # Create stock if doesn't exist
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        stock = Stock(
            symbol=symbol,
            name=name,
            is_nifty50=True,
            is_active=True
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)
    
    # Delete existing data
    db.query(OHLCVData).filter(OHLCVData.stock_id == stock.id).delete()
    db.commit()
    
    # Generate and insert data
    df = generate_stock_data(symbol, name, start_price)
    
    for _, row in df.iterrows():
        ohlcv = OHLCVData(
            time=row['time'],
            stock_id=stock.id,
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume'],
            adjusted_close=row['close']
        )
        db.add(ohlcv)
    
    db.commit()
    print(f"✅ Created {len(df)} records for {symbol}")

db.close()

print("\n" + "="*60)
print("✅ Sample data created successfully!")
print(f"Total stocks: {len(stocks_data)}")
print(f"Records per stock: 1,250")
print(f"Total records: {len(stocks_data) * 1250:,}")
print("="*60)
