"""
Technical Indicators Library
All indicators are vectorized using pandas/numpy for maximum performance
"""
import pandas as pd
import numpy as np
from typing import Tuple


class Indicators:
    """Collection of technical indicators for trading strategies"""
    
    @staticmethod
    def sma(data: pd.Series, window: int) -> pd.Series:
        """
        Simple Moving Average
        
        Args:
            data: Price series (usually close price)
            window: Number of periods
            
        Returns:
            SMA series
        """
        return data.rolling(window=window).mean()
    
    @staticmethod
    def ema(data: pd.Series, span: int) -> pd.Series:
        """
        Exponential Moving Average
        
        Args:
            data: Price series
            span: Number of periods
            
        Returns:
            EMA series
        """
        return data.ewm(span=span, adjust=False).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index (RSI)
        
        Measures momentum on a scale of 0-100
        RSI > 70: Overbought
        RSI < 30: Oversold
        
        Args:
            data: Price series (usually close price)
            period: RSI period (default 14)
            
        Returns:
            RSI series
        """
        delta = data.diff()
        
        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence (MACD)
        
        Args:
            data: Price series
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line period (default 9)
            
        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        
        Args:
            data: Price series
            window: Moving average period
            num_std: Number of standard deviations
            
        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        middle_band = data.rolling(window=window).mean()
        std = data.rolling(window=window).std()
        
        upper_band = middle_band + (std * num_std)
        lower_band = middle_band - (std * num_std)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Average True Range (ATR)
        Measures volatility
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: ATR period
            
        Returns:
            ATR series
        """
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR as moving average of TR
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            k_period: %K period
            d_period: %D period
            
        Returns:
            Tuple of (%K, %D)
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        # %K line
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        
        # %D line (moving average of %K)
        d = k.rolling(window=d_period).mean()
        
        return k, d
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Volume Weighted Average Price (VWAP)
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            volume: Volume series
            
        Returns:
            VWAP series
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        
        return vwap


# Convenience functions for quick access
def calculate_ma_crossover_signals(data: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    """
    Calculate buy/sell signals for MA Crossover strategy
    
    Returns DataFrame with 'signal' column (1=buy, -1=sell, 0=hold)
    """
    df = data.copy()
    df['sma_short'] = Indicators.sma(df['close'], short_window)
    df['sma_long'] = Indicators.sma(df['close'], long_window)
    
    # Generate signals
    df['signal'] = 0
    df.loc[df['sma_short'] > df['sma_long'], 'signal'] = 1  # Buy signal
    df.loc[df['sma_short'] < df['sma_long'], 'signal'] = -1  # Sell signal
    
    return df


def calculate_rsi_signals(data: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70) -> pd.DataFrame:
    """
    Calculate buy/sell signals for RSI strategy
    
    Returns DataFrame with 'signal' column
    """
    df = data.copy()
    df['rsi'] = Indicators.rsi(df['close'], period)
    
    # Generate signals
    df['signal'] = 0
    df.loc[df['rsi'] < oversold, 'signal'] = 1  # Buy when oversold
    df.loc[df['rsi'] > overbought, 'signal'] = -1  # Sell when overbought
    
    return df


def calculate_macd_signals(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    Calculate buy/sell signals for MACD strategy
    
    Returns DataFrame with 'signal' column
    """
    df = data.copy()
    df['macd'], df['macd_signal'], df['macd_hist'] = Indicators.macd(df['close'], fast, slow, signal)
    
    # Generate signals based on MACD crossover
    df['signal'] = 0
    df.loc[df['macd'] > df['macd_signal'], 'signal'] = 1  # Buy when MACD crosses above signal
    df.loc[df['macd'] < df['macd_signal'], 'signal'] = -1  # Sell when MACD crosses below signal
    
    return df
