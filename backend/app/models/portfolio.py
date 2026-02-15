"""
Portfolio model - Paper trading portfolios
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Portfolio(Base):
    """Paper trading portfolio"""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    
    # Capital tracking
    initial_capital = Column(Numeric(15, 2), nullable=False)
    current_capital = Column(Numeric(15, 2), nullable=False)
    invested_amount = Column(Numeric(15, 2), default=0)
    total_pnl = Column(Numeric(15, 2), default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    strategy = relationship("Strategy", back_populates="portfolios")
    trades = relationship("Trade", back_populates="portfolio")
    positions = relationship("PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("DailyPortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio(name='{self.name}', capital={self.current_capital})>"


class PortfolioPosition(Base):
    """Current holdings in a portfolio"""
    __tablename__ = "portfolio_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    avg_buy_price = Column(Numeric(12, 2), nullable=False)
    current_price = Column(Numeric(12, 2))
    unrealized_pnl = Column(Numeric(12, 2))
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    stock = relationship("Stock")
    
    def __repr__(self):
        return f"<Position(stock={self.stock_id}, qty={self.quantity}, pnl={self.unrealized_pnl})>"


class DailyPortfolioSnapshot(Base):
    """Daily snapshot of portfolio value for performance tracking"""
    __tablename__ = "daily_portfolio_snapshots"
    
    time = Column(TIMESTAMP(timezone=True), nullable=False, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, primary_key=True)
    
    total_value = Column(Numeric(15, 2), nullable=False)
    cash = Column(Numeric(15, 2), nullable=False)
    invested = Column(Numeric(15, 2), nullable=False)
    day_pnl = Column(Numeric(12, 2))
    total_pnl = Column(Numeric(12, 2))
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")
    
    def __repr__(self):
        return f"<Snapshot(portfolio={self.portfolio_id}, value={self.total_value})>"
