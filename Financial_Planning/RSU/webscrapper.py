"""
RSU Market Data Pipeline - S&P 500 Closing Prices & USD/INR Conversion Rate

What this file does:
This script implements a data pipeline that fetches the latest closing prices for
S&P 500 stocks using yfinance, and scrapes the live USD to INR conversion rate via
Tavily web search + LLM extraction. The combined data is persisted as a Parquet file
for consumption by the RSU financial planning module.

What this file contains:
- scrape_usd_to_inr_rate: Fetches live USD/INR rate via Tavily + LLM extraction
- fetch_sp500_closing_prices: Downloads latest closing prices from yfinance for all tickers
- build_rsu_market_data: Orchestrates the full pipeline and returns a DataFrame
- save_market_data_parquet: Persists the DataFrame to a Parquet file
- generate_rsu_parquet: Main entry point — runs pipeline, respects daily refresh cadence
- load_rsu_market_data: Helper to load the Parquet file for use in the workflow
- get_stock_price_inr: Look up a ticker's INR price from the cached data
- get_usd_to_inr_rate: Retrieve the cached USD/INR rate
"""

import os
import re
import json
import yfinance as yf
import pandas as pd
from datetime import date, datetime
from typing import Optional, List
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage

from pathlib import Path

from Financial_Planning.Toools.standard_tools import tavily_tool

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FP_RSU_DIR = Path(__file__).resolve().parent
_BACKEND_PARQUET = _REPO_ROOT / "backend" / "data" / "rsu_market_data.parquet"
_FP_PARQUET = _FP_RSU_DIR / "rsu_market_data.parquet"

# Prefer shared backend cache; else RSU folder under Financial_Planning
PARQUET_DIR = str(_FP_RSU_DIR)
PARQUET_FILE = str(_BACKEND_PARQUET if _BACKEND_PARQUET.exists() else _FP_PARQUET)
LAST_UPDATE_FILE = str(_FP_RSU_DIR / "rsu_last_update.json")

# ======================== ENV / LLM SETUP ========================

load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_API_BASE = os.getenv("AZURE_API_BASE")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")

llm_azure = AzureChatOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_API_BASE,
    api_version=AZURE_API_VERSION,
    deployment_name=AZURE_DEPLOYMENT_NAME,
    temperature=0,
)

# Refresh interval in days — skip re-scrape if data is newer than this
REFRESH_INTERVAL_DAYS = 1

