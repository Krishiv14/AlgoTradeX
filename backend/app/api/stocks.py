"""
Stocks API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Stock, OHLCVData
from app.schemas.stock import StockResponse, StockCreate, OHLCVResponse
from app.services.data_fetcher import DataFetcher

router = APIRouter()


@router.get("/", response_model=List[StockResponse])
def list_stocks(
    skip: int = 0,
    limit: int = 100,
    nifty50_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all stocks
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **nifty50_only**: Filter for Nifty 50 stocks only
    """
    query = db.query(Stock)
    
    if nifty50_only:
        query = query.filter(Stock.is_nifty50 == True)
    
    stocks = query.offset(skip).limit(limit).all()
    return stocks


@router.get("/nifty50", response_model=List[StockResponse])
def get_nifty50_stocks(db: Session = Depends(get_db)):
    """Get all Nifty 50 stocks"""
    stocks = db.query(Stock).filter(Stock.is_nifty50 == True).all()
    return stocks


@router.get("/{symbol}", response_model=StockResponse)
def get_stock(symbol: str, db: Session = Depends(get_db)):
    """Get stock details by symbol"""
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    return stock


@router.get("/{symbol}/ohlcv", response_model=List[OHLCVResponse])
def get_stock_ohlcv(
    symbol: str,
    start_date: datetime = Query(default=None),
    end_date: datetime = Query(default=None),
    limit: int = Query(default=500, le=5000),
    db: Session = Depends(get_db)
):
    """
    Get OHLCV data for a stock
    
    - **symbol**: Stock symbol (e.g., RELIANCE.NS)
    - **start_date**: Start date (optional)
    - **end_date**: End date (optional)
    - **limit**: Maximum records to return
    """
    # Get stock
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Build query
    query = db.query(OHLCVData).filter(OHLCVData.stock_id == stock.id)
    
    if start_date:
        query = query.filter(OHLCVData.time >= start_date)
    
    if end_date:
        query = query.filter(OHLCVData.time <= end_date)
    
    # Order by time descending and limit
    ohlcv_data = query.order_by(OHLCVData.time.desc()).limit(limit).all()
    
    # Reverse to get chronological order
    return list(reversed(ohlcv_data))


@router.post("/fetch-historical")
def fetch_historical_data(
    symbol: str = Query(..., description="Stock symbol to fetch"),
    years: int = Query(default=5, description="Number of years of data to fetch"),
    db: Session = Depends(get_db)
):
    """
    Fetch and store historical data for a stock
    
    - **symbol**: Stock symbol (e.g., RELIANCE.NS)
    - **years**: Number of years to fetch (default: 5)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    fetcher = DataFetcher(db)
    
    success = fetcher.fetch_and_store(symbol, start_date, end_date)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data for {symbol}")
    
    return {
        "message": f"Successfully fetched {years} years of data for {symbol}",
        "symbol": symbol,
        "start_date": start_date.date(),
        "end_date": end_date.date()
    }


@router.post("/sync-nifty50")
def sync_nifty50_data(
    years: int = Query(default=5, description="Number of years to fetch"),
    db: Session = Depends(get_db)
):
    """
    Fetch historical data for all Nifty 50 stocks
    
    ⚠️ This will take 5-10 minutes depending on API speed
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    fetcher = DataFetcher(db)
    fetcher.fetch_nifty50_data(start_date, end_date)
    
    return {
        "message": "Nifty 50 data sync completed",
        "start_date": start_date.date(),
        "end_date": end_date.date()
    }


@router.get("/data/stats")
def get_data_stats(db: Session = Depends(get_db)):
    """Get statistics about available data"""
    total_stocks = db.query(Stock).count()
    nifty50_stocks = db.query(Stock).filter(Stock.is_nifty50 == True).count()
    total_records = db.query(OHLCVData).count()
    
    # Get date range
    oldest = db.query(OHLCVData).order_by(OHLCVData.time).first()
    latest = db.query(OHLCVData).order_by(OHLCVData.time.desc()).first()
    
    return {
        "total_stocks": total_stocks,
        "nifty50_stocks": nifty50_stocks,
        "total_ohlcv_records": total_records,
        "date_range": {
            "oldest": oldest.time if oldest else None,
            "latest": latest.time if latest else None
        }
    }
