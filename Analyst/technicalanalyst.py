import yfinance as yf
import pandas as pd
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser

# Step 1: Collecting Technical Analysis Data using Yahoo Finance
def get_technical_analysis_data(ticker):
    # Fetch historical data (weekly interval for last 1 year)
    stock_data = yf.download(ticker, period="1y", interval="1wk")
    
    if stock_data.empty:
        raise ValueError("No data downloaded. Check your internet connection or ticker symbol.")
    
    # Calculate 50-week SMA
    stock_data["SMA50"] = stock_data["Close"].rolling(window=50).mean()

    # Calculate 20-week EMA
    stock_data["EMA20"] = stock_data["Close"].ewm(span=20, adjust=False).mean()

    # Calculate 12-week EMA & 26-week EMA for MACD
    stock_data["EMA12"] = stock_data["Close"].ewm(span=12, adjust=False).mean()
    stock_data["EMA26"] = stock_data["Close"].ewm(span=26, adjust=False).mean()

    # Calculate MACD and Signal Line
    stock_data["MACD"] = stock_data["EMA12"] - stock_data["EMA26"]
    stock_data["Signal_Line"] = stock_data["MACD"].ewm(span=9, adjust=False).mean()

    # Calculate RSI (Relative Strength Index)
    delta = stock_data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    stock_data["RSI"] = 100 - (100 / (1 + rs))
    
    # Get current price
    current_price = yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1]
    
    return stock_data, current_price

# Step 2: Setting up Langchain for Technical Analysis Insights
class TechnicalAnalysisAnalyzer:
    def __init__(self, openai_api_key: str, model_name: str = "gpt-4"):
        self.model = ChatOpenAI(openai_api_key=openai_api_key, model=model_name)
        
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", "You're a stock market expert with vast knowledge in technical analysis. Your task is to analyze the stock's technical indicators and give an insightful prediction."),
            ("human", "Based on the following technical analysis data for the company {ticker}: \n SMA50: {SMA50}\n EMA20: {EMA20}\n MACD: {MACD}\n Signal_Line: {Signal_Line}\n RSI: {RSI}\n Current Price: {current_price}\n Please analyze and provide insights about the stock's potential movement. Should investors consider buying, holding, or selling? What should be the strategy?")
        ])

    def analyze_technical_data(self, ticker):
        # Get technical analysis data
        stock_data, current_price = get_technical_analysis_data(ticker)
        
        # Extract the latest data for prompt
        latest_data = stock_data.iloc[-1]
        
        # Generate prompt input
        analysis_input = {
            "ticker": ticker,
            "SMA50": latest_data["SMA50"],
            "EMA20": latest_data["EMA20"],
            "MACD": latest_data["MACD"],
            "Signal_Line": latest_data["Signal_Line"],
            "RSI": latest_data["RSI"],
            "current_price": current_price
        }
        
        # Use Langchain to get analysis
        chain = self.analysis_prompt | self.model | StrOutputParser()
        response = chain.invoke(analysis_input)
        
        return response
