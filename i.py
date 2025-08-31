import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import time
import json

# Set page configuration
st.set_page_config(
    page_title="Real-Time Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.5rem;
        color: #2ca02c;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .stock-info {
        background-color: #f9f9f9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .github-section {
        background-color: #0d1117;
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 2rem;
    }
    .repo-card {
        background-color: #161b22;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

# Alpha Vantage API key (free tier)
API_KEY = "demo"  # In production, use a real API key from Alpha Vantage

# Function to get stock data
@st.cache_data(ttl=60)  # Cache data for 60 seconds
def get_stock_data(symbol, interval="5min"):
    """Fetch real-time stock data from Alpha Vantage API"""
    try:
        if interval == "5min":
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={API_KEY}"
        else:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
        
        response = requests.get(url)
        data = response.json()
        
        if interval == "5min":
            time_series = data.get("Time Series (5min)", {})
        else:
            time_series = data.get("Time Series (Daily)", {})
        
        if not time_series:
            st.error(f"Error fetching data for {symbol}: {data.get('Note', 'Unknown error')}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(time_series, orient="index")
        df.columns = [col.split(" ")[1].capitalize() for col in df.columns]
        df.index = pd.to_datetime(df.index)
        df = df.astype(float)
        df = df.sort_index()
        
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Function to get stock overview
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_stock_overview(symbol):
    """Fetch company overview data"""
    try:
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
        response = requests.get(url)
        data = response.json()
        return data
    except Exception as e:
        st.error(f"Error fetching overview: {e}")
        return None

# Function to get GitHub profile data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_github_profile(username):
    """Fetch GitHub profile data"""
    try:
        url = f"https://api.github.com/users/{username}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching GitHub profile: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching GitHub data: {e}")
        return None

# Function to get GitHub repositories
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_github_repos(username):
    """Fetch GitHub repositories"""
    try:
        url = f"https://api.github.com/users/{username}/repos?sort=updated"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching GitHub repos: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching GitHub repos: {e}")
        return None

# Function to calculate technical indicators
def calculate_technical_indicators(df, window=20):
    """Calculate SMA, RSI, and other technical indicators"""
    df = df.copy()
    
    # Simple Moving Average
    df['SMA'] = df['Close'].rolling(window=window).mean()
    
    # RSI (Relative Strength Index)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    return df

# Function to create stock chart
def create_stock_chart(df, symbol):
    """Create an interactive stock chart with technical indicators"""
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol} Price', 'Volume', 'RSI'),
        row_width=[0.2, 0.2, 0.6]
    )
    
    # Price data
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ), row=1, col=1)
    
    # SMA
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA'],
        line=dict(color='orange', width=1),
        name='SMA (20)'
    ), row=1, col=1)
    
    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['BB_Upper'],
        line=dict(color='gray', width=1, dash='dash'),
        name='BB Upper'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['BB_Lower'],
        line=dict(color='gray', width=1, dash='dash'),
        name='BB Lower',
        fill='tonexty'
    ), row=1, col=1)
    
    # Volume
    colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for _, row in df.iterrows()]
    fig.add_trace(go.Bar(
        x=df.index,
        y=df['Volume'],
        name='Volume',
        marker_color=colors
    ), row=2, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['RSI'],
        line=dict(color='purple', width=2),
        name='RSI'
    ), row=3, col=1)
    
    # Add RSI markers
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    
    return fig

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">📈 Real-Time Stock Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("Configuration")
    
    # Stock selection
    popular_stocks = {
        "Apple Inc. (AAPL)": "AAPL",
        "Microsoft Corporation (MSFT)": "MSFT",
        "Amazon.com Inc. (AMZN)": "AMZN",
        "Google LLC (GOOGL)": "GOOGL",
        "Tesla Inc. (TSLA)": "TSLA",
        "NVIDIA Corporation (NVDA)": "NVDA",
        "Meta Platforms Inc. (META)": "META",
        "JPMorgan Chase & Co. (JPM)": "JPM",
        "Johnson & Johnson (JNJ)": "JNJ",
        "Visa Inc. (V)": "V"
    }
    
    selected_stock_name = st.sidebar.selectbox(
        "Select a stock:",
        options=list(popular_stocks.keys())
    )
    selected_stock = popular_stocks[selected_stock_name]
    
    # Time frame selection
    time_frame = st.sidebar.selectbox(
        "Select time frame:",
        options=["Intraday (5min)", "Daily"]
    )
    
    # Refresh control
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 300, 60)
    
    # Get stock data
    interval = "5min" if time_frame == "Intraday (5min)" else "daily"
    df = get_stock_data(selected_stock, interval)
    
    if df is not None and not df.empty:
        # Calculate technical indicators
        df = calculate_technical_indicators(df)
        
        # Get the latest data point
        latest = df.iloc[-1]
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Current Price", f"${latest['Close']:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            change = latest['Close'] - df.iloc[-2]['Close']
            change_percent = (change / df.iloc[-2]['Close']) * 100
            st.metric("Change", f"${change:.2f}", f"{change_percent:.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Volume", f"{latest['Volume']:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("RSI", f"{latest['RSI']:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Display stock chart
        st.markdown('<div class="subheader">Price Chart with Technical Indicators</div>', unsafe_allow_html=True)
        fig = create_stock_chart(df, selected_stock)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display additional stock information
        st.markdown('<div class="subheader">Stock Information</div>', unsafe_allow_html=True)
        
        # Get company overview
        overview = get_stock_overview(selected_stock)
        
        if overview and not overview.get("Note"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown('<div class="stock-info">', unsafe_allow_html=True)
                st.write("**Company Overview**")
                st.write(f"**Name:** {overview.get('Name', 'N/A')}")
                st.write(f"**Sector:** {overview.get('Sector', 'N/A')}")
                st.write(f"**Industry:** {overview.get('Industry', 'N/A')}")
                st.write(f"**Exchange:** {overview.get('Exchange', 'N/A')}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="stock-info">', unsafe_allow_html=True)
                st.write("**Financial Metrics**")
                st.write(f"**Market Cap:** ${float(overview.get('MarketCapitalization', 0)):,.2f}")
                st.write(f"**PE Ratio:** {overview.get('PERatio', 'N/A')}")
                st.write(f"**EPS:** {overview.get('EPS', 'N/A')}")
                st.write(f"**Dividend Yield:** {overview.get('DividendYield', 'N/A')}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="stock-info">', unsafe_allow_html=True)
                st.write("**Performance**")
                st.write(f"**52 Week High:** ${float(overview.get('52WeekHigh', 0)):.2f}")
                st.write(f"**52 Week Low:** ${float(overview.get('52WeekLow', 0)):.2f}")
                st.write(f"**Analyst Target:** ${overview.get('AnalystTargetPrice', 'N/A')}")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Company overview data not available in demo mode. Use a real API key for full functionality.")
        
        # Display raw data
        if st.checkbox("Show Raw Data"):
            st.subheader("Raw Stock Data")
            st.dataframe(df.sort_index(ascending=False))
    
    else:
        st.warning("No data available for the selected stock. Try another stock or check your API key.")
    
    # GitHub Section
    st.markdown("---")
    st.markdown('<div class="github-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="subheader" style="color: white;">👨‍💻 GitHub Profile: praneeth11-busi</h2>', unsafe_allow_html=True)
    
    # Get GitHub data
    github_profile = get_github_profile("praneeth11-busi")
    github_repos = get_github_repos("praneeth11-busi")
    
    if github_profile:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"**Name:** {github_profile.get('name', 'N/A')}")
        with col2:
            st.markdown(f"**Public Repos:** {github_profile.get('public_repos', 'N/A')}")
        with col3:
            st.markdown(f"**Followers:** {github_profile.get('followers', 'N/A')}")
        with col4:
            st.markdown(f"**Following:** {github_profile.get('following', 'N/A')}")
        
        st.markdown(f"**Bio:** {github_profile.get('bio', 'No bio available')}")
        st.markdown(f"**Profile URL:** [@{github_profile.get('login', '')}]({github_profile.get('html_url', '')})")
    
    if github_repos:
        st.markdown("### Latest Repositories")
        for repo in github_repos[:5]:  # Show only 5 most recent repos
            with st.container():
                st.markdown('<div class="repo-card">', unsafe_allow_html=True)
                st.markdown(f"#### [{repo['name']}]({repo['html_url']})")
                st.markdown(f"**Description:** {repo['description'] or 'No description available'}")
                st.markdown(f"**Language:** {repo['language'] or 'Not specified'} • **Stars:** {repo['stargazers_count']} • **Forks:** {repo['forks_count']}")
                st.markdown(f"**Last updated:** {repo['updated_at'][:10]}")
                st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
