"""
Strategy Engine - Implements trading strategies and generates buy/sell signals
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

from app.utils.indicators import (
    Indicators,
    calculate_ma_crossover_signals,
    calculate_rsi_signals,
    calculate_macd_signals
)


class StrategyEngine:
    """
    Trading strategy implementation engine
    Generates buy/sell signals based on strategy type and parameters
    """
    
    def __init__(self, strategy_type: str, parameters: Dict[str, Any]):
        """
        Initialize strategy engine
        
        Args:
            strategy_type: Type of strategy ('ma_crossover', 'rsi', 'macd', 'custom')
            parameters: Strategy parameters
        """
        self.strategy_type = strategy_type
        self.parameters = parameters
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals for the given data
        
        Args:
            data: DataFrame with OHLCV data (columns: time, open, high, low, close, volume)
            
        Returns:
            DataFrame with added 'signal' column (1=buy, -1=sell, 0=hold)
        """
        if self.strategy_type == 'ma_crossover':
            return self._ma_crossover_strategy(data)
        elif self.strategy_type == 'rsi':
            return self._rsi_strategy(data)
        elif self.strategy_type == 'macd':
            return self._macd_strategy(data)
        elif self.strategy_type == 'combined':
            return self._combined_strategy(data)
        else:
            raise ValueError(f"Unknown strategy type: {self.strategy_type}")
    
    def _ma_crossover_strategy(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Moving Average Crossover Strategy
        
        Buy when short MA crosses above long MA
        Sell when short MA crosses below long MA
        
        Parameters:
            - short_window: Short MA period (default: 50)
            - long_window: Long MA period (default: 200)
        """
        short_window = self.parameters.get('short_window', 50)
        long_window = self.parameters.get('long_window', 200)
        
        df = data.copy()
        
        # Calculate moving averages
        df['sma_short'] = Indicators.sma(df['close'], short_window)
        df['sma_long'] = Indicators.sma(df['close'], long_window)
        
        # Generate raw signals
        df['position'] = 0
        df.loc[df['sma_short'] > df['sma_long'], 'position'] = 1  # Long position
        
        # Generate buy/sell signals on crossover (difference in position)
        df['signal'] = df['position'].diff()
        
        return df
    
    def _rsi_strategy(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        RSI Mean Reversion Strategy
        
        Buy when RSI crosses below oversold threshold
        Sell when RSI crosses above overbought threshold
        
        Parameters:
            - period: RSI period (default: 14)
            - oversold: Oversold threshold (default: 30)
            - overbought: Overbought threshold (default: 70)
        """
        period = self.parameters.get('period', 14)
        oversold = self.parameters.get('oversold', 30)
        overbought = self.parameters.get('overbought', 70)
        
        df = data.copy()
        
        # Calculate RSI
        df['rsi'] = Indicators.rsi(df['close'], period)
        
        # Generate signals
        df['position'] = 0
        df.loc[df['rsi'] < oversold, 'position'] = 1  # Long when oversold
        df.loc[df['rsi'] > overbought, 'position'] = 0  # Exit when overbought
        
        # Signal on position change
        df['signal'] = df['position'].diff()
        
        return df
    
    def _macd_strategy(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        MACD Momentum Strategy
        
        Buy when MACD line crosses above signal line
        Sell when MACD line crosses below signal line
        
        Parameters:
            - fast: Fast EMA period (default: 12)
            - slow: Slow EMA period (default: 26)
            - signal: Signal line period (default: 9)
        """
        fast = self.parameters.get('fast', 12)
        slow = self.parameters.get('slow', 26)
        signal_period = self.parameters.get('signal', 9)
        
        df = data.copy()
        
        # Calculate MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = Indicators.macd(
            df['close'], fast, slow, signal_period
        )
        
        # Generate signals
        df['position'] = 0
        df.loc[df['macd'] > df['macd_signal'], 'position'] = 1  # Long when MACD > Signal
        
        # Signal on crossover
        df['signal'] = df['position'].diff()
        
        return df
    
    def _combined_strategy(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Combined Strategy - Uses multiple indicators
        
        Buy when:
        - MA crossover is bullish AND
        - RSI is not overbought AND
        - MACD is positive
        
        Sell when any condition reverses
        
        Parameters: Combines all parameters from individual strategies
        """
        df = data.copy()
        
        # Calculate all indicators
        short_window = self.parameters.get('short_window', 50)
        long_window = self.parameters.get('long_window', 200)
        rsi_period = self.parameters.get('rsi_period', 14)
        rsi_overbought = self.parameters.get('rsi_overbought', 70)
        
        df['sma_short'] = Indicators.sma(df['close'], short_window)
        df['sma_long'] = Indicators.sma(df['close'], long_window)
        df['rsi'] = Indicators.rsi(df['close'], rsi_period)
        df['macd'], df['macd_signal'], _ = Indicators.macd(df['close'])
        
        # Combined condition
        df['ma_bullish'] = df['sma_short'] > df['sma_long']
        df['rsi_ok'] = df['rsi'] < rsi_overbought
        df['macd_bullish'] = df['macd'] > df['macd_signal']
        
        # All conditions must be true
        df['position'] = 0
        df.loc[df['ma_bullish'] & df['rsi_ok'] & df['macd_bullish'], 'position'] = 1
        
        # Generate signals
        df['signal'] = df['position'].diff()
        
        return df
    
    @staticmethod
    def backtest_strategy(
        data: pd.DataFrame,
        signals: pd.DataFrame,
        initial_capital: float = 100000.0,
        transaction_cost: float = 0.0005  # 0.05%
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Backtest a strategy with given signals
        
        Args:
            data: Original OHLCV data
            signals: DataFrame with 'signal' column
            initial_capital: Starting capital
            transaction_cost: Transaction cost as percentage (0.0005 = 0.05%)
            
        Returns:
            Tuple of (portfolio_data, metrics)
        """
        df = signals.copy()
        
        # Initialize portfolio
        df['position'] = df['signal'].fillna(0).cumsum()  # Current position (0 or 1)
        df['holdings'] = df['position'] * df['close']  # Value of holdings
        
        # Calculate cash and total portfolio value
        df['cash'] = initial_capital
        df['total'] = initial_capital
        
        cash = initial_capital
        shares = 0
        
        for i in range(len(df)):
            if df['signal'].iloc[i] == 1:  # Buy signal
                # Buy as many shares as possible
                cost_per_share = df['close'].iloc[i] * (1 + transaction_cost)
                shares_to_buy = int(cash / cost_per_share)
                
                if shares_to_buy > 0:
                    cost = shares_to_buy * cost_per_share
                    cash -= cost
                    shares += shares_to_buy
            
            elif df['signal'].iloc[i] == -1 and shares > 0:  # Sell signal
                # Sell all shares
                proceeds_per_share = df['close'].iloc[i] * (1 - transaction_cost)
                proceeds = shares * proceeds_per_share
                cash += proceeds
                shares = 0
            
            # Update portfolio values
            df.loc[df.index[i], 'cash'] = cash
            df.loc[df.index[i], 'holdings'] = shares * df['close'].iloc[i]
            df.loc[df.index[i], 'total'] = cash + (shares * df['close'].iloc[i])
        
        # Calculate metrics
        final_value = df['total'].iloc[-1]
        total_return = (final_value - initial_capital) / initial_capital
        
        # Calculate daily returns for Sharpe ratio
        df['returns'] = df['total'].pct_change()
        sharpe_ratio = (df['returns'].mean() / df['returns'].std()) * np.sqrt(252) if df['returns'].std() > 0 else 0
        
        # Calculate maximum drawdown
        df['cummax'] = df['total'].cummax()
        df['drawdown'] = (df['total'] - df['cummax']) / df['cummax']
        max_drawdown = df['drawdown'].min()
        
        metrics = {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': abs(max_drawdown),
            'final_value': final_value
        }
        
        return df, metrics
