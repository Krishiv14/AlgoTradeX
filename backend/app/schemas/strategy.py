"""
Pydantic schemas for Strategy-related API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class StrategyBase(BaseModel):
    """Base schema for strategy"""
    name: str = Field(..., description="Strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    strategy_type: str = Field(..., description="Type: ma_crossover, rsi, macd, custom")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters as JSON")
    risk_params: Optional[Dict[str, Any]] = Field(None, description="Risk management parameters")


class StrategyCreate(StrategyBase):
    """Schema for creating a new strategy"""
    pass


class StrategyUpdate(BaseModel):
    """Schema for updating a strategy"""
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    risk_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class StrategyResponse(StrategyBase):
    """Schema for strategy response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Strategy Templates (pre-configured strategies)
STRATEGY_TEMPLATES = {
    "ma_crossover": {
        "name": "Moving Average Crossover",
        "description": "Buy when short MA crosses above long MA, sell when crosses below",
        "strategy_type": "ma_crossover",
        "parameters": {
            "short_window": 50,
            "long_window": 200
        },
        "risk_params": {
            "stop_loss": 0.05,  # 5% stop loss
            "position_size": 0.1  # 10% of portfolio per trade
        }
    },
    "rsi": {
        "name": "RSI Mean Reversion",
        "description": "Buy when RSI is oversold, sell when overbought",
        "strategy_type": "rsi",
        "parameters": {
            "period": 14,
            "oversold": 30,
            "overbought": 70
        },
        "risk_params": {
            "stop_loss": 0.03,
            "position_size": 0.15
        }
    },
    "macd": {
        "name": "MACD Momentum",
        "description": "Buy on MACD bullish crossover, sell on bearish crossover",
        "strategy_type": "macd",
        "parameters": {
            "fast": 12,
            "slow": 26,
            "signal": 9
        },
        "risk_params": {
            "stop_loss": 0.04,
            "position_size": 0.12
        }
    }
}
