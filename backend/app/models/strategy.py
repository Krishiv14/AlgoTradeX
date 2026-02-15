"""
Strategy model - Trading strategy configurations
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Strategy(Base):
    """Trading strategy configuration"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False)  # 'ma_crossover', 'rsi', 'macd', 'custom'
    
    # Strategy parameters stored as JSON
    # Example for MA Crossover: {"short_window": 50, "long_window": 200}
    # Example for RSI: {"period": 14, "oversold": 30, "overbought": 70}
    # Example for MACD: {"fast": 12, "slow": 26, "signal": 9}
    parameters = Column(JSON, nullable=False)
    
    # Risk management parameters
    # Example: {"stop_loss": 0.05, "position_size": 0.1, "max_drawdown": 0.2}
    risk_params = Column(JSON)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    backtests = relationship("Backtest", back_populates="strategy")
    portfolios = relationship("Portfolio", back_populates="strategy")
    
    def __repr__(self):
        return f"<Strategy(name='{self.name}', type='{self.strategy_type}')>"
