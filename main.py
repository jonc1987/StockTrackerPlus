import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import os

# Set page configuration
st.set_page_config(page_title="Stock Data Visualization", layout="wide")

# Move selected_stocks outside of main() to make it persistent
if 'selected_stocks' not in st.session_state:
    st.session_state.selected_stocks = []

# Function to fetch stock data
def get_stock_data(symbols, period="1y"):
    data = {}
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            info = stock.info
            data[symbol] = {"history": hist, "info": info}
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
    return data

# Function to create price history chart for multiple stocks
def create_price_chart(data):
    fig = go.Figure()
    for symbol, stock_data in data.items():
        fig.add_trace(go.Scatter(x=stock_data["history"].index, y=stock_data["history"]['Close'], mode='lines', name=f'{symbol} Close Price'))
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

# Function to display key metrics for multiple stocks
def display_key_metrics(data):
    metrics = ["currentPrice", "marketCap", "trailingPE", "forwardPE", "dividendYield", "52WeekChange"]
    metric_names = ["Current Price", "Market Cap", "P/E Ratio (TTM)", "Forward P/E", "Dividend Yield", "52 Week Change"]
    
    df = pd.DataFrame(index=metric_names)
    
    for symbol, stock_data in data.items():
        info = stock_data["info"]
        values = []
        for metric in metrics:
            value = info.get(metric, 'N/A')
            if metric == "currentPrice":
                values.append(f"${value}" if isinstance(value, (int, float)) else str(value))
            elif metric == "marketCap":
                values.append(f"${value:,.0f}" if isinstance(value, (int, float)) else str(value))
            elif metric in ["trailingPE", "forwardPE"]:
                values.append(f"{value:.2f}" if isinstance(value, (int, float)) else str(value))
            elif metric == "dividendYield":
                values.append(f"{value:.2%}" if isinstance(value, (int, float)) else str(value))
            elif metric == "52WeekChange":
                values.append(f"{value:.2%}" if isinstance(value, (int, float)) else str(value))
            else:
                values.append(str(value))
        df[symbol] = values
    
    st.table(df)

# Function to generate AI stock analysis

# Main app
def main():
    st.title("Stock Data Visualization App")
    
    # Search functionality
    search_query = st.text_input("Search for stocks (enter company name or symbol)", key="stock_search")
    
    if search_query:
        search_results = search_stocks(search_query)
        if search_results:
            st.subheader("Search Results")
            selected_stock = st.selectbox(
                "Select a stock to add",
                options=[f"{result['symbol']} - {result['name']}" for result in search_results],
                format_func=lambda x: x.split(' - ')[1]
            )
            if st.button("Add Stock"):
                if selected_stock not in st.session_state.selected_stocks:
                    st.session_state.selected_stocks.append(selected_stock)
                    st.success(f"Added {selected_stock} to the comparison list.")
                else:
                    st.warning(f"{selected_stock} is already in the comparison list.")
        else:
            st.warning("No results found. Please try a different search term.")
    
    # Display currently selected stocks
    if st.session_state.selected_stocks:
        st.subheader("Currently Selected Stocks")
        st.write(", ".join(st.session_state.selected_stocks))
        
        # Compare button
        if st.button("Compare Selected Stocks"):
            symbols = [stock.split(' - ')[0] for stock in st.session_state.selected_stocks]
            
            # Fetch stock data
            stock_data = get_stock_data(symbols)
            
            # Filter out symbols with no data
            valid_stock_data = {symbol: data for symbol, data in stock_data.items() if data}
            
            if len(valid_stock_data) >= 1:
                # Display key financial information
                st.subheader("Key Financial Metrics")
                display_key_metrics(valid_stock_data)
                
                # Display price history chart
                st.subheader("Stock Price History")
                chart = create_price_chart(valid_stock_data)
                st.plotly_chart(chart, use_container_width=True)
                
                # Generate and display AI analysis for each stock
                
                # Display data tables
                st.subheader("Historical Data")
                for symbol, data in valid_stock_data.items():
                    with st.expander(f"Historical Data for {symbol}"):
                        st.dataframe(data["history"])
                        
                        # CSV download button
                        csv = data["history"].to_csv(index=True)
                        st.download_button(
                            label=f"Download CSV for {symbol}",
                            data=csv,
                            file_name=f"{symbol}_stock_data.csv",
                            mime="text/csv",
                        )
            else:
                st.warning("Unable to fetch data for the selected stock(s). Please try different symbols.")
    else:
        st.info("Please search and add stocks to compare.")

if __name__ == "__main__":
    main()

