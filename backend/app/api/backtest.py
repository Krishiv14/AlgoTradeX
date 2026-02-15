"""
Backtest API Endpoints
This is the CORE API - runs backtests and returns results
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models import Backtest, Trade, Strategy, Stock
from app.schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    BacktestWithTrades,
    TradeResponse,
    BacktestMetrics
)
from app.services.backtest_engine import BacktestEngine

router = APIRouter()


@router.post("/run", response_model=dict)
def run_backtest(request: BacktestRequest, db: Session = Depends(get_db)):
    """
    Run a backtest with the specified strategy and parameters
    
    This is the MAIN endpoint that recruiters will care about!
    
    - **strategy_id**: ID of the strategy to test
    - **stock_symbol**: Stock to backtest (e.g., RELIANCE.NS)
    - **start_date**: Backtest start date
    - **end_date**: Backtest end date
    - **initial_capital**: Starting capital (default: ₹1,00,000)
    
    Returns:
        Complete backtest results with metrics, trades, and equity curve
    """
    try:
        engine = BacktestEngine(db)
        
        result = engine.run_backtest(
            strategy_id=request.strategy_id,
            stock_symbol=request.stock_symbol,
            start_date=datetime.combine(request.start_date, datetime.min.time()),
            end_date=datetime.combine(request.end_date, datetime.min.time()),
            initial_capital=request.initial_capital
        )
        
        # Get strategy and stock names for response
        strategy = db.query(Strategy).filter(Strategy.id == request.strategy_id).first()
        stock = db.query(Stock).filter(Stock.symbol == request.stock_symbol).first()
        
        return {
            "backtest_id": result['backtest_id'],
            "strategy_name": strategy.name,
            "stock_symbol": request.stock_symbol,
            "stock_name": stock.name if stock else None,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "initial_capital": request.initial_capital,
            "final_capital": result['metrics']['final_value'],
            "metrics": result['metrics'],
            "total_trades": len(result['trades']),
            "execution_time_ms": result['execution_time_ms'],
            "message": f"✅ Backtest completed in {result['execution_time_ms']}ms"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.get("/{backtest_id}", response_model=dict)
def get_backtest(backtest_id: int, db: Session = Depends(get_db)):
    """Get backtest results by ID"""
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    
    if not backtest:
        raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
    
    # Get related data
    strategy = db.query(Strategy).filter(Strategy.id == backtest.strategy_id).first()
    stock = db.query(Stock).filter(Stock.id == backtest.stock_id).first()
    
    return {
        "backtest_id": backtest.id,
        "strategy_name": strategy.name if strategy else "Unknown",
        "stock_symbol": stock.symbol if stock else "Unknown",
        "stock_name": stock.name if stock else "Unknown",
        "start_date": backtest.start_date,
        "end_date": backtest.end_date,
        "initial_capital": float(backtest.initial_capital),
        "final_capital": float(backtest.final_capital),
        "metrics": {
            "total_return": float(backtest.total_return),
            "sharpe_ratio": float(backtest.sharpe_ratio),
            "max_drawdown": float(backtest.max_drawdown),
            "win_rate": float(backtest.win_rate),
            "total_trades": backtest.total_trades,
            "winning_trades": backtest.winning_trades,
            "losing_trades": backtest.losing_trades,
            "avg_win": float(backtest.avg_win),
            "avg_loss": float(backtest.avg_loss),
            "profit_factor": float(backtest.profit_factor),
            "benchmark_return": float(backtest.benchmark_return),
            "alpha": float(backtest.alpha)
        },
        "execution_time_ms": backtest.execution_time_ms,
        "created_at": backtest.created_at
    }


@router.get("/{backtest_id}/trades", response_model=List[TradeResponse])
def get_backtest_trades(backtest_id: int, db: Session = Depends(get_db)):
    """Get all trades from a backtest"""
    # Verify backtest exists
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    
    if not backtest:
        raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
    
    # Get trades
    trades = db.query(Trade).filter(Trade.backtest_id == backtest_id).all()
    
    return trades


@router.get("/", response_model=List[dict])
def list_backtests(
    skip: int = 0,
    limit: int = 50,
    strategy_id: int = Query(default=None),
    stock_symbol: str = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    List all backtests with optional filtering
    
    - **strategy_id**: Filter by strategy
    - **stock_symbol**: Filter by stock
    """
    query = db.query(Backtest)
    
    if strategy_id:
        query = query.filter(Backtest.strategy_id == strategy_id)
    
    if stock_symbol:
        stock = db.query(Stock).filter(Stock.symbol == stock_symbol).first()
        if stock:
            query = query.filter(Backtest.stock_id == stock.id)
    
    backtests = query.order_by(Backtest.created_at.desc()).offset(skip).limit(limit).all()
    
    # Format response
    results = []
    for bt in backtests:
        strategy = db.query(Strategy).filter(Strategy.id == bt.strategy_id).first()
        stock = db.query(Stock).filter(Stock.id == bt.stock_id).first()
        
        results.append({
            "backtest_id": bt.id,
            "strategy_name": strategy.name if strategy else "Unknown",
            "stock_symbol": stock.symbol if stock else "Unknown",
            "start_date": bt.start_date,
            "end_date": bt.end_date,
            "total_return": float(bt.total_return) * 100,  # Convert to percentage
            "sharpe_ratio": float(bt.sharpe_ratio),
            "max_drawdown": float(bt.max_drawdown) * 100,  # Convert to percentage
            "total_trades": bt.total_trades,
            "created_at": bt.created_at
        })
    
    return results


