"""
Stock model - represents NSE/BSE stocks
"""
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, TIMESTAMP, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Stock(Base):
    """Stock master table for NSE/BSE stocks"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "RELIANCE.NS"
    name = Column(String(200))  # e.g., "Reliance Industries Ltd"
    sector = Column(String(100))  # e.g., "Oil & Gas"
    market_cap = Column(BigInteger)  # Market capitalization in crores
    is_nifty50 = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    ohlcv_data = relationship("OHLCVData", back_populates="stock", cascade="all, delete-orphan")
    backtests = relationship("Backtest", back_populates="stock")
    trades = relationship("Trade", back_populates="stock")
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"


# Create index for Nifty 50 stocks
Index('idx_stocks_nifty50', Stock.is_nifty50)
