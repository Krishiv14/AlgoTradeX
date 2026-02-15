"""Add proper trade statistics calculation"""

with open('/app/app/services/backtest_engine.py', 'r') as f:
    content = f.read()

# Add the method call in run_backtest
old_code = '''        # 6. Calculate performance metrics
        metrics = self._calculate_metrics(portfolio_df, data, initial_capital)'''

new_code = '''        # 6. Calculate performance metrics
        metrics = self._calculate_metrics(portfolio_df, data, initial_capital)
        
        # 6b. Add trade statistics
        trade_stats = self._calculate_trade_stats(trades_list)
        metrics.update(trade_stats)'''

content = content.replace(old_code, new_code)

with open('/app/app/services/backtest_engine.py', 'w') as f:
    f.write(content)

print("✅ Added trade statistics calculation")
