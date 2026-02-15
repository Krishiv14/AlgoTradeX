"""
Backtesting Engine - Runs historical backtests with full performance metrics
This is the CORE of the platform - optimized for speed with vectorized operations
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
import time

from app.models import Stock, OHLCVData, Strategy, Backtest, Trade
from app.services.strategy_engine import StrategyEngine
from app.config import settings


class BacktestEngine:
    """
    High-performance backtesting engine
    Uses vectorized operations for speed
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.transaction_cost = settings.TRANSACTION_COST_PERCENT / 100  # Convert to decimal
    
    def run_backtest(
        self,
        strategy_id: int,
        stock_symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0
    ) -> Dict[str, Any]:
        """
        Run complete backtest
        
        Args:
            strategy_id: Strategy to test
            stock_symbol: Stock symbol (e.g., RELIANCE.NS)
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            
        Returns:
            Dictionary with backtest results and metrics
        """
        start_time = time.time()
        
        # 1. Load strategy
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        # 2. Load stock
        stock = self.db.query(Stock).filter(Stock.symbol == stock_symbol).first()
        if not stock:
            raise ValueError(f"Stock {stock_symbol} not found")
        
        # 3. Load OHLCV data
        ohlcv_query = self.db.query(OHLCVData).filter(
            OHLCVData.stock_id == stock.id,
            OHLCVData.time >= start_date,
            OHLCVData.time <= end_date
        ).order_by(OHLCVData.time)
        
        # Convert to pandas DataFrame
        data = pd.read_sql(ohlcv_query.statement, self.db.bind)
        
        if data.empty:
            raise ValueError(f"No data found for {stock_symbol} between {start_date} and {end_date}")
        
        # 4. Generate strategy signals
        strategy_engine = StrategyEngine(strategy.strategy_type, strategy.parameters)
        signals_df = strategy_engine.generate_signals(data)
        
        # 5. Run backtest simulation
        portfolio_df, trades_list = self._simulate_trading(
            signals_df, 
            initial_capital, 
            strategy.risk_params or {}
        )
        
        # 6. Calculate performance metrics
        metrics = self._calculate_metrics(portfolio_df, data, initial_capital)
        
        # 6b. Add trade statistics
        trade_stats = self._calculate_trade_stats(trades_list)
        metrics.update(trade_stats)
        
        # 7. Calculate benchmark (Nifty 50) return
        benchmark_return = self._calculate_benchmark_return(start_date, end_date)
        metrics['benchmark_return'] = benchmark_return
        metrics['alpha'] = metrics['total_return'] - benchmark_return
        
        # 8. Save backtest results to database
        execution_time = int((time.time() - start_time) * 1000)  # milliseconds
        
        backtest = Backtest(
            strategy_id=strategy_id,
            stock_id=stock.id,
            start_date=start_date.date(),
            end_date=end_date.date(),
            initial_capital=initial_capital,
            final_capital=portfolio_df['total'].iloc[-1],
            total_return=metrics['total_return'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            total_trades=metrics['total_trades'],
            winning_trades=metrics['winning_trades'],
            losing_trades=metrics['losing_trades'],
            avg_win=metrics['avg_win'],
            avg_loss=metrics['avg_loss'],
            profit_factor=metrics['profit_factor'],
            benchmark_return=benchmark_return,
            alpha=metrics['alpha'],
            beta=metrics.get('beta', 1.0),
            execution_time_ms=execution_time
        )
        
        self.db.add(backtest)
        self.db.commit()
        self.db.refresh(backtest)
        
        # 9. Save trades
        for trade_data in trades_list:
            trade = Trade(
                backtest_id=backtest.id,
                stock_id=stock.id,
                **trade_data
            )
            self.db.add(trade)
        
        self.db.commit()
        
        return {
            'backtest_id': backtest.id,
            'metrics': metrics,
            'trades': trades_list,
            'equity_curve': portfolio_df[['time', 'total', 'drawdown']].to_dict('records'),
            'execution_time_ms': execution_time
        }
    
    def _simulate_trading(
        self, 
        signals_df: pd.DataFrame, 
        initial_capital: float,
        risk_params: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Simulate actual trading with transaction costs and risk management
        
        Args:
            signals_df: DataFrame with signals
            initial_capital: Starting capital
            risk_params: Risk management parameters
            
        Returns:
            Tuple of (portfolio_df, trades_list)
        """
        df = signals_df.copy()
        
        # Risk parameters
        position_size = risk_params.get('position_size', 0.95)  # Use 95% of capital
        stop_loss = risk_params.get('stop_loss', 0.0)  # Stop loss percentage
        
        # Initialize tracking
        cash = initial_capital
        shares = 0
        current_position = None  # Track open position
        trades = []
        
        # Portfolio value tracking
        portfolio_values = []
        
        for idx, row in df.iterrows():
            signal = row.get('signal', 0)
            current_price = row['close']
            current_time = row['time']
            
            # Check stop loss if we have an open position
            if current_position and stop_loss > 0:
                entry_price = current_position['entry_price']
                loss_pct = (entry_price - current_price) / entry_price
                
                if loss_pct >= stop_loss:
                    # Stop loss triggered - sell immediately
                    signal = -1
            
            # Process signals
            if signal == 1 and shares == 0:  # Buy signal and no position
                # Calculate shares to buy
                capital_to_use = cash * position_size
                cost_per_share = current_price * (1 + self.transaction_cost)
                shares_to_buy = int(capital_to_use / cost_per_share)
                
                if shares_to_buy > 0:
                    total_cost = shares_to_buy * cost_per_share
                    cash -= total_cost
                    shares = shares_to_buy
                    
                    # Record position
                    current_position = {
                        'entry_date': current_time,
                        'entry_price': current_price,
                        'quantity': shares,
                        'transaction_cost': total_cost - (shares_to_buy * current_price)
                    }
            
            elif signal == -1 and shares > 0:  # Sell signal and have position
                # Sell all shares
                proceeds_per_share = current_price * (1 - self.transaction_cost)
                total_proceeds = shares * proceeds_per_share
                transaction_cost = (shares * current_price) - total_proceeds
                
                # Calculate P&L
                entry_value = current_position['quantity'] * current_position['entry_price']
                exit_value = shares * current_price
                total_costs = current_position['transaction_cost'] + transaction_cost
                pnl = (exit_value - entry_value) - total_costs
                pnl_pct = pnl / entry_value
                
                # Calculate hold period
                hold_period = (current_time - current_position['entry_date']).days
                
                # Record trade
                trades.append({
                    'trade_type': 'BUY',  # Entry was a buy
                    'entry_date': current_position['entry_date'],
                    'entry_price': current_position['entry_price'],
                    'exit_date': current_time,
                    'exit_price': current_price,
                    'quantity': shares,
                    'transaction_cost': total_costs,
                    'pnl': float(pnl),
                    'pnl_percentage': float(pnl_pct),
                    'hold_period_days': hold_period,
                    'exit_reason': 'stop_loss' if stop_loss > 0 and (current_position['entry_price'] - current_price) / current_position['entry_price'] >= stop_loss else 'signal'
                })
                
                # Update cash
                cash += total_proceeds
                shares = 0
                current_position = None
            
            # Record portfolio value
            portfolio_value = cash + (shares * current_price)
            portfolio_values.append({
                'time': current_time,
                'cash': cash,
                'holdings': shares * current_price,
                'total': portfolio_value
            })
        
        # Close any open position at end
        if shares > 0:
            final_price = df['close'].iloc[-1]
            final_time = df['time'].iloc[-1]
            proceeds = shares * final_price * (1 - self.transaction_cost)
            
            entry_value = current_position['quantity'] * current_position['entry_price']
            exit_value = shares * final_price
            pnl = (exit_value - entry_value) - current_position['transaction_cost']
            
            trades.append({
                'trade_type': 'BUY',
                'entry_date': current_position['entry_date'],
                'entry_price': current_position['entry_price'],
                'exit_date': final_time,
                'exit_price': final_price,
                'quantity': shares,
                'transaction_cost': current_position['transaction_cost'],
                'pnl': float(pnl),
                'pnl_percentage': float(pnl / entry_value),
                'hold_period_days': (final_time - current_position['entry_date']).days,
                'exit_reason': 'end_of_period'
            })
            
            cash += proceeds
        
        # Convert portfolio values to DataFrame
        portfolio_df = pd.DataFrame(portfolio_values)
        
        # Calculate drawdown
        portfolio_df['cummax'] = portfolio_df['total'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['total'] - portfolio_df['cummax']) / portfolio_df['cummax']
        
        return portfolio_df, trades
    
    def _calculate_metrics(
        self, 
        portfolio_df: pd.DataFrame, 
        price_data: pd.DataFrame,
        initial_capital: float
    ) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics
        """
        final_value = portfolio_df['total'].iloc[-1]
        total_return = (final_value - initial_capital) / initial_capital
        
        # Calculate daily returns
        portfolio_df['returns'] = portfolio_df['total'].pct_change()
        
        # Sharpe Ratio (annualized)
        mean_return = portfolio_df['returns'].mean()
        std_return = portfolio_df['returns'].std()
        sharpe_ratio = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        
        # Maximum Drawdown
        max_drawdown = abs(portfolio_df['drawdown'].min())
        
        return {
            'total_return': float(total_return),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'final_value': float(final_value),
            'win_rate': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0
        }
    
    def _calculate_benchmark_return(self, start_date: datetime, end_date: datetime) -> float:
        """
        Calculate Nifty 50 benchmark return for the same period
        For now, returns a placeholder - in production, load actual Nifty 50 data
        """
        # TODO: Load actual Nifty 50 data
        # For now, return estimated market return
        days = (end_date - start_date).days
        years = days / 365.25
        annual_return = 0.12  # Assume 12% annual return for Nifty 50
        
        return annual_return * years
    
    @staticmethod
    def _calculate_trade_stats(trades: List[Dict]) -> Dict[str, Any]:
        """Calculate trade-level statistics"""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }
        
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]
        
        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades) if trades else 0,
            'avg_win': total_wins / len(winning_trades) if winning_trades else 0,
            'avg_loss': total_losses / len(losing_trades) if losing_trades else 0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else 0
        }