# Full S&P 500 constituent list.
# yfinance can batch-download all of these in a single call.
SP500_TICKERS = [
    "MMM", "AOS", "ABT", "ABBV", "ACN", "ADBE", "AMD", "AES", "AFL", "A",
    "APD", "ABNB", "AKAM", "ALB", "ARE", "ALGN", "ALLE", "LNT", "ALL", "GOOGL",
    "GOOG", "MO", "AMZN", "AMCR", "AEE", "AAL", "AEP", "AXP", "AIG", "AMT",
    "AWK", "AMP", "AME", "AMGN", "APH", "ADI", "ANSS", "AON", "APA", "AAPL",
    "AMAT", "APTV", "ACGL", "ADM", "ANET", "AJG", "AIZ", "T", "ATO", "ADSK",
    "AZO", "AVB", "AVY", "AXON", "BKR", "BALL", "BAC", "BK", "BBWI", "BAX",
    "BDX", "BRK.B", "BBY", "TECH", "BIIB", "BLK", "BX", "BA", "BCR", "BSX",
    "BMY", "AVGO", "BR", "BRO", "BF.B", "BLDR", "BG", "CDNS", "CZR", "CPT",
    "CPB", "COF", "CAH", "KMX", "CCL", "CARR", "CTLT", "CAT", "CBOE", "CBRE",
    "CDW", "CE", "COR", "CNC", "CNX", "CF", "CRL", "SCHW", "CHTR", "CVX",
    "CMG", "CB", "CHD", "CI", "CINF", "CTAS", "CSCO", "C", "CFG", "CLX",
    "CME", "CMS", "KO", "CTSH", "CL", "CMCSA", "CMA", "CAG", "COP", "ED",
    "STZ", "CEG", "COO", "CPRT", "GLW", "CTVA", "CSGP", "COST", "CTRA", "CCI",
    "CSX", "CMI", "CVS", "DHR", "DRI", "DVA", "DE", "DAL", "XRAY", "DVN",
    "DXCM", "FANG", "DLR", "DFS", "DG", "DLTR", "D", "DPZ", "DOV", "DOW",
    "DHI", "DTE", "DUK", "DD", "EMN", "ETN", "EBAY", "ECL", "EIX", "EW",
    "EA", "ELV", "LLY", "EMR", "ENPH", "ETR", "EOG", "EPAM", "EQT", "EFX",
    "EQIX", "EQR", "ESS", "EL", "ETSY", "EG", "EVRG", "ES", "EXC", "EXPE",
    "EXPD", "EXR", "XOM", "FFIV", "FDS", "FICO", "FAST", "FRT", "FDX", "FITB",
    "FSLR", "FE", "FIS", "FI", "FLT", "FMC", "F", "FTNT", "FTV", "FOXA",
    "FOX", "BEN", "FCX", "GRMN", "IT", "GE", "GEHC", "GEV", "GEN", "GNRC",
    "GD", "GIS", "GM", "GPC", "GILD", "GPN", "GL", "GS", "HAL", "HIG",
    "HAS", "HCA", "DOC", "HSIC", "HSY", "HES", "HPE", "HLT", "HOLX", "HD",
    "HON", "HRL", "HST", "HWM", "HPQ", "HUBB", "HUM", "HBAN", "HII", "IBM",
    "IEX", "IDXX", "ITW", "INCY", "IR", "PODD", "INTC", "ICE", "IFF", "IP",
    "IPG", "INTU", "ISRG", "IVZ", "INVH", "IQV", "IRM", "JBHT", "JBL", "JKHY",
    "J", "JNJ", "JCI", "JPM", "JNPR", "K", "KVUE", "KDP", "KEY", "KEYS",
    "KMB", "KIM", "KMI", "KLAC", "KHC", "KR", "LHX", "LH", "LRCX", "LW",
    "LVS", "LDOS", "LEN", "LNC", "LIN", "LYV", "LKQ", "LMT", "L", "LOW",
    "LULU", "LYB", "MTB", "MRO", "MPC", "MKTX", "MAR", "MMC", "MLM", "MAS",
    "MA", "MTCH", "MKC", "MCD", "MCK", "MDT", "MRK", "META", "MET", "MTD",
    "MGM", "MCHP", "MU", "MSFT", "MAA", "MRNA", "MHK", "MOH", "TAP", "MDLZ",
    "MPWR", "MNST", "MCO", "MS", "MOS", "MSI", "MSCI", "NDAQ", "NTAP", "NFLX",
    "NEM", "NWSA", "NWS", "NEE", "NKE", "NI", "NDSN", "NSC", "NTRS", "NOC",
    "NCLH", "NRG", "NUE", "NVDA", "NVR", "NXPI", "ORLY", "OXY", "ODFL", "OMC",
    "ON", "OKE", "ORCL", "OTIS", "PCAR", "PKG", "PANW", "PARA", "PH", "PAYX",
    "PAYC", "PYPL", "PNR", "PEP", "PFE", "PCG", "PM", "PSX", "PNW", "PXD",
    "PNC", "POOL", "PPG", "PPL", "PFG", "PG", "PGR", "PLD", "PRU", "PEG",
    "PTVE", "PSA", "PHM", "QRVO", "PWR", "QCOM", "DGX", "RL", "RJF", "RTX",
    "O", "REG", "REGN", "RF", "RSG", "RMD", "RVTY", "ROK", "ROL", "ROP",
    "ROST", "RCL", "SPGI", "CRM", "SBAC", "SLB", "STX", "SRE", "NOW", "SHW",
    "SPG", "SWKS", "SJM", "SW", "SNA", "SOLV", "SO", "LUV", "SWK", "SBUX",
    "STT", "STLD", "STE", "SYK", "SYF", "SNPS", "SYY", "TMUS", "TROW", "TTWO",
    "TPR", "TRGP", "TGT", "TEL", "TDY", "TFX", "TER", "TSLA", "TXN", "TXT",
    "TMO", "TJX", "TSCO", "TT", "TDG", "TRV", "TRMB", "TFC", "TYL", "TSN",
    "USB", "UBER", "UDR", "ULTA", "UNP", "UAL", "UPS", "URI", "UNH", "UHS",
    "VLO", "VTR", "VLTO", "VRSN", "VRSK", "VZ", "VRTX", "VTRS", "VICI", "V",
    "VMC", "WRB", "WAB", "WBA", "WMT", "DIS", "WBD", "WM", "WAT", "WEC",
    "WFC", "WELL", "WST", "WDC", "WRK", "WY", "WMB", "WTW", "GWW", "WYNN",
    "XEL", "XYL", "YUM", "ZBRA", "ZBH", "ZTS"]

