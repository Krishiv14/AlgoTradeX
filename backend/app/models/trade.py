"""
Trade model - Individual buy/sell trades from backtests or paper trading
"""
from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Trade(Base):
    """Individual trade record"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    
    # Trade details
    trade_type = Column(String(10), nullable=False)  # 'BUY' or 'SELL'
    entry_date = Column(TIMESTAMP(timezone=True), nullable=False)
    entry_price = Column(Numeric(12, 2), nullable=False)
    exit_date = Column(TIMESTAMP(timezone=True))
    exit_price = Column(Numeric(12, 2))
    quantity = Column(Integer, nullable=False)
    
    # Costs and P&L
    transaction_cost = Column(Numeric(12, 2))  # Brokerage + taxes
    pnl = Column(Numeric(12, 2))  # Profit/Loss in rupees
    pnl_percentage = Column(Numeric(8, 4))  # P&L as percentage
    
    # Trade metadata
    hold_period_days = Column(Integer)  # How long position was held
    exit_reason = Column(String(50))  # 'signal', 'stop_loss', 'target', 'manual'
    created_at = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    backtest = relationship("Backtest", back_populates="trades")
    portfolio = relationship("Portfolio", back_populates="trades")
    stock = relationship("Stock", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(type={self.trade_type}, stock={self.stock_id}, pnl={self.pnl})>"


# Indexes for faster queries
Index('idx_trades_backtest', Trade.backtest_id)
Index('idx_trades_portfolio', Trade.portfolio_id)
Index('idx_trades_stock_entry', Trade.stock_id, Trade.entry_date)
