"""
Pydantic schemas for Stock-related API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StockBase(BaseModel):
    """Base schema for stock data"""
    symbol: str = Field(..., description="Stock symbol with exchange suffix (e.g., RELIANCE.NS)")
    name: Optional[str] = Field(None, description="Company name")
    sector: Optional[str] = Field(None, description="Industry sector")
    market_cap: Optional[int] = Field(None, description="Market capitalization")
    is_nifty50: bool = Field(False, description="Is this stock part of Nifty 50?")


class StockCreate(StockBase):
    """Schema for creating a new stock"""
    pass


class StockUpdate(BaseModel):
    """Schema for updating stock information"""
    name: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[int] = None
    is_nifty50: Optional[bool] = None
    is_active: Optional[bool] = None


class StockResponse(StockBase):
    """Schema for stock response"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # Allows reading from ORM models


class OHLCVResponse(BaseModel):
    """Schema for OHLCV data response"""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    
    class Config:
        from_attributes = True


class StockWithOHLCV(StockResponse):
    """Stock response with OHLCV data"""
    ohlcv_data: list[OHLCVResponse] = []
