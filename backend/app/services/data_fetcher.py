"""
Data Fetcher Service - Downloads historical NSE data using yfinance
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
import time

from app.models import Stock, OHLCVData
from app.config import settings


# Nifty 50 stocks (as of 2024)
NIFTY50_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "BAJFINANCE.NS", "NESTLEIND.NS", "HCLTECH.NS", "WIPRO.NS",
    "ULTRACEMCO.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "M&M.NS",
    "TATAMOTORS.NS", "TATASTEEL.NS", "ADANIPORTS.NS", "JSWSTEEL.NS", "INDUSINDBK.NS",
    "HINDALCO.NS", "COALINDIA.NS", "DRREDDY.NS", "BAJAJFINSV.NS", "GRASIM.NS",
    "CIPLA.NS", "TECHM.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "DIVISLAB.NS",
    "BRITANNIA.NS", "TATACONSUM.NS", "APOLLOHOSP.NS", "SBILIFE.NS", "HDFCLIFE.NS",
    "BPCL.NS", "ADANIENT.NS", "LTIM.NS", "BAJAJ-AUTO.NS", "SHRIRAMFIN.NS"
]


class DataFetcher:
    """Fetch and store historical stock data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def fetch_stock_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from yfinance
        
        Args:
            symbol: Stock symbol (e.g., RELIANCE.NS)
            start_date: Start date
            end_date: End date
            interval: Data interval (1d, 1h, etc.)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                print(f"⚠️ No data found for {symbol}")
                return pd.DataFrame()
            
            # Rename columns to lowercase
            data.columns = [col.lower() for col in data.columns]
            
            # Reset index to get time as column
            data = data.reset_index()
            data = data.rename(columns={'date': 'time'})
            
            return data[['time', 'open', 'high', 'low', 'close', 'volume']]
        
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def store_stock_data(self, symbol: str, data: pd.DataFrame) -> bool:
        """
        Store OHLCV data in database
        
        Args:
            symbol: Stock symbol
            data: DataFrame with OHLCV data
            
        Returns:
            True if successful
        """
        try:
            # Get or create stock
            stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
            
            if not stock:
                # Create new stock entry
                stock = Stock(
                    symbol=symbol,
                    is_nifty50=symbol in NIFTY50_STOCKS,
                    is_active=True
                )
                self.db.add(stock)
                self.db.commit()
                self.db.refresh(stock)
            
            # Delete existing data for this period to avoid duplicates
            self.db.query(OHLCVData).filter(
                OHLCVData.stock_id == stock.id,
                OHLCVData.time >= data['time'].min(),
                OHLCVData.time <= data['time'].max()
            ).delete()
            
            # Insert new data
            for _, row in data.iterrows():
                ohlcv = OHLCVData(
                    time=row['time'],
                    stock_id=stock.id,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']),
                    adjusted_close=float(row['close'])  # yfinance already adjusts
                )
                self.db.add(ohlcv)
            
            self.db.commit()
            print(f"✅ Stored {len(data)} records for {symbol}")
            return True
        
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error storing data for {symbol}: {str(e)}")
            return False
    
    def fetch_and_store(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> bool:
        """
        Fetch and store data in one step
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            True if successful
        """
        data = self.fetch_stock_data(symbol, start_date, end_date)
        
        if data.empty:
            return False
        
        return self.store_stock_data(symbol, data)
    
    def fetch_nifty50_data(
        self,
        start_date: datetime,
        end_date: datetime,
        delay: float = 1.0
    ) -> None:
        """
        Fetch data for all Nifty 50 stocks
        
        Args:
            start_date: Start date
            end_date: End date
            delay: Delay between API calls (seconds)
        """
        print(f"📥 Fetching Nifty 50 data from {start_date.date()} to {end_date.date()}")
        print(f"Total stocks: {len(NIFTY50_STOCKS)}")
        
        success_count = 0
        failed_stocks = []
        
        for i, symbol in enumerate(NIFTY50_STOCKS, 1):
            print(f"\n[{i}/{len(NIFTY50_STOCKS)}] Fetching {symbol}...")
            
            if self.fetch_and_store(symbol, start_date, end_date):
                success_count += 1
            else:
                failed_stocks.append(symbol)
            
            # Rate limiting
            if i < len(NIFTY50_STOCKS):
                time.sleep(delay)
        
        print(f"\n{'='*50}")
        print(f"✅ Successfully fetched: {success_count}/{len(NIFTY50_STOCKS)} stocks")
        
        if failed_stocks:
            print(f"❌ Failed stocks: {', '.join(failed_stocks)}")
    
    def update_stock_info(self, symbol: str) -> None:
        """
        Update stock metadata (name, sector, market cap)
        
        Args:
            symbol: Stock symbol
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
            
            if stock:
                stock.name = info.get('longName') or info.get('shortName')
                stock.sector = info.get('sector')
                stock.market_cap = info.get('marketCap')
                
                self.db.commit()
                print(f"✅ Updated info for {symbol}")
        
        except Exception as e:
            print(f"❌ Error updating info for {symbol}: {str(e)}")
    
    def get_latest_date(self, symbol: str) -> Optional[datetime]:
        """
        Get latest available date for a stock
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest date or None
        """
        stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
        
        if not stock:
            return None
        
        latest = self.db.query(OHLCVData).filter(
            OHLCVData.stock_id == stock.id
        ).order_by(OHLCVData.time.desc()).first()
        
        return latest.time if latest else None
    
    def sync_latest_data(self, symbol: str) -> bool:
        """
        Sync latest data (from last available date to today)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if successful
        """
        latest_date = self.get_latest_date(symbol)
        
        if not latest_date:
            # No data exists, fetch last 5 years
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)
        else:
            # Fetch from day after latest date
            start_date = latest_date + timedelta(days=1)
            end_date = datetime.now()
        
        if start_date >= end_date:
            print(f"✅ {symbol} is already up to date")
            return True
        
        print(f"🔄 Syncing {symbol} from {start_date.date()} to {end_date.date()}")
        return self.fetch_and_store(symbol, start_date, end_date)