@router.get("/compare/multiple")
def compare_backtests(
    backtest_ids: str = Query(..., description="Comma-separated backtest IDs (e.g., '1,2,3')"),
    db: Session = Depends(get_db)
):
    """
    Compare multiple backtests side-by-side
    
    - **backtest_ids**: Comma-separated list of backtest IDs
    
    Example: /api/v1/backtest/compare/multiple?backtest_ids=1,2,3
    """
    ids = [int(id.strip()) for id in backtest_ids.split(",")]
    
    backtests = db.query(Backtest).filter(Backtest.id.in_(ids)).all()
    
    if not backtests:
        raise HTTPException(status_code=404, detail="No backtests found with provided IDs")
    
    # Format comparison data
    comparison = []
    
    for bt in backtests:
        strategy = db.query(Strategy).filter(Strategy.id == bt.strategy_id).first()
        stock = db.query(Stock).filter(Stock.id == bt.stock_id).first()
        
        comparison.append({
            "backtest_id": bt.id,
            "strategy": strategy.name if strategy else "Unknown",
            "stock": stock.symbol if stock else "Unknown",
            "total_return": float(bt.total_return) * 100,
            "sharpe_ratio": float(bt.sharpe_ratio),
            "max_drawdown": float(bt.max_drawdown) * 100,
            "win_rate": float(bt.win_rate) * 100,
            "total_trades": bt.total_trades,
            "alpha": float(bt.alpha) * 100
        })
    
    # Find best performers
    best_return = max(comparison, key=lambda x: x['total_return'])
    best_sharpe = max(comparison, key=lambda x: x['sharpe_ratio'])
    best_drawdown = min(comparison, key=lambda x: x['max_drawdown'])
    
    return {
        "backtests": comparison,
        "best_by_return": best_return['backtest_id'],
        "best_by_sharpe": best_sharpe['backtest_id'],
        "best_by_drawdown": best_drawdown['backtest_id']
    }


@router.delete("/{backtest_id}")
def delete_backtest(backtest_id: int, db: Session = Depends(get_db)):
    """Delete a backtest and all its trades"""
    backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    
    if not backtest:
        raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")
    
    # Delete trades first (due to foreign key)
    db.query(Trade).filter(Trade.backtest_id == backtest_id).delete()
    
    # Delete backtest
    db.delete(backtest)
    db.commit()
    
    return {"message": f"Backtest {backtest_id} and all trades deleted successfully"}
