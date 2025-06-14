"""
Report Generation Module for FFN Portfolio Analysis

This module contains all report generation functions including:
- HTML report generation with comprehensive analytics
- CSV export functionality  
- URL construction for different environments
- Performance statistics and drawdown analysis
"""

import os
import pandas as pd
import numpy as np
import ffn
from datetime import datetime
import logging
import io
from contextlib import redirect_stdout

# Import the centralized data processor
from scripts.data_processor import DataProcessor

# Get logger
logger = logging.getLogger(__name__)

# These will be imported from main (environment variables)
IS_LOCAL_DEVELOPMENT = None
BASE_URL_FOR_REPORTS = None
REPORTS_DIR = os.path.join('static', 'reports')


def set_environment_config(is_local_dev, base_url_for_reports, reports_dir):
    """Set environment configuration for report generation."""
    global IS_LOCAL_DEVELOPMENT, BASE_URL_FOR_REPORTS, REPORTS_DIR
    IS_LOCAL_DEVELOPMENT = is_local_dev
    BASE_URL_FOR_REPORTS = base_url_for_reports
    REPORTS_DIR = reports_dir


def construct_report_url(filename: str) -> str:
    """Construct the appropriate URL for report files based on environment."""
    logger.info(f"construct_report_url called with filename: {filename}")
    logger.info(f"IS_LOCAL_DEVELOPMENT: {IS_LOCAL_DEVELOPMENT}")
    logger.info(f"BASE_URL_FOR_REPORTS: '{BASE_URL_FOR_REPORTS}'")
    
    if IS_LOCAL_DEVELOPMENT:
        url = f"/static/reports/{filename}"
        logger.info(f"Using local development URL: {url}")
        return url
    else:
        # For remote deployment, BASE_URL_FOR_REPORTS must be provided
        if not BASE_URL_FOR_REPORTS:
            logger.error("BASE_URL_FOR_REPORTS environment variable is required for remote deployment but not provided")
            raise ValueError(
                "Configuration Error: BASE_URL_FOR_REPORTS environment variable is required for remote deployment. "
                "Please set BASE_URL_FOR_REPORTS to your deployment URL (e.g., https://yourdomain.com/)"
            )
        
        # Ensure BASE_URL_FOR_REPORTS ends with a slash
        base_url = BASE_URL_FOR_REPORTS.rstrip('/') + '/'
        url = f"{base_url}static/reports/{filename}"
        logger.info(f"Using remote deployment URL: {url}")
        return url


def generate_csv_exports(data_processor: DataProcessor, perf, report_filename_base):
    """Generate multiple CSV files with different datasets using centralized processor."""
    csv_files = {}
    
    try:
        # Get all processed datasets from the centralized processor
        processed_data = data_processor.get_processed_for_export()
        
        # 1. Raw Price Data (now correctly named as "processed" since it has transformations)
        price_data = processed_data['price_data']
        price_filename = f"{report_filename_base}_processed_price_data.csv"
        price_path = os.path.join(REPORTS_DIR, price_filename)
        price_data.to_csv(price_path)
        csv_files['price_data'] = price_filename
        logger.info(f"Exported processed price data: {price_data.shape}")
        
        # 2. Daily Returns Data (as percentage)
        daily_returns = processed_data['daily_returns']
        returns_filename = f"{report_filename_base}_daily_returns.csv"
        returns_path = os.path.join(REPORTS_DIR, returns_filename)
        daily_returns.to_csv(returns_path)
        csv_files['daily_returns'] = returns_filename
        logger.info(f"Exported daily returns: {daily_returns.shape}")
        
        # 3. Cumulative Returns Data (as percentage)
        cumulative_returns = processed_data['cumulative_returns']
        cumulative_filename = f"{report_filename_base}_cumulative_returns.csv"
        cumulative_path = os.path.join(REPORTS_DIR, cumulative_filename)
        cumulative_returns.to_csv(cumulative_path)
        csv_files['cumulative_returns'] = cumulative_filename
        logger.info(f"Exported cumulative returns: {cumulative_returns.shape}")
        
        # 4. Correlation Matrix
        correlation_matrix = processed_data['correlation_matrix']
        correlation_filename = f"{report_filename_base}_correlation_matrix.csv"
        correlation_path = os.path.join(REPORTS_DIR, correlation_filename)
        correlation_matrix.to_csv(correlation_path)
        csv_files['correlation_matrix'] = correlation_filename
        logger.info(f"Exported correlation matrix: {correlation_matrix.shape}")
        
        # 5. Summary Statistics Data (from FFN)
        summary_stats = {}
        ffn_data = data_processor.get_data_for_ffn()
        for symbol in ffn_data.columns:
            stats = perf[symbol].stats
            summary_stats[symbol] = stats
        
        summary_df = pd.DataFrame(summary_stats)
        summary_filename = f"{report_filename_base}_summary_statistics.csv"
        summary_path = os.path.join(REPORTS_DIR, summary_filename)
        summary_df.to_csv(summary_path)
        csv_files['summary_statistics'] = summary_filename
        logger.info(f"Exported summary statistics: {summary_df.shape}")
        
        # 6. Monthly Returns Data (if available from FFN)
        try:
            monthly_data = {}
            for symbol in ffn_data.columns:
                if hasattr(perf[symbol], 'return_table') and len(perf[symbol].return_table) > 0:
                    monthly_data[symbol] = perf[symbol].return_table
            
            if monthly_data:
                # Convert to a more readable format
                monthly_df_list = []
                for symbol, monthly_table in monthly_data.items():
                    for year, months in monthly_table.items():
                        for month, return_val in months.items():
                            if month != 13:  # Skip YTD column
                                monthly_df_list.append({
                                    'Symbol': symbol,
                                    'Year': year,
                                    'Month': month,
                                    'Return_%': return_val * 100 if not pd.isna(return_val) else np.nan
                                })
                
                if monthly_df_list:
                    monthly_df = pd.DataFrame(monthly_df_list)
                    monthly_filename = f"{report_filename_base}_monthly_returns.csv"
                    monthly_path = os.path.join(REPORTS_DIR, monthly_filename)
                    monthly_df.to_csv(monthly_path, index=False)
                    csv_files['monthly_returns'] = monthly_filename
                    logger.info(f"Exported monthly returns: {monthly_df.shape}")
        except Exception as e:
            logger.warning(f"Could not generate monthly returns CSV: {str(e)}")
        
        logger.info(f"Generated {len(csv_files)} CSV files successfully")
        return csv_files
        
    except Exception as e:
        logger.error(f"Error generating CSV exports: {str(e)}")
        return {}