# ======================== USD/INR SCRAPING ========================

def scrape_usd_to_inr_rate() -> float:
    """
    Scrape the current USD to INR conversion rate using Tavily + LLM extraction.

    Returns:
        float: Current USD to INR exchange rate.
    """
    query = f"USD to INR conversion rate today {date.today().strftime('%B %Y')}"
    print(f"\nFetching USD/INR rate: {query}")

    search_results = tavily_tool.invoke({"query": query})

    extraction_prompt = f"""You are a currency data extraction expert.
From the search results below, extract the current USD to INR exchange rate.

Search results:
{search_results}

Return ONLY a single float number representing how many Indian Rupees equal 1 US Dollar.
Example: if 1 USD = 83.47 INR, return exactly: 83.47
Do not include any text, currency symbols, or explanation — just the number."""

    response = llm_azure.invoke([HumanMessage(content=extraction_prompt)])
    rate_text = response.content.strip()

    matches = re.findall(r'\d+(?:\.\d+)?', rate_text)
    if not matches:
        raise ValueError(f"Could not parse USD/INR rate from LLM response: {rate_text}")

    rate = float(matches[0])

    # Sanity check
    if not (60.0 <= rate <= 150.0):
        raise ValueError(f"USD/INR rate {rate} is outside expected range [60, 150]")

    print(f"USD to INR rate: {rate}")
    return rate


# ======================== YFINANCE PRICE FETCH ========================

