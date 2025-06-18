"""
Centralized Data Processing Module for FFN Portfolio Analysis

This module provides a single source of truth for all data transformations including:
- Raw price data processing
- Returns calculations (daily and cumulative)
- Percentage conversions
- Date formatting for exports
- Data validation and consistency checks
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Optional

# Get logger
logger = logging.getLogger(__name__)


class DataProcessor:
    """Centralized data processor for consistent transformations across the application."""
    
    def __init__(self, raw_data: pd.DataFrame):
        """
        Initialize the data processor with raw price data.
        
        Args:
            raw_data: DataFrame with DatetimeIndex and stock symbols as columns
        """
        self.raw_data = raw_data.copy()
        self.validate_raw_data()
        
        # Cached processed data to avoid recomputation
        self._daily_returns = None
        self._cumulative_returns = None
        self._processed_for_export = None
    
    def validate_raw_data(self):
        """Validate the raw data format and quality."""
        if self.raw_data.empty:
            raise ValueError("Raw data is empty")
        
        if not isinstance(self.raw_data.index, pd.DatetimeIndex):
            raise ValueError("Data index must be DatetimeIndex")
        
        if self.raw_data.index.duplicated().any():
            logger.error(f"Raw data contains {self.raw_data.index.duplicated().sum()} duplicate dates")
            raise ValueError("Raw data contains duplicate dates - this should have been fixed in data_fetcher")
        
        if self.raw_data.isna().any().any():
            logger.warning(f"Raw data contains NaN values: {self.raw_data.isna().sum().to_dict()}")
        
        logger.info(f"Data validation passed: {self.raw_data.shape[0]} dates, {self.raw_data.shape[1]} symbols")
    
    def get_daily_returns(self, as_percentage: bool = False) -> pd.DataFrame:
        """
        Calculate daily returns with QuantStats-compatible methodology.
        
        Args:
            as_percentage: If True, returns as percentage (multiplied by 100)
            
        Returns:
            DataFrame with daily returns (QuantStats-compatible preprocessing)
        """
        if self._daily_returns is None:
            # QuantStats-compatible preprocessing
            returns_data = self.raw_data.pct_change()
            
            # Handle infinities (QuantStats approach)
            returns_data = returns_data.replace([np.inf, -np.inf], float("NaN"))
            
            # Fill NaN with 0 instead of dropping (QuantStats approach)
            returns_data = returns_data.fillna(0)
            
            # Apply QuantStats _match_dates logic: drop dates until first non-zero return
            # This matches QuantStats behavior exactly
            first_nonzero_indices = []
            for col in returns_data.columns:
                first_nonzero_idx = returns_data[col].ne(0).idxmax()
                if returns_data[col].ne(0).any():  # Only if there are non-zero values
                    first_nonzero_indices.append(first_nonzero_idx)
            
            if first_nonzero_indices:
                # Use the latest first non-zero date among all columns
                start_date = max(first_nonzero_indices)
                returns_data = returns_data.loc[start_date:]
                logger.info(f"Applied QuantStats date matching: dropped dates until {start_date}")
            
            self._daily_returns = returns_data
            logger.info(f"Calculated daily returns (QuantStats method): {self._daily_returns.shape}")
        
        if as_percentage:
            return self._daily_returns * 100
        return self._daily_returns.copy()
    
    def get_cumulative_returns(self, as_percentage: bool = False) -> pd.DataFrame:
        """
        Calculate cumulative returns with consistent methodology.
        
        Args:
            as_percentage: If True, returns as percentage
            
        Returns:
            DataFrame with cumulative returns (rebased to start at 0)
        """
        if self._cumulative_returns is None:
            daily_returns = self.get_daily_returns(as_percentage=False)
            # Fill first NaN with 0 (no return on first day)
            daily_returns_filled = daily_returns.fillna(0)
            # Calculate cumulative returns: (1 + r1) * (1 + r2) * ... - 1
            self._cumulative_returns = (1 + daily_returns_filled).cumprod() - 1
            logger.info(f"Calculated cumulative returns: {self._cumulative_returns.shape}")
        
        if as_percentage:
            return self._cumulative_returns * 100
        return self._cumulative_returns.copy()
    
    def get_processed_for_export(self) -> Dict[str, pd.DataFrame]:
        """
        Get all processed datasets formatted for CSV export.
        
        Returns:
            Dictionary with processed datasets ready for export
        """
        if self._processed_for_export is None:
            # Format dates as strings for CSV export consistency
            date_strings = self.raw_data.index.strftime('%Y-%m-%d')
            
            # 1. Raw price data (with string dates)
            price_data = self.raw_data.copy()
            price_data.index = date_strings
            
            # 2. Daily returns as percentage
            daily_returns = self.get_daily_returns(as_percentage=True)
            daily_returns.index = daily_returns.index.strftime('%Y-%m-%d')
            
            # 3. Cumulative returns as percentage  
            cumulative_returns = self.get_cumulative_returns(as_percentage=True)
            cumulative_returns.index = cumulative_returns.index.strftime('%Y-%m-%d')
            
            # 4. Correlation matrix (using daily returns, not percentage)
            correlation_matrix = self.get_daily_returns(as_percentage=False).corr()
            
            self._processed_for_export = {
                'price_data': price_data,
                'daily_returns': daily_returns,
                'cumulative_returns': cumulative_returns,
                'correlation_matrix': correlation_matrix
            }
            
            logger.info("Processed all export datasets consistently")
        
        return self._processed_for_export.copy()
    
    def get_data_for_ffn(self) -> pd.DataFrame:
        """
        Get data formatted for FFN analysis (original format with DatetimeIndex).
        
        Returns:
            DataFrame ready for FFN calc_stats()
        """
        return self.raw_data.copy()
    
    def get_data_for_charts(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get data formatted for chart generation.
        
        Returns:
            Tuple of (raw_data, cumulative_returns) with DatetimeIndex preserved
        """
        return self.raw_data.copy(), self.get_cumulative_returns(as_percentage=False)
    
    def get_summary_info(self) -> Dict:
        """Get summary information about the processed data."""
        # Get the actual date range used for calculations (post-preprocessing)
        daily_returns = self.get_daily_returns(as_percentage=False)
        
        return {
            'raw_start_date': self.raw_data.index[0],
            'raw_end_date': self.raw_data.index[-1],
            'effective_start_date': daily_returns.index[0],
            'effective_end_date': daily_returns.index[-1],
            'raw_trading_days': len(self.raw_data),
            'effective_trading_days': len(daily_returns),
            'symbols': list(self.raw_data.columns),
            'first_prices': self.raw_data.iloc[0].round(2).to_dict(),
            'last_prices': self.raw_data.iloc[-1].round(2).to_dict(),
            'has_duplicates': self.raw_data.index.duplicated().any(),
            'has_missing_values': self.raw_data.isna().any().any()
        }
    
    # Performance Metrics Functions - QuantStats Compatible
    def _prepare_returns_quantstats_style(self, returns: pd.Series, rf: float = 0.0, periods: int = 365) -> pd.Series:
        """
        Apply QuantStats-style preprocessing to returns data.
        Based on QuantStats _prepare_returns function with RF handling.
        """
        # Handle infinities (QuantStats approach)
        returns_processed = returns.replace([np.inf, -np.inf], float("NaN"))
        
        # Fill NaN with 0 (QuantStats approach)
        returns_processed = returns_processed.fillna(0)
        
        # Apply RF subtraction if > 0 (QuantStats approach)
        if rf > 0:
            daily_rf = np.power(1 + rf, 1.0 / periods) - 1.0
            returns_processed = returns_processed - daily_rf
        
        return returns_processed
    
    def compute_total_return(self, returns: pd.Series) -> float:
        """
        Compounded Total Return: (1 + r1) * (1 + r2) * ... * (1 + rn) - 1
        QuantStats compatible calculation with proper preprocessing
        """
        # Apply QuantStats preprocessing to the returns (no RF for total return)
        returns_processed = self._prepare_returns_quantstats_style(returns, rf=0.0)
        if len(returns_processed) == 0:
            return np.nan
        return (returns_processed + 1).prod() - 1

    def compute_cagr(self, returns: pd.Series) -> float:
        """
        CAGR using fractional years between first and last valid date
        QuantStats compatible calculation using 365.25 day year
        """
        # Apply QuantStats preprocessing to the returns (no RF for CAGR)
        returns_processed = self._prepare_returns_quantstats_style(returns, rf=0.0)
        if len(returns_processed) < 2:
            return np.nan

        delta_seconds = (returns_processed.index[-1] - returns_processed.index[0]).total_seconds()
        years = delta_seconds / (365.25 * 24 * 60 * 60)
        if years <= 0:
            return np.nan

        total_return_factor = (returns_processed + 1).prod()
        if total_return_factor <= 0:
            return np.nan
        return total_return_factor ** (1 / years) - 1

    def compute_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        Annualized Sharpe Ratio - QuantStats compatible
        Uses 365 periods per year and matches QuantStats preprocessing order
        """
        periods_per_year = 365  # QuantStats default
        # Apply QuantStats preprocessing WITH RF subtraction (matching their order)
        excess_returns = self._prepare_returns_quantstats_style(returns, rf=risk_free_rate, periods=periods_per_year)
        if len(excess_returns) < 2:
            return np.nan
        
        # Debug information
        symbol_name = returns.name if hasattr(returns, 'name') else 'Unknown'
        
        # Calculate "Time in Market" like QuantStats (exclude very small returns as proxy)
        non_zero_returns = excess_returns[abs(excess_returns) > 1e-8]
        time_in_market_pct = len(non_zero_returns) / len(excess_returns) * 100
        
        logger.info(f"Sharpe calculation for {symbol_name}:")
        logger.info(f"  Total sample size: {len(excess_returns)}")
        logger.info(f"  Non-zero returns: {len(non_zero_returns)}")
        logger.info(f"  Time in Market: {time_in_market_pct:.1f}%")
        logger.info(f"  Mean return: {excess_returns.mean():.8f}")
        logger.info(f"  Std dev: {excess_returns.std(ddof=1):.8f}")
        logger.info(f"  Annualization factor: {np.sqrt(periods_per_year):.6f}")
        
        std_dev = excess_returns.std(ddof=1)
        
        if std_dev == 0 or np.isnan(std_dev):
            return np.nan
        
        result = excess_returns.mean() / std_dev * np.sqrt(periods_per_year)
        logger.info(f"  Final Sharpe: {result:.6f}")
        return result

    def compute_sortino(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        Annualized Sortino Ratio - QuantStats compatible
        Matches QuantStats preprocessing order and methodology exactly
        """
        periods_per_year = 365  # QuantStats default
        # Apply QuantStats preprocessing WITH RF subtraction (matching their order)
        excess_returns = self._prepare_returns_quantstats_style(returns, rf=risk_free_rate, periods=periods_per_year)
        if len(excess_returns) < 2:
            return np.nan
        
        downside = excess_returns[excess_returns < 0]
        
        if len(downside) == 0:
            # No downside returns - handle this case
            return np.nan
        
        # Debug information
        symbol_name = returns.name if hasattr(returns, 'name') else 'Unknown'
        logger.info(f"Sortino calculation for {symbol_name}:")
        logger.info(f"  Sample size: {len(excess_returns)}")
        logger.info(f"  Downside observations: {len(downside)}")
        logger.info(f"  Mean return: {excess_returns.mean():.8f}")
        logger.info(f"  Downside deviation: {np.sqrt((downside ** 2).sum() / len(excess_returns)):.8f}")
        
        # QuantStats methodology: Use len(all_returns) in denominator, not len(downside_returns)
        downside_deviation = np.sqrt((downside ** 2).sum() / len(excess_returns))
        
        if downside_deviation == 0 or np.isnan(downside_deviation):
            return np.nan
        
        result = excess_returns.mean() / downside_deviation * np.sqrt(periods_per_year)
        logger.info(f"  Final Sortino: {result:.6f}")
        return result
    
    def get_performance_metrics(self, risk_free_rate: float = 0.0) -> Dict[str, Dict[str, float]]:
        """
        Calculate all QuantStats-compatible performance metrics for each symbol.
        
        Args:
            risk_free_rate: Annual risk-free rate as decimal (e.g., 0.05 for 5%)
        
        Returns:
            Dictionary with metrics for each symbol
        """
        daily_returns = self.get_daily_returns(as_percentage=False)
        metrics = {}
        
        for symbol in daily_returns.columns:
            symbol_returns = daily_returns[symbol]
            
            # Calculate all metrics using QuantStats-compatible methods
            metrics[symbol] = {
                'Total Return': self.compute_total_return(symbol_returns),
                'CAGR': self.compute_cagr(symbol_returns),
                'Sharpe Ratio': self.compute_sharpe(symbol_returns, risk_free_rate),
                'Sortino Ratio': self.compute_sortino(symbol_returns, risk_free_rate)
            }
        
        logger.info(f"Calculated QuantStats-compatible performance metrics for {len(metrics)} symbols")
        return metrics 