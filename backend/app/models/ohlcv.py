"""
OHLCV Data model - Time-series stock price data
This will be converted to TimescaleDB hypertable for efficient time-series queries
"""
from sqlalchemy import Column, Integer, String, Numeric, BigInteger, TIMESTAMP, ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class OHLCVData(Base):
    """OHLCV (Open, High, Low, Close, Volume) time-series data"""
    __tablename__ = "ohlcv_data"
    
    time = Column(TIMESTAMP(timezone=True), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    open = Column(Numeric(12, 2), nullable=False)
    high = Column(Numeric(12, 2), nullable=False)
    low = Column(Numeric(12, 2), nullable=False)
    close = Column(Numeric(12, 2), nullable=False)
    volume = Column(BigInteger, nullable=False)
    adjusted_close = Column(Numeric(12, 2))  # Adjusted for splits/dividends
    
    # Composite primary key (time + stock_id)
    __table_args__ = (
        PrimaryKeyConstraint('time', 'stock_id'),
        Index('idx_ohlcv_stock_time', 'stock_id', 'time'),
        Index('idx_ohlcv_time', 'time'),
    )
    
    # Relationships
    stock = relationship("Stock", back_populates="ohlcv_data")
    
    def __repr__(self):
        return f"<OHLCVData(stock_id={self.stock_id}, time={self.time}, close={self.close})>"


# Note: After creating this table, run this SQL to convert to TimescaleDB hypertable:
# SELECT create_hypertable('ohlcv_data', 'time');
# 
# Enable compression for older data:
# ALTER TABLE ohlcv_data SET (timescaledb.compress, timescaledb.compress_segmentby = 'stock_id');
# SELECT add_compression_policy('ohlcv_data', INTERVAL '7 days');