def fetch_sp500_closing_prices(tickers: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Fetch the latest available closing prices for S&P 500 tickers using yfinance.
    Downloads all tickers in a single batched API call for efficiency.

    Args:
        tickers: List of ticker symbols. Defaults to SP500_TICKERS.

    Returns:
        pd.DataFrame with columns: ticker, price_usd  (one row per ticker)
    """
    if tickers is None:
        tickers = SP500_TICKERS

    print(f"\nDownloading closing prices for {len(tickers)} tickers via yfinance...")

    # Download last 5 days; take the most recent available close to handle weekends/holidays
    raw = yf.download(
        tickers=tickers,
        period="5d",
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True
    )

    if raw.empty:
        raise RuntimeError("yfinance returned an empty DataFrame — check your internet connection.")

    # raw["Close"] is a DataFrame with tickers as columns when multiple tickers are passed
    close_df = raw["Close"]

    # Take the last non-NaN closing price for each ticker
    latest_prices = close_df.ffill().iloc[-1]

    records = []
    for ticker in tickers:
        if ticker in latest_prices.index and pd.notna(latest_prices[ticker]):
            records.append({
                'ticker': ticker,
                'price_usd': round(float(latest_prices[ticker]), 4)
            })
        else:
            print(f"  No closing price found for {ticker} — skipped")

    price_df = pd.DataFrame(records)
    print(f" Retrieved prices for {len(price_df)}/{len(tickers)} tickers.")
    return price_df


# ======================== PIPELINE ORCHESTRATION ========================

def build_rsu_market_data(tickers: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Orchestrates the full pipeline:
    1. Fetch USD/INR rate via Tavily
    2. Fetch S&P 500 closing prices via yfinance
    3. Compute INR prices and assemble the final DataFrame

    Args:
        tickers: Optional list of ticker symbols.

    Returns:
        pd.DataFrame with columns:
            ticker, price_usd, price_inr, usd_to_inr_rate, scrape_date
    """
    print("\n" + "=" * 60)
    print("RSU MARKET DATA PIPELINE")
    print("=" * 60)

    # Step 1: USD/INR rate (Tavily)
    print("\n[1/2] Fetching USD to INR conversion rate...")
    usd_to_inr = scrape_usd_to_inr_rate()

    # Step 2: S&P 500 closing prices (yfinance)
    print("\n[2/2] Fetching S&P 500 closing prices...")
    price_df = fetch_sp500_closing_prices(tickers)

    if price_df.empty:
        raise RuntimeError("No stock prices were retrieved from yfinance.")

    # Step 3: Compute INR prices
    scrape_date = date.today().isoformat()
    price_df['price_inr'] = (price_df['price_usd'] * usd_to_inr).round(2)
    price_df['usd_to_inr_rate'] = usd_to_inr
    price_df['scrape_date'] = scrape_date

    return price_df


def save_market_data_parquet(df: pd.DataFrame, path: str = PARQUET_FILE) -> str:
    """
    Save the market data DataFrame to a Parquet file.

    Args:
        df: DataFrame to persist.
        path: Destination file path.

    Returns:
        Absolute path of the saved Parquet file.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False, engine='pyarrow')
    print(f" Saved market data to: {path}  ({len(df)} records)")
    return os.path.abspath(path)


def _save_last_update(path: str = LAST_UPDATE_FILE):
    """Persist today's date as the last update timestamp."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump({'last_update': date.today().isoformat()}, f)


def _needs_refresh(path: str = LAST_UPDATE_FILE) -> bool:
    """Return True if data is stale or the update file is missing."""
    if not os.path.exists(path):
        return True
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        last = datetime.fromisoformat(data['last_update']).date()
        return (date.today() - last).days >= REFRESH_INTERVAL_DAYS
    except Exception:
        return True


def _load_last_update_date(path: str = LAST_UPDATE_FILE) -> str:
    try:
        with open(path, 'r') as f:
            return json.load(f).get('last_update', 'unknown')
    except Exception:
        return 'unknown'


# ======================== MAIN ENTRY POINTS ========================

def generate_rsu_parquet(tickers: Optional[List[str]] = None, force: bool = False) -> str:
    """
    Main pipeline entry point. Runs the full scrape and saves results as Parquet.
    Skips re-scraping if data is already fresh (within REFRESH_INTERVAL_DAYS).

    Args:
        tickers: Optional list of ticker symbols. Defaults to full SP500_TICKERS.
        force: If True, always re-scrape regardless of last update.

    Returns:
        Absolute path to the saved Parquet file.
    """
    if not force and not _needs_refresh():
        print(f" RSU market data is up to date (last updated: {_load_last_update_date()}). Skipping scrape.")
        return os.path.abspath(PARQUET_FILE)

    df = build_rsu_market_data(tickers)
    parquet_path = save_market_data_parquet(df)
    _save_last_update()

    print("\n" + "=" * 60)
    print("RSU PIPELINE COMPLETED SUCCESSFULLY")
    print(f"  Tickers stored  : {len(df)}")
    print(f"  USD/INR rate    : {df['usd_to_inr_rate'].iloc[0]}")
    print(f"  Scrape date     : {df['scrape_date'].iloc[0]}")
    print(f"  Parquet path    : {parquet_path}")
    print("=" * 60)

    return parquet_path


def load_rsu_market_data(path: str = PARQUET_FILE) -> pd.DataFrame:
    """
    Load the RSU market data Parquet file for use in the financial planning workflow.

    Args:
        path: Path to the Parquet file.

    Returns:
        pd.DataFrame with columns: ticker, price_usd, price_inr, usd_to_inr_rate, scrape_date

    Raises:
        FileNotFoundError: If the Parquet file does not exist yet.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"RSU market data not found at '{path}'. "
            "Run generate_rsu_parquet() first to populate the data file."
        )
    return pd.read_parquet(path, engine='pyarrow')


def get_stock_price_inr(ticker: str, df: Optional[pd.DataFrame] = None) -> Optional[float]:
    """
    Look up a ticker's current price in INR from the cached Parquet data.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL').
        df: Optional pre-loaded DataFrame. Loads from disk if not provided.

    Returns:
        Price in INR, or None if the ticker is not in the dataset.
    """
    if df is None:
        df = load_rsu_market_data()
    row = df[df['ticker'] == ticker.upper()]
    if row.empty:
        return None
    return float(row.iloc[0]['price_inr'])


def get_usd_to_inr_rate(df: Optional[pd.DataFrame] = None) -> Optional[float]:
    """
    Retrieve the USD to INR rate stored in the Parquet file.

    Args:
        df: Optional pre-loaded DataFrame. Loads from disk if not provided.

    Returns:
        USD to INR rate as float, or None if data is unavailable.
    """
    if df is None:
        df = load_rsu_market_data()
    if df.empty:
        return None
    return float(df.iloc[0]['usd_to_inr_rate'])


# ======================== SCRIPT EXECUTION ========================

if __name__ == "__main__":
    generate_rsu_parquet(force=True)
