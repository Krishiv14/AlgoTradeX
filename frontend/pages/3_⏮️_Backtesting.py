"""
Backtesting Page - Run and analyze backtests
This is the MAIN PAGE that demonstrates your platform's capabilities
"""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="Backtesting", page_icon="⏮️", layout="wide")

API_URL = "http://localhost:8000/api/v1"

st.title("⏮️ Strategy Backtesting")
st.markdown("Test trading strategies on historical NSE data with comprehensive performance metrics")

st.markdown("---")

# Fetch available strategies
@st.cache_data(ttl=60)
def get_strategies():
    try:
        response = requests.get(f"{API_URL}/strategies/")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

@st.cache_data(ttl=60)
def get_nifty50_stocks():
    try:
        response = requests.get(f"{API_URL}/stocks/nifty50")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

# Backtest Configuration
st.subheader("🔧 Backtest Configuration")

col1, col2 = st.columns(2)

with col1:
    # Strategy selection
    strategies = get_strategies()
    
    if not strategies:
        st.warning("⚠️ No strategies found. Please create a strategy first.")
        if st.button("Create Default Strategies"):
            # Create default strategies from templates
            templates = ['ma_crossover', 'rsi', 'macd']
            for template in templates:
                try:
                    requests.post(f"{API_URL}/strategies/from-template/{template}")
                except:
                    pass
            st.success("✅ Default strategies created! Refresh the page.")
            st.rerun()
    else:
        strategy_options = {f"{s['name']} ({s['strategy_type']})": s['id'] for s in strategies}
        selected_strategy_name = st.selectbox(
            "Select Strategy",
            options=list(strategy_options.keys()),
            help="Choose a trading strategy to backtest"
        )
        selected_strategy_id = strategy_options[selected_strategy_name]
        
        # Show strategy details
        selected_strategy = next(s for s in strategies if s['id'] == selected_strategy_id)
        with st.expander("📋 Strategy Parameters"):
            st.json(selected_strategy['parameters'])
            if selected_strategy.get('risk_params'):
                st.markdown("**Risk Management:**")
                st.json(selected_strategy['risk_params'])

with col2:
    # Stock selection
    stocks = get_nifty50_stocks()
    
    if not stocks:
        st.warning("⚠️ No stocks found. Please sync Nifty 50 data first.")
        if st.button("Sync Nifty 50 Data"):
            st.info("This will take 5-10 minutes. Starting sync...")
            try:
                requests.post(f"{API_URL}/stocks/sync-nifty50?years=5")
                st.success("✅ Data sync initiated!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        stock_options = {f"{s['symbol']} - {s['name']}": s['symbol'] for s in stocks}
        selected_stock_display = st.selectbox(
            "Select Stock",
            options=list(stock_options.keys()),
            help="Choose a Nifty 50 stock to backtest"
        )
        selected_stock = stock_options[selected_stock_display]

# Date range selection
col1, col2, col3 = st.columns(3)

with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.now() - timedelta(days=2*365),
        help="Backtest start date"
    )

with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.now(),
        help="Backtest end date"
    )

with col3:
    initial_capital = st.number_input(
        "Initial Capital (₹)",
        min_value=10000,
        max_value=10000000,
        value=100000,
        step=10000,
        help="Starting capital for backtest"
    )

st.markdown("---")

