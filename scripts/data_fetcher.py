"""
Data Fetching Module for FFN Portfolio Analysis

This module contains data acquisition functions including:
- Stock data fetching from Yahoo Finance
- Data cleaning and preprocessing
- Error handling and retry logic
- Date formatting and timezone handling
- Data validation and quality checks
"""

import os
import pandas as pd
import yfinance as yf
import numpy as np
import logging
import requests
import time

# Get logger
logger = logging.getLogger(__name__)


def get_stock_data(symbols, start_date, end_date):
    """
    Fetch stock data for the given symbols from Yahoo Finance.
    
    Args:
        symbols (str): Comma-separated stock symbols (e.g., 'AAPL,MSFT,GOOG')
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        pd.DataFrame: DataFrame with stock prices indexed by date, columns are symbols
        
    Raises:
        ValueError: If no data is available or insufficient data points
    """
    try:
        # Convert symbols string to list
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        logger.info(f"Processing symbols: {symbol_list}")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # SIMPLIFIED APPROACH: Use yf.download which returns clean date-only indexes
        # This eliminates all timestamp/timezone complications
        logger.info("Fetching data using yf.download (no timestamp issues)...")
        
        # Add retry logic for rate limiting
        max_retries = 3
        retry_delay = 5  # Start with 5 seconds
        
        data = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Download attempt {attempt + 1}/{max_retries}")
                
                # Download data for all symbols at once - much simpler and cleaner
                data = yf.download(
                    tickers=' '.join(symbol_list),
                    start=start_date,
                    end=end_date,
                    progress=False,
                    group_by='ticker',
                    threads=True        # Use threading for multiple symbols
                )
                
                if not data.empty:
                    logger.info("Data downloaded successfully!")
                    break
                else:
                    logger.warning(f"Empty data returned on attempt {attempt + 1}")
                    
            except Exception as e:
                error_str = str(e).lower()
                if 'rate limit' in error_str or 'too many requests' in error_str:
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limited on attempt {attempt + 1}. Waiting {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Rate limited on final attempt. Error: {str(e)}")
                        raise
                else:
                    logger.error(f"Download failed with error: {str(e)}")
                    raise
        
        if data is None or data.empty:
            raise ValueError(f"No data available for the provided symbols in the date range {start_date} to {end_date}")
        
        logger.info(f"Downloaded data shape: {data.shape}")
        logger.info(f"Data index type: {type(data.index)}")
        logger.info(f"Sample dates: {data.index[:3].tolist()}")
        
        # Extract close prices for each symbol
        all_data = pd.DataFrame()
        
        for symbol in symbol_list:
            try:
                # Always use MultiIndex tuple format since group_by='ticker' creates MultiIndex columns
                # regardless of whether we have single or multiple symbols
                if (symbol, 'Close') in data.columns:
                    prices = data[(symbol, 'Close')].copy()
                else:
                    logger.error(f"No Close data found for symbol {symbol}")
                    continue
                
                # Clean the data
                prices = prices.dropna()  # Remove NaN values
                prices = prices[prices > 0]  # Remove zero/negative prices
                
                # Remove any duplicated indices (shouldn't happen with yf.download but safety check)
                prices = prices[~prices.index.duplicated(keep='first')]
                
                logger.info(f"\nProcessed data for {symbol}:")
                logger.info(f"  Date range: {prices.index[0]} to {prices.index[-1]}")
                logger.info(f"  Total dates: {len(prices)}")
                logger.info(f"  Sample prices: {prices.head()}")
                
                # Add to main DataFrame
                if all_data.empty:
                    all_data = pd.DataFrame({symbol: prices})
                else:
                    # Merge with existing data
                    symbol_df = pd.DataFrame({symbol: prices})
                    all_data = pd.merge(all_data, symbol_df,
                                      left_index=True, right_index=True,
                                      how='outer')
                
                logger.info(f"DataFrame after adding {symbol}: shape {all_data.shape}")
                
            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {str(e)}")
                continue
        
        if all_data.empty:
            raise ValueError(f"No valid data available for the provided symbols in the date range {start_date} to {end_date}")
        
        # Handle missing values
        logger.info(f"\nBefore NaN handling:")
        logger.info(f"Shape: {all_data.shape}")
        logger.info(f"NaN counts: {all_data.isna().sum().to_dict()}")
        
        # Forward fill missing values (up to 5 days)
        all_data = all_data.ffill(limit=5)
        
        # Drop any remaining NaN values
        all_data = all_data.dropna()
        
        # Final deduplication check (should not be needed with yf.download but safety first)
        if all_data.index.duplicated().any():
            logger.warning(f"Found {all_data.index.duplicated().sum()} duplicate dates. Removing...")
            all_data = all_data[~all_data.index.duplicated(keep='first')]
        
        logger.info(f"\nFinal clean dataset:")
        logger.info(f"Shape: {all_data.shape}")
        logger.info(f"Date range: {all_data.index[0]} to {all_data.index[-1]}")
        logger.info(f"Symbols: {all_data.columns.tolist()}")
        logger.info(f"Sample data:")
        logger.info(all_data.head())
        
        # Ensure we have enough data points
        if len(all_data) < 20:
            raise ValueError(f"Not enough data points for meaningful analysis. Only {len(all_data)} data points found.")
            
        return all_data
        
    except Exception as e:
        logger.error(f"Error fetching stock data: {str(e)}")
        raise ValueError(f"Error fetching stock data: {str(e)}")


def validate_symbols(symbols):
    """
    Validate symbol format and return cleaned symbol list.
    
    Args:
        symbols (str): Comma-separated stock symbols
        
    Returns:
        list: Cleaned and validated symbol list
        
    Raises:
        ValueError: If symbols format is invalid
    """
    if not symbols or not symbols.strip():
        raise ValueError("No symbols provided")
    
    symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
    
    if not symbol_list:
        raise ValueError("No valid symbols found")
    
    if len(symbol_list) > 10:
        raise ValueError("Too many symbols (maximum 10 allowed)")
    
    # Basic symbol validation (alphanumeric and common punctuation)
    import re
    valid_pattern = re.compile(r'^[A-Z0-9\.\-\^]+$')
    
    for symbol in symbol_list:
        if not valid_pattern.match(symbol):
            raise ValueError(f"Invalid symbol format: {symbol}")
    
    return symbol_list


def validate_date_range(start_date, end_date):
    """
    Validate date range for stock data fetching.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Raises:
        ValueError: If date range is invalid
    """
    from datetime import datetime, timedelta
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    
    if start >= end:
        raise ValueError("Start date must be before end date")
    
    # Check if start date is too far in the past (reasonable limit)
    min_date = datetime(1970, 1, 1)
    if start < min_date:
        raise ValueError(f"Start date too early (minimum: {min_date.strftime('%Y-%m-%d')})")
    
    # Check if end date is in the future
    max_date = datetime.now()
    if end > max_date:
        raise ValueError("End date cannot be in the future")
    
    # Check minimum date range (at least 30 days for meaningful analysis)
    min_days = 30
    if (end - start).days < min_days:
        raise ValueError(f"Date range too short (minimum {min_days} days required)")
    
    logger.info(f"Date range validation passed: {start_date} to {end_date} ({(end - start).days} days)") 