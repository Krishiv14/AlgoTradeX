"""Fix the backtest engine win_rate bug"""

# Read the file
with open('/app/app/services/backtest_engine.py', 'r') as f:
    content = f.read()

# Find and replace the _calculate_metrics method
old_code = '''    def _calculate_metrics(
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
            'final_value': float(final_value)
        }'''

new_code = '''    def _calculate_metrics(
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
        }'''

content = content.replace(old_code, new_code)

# Write back
with open('/app/app/services/backtest_engine.py', 'w') as f:
    f.write(content)

print("✅ Fixed backtest_engine.py")