def generate_perf_report(data, risk_free_rate=0.0, chart_generator_functions=None):
    """Generate a performance report using centralized data processing and FFN's GroupStats."""
    try:
        # Import chart generation functions
        if chart_generator_functions is None:
            from scripts.chart_generator import (
                generate_cumulative_returns_chart,
                generate_plotly_cumulative_returns_chart,
                generate_cagr_bar_chart
            )
        else:
            generate_cumulative_returns_chart = chart_generator_functions['cumulative']
            generate_plotly_cumulative_returns_chart = chart_generator_functions['plotly']
            generate_cagr_bar_chart = chart_generator_functions['cagr']
        
        # STEP 2 IMPLEMENTATION: Use centralized data processor
        logger.info("Initializing centralized data processor...")
        data_processor = DataProcessor(data)
        
        # Get data for FFN analysis (preserves DatetimeIndex)
        ffn_data = data_processor.get_data_for_ffn()
        
        # Calculate performance statistics using calc_stats()
        logger.info("Calculating FFN performance statistics...")
        perf = ffn_data.calc_stats()
        
        # Set the risk-free rate on the GroupStats object
        rf_decimal = risk_free_rate / 100.0
        perf.set_riskfree_rate(rf_decimal)
        logger.info(f"Set risk-free rate to {risk_free_rate}% ({rf_decimal})")
        
        # Generate a timestamp for the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a filename for the report
        symbols_text = '-'.join(ffn_data.columns).replace(' ', '_')
        filename = f"report_{symbols_text}_{timestamp}.html"
        report_filename_base = f"report_{symbols_text}_{timestamp}"
        
        # Get data for chart generation (preserves DatetimeIndex for charts)
        chart_raw_data, chart_cumulative_data = data_processor.get_data_for_charts()
        
        # Generate the cumulative returns chart
        chart_filename = generate_cumulative_returns_chart(chart_raw_data, report_filename_base)
        chart_url = None
        if chart_filename:
            if IS_LOCAL_DEVELOPMENT:
                chart_url = f"/static/reports/{chart_filename}"
            else:
                base_url = BASE_URL_FOR_REPORTS.rstrip('/') + '/' if BASE_URL_FOR_REPORTS else ""
                chart_url = f"{base_url}static/reports/{chart_filename}"
        
        # Generate the interactive Plotly cumulative returns chart
        plotly_chart_filename = generate_plotly_cumulative_returns_chart(chart_raw_data, report_filename_base)
        plotly_chart_url = None
        if plotly_chart_filename:
            if IS_LOCAL_DEVELOPMENT:
                plotly_chart_url = f"/static/reports/{plotly_chart_filename}"
            else:
                base_url = BASE_URL_FOR_REPORTS.rstrip('/') + '/' if BASE_URL_FOR_REPORTS else ""
                plotly_chart_url = f"{base_url}static/reports/{plotly_chart_filename}"
        
        # Generate the CAGR bar chart (keep as matplotlib)
        cagr_chart_filename = generate_cagr_bar_chart(chart_raw_data, report_filename_base)
        cagr_chart_url = None
        if cagr_chart_filename:
            if IS_LOCAL_DEVELOPMENT:
                cagr_chart_url = f"/static/reports/{cagr_chart_filename}"
            else:
                base_url = BASE_URL_FOR_REPORTS.rstrip('/') + '/' if BASE_URL_FOR_REPORTS else ""
                cagr_chart_url = f"{base_url}static/reports/{cagr_chart_filename}"
        
        # Generate CSV exports using centralized processor
        logger.info("Generating CSV exports with centralized processor...")
        csv_files = generate_csv_exports(data_processor, perf, report_filename_base)
        csv_urls = {}
        for csv_type, csv_filename in csv_files.items():
            if IS_LOCAL_DEVELOPMENT:
                csv_urls[csv_type] = f"/static/reports/{csv_filename}"
            else:
                base_url = BASE_URL_FOR_REPORTS.rstrip('/') + '/' if BASE_URL_FOR_REPORTS else ""
                csv_urls[csv_type] = f"{base_url}static/reports/{csv_filename}"
        
        # Full path for the report
        report_path = os.path.join(REPORTS_DIR, filename)
        
        # Generate HTML report with tabular performance data
        _generate_html_report(report_path, data_processor, perf, risk_free_rate, chart_url, plotly_chart_url, cagr_chart_url)
        
        html_url = construct_report_url(filename)
        logger.info(f"Report generation completed successfully: {html_url}")
        return html_url, csv_urls
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise ValueError(f"Error generating report: {str(e)}")


