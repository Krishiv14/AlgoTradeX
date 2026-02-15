"""
Backtest model - Stores backtest results and performance metrics
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, TIMESTAMP, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Backtest(Base):
    """Backtest results with performance metrics"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    
    # Backtest period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Capital
    initial_capital = Column(Numeric(15, 2), nullable=False)
    final_capital = Column(Numeric(15, 2), nullable=False)
    
    # Performance Metrics
    total_return = Column(Numeric(8, 4))  # 0.2345 = 23.45%
    sharpe_ratio = Column(Numeric(6, 4))  # Risk-adjusted return
    max_drawdown = Column(Numeric(8, 4))  # Maximum peak-to-trough decline
    
    # Trade Statistics
    win_rate = Column(Numeric(6, 4))  # Percentage of winning trades
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    avg_win = Column(Numeric(12, 2))
    avg_loss = Column(Numeric(12, 2))
    profit_factor = Column(Numeric(8, 4))  # Total wins / Total losses
    
    # Benchmark Comparison (vs Nifty 50)
    benchmark_return = Column(Numeric(8, 4))
    alpha = Column(Numeric(8, 4))  # Excess return vs benchmark
    beta = Column(Numeric(6, 4))  # Volatility vs benchmark
    
    # Execution metadata
    execution_time_ms = Column(Integer)  # Time taken to run backtest
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")
    stock = relationship("Stock", back_populates="backtests")
    trades = relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Backtest(id={self.id}, strategy={self.strategy_id}, return={self.total_return})>"


# Indexes for faster queries
Index('idx_backtests_strategy', Backtest.strategy_id)
Index('idx_backtests_stock', Backtest.stock_id)
