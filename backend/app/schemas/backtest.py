"""
Pydantic schemas for Backtest-related API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class BacktestRequest(BaseModel):
    """Schema for backtest request"""
    strategy_id: int = Field(..., description="Strategy ID to backtest")
    stock_symbol: str = Field(..., description="Stock symbol (e.g., RELIANCE.NS)")
    start_date: date = Field(..., description="Backtest start date")
    end_date: date = Field(..., description="Backtest end date")
    initial_capital: float = Field(100000.0, description="Initial capital in rupees")


class BacktestMetrics(BaseModel):
    """Performance metrics from backtest"""
    total_return: float = Field(..., description="Total return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio (risk-adjusted return)")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    win_rate: float = Field(..., description="Percentage of winning trades")
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    avg_win: float = Field(..., description="Average win amount")
    avg_loss: float = Field(..., description="Average loss amount")
    profit_factor: float = Field(..., description="Profit factor (total wins / total losses)")
    benchmark_return: float = Field(..., description="Benchmark (Nifty 50) return")
    alpha: float = Field(..., description="Excess return vs benchmark")
    beta: float = Field(..., description="Beta (volatility vs benchmark)")


class TradeResponse(BaseModel):
    """Individual trade from backtest"""
    id: int
    trade_type: str
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime]
    exit_price: Optional[float]
    quantity: int
    pnl: Optional[float]
    pnl_percentage: Optional[float]
    hold_period_days: Optional[int]
    exit_reason: Optional[str]
    
    class Config:
        from_attributes = True


class EquityCurvePoint(BaseModel):
    """Single point in equity curve"""
    date: datetime
    portfolio_value: float
    benchmark_value: float
    drawdown: float


class BacktestResponse(BaseModel):
    """Complete backtest response"""
    backtest_id: int
    strategy_name: str
    stock_symbol: str
    start_date: date
    end_date: date
    initial_capital: float
    final_capital: float
    metrics: BacktestMetrics
    execution_time_ms: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class BacktestWithTrades(BacktestResponse):
    """Backtest response with trade history"""
    trades: List[TradeResponse] = []


class BacktestWithEquityCurve(BacktestResponse):
    """Backtest response with equity curve data"""
    equity_curve: List[EquityCurvePoint] = []


class BacktestComparison(BaseModel):
    """Comparison of multiple backtests"""
    backtests: List[BacktestResponse]
    best_by_return: int  # Backtest ID
    best_by_sharpe: int  # Backtest ID
    best_by_drawdown: int  # Backtest ID