# Run Backtest Button
if st.button("🚀 Run Backtest", type="primary", use_container_width=True):
    if not strategies or not stocks:
        st.error("Please ensure strategies and stocks are available")
    else:
        with st.spinner("Running backtest... This may take a few seconds"):
            try:
                payload = {
                    "strategy_id": selected_strategy_id,
                    "stock_symbol": selected_stock,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "initial_capital": float(initial_capital)
                }
                
                response = requests.post(
                    f"{API_URL}/backtest/run",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Store result in session state
                    st.session_state['backtest_result'] = result
                    st.success(f"✅ {result['message']}")
                    st.info(f"Backtest ID: {result['backtest_id']} | Execution Time: {result['execution_time_ms']}ms")
                else:
                    st.error(f"Backtest failed: {response.json().get('detail', 'Unknown error')}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Display Results
if 'backtest_result' in st.session_state:
    result = st.session_state['backtest_result']
    
    st.markdown("---")
    st.subheader("📊 Backtest Results")
    
    # Performance Metrics
    metrics = result['metrics']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_return_pct = metrics['total_return'] * 100
        st.metric(
            "Total Return",
            f"{total_return_pct:.2f}%",
            delta=f"₹{result['final_capital'] - result['initial_capital']:,.0f}"
        )
    
    with col2:
        st.metric(
            "Sharpe Ratio",
            f"{metrics['sharpe_ratio']:.2f}",
            delta="Risk-Adjusted Return"
        )
    
    with col3:
        max_dd_pct = metrics['max_drawdown'] * 100
        st.metric(
            "Max Drawdown",
            f"{max_dd_pct:.2f}%",
            delta="Peak to Trough",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Total Trades",
            result['total_trades'],
            delta=f"Execution: {result['execution_time_ms']}ms"
        )
    
    # Additional Metrics
    st.markdown("### 📈 Detailed Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Capital Performance**")
        st.markdown(f"- Initial Capital: ₹{result['initial_capital']:,.0f}")
        st.markdown(f"- Final Capital: ₹{result['final_capital']:,.0f}")
        st.markdown(f"- Net Profit/Loss: ₹{result['final_capital'] - result['initial_capital']:,.0f}")
        st.markdown(f"- Return: {total_return_pct:.2f}%")
    
    with col2:
        st.markdown("**Risk Metrics**")
        st.markdown(f"- Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
        st.markdown(f"- Max Drawdown: {max_dd_pct:.2f}%")
        st.markdown(f"- Execution Time: {result['execution_time_ms']}ms")
    
    st.markdown("---")
    
    # Fetch detailed backtest data
    try:
        backtest_id = result['backtest_id']
        
        # Get trades
        trades_response = requests.get(f"{API_URL}/backtest/{backtest_id}/trades")
        
        if trades_response.status_code == 200:
            trades = trades_response.json()
            
            if trades:
                st.subheader("📝 Trade History")
                
                # Convert to DataFrame
                trades_df = pd.DataFrame(trades)
                
                # Format columns
                trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date']).dt.strftime('%Y-%m-%d')
                trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date']).dt.strftime('%Y-%m-%d')
                trades_df['pnl'] = trades_df['pnl'].apply(lambda x: f"₹{x:,.2f}")
                trades_df['pnl_percentage'] = trades_df['pnl_percentage'].apply(lambda x: f"{x*100:.2f}%")
                
                # Display table
                display_cols = ['trade_type', 'entry_date', 'entry_price', 'exit_date', 'exit_price', 
                               'quantity', 'pnl', 'pnl_percentage', 'hold_period_days', 'exit_reason']
                
                st.dataframe(
                    trades_df[display_cols],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Trade Statistics
                st.markdown("### 📊 Trade Statistics")
                
                col1, col2, col3 = st.columns(3)
                
                winning_trades = len([t for t in trades if t['pnl'] > 0])
                losing_trades = len([t for t in trades if t['pnl'] < 0])
                
                with col1:
                    st.metric("Winning Trades", winning_trades)
                    st.metric("Win Rate", f"{(winning_trades/len(trades)*100):.1f}%")
                
                with col2:
                    st.metric("Losing Trades", losing_trades)
                    avg_hold = sum(t['hold_period_days'] for t in trades) / len(trades)
                    st.metric("Avg Hold Period", f"{avg_hold:.1f} days")
                
                with col3:
                    total_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
                    total_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
                    st.metric("Total Profit", f"₹{total_profit:,.0f}")
                    st.metric("Total Loss", f"₹{total_loss:,.0f}")
                
                # P&L Distribution Chart
                st.markdown("### 📊 P&L Distribution")
                
                fig = go.Figure()
                
                pnl_values = [t['pnl'] for t in trades]
                colors = ['green' if p > 0 else 'red' for p in pnl_values]
                
                fig.add_trace(go.Bar(
                    x=list(range(1, len(trades) + 1)),
                    y=pnl_values,
                    marker_color=colors,
                    name='P&L per Trade'
                ))
                
                fig.update_layout(
                    title="Profit & Loss by Trade",
                    xaxis_title="Trade Number",
                    yaxis_title="P&L (₹)",
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error fetching trade details: {str(e)}")

else:
    st.info("👆 Configure and run a backtest above to see results")

# Sidebar - Recent Backtests
with st.sidebar:
    st.markdown("### 📜 Recent Backtests")
    
    try:
        recent = requests.get(f"{API_URL}/backtest/?limit=5")
        if recent.status_code == 200:
            backtests = recent.json()
            
            for bt in backtests:
                with st.expander(f"#{bt['backtest_id']} - {bt['strategy_name']}"):
                    st.markdown(f"**Stock:** {bt['stock_symbol']}")
                    st.markdown(f"**Return:** {bt['total_return']:.2f}%")
                    st.markdown(f"**Sharpe:** {bt['sharpe_ratio']:.2f}")
                    st.markdown(f"**Trades:** {bt['total_trades']}")
                    
                    if st.button(f"Load #{bt['backtest_id']}", key=f"load_{bt['backtest_id']}"):
                        # Fetch this backtest
                        response = requests.get(f"{API_URL}/backtest/{bt['backtest_id']}")
                        if response.status_code == 200:
                            st.session_state['backtest_result'] = response.json()
                            st.rerun()
    except:
        st.info("No recent backtests")
