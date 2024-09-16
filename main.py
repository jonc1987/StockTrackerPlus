import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# Set page configuration
st.set_page_config(page_title="Stock Data Visualization", layout="wide")

# Function to fetch stock data
def get_stock_data(symbol, period="1y"):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        info = stock.info
        return hist, info
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None, None

# Function to create price history chart
def create_price_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price'))
    fig.update_layout(title='Stock Price History', xaxis_title='Date', yaxis_title='Price (USD)')
    return fig

# Function to search for stocks
def search_stocks(query):
    url = f"https://finance.yahoo.com/lookup?s={query}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'lookup-table'})
    
    if table:
        results = []
        rows = table.find_all('tr')[1:]  # Skip header row
        for row in rows[:10]:  # Limit to top 10 results
            cols = row.find_all('td')
            if len(cols) >= 2:
                symbol = cols[0].text.strip()
                name = cols[1].text.strip()
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'exchange': 'N/A'  # Yahoo Finance lookup doesn't provide exchange info
                })
        return results
    else:
        return []

# Main app
def main():
    st.title("Stock Data Visualization App")

    # Search input
    search_query = st.text_input("Search for a stock (enter company name or symbol)", "")
    
    if search_query:
        search_results = search_stocks(search_query)
        if search_results:
            st.subheader("Search Results")
            selected_stock = st.selectbox(
                "Select a stock",
                options=[f"{result['symbol']} - {result['name']}" for result in search_results],
                format_func=lambda x: x.split(' - ')[1]
            )
            symbol = selected_stock.split(' - ')[0]
        else:
            st.warning("No results found. Please try a different search term.")
            return
    else:
        # Default to AAPL if no search is performed
        symbol = "AAPL"

    # Fetch stock data
    hist_data, info = get_stock_data(symbol)

    if hist_data is not None and info is not None:
        # Display key financial information
        st.subheader(f"Key Financial Information for {symbol}")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current Price", f"${info.get('currentPrice', 'N/A')}")
            st.metric("Market Cap", f"${info.get('marketCap', 'N/A'):,.0f}")
        
        with col2:
            st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
            st.metric("52 Week High", f"${info.get('fiftyTwoWeekHigh', 'N/A')}")
        
        with col3:
            st.metric("Dividend Yield", f"{info.get('dividendYield', 'N/A'):.2%}" if info.get('dividendYield') else "N/A")
            st.metric("52 Week Low", f"${info.get('fiftyTwoWeekLow', 'N/A')}")

        # Display price history chart
        st.subheader("Stock Price History")
        chart = create_price_chart(hist_data)
        st.plotly_chart(chart, use_container_width=True)

        # Display data table
        st.subheader("Historical Data")
        st.dataframe(hist_data)

        # CSV download button
        csv = hist_data.to_csv(index=True)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"{symbol}_stock_data.csv",
            mime="text/csv",
        )
    else:
        st.warning("Unable to fetch stock data. Please check the symbol and try again.")

if __name__ == "__main__":
    main()
