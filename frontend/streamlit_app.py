"""
AlgoTradeX - Streamlit Dashboard
Main entry point for the frontend
"""
import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="AlgoTradeX - Algorithmic Trading Platform",
    page_icon="ðŸ“ˆ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL
API_URL = "http://algotrader_backend:8000/api/v1"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    
    .success-metric {
        border-left-color: #28a745;
    }
    
    .danger-metric {
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)


def get_data_stats():
    """Fetch database statistics"""
    try:
        response = requests.get(f"{API_URL}/stocks/data/stats")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def get_nifty50_stocks():
    """Fetch Nifty 50 stocks"""
    try:
        response = requests.get(f"{API_URL}/stocks/nifty50")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []


def get_recent_backtests(limit=10):
    """Fetch recent backtests"""
    try:
        response = requests.get(f"{API_URL}/backtest/?limit={limit}")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []


# Header
st.markdown('<h1 class="main-header">ðŸ“ˆ AlgoTradeX</h1>', unsafe_allow_html=True)
st.markdown("### Algorithmic Trading Platform for NSE Stocks")

st.markdown("---")

# Main Dashboard
col1, col2, col3, col4 = st.columns(4)

# Fetch stats
stats = get_data_stats()

if stats:
    with col1:
        st.metric(
            label="ðŸ“Š Total Stocks",
            value=stats['total_stocks'],
            delta="Active"
        )
    
    with col2:
        st.metric(
            label="ðŸŽ¯ Nifty 50 Stocks",
            value=stats['nifty50_stocks'],
            delta="Premium"
        )
    
    with col3:
        st.metric(
            label="ðŸ’¾ OHLCV Records",
            value=f"{stats['total_ohlcv_records']:,}",
            delta="Historical Data"
        )
    
    with col4:
        if stats['date_range']['latest']:
            latest_date = datetime.fromisoformat(stats['date_range']['latest'].replace('Z', '+00:00'))
            days_old = (datetime.now() - latest_date.replace(tzinfo=None)).days
            st.metric(
                label="ðŸ“… Data Freshness",
                value=f"{days_old} days old",
                delta="Last Update"
            )
else:
    st.warning("âš ï¸ Could not connect to backend. Please ensure FastAPI server is running on port 8000.")
    st.code("cd backend && python -m app.main")

st.markdown("---")

# Quick Actions
st.subheader("ðŸš€ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("ðŸ“Š View Strategies", use_container_width=True):
        st.switch_page("pages/2_ðŸ”§_Strategy_Builder.py")

with col2:
    if st.button("â®ï¸ Run Backtest", use_container_width=True):
        st.switch_page("pages/3_â®ï¸_Backtesting.py")

with col3:
    if st.button("ðŸ“ˆ View Analytics", use_container_width=True):
        st.switch_page("pages/5_ðŸ“‰_Analytics.py")

st.markdown("---")

# Recent Backtests
st.subheader("ðŸ“œ Recent Backtests")

backtests = get_recent_backtests(limit=5)

if backtests:
    df = pd.DataFrame(backtests)
    
    # Format columns
    if not df.empty:
        df['Return %'] = df['total_return'].apply(lambda x: f"{x:.2f}%")
        df['Sharpe'] = df['sharpe_ratio'].apply(lambda x: f"{x:.2f}")
        df['Max DD %'] = df['max_drawdown'].apply(lambda x: f"{x:.2f}%")
        
        display_df = df[[
            'backtest_id', 
            'strategy_name', 
            'stock_symbol', 
            'Return %',
            'Sharpe',
            'Max DD %',
            'total_trades'
        ]]
        
        display_df.columns = ['ID', 'Strategy', 'Stock', 'Return', 'Sharpe', 'Max DD', 'Trades']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Quick visualization
        if len(backtests) > 0:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df['strategy_name'],
                y=df['total_return'],
                name='Return %',
                marker_color='lightblue'
            ))
            
            fig.update_layout(
                title="Strategy Performance Comparison",
                xaxis_title="Strategy",
                yaxis_title="Return (%)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No backtests found. Run your first backtest to see results here!")
    
st.markdown("---")

# Feature Highlights
st.subheader("âœ¨ Platform Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **ðŸ“Š Backtesting Engine**
    - Vectorized operations for speed
    - Transaction cost modeling
    - Risk management (stop-loss, position sizing)
    - Comprehensive metrics (Sharpe, Drawdown, etc.)
    """)

with col2:
    st.markdown("""
    **ðŸ”§ Strategy Builder**
    - Moving Average Crossover
    - RSI Mean Reversion
    - MACD Momentum
    - Custom indicator combinations
    """)

with col3:
    st.markdown("""
    **ðŸ“ˆ Analytics Dashboard**
    - Interactive charts
    - Trade-by-trade analysis
    - Strategy comparison
    - Performance visualization
    """)

st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>AlgoTradeX v1.0 | Built with FastAPI + PostgreSQL + Streamlit</p>
    <p>NSE Historical Data | Transaction Cost: 0.05% | Benchmark: Nifty 50</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/stocks-growth.png", width=80)
    st.title("Navigation")
    
    st.markdown("---")
    
    st.markdown("### ðŸ“Œ Quick Links")
    st.markdown("- [Dashboard](streamlit_app.py)")
    st.markdown("- [Strategy Builder](pages/2_ðŸ”§_Strategy_Builder.py)")
    st.markdown("- [Backtesting](pages/3_â®ï¸_Backtesting.py)")
    st.markdown("- [Analytics](pages/5_ðŸ“‰_Analytics.py)")
    
    st.markdown("---")
    
    st.markdown("### ðŸŽ¯ System Status")
    
    # Check backend status
    try:
        response = requests.get("http://algotrader_backend:8000/health", timeout=2)
        if response.status_code == 200:
            st.success("âœ… Backend Online")
        else:
            st.error("âŒ Backend Issues")
    except:
        st.error("âŒ Backend Offline")
    
    st.markdown("---")
    
    st.markdown("### ðŸ“š Documentation")
    st.markdown("""
    For deployment, interview prep, and technical details, 
    check the `docs/` folder in the repository.
    """)