def _generate_html_report(report_path, data_processor: DataProcessor, perf, risk_free_rate, chart_url, plotly_chart_url, cagr_chart_url):
    """Generate the HTML report file using centralized data processor (internal function)."""
    with open(report_path, 'w', encoding='utf-8') as f:
        # Write HTML header
        f.write('<!DOCTYPE html>\n')
        f.write('<html lang="en">\n')
        f.write('<head>\n')
        f.write('    <meta charset="UTF-8">\n')
        f.write('    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
        f.write('    <title>Security Performance Report</title>\n')
        f.write('    <link href="https://cdn.tailwindcss.com" rel="stylesheet">\n')
        f.write('    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">\n')
        
        # Write CSS styles
        _write_css_styles(f)
        
        f.write('</head>\n')
        f.write('<body class="bg-gray-50">\n')
        
        # Write header
        _write_header(f)
        
        f.write('    <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px 32px 24px;">\n')
        
        # Write main content sections
        _write_title_section(f, data_processor, risk_free_rate)
        _write_data_summary(f, data_processor, risk_free_rate)
        _write_charts_and_tables(f, data_processor, perf, chart_url, plotly_chart_url, cagr_chart_url, risk_free_rate)
        
        # Write footer
        _write_footer(f)
        
        f.write('    </div>\n')
        f.write('</body>\n')
        f.write('</html>\n')


def _write_css_styles(f):
    """Write CSS styles to the HTML file."""
    f.write('    <style>\n')
    f.write('        * {\n')
    f.write('            font-weight: normal !important;\n')
    f.write('        }\n')
    f.write('        .report-table {\n')
    f.write('            background-image: linear-gradient(#e5e7eb 1px, transparent 1px),\n')
    f.write('                              linear-gradient(90deg, #e5e7eb 1px, transparent 1px);\n')
    f.write('            background-size: 100% 1.5em, 25% 100%;\n')
    f.write('            background-color: white;\n')
    f.write('            font-size: 1.1em;\n')
    f.write('            color: #374151;\n')
    f.write('            font-weight: normal;\n')
    f.write('        }\n')
    f.write('        .main-header {\n')
    f.write('            color: #1e40af;\n')
    f.write('            font-weight: 800 !important;\n')
    f.write('        }\n')
    f.write('        .section-header {\n')
    f.write('            color: #3b82f6;\n')
    f.write('            font-weight: 700 !important;\n')
    f.write('        }\n')
    f.write('        body {\n')
    f.write('            color: #374151;\n')
    f.write('            font-weight: normal;\n')
    f.write('            margin: 0 !important;\n')
    f.write('            padding-top: 0 !important;\n')
    f.write('        }\n')
    f.write('        h1, h2, h3, h4, h5, h6 {\n')
    f.write('            font-weight: normal !important;\n')
    f.write('        }\n')
    f.write('        h1.main-header, h2.section-header, h3.section-header {\n')
    f.write('            font-weight: 700 !important;\n')
    f.write('        }\n')
    f.write('        strong {\n')
    f.write('            font-weight: normal !important;\n')
    f.write('        }\n')
    f.write('        .chart-container {\n')
    f.write('            position: sticky;\n')
    f.write('            top: 20px;\n')
    f.write('        }\n')
    f.write('        .chart-img {\n')
    f.write('            width: 60%;\n')
    f.write('            height: auto;\n')
    f.write('            border-radius: 8px;\n')
    f.write('            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);\n')
    f.write('            max-width: 100%;\n')
    f.write('        }\n')
    f.write('    </style>\n')


def _write_header(f):
    """Write the header section to the HTML file."""
    f.write('    <header style="\n')
    f.write('        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);\n')
    f.write('        color: white;\n')
    f.write('        padding: 8px 0;\n')
    f.write('        margin: 0;\n')
    f.write('        font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;\n')
    f.write('        box-shadow: 0 2px 4px rgba(0,0,0,0.1);\n')
    f.write('        margin-bottom: 20px;\n')
    f.write('    ">\n')
    f.write('        <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; justify-content: space-between; align-items: center;">\n')
    f.write('            <div style="display: flex; align-items: center; gap: 12px; font-size: 18px; font-weight: 900;">\n')
    f.write('                <!-- Icons first -->\n')
    f.write('                <div style="display: flex; align-items: center; gap: 3px; font-size: 20px;">\n')
    f.write('                    <span style="font-family: \'Times New Roman\', serif; font-style: italic; font-weight: 700;">f(x)</span>\n')
    f.write('                    <span style="font-family: monospace; font-weight: 700; letter-spacing: -1px;">&lt;/&gt;</span>\n')
    f.write('                </div>\n')
    f.write('                <!-- REX text with full hyperlink -->\n')
    f.write('                <a href="https://rex.tigzig.com" target="_blank" rel="noopener noreferrer" style="color: #fbbf24; text-decoration: none; font-weight: 900;">\n')
    f.write('                    REX <span style="color: #ffffff; font-weight: 900;">: AI Co-Analyst</span>\n')
    f.write('                </a>\n')
    f.write('                <span style="color: #ffffff; font-weight: 700;">- Portfolio Analytics</span>\n')
    f.write('            </div>\n')
    f.write('        </div>\n')
    f.write('    </header>\n')


def _write_title_section(f, data_processor, risk_free_rate):
    """Write the title section to the HTML file."""
    f.write('        <div class="mb-6">\n')
    f.write('            <h1 class="text-3xl main-header" style="margin-bottom: 4px;">Security Performance Report</h1>\n')
    f.write('            <p style="font-size: 16px; color: #6b7280; margin-bottom: 8px; line-height: 1.4; margin-top: 0;">\n')
    f.write('                Generated with independent calculations (NEW) and open-source \n')
    f.write('                <a href="https://github.com/pmorissette/ffn" target="_blank" style="color: #1d4ed8; text-decoration: none; font-weight: 500;">FFN library</a>\n')
    f.write('            </p>\n')
    f.write('        </div>\n')


def _write_data_summary(f, data_processor, risk_free_rate):
    """Write the data summary section to the HTML file."""
    # Get summary info with effective date ranges
    summary_info = data_processor.get_summary_info()
    
    f.write('        <div class="mb-12">\n')
    f.write('            <h2 class="text-2xl mb-4 section-header">Data Summary</h2>\n')
    f.write('            <div class="bg-white rounded-lg shadow overflow-x-auto">\n')
    f.write('                <pre class="p-4 font-mono text-sm report-table">\n')
    
    # Show the effective date range (what's actually used in calculations)
    f.write(f'Analysis Period: {summary_info["effective_start_date"].strftime("%Y-%m-%d")} to {summary_info["effective_end_date"].strftime("%Y-%m-%d")}\n')
    f.write(f'Trading Days (Analysis): {summary_info["effective_trading_days"]}\n')
    
    # Show raw data range for transparency
    f.write(f'Raw Data Period: {summary_info["raw_start_date"].strftime("%Y-%m-%d")} to {summary_info["raw_end_date"].strftime("%Y-%m-%d")}\n')
    f.write(f'Trading Days (Raw): {summary_info["raw_trading_days"]}\n')
    
    f.write(f'Risk-Free Rate: {risk_free_rate:.2f}% (annual)\n')
    f.write(f'First Prices: {summary_info["first_prices"]}\n')
    f.write(f'Last Prices: {summary_info["last_prices"]}\n')
    
    # Add note if there's a difference
    if summary_info["raw_trading_days"] != summary_info["effective_trading_days"]:
        f.write('\nNote: Analysis period may differ from raw data due to QuantStats-compatible preprocessing\n')
    
    f.write('                </pre>\n')
    f.write('            </div>\n')
    f.write('        </div>\n')


def _write_charts_and_tables(f, data_processor, perf, chart_url, plotly_chart_url, cagr_chart_url, risk_free_rate):
    """Write the charts and tables section to the HTML file."""
    # Create two-column layout
    f.write('        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">\n')
    
    # Left column: Charts (1/3 width on large screens)
    f.write('            <div class="lg:col-span-1">\n')
    f.write('                <div class="chart-container">\n')
    
    # Chart switching functionality
    _write_chart_switching(f, chart_url, plotly_chart_url, cagr_chart_url)
    
    f.write('                </div>\n')
    f.write('            </div>\n')
    
    # Right column: Tables (2/3 width on large screens)
    f.write('            <div class="lg:col-span-2">\n')
    
    # Custom Performance Metrics
    _write_custom_performance_metrics(f, data_processor, risk_free_rate)
    
    # Drawdown Analysis
    _write_drawdown_analysis(f, data_processor.raw_data)
    
    # Monthly Returns
    _write_monthly_returns(f, data_processor.raw_data, perf)
    
    f.write('            </div>\n')
    f.write('        </div>\n')


def _write_chart_switching(f, chart_url, plotly_chart_url, cagr_chart_url):
    """Write the chart switching functionality to the HTML file."""
    f.write('                    <div class="mb-6">\n')
    f.write('                        <!-- All Chart Buttons in One Row -->\n')
    f.write('                        <div style="display: flex; align-items: center; margin-bottom: 24px;">\n')
    f.write('                            <!-- Left Side: Chart Selection Buttons -->\n')
    f.write('                            <div style="display: flex; gap: 12px;">\n')
    f.write('                                <button id="showFixedChart" onclick="showChart(\'fixed\')" \n')
    f.write('                                        style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; font-size: 14px; font-weight: 500; border-radius: 8px; border: 1px solid #3b82f6; background-color: #3b82f6; color: white; cursor: pointer; transition: all 0.15s ease; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">\n')
    f.write('                                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">\n')
    f.write('                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>\n')
    f.write('                                    </svg>\n')
    f.write('                                    Fixed Chart\n')
    f.write('                                </button>\n')
    f.write('                                <button id="showInteractiveChart" onclick="showChart(\'interactive\')" \n')
    f.write('                                        style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; font-size: 14px; font-weight: 500; border-radius: 8px; border: 1px solid #d1d5db; background-color: white; color: #374151; cursor: pointer; transition: all 0.15s ease; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">\n')
    f.write('                                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">\n')
    f.write('                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>\n')
    f.write('                                    </svg>\n')
    f.write('                                    Interactive Chart\n')
    f.write('                                </button>\n')
    f.write('                            </div>\n')
    f.write('                            <!-- Maximize Button with closer spacing -->\n')
    f.write('                            <button id="maximizeBtn" onclick="maximizeChart()" \n')
    f.write('                                    style="display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; font-size: 13px; font-weight: 500; border-radius: 6px; background-color: #059669; color: white; border: 1px solid #059669; cursor: pointer; transition: all 0.15s ease; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); margin-left: 24px;" \n')
    f.write('                                    title="Open in full view">\n')
    f.write('                                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">\n')
    f.write('                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>\n')
    f.write('                                </svg>\n')
    f.write('                                Maximize (opens in new window)\n')
    f.write('                            </button>\n')
    f.write('                        </div>\n')
    
    # Chart container without maximize button (now it's above)
    f.write('                        <div id="chartContainer" class="bg-white rounded-lg shadow-lg border-2 border-gray-200 p-4" style="min-height: 500px;">\n')
    
    # Charts
    if chart_url:
        f.write('                            <div id="fixedChart" class="chart-display">\n')
        f.write(f'                                <img src="{chart_url}" alt="Fixed Cumulative Returns Chart" class="chart-img" style="width: 100%; height: auto; max-width: 800px;">\n')
        f.write('                            </div>\n')
    
    if plotly_chart_url:
        f.write('                            <div id="interactiveChart" class="chart-display" style="display: none;">\n')
        f.write(f'                                <iframe src="{plotly_chart_url}" width="100%" height="440px" frameborder="0" style="border-radius: 8px; overflow: hidden;"></iframe>\n')
        f.write('                            </div>\n')
    
    if not chart_url and not plotly_chart_url:
        f.write('                            <div class="chart-display">\n')
        f.write('                                <p class="text-gray-500 text-center py-8">Chart generation failed</p>\n')
        f.write('                            </div>\n')
    
    f.write('                        </div>\n')
    f.write('                    </div>\n')
    
    # CAGR Bar Chart (separate, always visible)
    if cagr_chart_url:
        f.write('                    <div class="bg-white rounded-lg shadow p-4 mb-6">\n')
        f.write(f'                        <img src="{cagr_chart_url}" alt="CAGR Bar Chart" class="chart-img" style="width: 80%; height: auto; max-width: 600px;">\n')
        f.write('                    </div>\n')
    
    # Add JavaScript for chart switching
    _write_chart_javascript(f, chart_url, plotly_chart_url)


def _write_chart_javascript(f, chart_url, plotly_chart_url):
    """Write the JavaScript for chart switching functionality."""
    f.write('                    <script>\n')
    f.write('                        let currentChart = "fixed";\n')
    f.write('                        let fixedChartUrl = "";\n')
    f.write('                        let interactiveChartUrl = "";\n')
    f.write('                        \n')
    
    # Set URLs based on what's available
    if chart_url:
        f.write(f'                        fixedChartUrl = "{chart_url}";\n')
    if plotly_chart_url:
        f.write(f'                        interactiveChartUrl = "{plotly_chart_url}";\n')
    
    f.write('                        \n')
    f.write('                        function showChart(chartType) {\n')
    f.write('                            currentChart = chartType;\n')
    f.write('                            const fixedChart = document.getElementById("fixedChart");\n')
    f.write('                            const interactiveChart = document.getElementById("interactiveChart");\n')
    f.write('                            const fixedBtn = document.getElementById("showFixedChart");\n')
    f.write('                            const interactiveBtn = document.getElementById("showInteractiveChart");\n')
    f.write('                            \n')
    f.write('                            if (chartType === "fixed") {\n')
    f.write('                                if (fixedChart) fixedChart.style.display = "block";\n')
    f.write('                                if (interactiveChart) interactiveChart.style.display = "none";\n')
    f.write('                                fixedBtn.style.cssText = "display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; font-size: 14px; font-weight: 500; border-radius: 8px; border: 1px solid #3b82f6; background-color: #3b82f6; color: white; cursor: pointer; transition: all 0.15s ease; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);";\n')
    f.write('                                interactiveBtn.style.cssText = "display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; font-size: 14px; font-weight: 500; border-radius: 8px; border: 1px solid #d1d5db; background-color: white; color: #374151; cursor: pointer; transition: all 0.15s ease; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);";\n')
    f.write('                            } else {\n')
    f.write('                                if (fixedChart) fixedChart.style.display = "none";\n')
    f.write('                                if (interactiveChart) interactiveChart.style.display = "block";\n')
    f.write('                                fixedBtn.style.cssText = "display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; font-size: 14px; font-weight: 500; border-radius: 8px; border: 1px solid #d1d5db; background-color: white; color: #374151; cursor: pointer; transition: all 0.15s ease; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);";\n')
    f.write('                                interactiveBtn.style.cssText = "display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; font-size: 14px; font-weight: 500; border-radius: 8px; border: 1px solid #3b82f6; background-color: #3b82f6; color: white; cursor: pointer; transition: all 0.15s ease; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);";\n')
    f.write('                            }\n')
    f.write('                        }\n')
    f.write('                        \n')
    f.write('                        function maximizeChart() {\n')
    f.write('                            if (currentChart === "fixed" && fixedChartUrl) {\n')
    f.write('                                window.open(fixedChartUrl, "_blank");\n')
    f.write('                            } else if (currentChart === "interactive" && interactiveChartUrl) {\n')
    f.write('                                window.open(interactiveChartUrl, "_blank");\n')
    f.write('                            }\n')
    f.write('                        }\n')
    f.write('                    </script>\n')


def _write_drawdown_analysis(f, data):
    """Write the drawdown analysis section."""
    f.write('                <div class="mb-12">\n')
    f.write('                    <h2 class="text-2xl mb-4 section-header">Drawdown Analysis (FFN)</h2>\n')
    
    for column in data.columns:
        try:
            # Calculate drawdown series
            drawdown_series = ffn.to_drawdown_series(data[column])
            logger.info(f"\nDrawdown series for {column}:")
            logger.info(drawdown_series.head())
            
            # Get detailed drawdown info
            drawdown_details = ffn.drawdown_details(drawdown_series)
            logger.info(f"\nDrawdown details for {column}:")
            logger.info(drawdown_details)
            
            if drawdown_details is not None and len(drawdown_details) > 0:
                # Sort by drawdown magnitude (ascending order since drawdowns are negative)
                drawdown_details = drawdown_details.sort_values('drawdown')
                
                f.write(f'                    <h3 class="text-xl mb-3 mt-6 section-header">{column}</h3>\n')
                f.write('                    <div class="bg-white rounded-lg shadow overflow-x-auto mb-6">\n')
                f.write('                        <pre class="p-4 font-mono text-sm report-table">\n')
                
                # Write header
                f.write('Start Date      End Date        Duration (Days)    Drawdown %\n')
                
                # Show top 10 drawdowns
                for _, row in drawdown_details.head(10).iterrows():
                    start_date = row["Start"].strftime("%Y-%m-%d")
                    end_date = row["End"].strftime("%Y-%m-%d")
                    duration = str(row["Length"]).rjust(8)  # Right align with more space
                    drawdown = f"{row['drawdown']*100:.2f}%".rjust(12)  # Right align with more space
                    
                    f.write(f'{start_date}    {end_date}    {duration}    {drawdown}\n')
                
                f.write('                        </pre>\n')
                f.write('                    </div>\n')
            else:
                logger.warning(f"No valid drawdown details for {column}")
                f.write(f'                    <h3 class="text-xl mb-3 mt-6 section-header">{column}</h3>\n')
                f.write('                    <div class="bg-white rounded-lg shadow overflow-x-auto mb-6">\n')
                f.write('                        <pre class="p-4 font-mono text-sm report-table">No significant drawdowns found.</pre>\n')
                f.write('                    </div>\n')
        
        except Exception as e:
            logger.error(f"Error processing drawdowns for {column}: {str(e)}")
            f.write(f'                    <h3 class="text-xl mb-3 mt-6 section-header">{column}</h3>\n')
            f.write('                    <div class="bg-white rounded-lg shadow overflow-x-auto mb-6">\n')
            f.write('                        <pre class="p-4 font-mono text-sm report-table">Error calculating drawdowns.</pre>\n')
            f.write('                    </div>\n')
    
    f.write('                </div>\n')


def _write_monthly_returns(f, data, perf):
    """Write the monthly returns section."""
    for symbol in data.columns:
        f.write('                <div class="mb-12">\n')
        f.write(f'                    <h2 class="text-2xl mb-4 section-header">Monthly Returns (FFN) - {symbol}</h2>\n')
        f.write('                    <div class="bg-white rounded-lg shadow overflow-x-auto">\n')
        f.write('                        <pre class="p-4 font-mono text-sm report-table">\n')
        
        monthly_output = io.StringIO()
        with redirect_stdout(monthly_output):
            perf[symbol].display_monthly_returns()
        f.write(monthly_output.getvalue())
        
        f.write('                        </pre>\n')
        f.write('                    </div>\n')
        f.write('                </div>\n')


def _write_footer(f):
    """Write the footer section."""
    # FFN disclaimer box
    f.write('        <div style="\n')
    f.write('            background: rgba(255,248,220,0.8);\n')
    f.write('            border: 1px solid #fbbf24;\n')
    f.write('            border-radius: 6px;\n')
    f.write('            padding: 12px;\n')
    f.write('            margin: 24px 0 16px 0;\n')
    f.write('            font-size: 13px;\n')
    f.write('            color: #92400e;\n')
    f.write('            font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;\n')
    f.write('            line-height: 1.5;\n')
    f.write('        ">\n')
    f.write('            <strong style="font-weight: bold !important;">Note:</strong> This report is for informational purposes only and should not be considered as investment advice. Metrics in this report are generated using Security Performance Report (SPR) implementations which use custom calculations as well as \n')
    f.write('            <a href="https://github.com/pmorissette/ffn" target="_blank" rel="noopener noreferrer" style="color: #1d4ed8; text-decoration: none; font-weight: 500;">FFN package</a> for some of the metrics. \n')
    f.write('            While some of the calculations metrics have been validated for consistency, users are encouraged to refer to \n')
    f.write('            <a href="https://github.com/amararun/shared-fastapi-mcp-ffn" target="_blank" rel="noopener noreferrer" style="color: #1d4ed8; text-decoration: none; font-weight: 500;">GitHub Repo for SPR</a>, the \n')
    f.write('            <a href="https://github.com/pmorissette/ffn" target="_blank" rel="noopener noreferrer" style="color: #1d4ed8; text-decoration: none; font-weight: 500;">official documentation for FFN</a> and \n')
    f.write('            <a href="https://github.com/Lumiwealth/quantstats_lumi" target="_blank" rel="noopener noreferrer" style="color: #1d4ed8; text-decoration: none; font-weight: 500;">QuantStats documentation</a> \n')
    f.write('            for full methodology details. For a methodology comparison between QuantStats and Security Performance Review implementations, users are advised to refer to this \n')
    f.write('            <a href="https://ffn.hosting.tigzig.com/static/docs/SPR_QS_METHODOLOGY.html" target="_blank" rel="noopener noreferrer" style="color: #1d4ed8; text-decoration: none; font-weight: 500;">methodology reference document</a>. \n')
    f.write('            Always validate outputs and interpret results in light of your specific analytical objectives.\n')
    f.write('        </div>\n')
    
    # Footer
    f.write('        <footer style="\n')
    f.write('            background: rgba(255,255,255,0.5);\n')
    f.write('            border-top: 1px solid #e0e7ff;\n')
    f.write('            padding: 8px 0;\n')
    f.write('            margin-top: 20px;\n')
    f.write('            font-size: 12px;\n')
    f.write('            color: #1e1b4b;\n')
    f.write('            font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;\n')
    f.write('            font-weight: normal;\n')
    f.write('        ">\n')
    f.write('            <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">\n')
    f.write('                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px;">\n')
    f.write('                    <div style="font-size: 12px; color: rgba(30, 27, 75, 0.7); font-weight: normal;">\n')
    f.write('                        Amar Harolikar <span style="margin: 0 6px; color: #c7d2fe;">•</span>\n')
    f.write('                        Specialist - Decision Sciences & Applied Generative AI <span style="margin: 0 6px; color: #c7d2fe;">•</span>\n')
    f.write('                        <a href="mailto:amar@harolikar.com" style="color: #4338ca; text-decoration: none; font-weight: normal;">amar@harolikar.com</a>\n')
    f.write('                    </div>\n')
    f.write('                    <div style="display: flex; align-items: center; gap: 16px; font-size: 12px;">\n')
    f.write('                        <a href="https://www.linkedin.com/in/amarharolikar" target="_blank" rel="noopener noreferrer"\n')
    f.write('                           style="color: #4338ca; text-decoration: none; font-weight: normal;">\n')
    f.write('                            LinkedIn\n')
    f.write('                        </a>\n')
    f.write('                        <a href="https://github.com/amararun" target="_blank" rel="noopener noreferrer"\n')
    f.write('                           style="color: #4338ca; text-decoration: none; font-weight: normal;">\n')
    f.write('                            GitHub\n')
    f.write('                        </a>\n')
    f.write('                        <a href="https://rex.tigzig.com" target="_blank" rel="noopener noreferrer"\n')
    f.write('                           style="color: #4338ca; text-decoration: none; font-weight: normal;">\n')
    f.write('                            rex.tigzig.com\n')
    f.write('                        </a>\n')
    f.write('                        <a href="https://tigzig.com" target="_blank" rel="noopener noreferrer"\n')
    f.write('                           style="color: #4338ca; text-decoration: none; font-weight: normal;">\n')
    f.write('                            tigzig.com\n')
    f.write('                        </a>\n')
    f.write('                    </div>\n')
    f.write('                </div>\n')
    f.write('            </div>\n')
    f.write('        </footer>\n')


def _write_custom_performance_metrics(f, data_processor, risk_free_rate):
    """Write the custom performance metrics section."""
    f.write('                <div class="mb-12">\n')
    f.write('                    <h2 class="text-2xl mb-4 section-header">Overall Returns and Risk Measures (NEW) </h2>\n')
    f.write('                    <div class="bg-white rounded-lg shadow overflow-x-auto">\n')
    f.write('                        <pre class="p-4 font-mono text-sm report-table">\n')
    
    # Get performance metrics from data processor
    rf_decimal = risk_free_rate / 100.0  # Convert percentage to decimal
    metrics = data_processor.get_performance_metrics(risk_free_rate=rf_decimal)
    
    # Format the metrics table
    if metrics:
        # Header
        symbols = list(metrics.keys())
        f.write('Metric                  ')
        for symbol in symbols:
            f.write(f'{symbol:<15} ')
        f.write('\n')
        f.write('-' * (24 + len(symbols) * 16) + '\n')
        
        # Metrics rows
        metric_names = ['Total Return', 'CAGR', 'Sharpe Ratio', 'Sortino Ratio']
        
        for metric_name in metric_names:
            f.write(f'{metric_name:<22}  ')
            for symbol in symbols:
                value = metrics[symbol][metric_name]
                if pd.isna(value):
                    formatted_value = 'N/A'
                elif metric_name in ['Total Return', 'CAGR']:
                    # Format as percentage
                    formatted_value = f'{value * 100:.2f}%'
                else:
                    # Format as ratio with 2 decimal places
                    formatted_value = f'{value:.2f}'
                f.write(f'{formatted_value:<15} ')
            f.write('\n')
        
        # Add a note about risk-free rate
        f.write('\n')
        f.write(f'Note: Sharpe and Sortino ratios calculated using {risk_free_rate:.2f}% annual risk-free rate\n')
    else:
        f.write('Error: Could not calculate performance metrics\n')
    
    f.write('                        </pre>\n')
    f.write('                    </div>\n')
    f.write('                </div>\n') 