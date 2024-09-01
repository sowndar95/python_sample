import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import pandas as pd
import yfinance as yf
from pydantic import BaseModel
from typing import Optional
import ta

app = FastAPI()

@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

class StockInfo(BaseModel):
    name: Optional[str] = None
    current_price: Optional[float] = None
    price_to_earnings_ratio: Optional[float] = None
    price_to_book_ratio: Optional[float] = None
    earnings_per_share: Optional[float] = None
    dividend_yield: Optional[float] = None
    market_cap: Optional[int] = None
    week_high: Optional[float] = None
    week_low: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_profit_margin: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    shareholders_equity: Optional[float] = None
    long_business_summary: Optional[str] = None

@app.get("/getStockList")
def get_stocks():
    try:
        # Open and read the JSON file
        with open('stockData.json', 'r') as file:
            stock_data = json.load(file)
        return stock_data
    except FileNotFoundError:
        print("The file stockData.json was not found.")
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON from the file.")
        return []

@app.get("/stock/{ticker}", response_model=StockInfo)
def get_stock_info(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        print(info)
        stock_info = StockInfo(
            name=info.get("longName"),
            current_price=info.get("currentPrice"),
            price_to_earnings_ratio=info.get("forwardEps") / info.get("currentPrice") if info.get("forwardEps") and info.get("currentPrice") else None,
            price_to_book_ratio=info.get("priceToBook"),
            earnings_per_share=info.get("earningsPerShare"),
            dividend_yield=info.get("dividendYield"),
            market_cap=info.get("marketCap"),
            week_high=info.get("fiftyTwoWeekHigh"),
            week_low=info.get("fiftyTwoWeekLow"),
            gross_margin=info.get("grossMargins"),
            operating_margin=info.get("operatingMargins"),
            net_profit_margin=info.get("profitMargins"),
            current_ratio=info.get("currentRatio"),
            quick_ratio=info.get("quickRatio"),
            total_assets=info.get("totalAssets"),
            total_liabilities=info.get("totalLiabilitiesNet"),
            shareholders_equity=info.get("shareholdersEquity"),
            long_business_summary=info.get("longBusinessSummary"),
        )
        return stock_info
    except Exception as e:
        raise HTTPException(status_code=404, detail="Stock not found")

@app.get("/compare/{ticker}")
def compare_stock(ticker: str):
    peers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]  # Example peers
    comparisons = {}

    for peer in peers:
        if peer != ticker:
            try:
                stock = yf.Ticker(peer)
                info = stock.info
                comparisons[peer] = {
                    "name": info.get("longName"),
                    "current_price": info.get("currentPrice"),
                    "price_to_earnings_ratio": info.get("forwardEps") / info.get("currentPrice") if info.get("forwardEps") and info.get("currentPrice") else None,
                    "market_cap": info.get("marketCap"),
                }
            except Exception as e:
                comparisons[peer] = {"error": str(e)}

    return comparisons

@app.get("/historical/{ticker}")
def get_historical_data(ticker: str, start: str, end: str):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start, end=end)
        data = hist.reset_index().to_dict(orient='records')
        return {"historical_data": data}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Stock not found or data unavailable")
    
@app.get("/technical/{ticker}")
def get_technical_indicators(ticker: str, start: str, end: str):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start, end=end)
        hist['SMA_50'] = ta.trend.sma_indicator(hist['Close'], window=50)
        hist['SMA_200'] = ta.trend.sma_indicator(hist['Close'], window=200)
        hist['RSI'] = ta.momentum.RSIIndicator(hist['Close']).rsi()
        
        indicators = hist[['SMA_50', 'SMA_200', 'RSI']].dropna().reset_index().to_dict(orient='records')
        return {"technical_indicators": indicators}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Stock not found or data unavailable")