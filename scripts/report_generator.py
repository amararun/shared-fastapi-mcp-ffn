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
import matplotlib.pyplot as plt
import seaborn as sns

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
                generate_cagr_bar_chart,
                generate_compound_performance_chart
            )
        else:
            generate_cumulative_returns_chart = chart_generator_functions['cumulative']
            generate_plotly_cumulative_returns_chart = chart_generator_functions['plotly']
            generate_cagr_bar_chart = chart_generator_functions['cagr']
            generate_compound_performance_chart = chart_generator_functions['compound']
        
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
        
        # Generate the compound performance chart (new addition)
        compound_chart_filename = generate_compound_performance_chart(chart_raw_data, data_processor, risk_free_rate, report_filename_base)
        compound_chart_url = None
        if compound_chart_filename:
            if IS_LOCAL_DEVELOPMENT:
                compound_chart_url = f"/static/reports/{compound_chart_filename}"
            else:
                base_url = BASE_URL_FOR_REPORTS.rstrip('/') + '/' if BASE_URL_FOR_REPORTS else ""
                compound_chart_url = f"{base_url}static/reports/{compound_chart_filename}"
        
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
        _generate_html_report(report_path, data_processor, perf, risk_free_rate, chart_url, plotly_chart_url, cagr_chart_url, compound_chart_url)
        
        html_url = construct_report_url(filename)
        logger.info(f"Report generation completed successfully: {html_url}")
        return html_url, csv_urls
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise ValueError(f"Error generating report: {str(e)}")


def _generate_html_report(report_path, data_processor: DataProcessor, perf, risk_free_rate, chart_url, plotly_chart_url, cagr_chart_url, compound_chart_url):
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
        _write_charts_and_tables(f, data_processor, perf, chart_url, plotly_chart_url, cagr_chart_url, compound_chart_url, risk_free_rate)
        
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
    f.write('        /* Override for table headers */\n')
    f.write('        .table-header-base, .metrics-table-row-label {\n')
    f.write('            font-weight: 600 !important;\n')
    f.write('        }\n')
    f.write('        .report-table {\n')
    f.write('            background-color: white;\n')
    f.write('            font-size: 1.0em;\n')
    f.write('            color: #374151;\n')
    f.write('            font-weight: normal;\n')
    f.write('        }\n')
    f.write('        .table-base {\n')
    f.write('            background-color: white;\n')
    f.write('            font-size: 1.0em;\n')
    f.write('            color: #374151;\n')
    f.write('            font-weight: normal;\n')
    f.write('            border-collapse: collapse;\n')
    f.write('            font-family: monospace;\n')
    f.write('        }\n')
    f.write('        .table-header-base {\n')
    f.write('            background-color: #dcfce7 !important;\n')  # Earlier green background
    f.write('            font-weight: 600 !important;\n')  # Increased font weight
    f.write('            border-bottom: 1px solid #60a5fa;\n')  # Nice thin blue border
    f.write('            padding: 4px 8px;\n')
    f.write('            font-size: 1.0em;\n')
    f.write('            color: #1e3a8a !important;\n')  # Stronger/heavier blue text color
    f.write('        }\n')
    f.write('        .table-cell-base {\n')
    f.write('            border-bottom: 1px solid #cbd5e1;\n')  # Slightly darker border
    f.write('            padding: 6px 12px;\n')  # Increased padding for better spacing
    f.write('            border-right: 1px solid #e2e8f0;\n')  # Subtle right border
    f.write('            font-size: 1.0em;\n')
    f.write('            color: #1f2937;\n')  # Darker text for better contrast
    f.write('            font-weight: normal;\n')
    f.write('            background-color: #fefefe;\n')  # Very subtle off-white background
    f.write('            transition: background-color 0.15s ease;\n')  # Smooth hover transition
    f.write('        }\n')
    f.write('        .table-cell-base:hover {\n')  # Add hover effect for interactivity
    f.write('            background-color: #f8fafc;\n')
    f.write('        }\n')
    f.write('        .table-row-alt {\n')  # Alternating row background
    f.write('            background-color: #f9fafb;\n')
    f.write('        }\n')
    f.write('        .table-row-alt:hover {\n')
    f.write('            background-color: #f1f5f9;\n')
    f.write('        }\n')
    f.write('        .main-header {\n')
    f.write('            color: #1e40af;\n')
    f.write('            font-weight: 800 !important;\n')
    f.write('        }\n')
    f.write('        .section-header {\n')
    f.write('            color: #1e3a8a;\n')
    f.write('            font-weight: 700 !important;\n')
    f.write('        }\n')
    f.write('        .body {\n')
    f.write('            color: #374151;\n')
    f.write('            font-weight: normal;\n')
    f.write('            margin: 0 !important;\n')
    f.write('            padding-top: 0 !important;\n')
    f.write('        }\n')
    f.write('        .h1, h2, h3, h4, h5, h6 {\n')
    f.write('            font-weight: normal !important;\n')
    f.write('        }\n')
    f.write('        .h1.main-header, h2.section-header, h3.section-header {\n')
    f.write('            font-weight: 700 !important;\n')
    f.write('        }\n')
    f.write('        .strong {\n')
    f.write('            font-weight: normal !important;\n')
    f.write('        }\n')
    f.write('        .chart-container {\n')
    f.write('            position: sticky;\n')
    f.write('            top: 20px;\n')
    f.write('        }\n')
    f.write('        .chart-img {\n')
    f.write('            width: 60%;\n')
    f.write('            height: auto;\n')
    f.write('            max-width: 100%;\n')
    f.write('            padding-left: 28px;\n')
    f.write('        }\n')
    f.write('        .data-summary-table {\n')
    f.write('            background-color: white;\n')
    f.write('            font-size: 1.0em;\n')
    f.write('            color: #374151;\n')
    f.write('            font-weight: normal;\n')
    f.write('            font-family: monospace;\n')
    f.write('            line-height: 1.4;\n')
    f.write('            white-space: pre-line;\n')
    f.write('        }\n')
    f.write('        .metrics-table {\n')
    f.write('            width: auto;\n')
    f.write('            max-width: 800px;\n')
    f.write('        }\n')
    f.write('        .metrics-table-header {\n')
    f.write('        }\n')
    f.write('        .metrics-table-cell {\n')
    f.write('        }\n')
    f.write('        .metrics-table-row-label {\n')
    f.write('            background-color: #dcfce7 !important;\n')  # Earlier green background (same as column headers)
    f.write('            font-weight: 600 !important;\n')  # Increased font weight
    f.write('            color: #1e3a8a !important;\n')  # Stronger/heavier blue text color
    f.write('            border-right: 1px solid #60a5fa;\n')  # Nice thin blue border (same as column headers)
    f.write('            text-align: left;\n')
    f.write('            padding: 6px 12px;\n')
    f.write('        }\n')
    f.write('        .drawdown-table {\n')
    f.write('            width: auto;\n')
    f.write('            max-width: 700px;\n')
    f.write('        }\n')
    f.write('        .drawdown-table-header {\n')
    f.write('        }\n')
    f.write('        .drawdown-table-cell {\n')
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
    f.write('                <!-- TIGZIG Quants full hyperlink in white -->\n')
    f.write('                <a href="https://app.tigzig.com" target="_blank" rel="noopener noreferrer" style="color: #ffffff; text-decoration: none; font-weight: 900;">\n')
    f.write('                    TIGZIG Quants\n')
    f.write('                </a>\n')
    f.write('            </div>\n')
    f.write('        </div>\n')
    f.write('    </header>\n')


def _write_title_section(f, data_processor, risk_free_rate):
    """Write the title section to the HTML file."""
    f.write('        <div class="mb-6">\n')
    f.write('            <h1 class="text-3xl main-header" style="margin-bottom: 8px;">Security Performance Report</h1>\n')
    f.write('        </div>\n')


def _write_data_summary(f, data_processor, risk_free_rate):
    """Write the data summary section as a compact single/two-line format."""
    # Get summary info with effective date ranges
    summary_info = data_processor.get_summary_info()
    
    # Use a compact paragraph format instead of table
    f.write('        <div style="margin-bottom: 16px; padding: 12px 16px; background-color: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 6px;">\n')
    
    # Main info line
    f.write('            <p style="margin: 0; font-size: 14px; color: #374151; line-height: 1.5;">\n')
    f.write(f'                <strong>Data Period:</strong> {summary_info["effective_start_date"].strftime("%d-%b-%Y")} to {summary_info["effective_end_date"].strftime("%d-%b-%Y")} ')
    f.write(f'({summary_info["effective_trading_days"]} trading days) • ')
    f.write(f'<strong>Risk-Free Rate:</strong> {risk_free_rate:.2f}% (annual)')
    f.write('            </p>\n')
    
    # Notes section - always show (includes generation info and data processing info if applicable)
    f.write('            <p style="margin: 4px 0 0 0; font-size: 12px; color: #6b7280; font-style: italic;">\n')
    f.write('                Generated with independent calculations (NEW) and open-source FFN library')
    
    # Add raw data info if there's a difference
    if summary_info["raw_trading_days"] != summary_info["effective_trading_days"]:
        f.write(f' • Raw data: {summary_info["raw_trading_days"]} trading days ')
        f.write(f'({summary_info["raw_start_date"].strftime("%d-%b-%Y")} to {summary_info["raw_end_date"].strftime("%d-%b-%Y")}) ')
        f.write('- Analysis period adjusted for date alignment')
    
    f.write('\n            </p>\n')
    
    f.write('        </div>\n')


def _write_charts_and_tables(f, data_processor, perf, chart_url, plotly_chart_url, cagr_chart_url, compound_chart_url, risk_free_rate):
    """Write the charts and tables section to the HTML file."""
    # Create two-column layout
    f.write('        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">\n')
    
    # Left column: Charts (1/3 width on large screens)
    f.write('            <div class="lg:col-span-1">\n')
    f.write('                <div class="chart-container">\n')
    
    # Chart switching functionality
    _write_chart_switching(f, chart_url, plotly_chart_url, cagr_chart_url, compound_chart_url)
    
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


def _write_chart_switching(f, chart_url, plotly_chart_url, cagr_chart_url, compound_chart_url):
    """Write the chart switching functionality to the HTML file."""
    f.write('                    <div>\n')
    f.write('                        <!-- Chart Maximize Buttons -->\n')
    f.write('                        <div style="display: flex; align-items: center; margin-bottom: 24px;">\n')
    f.write('                            <!-- Maximize Buttons -->\n')
    f.write('                            <div style="display: flex; gap: 12px;">\n')
    
    # Fixed Chart Maximised button (blue, uses existing maximize functionality)
    f.write('                                <button onclick="maximizeChart(\'fixed\')" \n')
    f.write('                                        style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; font-size: 14px; font-weight: 500; border-radius: 8px; border: 1px solid #3b82f6; background-color: #3b82f6; color: white; cursor: pointer; transition: all 0.15s ease; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);" \n')
    f.write('                                        title="Open fixed chart in full view">\n')
    f.write('                                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">\n')
    f.write('                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>\n')
    f.write('                                    </svg>\n')
    f.write('                                    Fixed Chart Maximised\n')
    f.write('                                </button>\n')
    
    # Interactive Chart Maximised button (green, uses existing maximize functionality)
    f.write('                                <button onclick="maximizeChart(\'interactive\')" \n')
    f.write('                                        style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 20px; font-size: 14px; font-weight: 500; border-radius: 8px; border: 1px solid #059669; background-color: #059669; color: white; cursor: pointer; transition: all 0.15s ease; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);" \n')
    f.write('                                        title="Open interactive chart in full view">\n')
    f.write('                                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">\n')
    f.write('                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>\n')
    f.write('                                    </svg>\n')
    f.write('                                    Interactive Chart Maximised\n')
    f.write('                                </button>\n')
    
    f.write('                            </div>\n')
    f.write('                        </div>\n')
    
    # Chart container - always shows fixed chart by default (removed shadow/border for embedded look)
    f.write('                        <div id="chartContainer" class="bg-white p-4">\n')
    
    # Always show fixed chart (no switching needed)
    if chart_url:
        f.write('                            <div id="fixedChart" class="chart-display">\n')
        f.write(f'                                <img src="{chart_url}" alt="Fixed Cumulative Returns Chart" class="chart-img" style="width: 100%; height: auto; max-width: 800px;">\n')
        f.write('                            </div>\n')
    else:
        f.write('                            <div class="chart-display">\n')
        f.write('                                <p class="text-gray-500 text-center py-8">Chart generation failed</p>\n')
        f.write('                            </div>\n')
    
    f.write('                        </div>\n')
    f.write('                    </div>\n')
    
    # Compound Performance Chart (new addition) - small gap and no border for embedded look
    if compound_chart_url:
        f.write('                    <div class="bg-white p-4" style="margin-top: 16px;">\n')
        f.write(f'                        <img src="{compound_chart_url}" alt="Compound Performance Chart" class="chart-img" style="width: 95%; height: auto; max-width: 800px;">\n')
        f.write('                    </div>\n')
    
    # Simplified JavaScript for maximize functionality only
    _write_chart_javascript(f, chart_url, plotly_chart_url)


def _write_chart_javascript(f, chart_url, plotly_chart_url):
    """Write the JavaScript for chart switching functionality."""
    f.write('        <script>\n')
    
    # Updated maximize function to handle both chart types
    f.write('            function maximizeChart(chartType = "fixed") {\n')
    f.write('                let url;\n')
    f.write('                \n')
    f.write('                if (chartType === "fixed") {\n')
    if chart_url:
        f.write(f'                    url = "{chart_url}";\n')
    else:
        f.write('                    console.error("Fixed chart URL not available");\n')
        f.write('                    return;\n')
    f.write('                } else if (chartType === "interactive") {\n')
    if plotly_chart_url:
        f.write(f'                    url = "{plotly_chart_url}";\n')
    else:
        f.write('                    console.error("Interactive chart URL not available");\n')
        f.write('                    return;\n')
    f.write('                }\n')
    f.write('                \n')
    f.write('                // Open chart in new window - let Plotly handle responsive sizing\n')
    f.write('                if (url) {\n')
    f.write('                    window.open(url, "_blank", "width=1200,height=800,scrollbars=yes,resizable=yes");\n')
    f.write('                }\n')
    f.write('            }\n')
    f.write('            \n')
    
    # Remove the automatic maximize call that was causing pop-up blocking
    f.write('            // Chart is ready to use - no automatic pop-ups\n')
    f.write('            document.addEventListener("DOMContentLoaded", function() {\n')
    f.write('                console.log("Chart interface ready");\n')
    f.write('            });\n')
    
    f.write('        </script>\n')


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
                
                # Start HTML table
                f.write('                        <table class="table-base drawdown-table">\n')
                
                # Header row
                f.write('                            <tr>\n')
                f.write('                                <th class="table-header-base">Start Date</th>\n')
                f.write('                                <th class="table-header-base">End Date</th>\n')
                f.write('                                <th class="table-header-base">Duration (Days)</th>\n')
                f.write('                                <th class="table-header-base">Drawdown %</th>\n')
                f.write('                            </tr>\n')
                
                # Show top 10 drawdowns
                for row_index, (_, row) in enumerate(drawdown_details.head(10).iterrows()):
                    start_date = row["Start"].strftime("%d-%b-%Y")
                    end_date = row["End"].strftime("%d-%b-%Y")
                    duration = str(row["Length"])
                    drawdown = f"{row['drawdown']*100:.2f}%"
                    
                    # Apply alternating row styling
                    row_class = "table-row-alt" if row_index % 2 == 1 else ""
                    f.write(f'                            <tr class="{row_class}">\n')
                    f.write(f'                                <td class="table-cell-base">{start_date}</td>\n')
                    f.write(f'                                <td class="table-cell-base">{end_date}</td>\n')
                    f.write(f'                                <td class="table-cell-base">{duration}</td>\n')
                    f.write(f'                                <td class="table-cell-base">{drawdown}</td>\n')
                    f.write('                            </tr>\n')
                
                f.write('                        </table>\n')
                f.write('                    </div>\n')
            else:
                logger.warning(f"No valid drawdown details for {column}")
                f.write(f'                    <h3 class="text-xl mb-3 mt-6 section-header">{column}</h3>\n')
                f.write('                    <div class="bg-white rounded-lg shadow overflow-x-auto mb-6">\n')
                f.write('                        <div class="p-4 text-gray-600">No significant drawdowns found.</div>\n')
                f.write('                    </div>\n')
        
        except Exception as e:
            logger.error(f"Error processing drawdowns for {column}: {str(e)}")
            f.write(f'                    <h3 class="text-xl mb-3 mt-6 section-header">{column}</h3>\n')
            f.write('                    <div class="bg-white rounded-lg shadow overflow-x-auto mb-6">\n')
            f.write('                        <div class="p-4 text-red-600">Error calculating drawdowns.</div>\n')
            f.write('                    </div>\n')
    
    f.write('                </div>\n')


def _calculate_monthly_returns_quantstats_style(returns_series, compounded=True):
    """
    Calculate monthly returns in QuantStats format for heatmap.
    Based on QuantStats monthly_returns function.
    """
    # Convert to DataFrame format that QuantStats expects
    returns_df = pd.DataFrame({'Returns': returns_series})
    returns_df.index = pd.to_datetime(returns_df.index)
    
    # Group returns by month (QuantStats methodology)
    def group_returns_compounded(rets):
        if compounded:
            return (1 + rets).prod() - 1
        else:
            return rets.sum()
    
    # Group by year-month
    monthly_grouped = returns_series.groupby(returns_series.index.to_period('M')).apply(group_returns_compounded)
    
    # Convert to DataFrame with Year and Month columns
    monthly_df = pd.DataFrame({'Returns': monthly_grouped})
    monthly_df.index = monthly_df.index.to_timestamp()
    monthly_df['Year'] = monthly_df.index.year.astype(str)
    monthly_df['Month'] = monthly_df.index.strftime('%b')
    
    # Create pivot table
    pivot_table = monthly_df.pivot(index='Year', columns='Month', values='Returns').fillna(0)
    
    # Ensure all months are present
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for month in month_order:
        if month not in pivot_table.columns:
            pivot_table[month] = 0
    
    # Reorder columns by month
    pivot_table = pivot_table[month_order]
    
    # Convert to percentage
    pivot_table = pivot_table * 100
    
    return pivot_table

def _generate_monthly_heatmap(returns_series, symbol, reports_dir, compounded=True):
    """
    Generate monthly returns heatmap using QuantStats methodology.
    """
    try:
        # Calculate monthly returns in QuantStats format
        monthly_returns = _calculate_monthly_returns_quantstats_style(returns_series, compounded=compounded)
        
        if monthly_returns.empty:
            logger.warning(f"No monthly returns data for {symbol}")
            return None
        
        # Set up the plot with QuantStats styling
        fig_height = len(monthly_returns) / 2.5
        figsize = (10, max([fig_height, 5]))
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Remove spines (QuantStats style)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)
        
        # Set background colors
        fig.set_facecolor("white")
        ax.set_facecolor("white")
        
        # Create heatmap with QuantStats parameters
        sns.heatmap(
            monthly_returns,
            ax=ax,
            annot=True,
            center=0,
            annot_kws={"size": 10},
            fmt="0.2f",
            linewidths=0.5,
            square=False,
            cbar=True,
            cmap="RdYlGn",  # QuantStats default colormap
            cbar_kws={"format": "%.0f%%"},
        )
        
        # Set ylabel
        ax.set_ylabel("Years", fontname="Arial", fontweight="bold", fontsize=12)
        ax.yaxis.set_label_coords(-0.1, 0.5)
        
        # Style ticks
        ax.tick_params(colors="#808080")
        plt.xticks(rotation=0, fontsize=12)
        plt.yticks(rotation=0, fontsize=12)
        
        # Adjust layout
        try:
            plt.subplots_adjust(hspace=0, bottom=0, top=1)
            fig.tight_layout(w_pad=0, h_pad=0)
        except Exception:
            pass
        
        # Save the heatmap
        heatmap_filename = f"monthly_heatmap_{symbol.lower()}.png"
        heatmap_path = os.path.join(reports_dir, heatmap_filename)
        
        plt.savefig(heatmap_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        logger.info(f"Generated monthly heatmap for {symbol}: {heatmap_path}")
        return heatmap_filename
        
    except Exception as e:
        logger.error(f"Error generating monthly heatmap for {symbol}: {str(e)}")
        plt.close()
        return None

def _write_monthly_returns(f, data, perf):
    """Write the monthly returns section with heatmaps and table view option."""
    for symbol in data.columns:
        f.write('                <div class="mb-12">\n')
        f.write(f'                    <h2 class="text-2xl mb-4 section-header">Monthly Returns - {symbol}</h2>\n')
        
        # Add button to view table data
        f.write('                    <div style="margin-bottom: 16px;">\n')
        f.write(f'                        <button id="toggleTable_{symbol}" onclick="toggleMonthlyTable(\'{symbol}\')" \n')
        f.write('                                style="display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; font-size: 13px; font-weight: 500; border-radius: 6px; background-color: #3b82f6; color: white; border: 1px solid #3b82f6; cursor: pointer; transition: all 0.15s ease; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);" \n')
        f.write('                                title="View detailed monthly returns table">\n')
        f.write('                            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">\n')
        f.write('                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 6h18m-9 8h9m-9 4h9m-9-8V6a2 2 0 012-2h14a2 2 0 012 2v12a2 2 0 01-2-2V10z"></path>\n')
        f.write('                            </svg>\n')
        f.write('                            View Monthly Return Table\n')
        f.write('                        </button>\n')
        f.write('                    </div>\n')
        
        # Hidden table that can be toggled - MOVED ABOVE THE HEATMAP with proper grid format
        f.write(f'                    <div id="monthlyTable_{symbol}" class="bg-white rounded-lg shadow overflow-x-auto mb-4" style="display: none;">\n')
        f.write('                        <div class="p-2" style="background-color: #f3f4f6; border-bottom: 1px solid #e5e7eb;">\n')
        f.write('                            <h4 style="margin: 0; font-size: 14px; font-weight: 600; color: #374151;">Monthly Returns Table Data</h4>\n')
        f.write('                        </div>\n')
        f.write('                        <pre class="p-4 font-mono text-sm report-table" style="margin: 0; white-space: pre; overflow-x: auto;">\n')
        
        # Generate the table data in proper grid format without YTD
        monthly_output = io.StringIO()
        with redirect_stdout(monthly_output):
            # Use the original display method but capture and modify the output
            perf[symbol].display_monthly_returns()
        
        # Process the output to remove YTD column
        table_output = monthly_output.getvalue()
        lines = table_output.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Remove lines that contain EOY or YTD references
            if 'EOY' not in line and line.strip():
                # Remove the last column (EOY) from data lines
                if any(month in line for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                    # Split and remove last column
                    parts = line.split()
                    if len(parts) > 13:  # Year + 12 months + EOY
                        line = ' '.join(parts[:-1])  # Remove last part (EOY)
                filtered_lines.append(line)
        
        f.write('\n'.join(filtered_lines))
        f.write('                        </pre>\n')
        f.write('                    </div>\n')
        
        # Heatmap section - NOW BELOW THE TABLE
        f.write('                    <div class="bg-white rounded-lg shadow overflow-x-auto">\n')
        
        # Generate heatmap
        returns_series = data[symbol].pct_change().dropna()
        heatmap_filename = _generate_monthly_heatmap(returns_series, symbol, REPORTS_DIR, compounded=True)
        
        if heatmap_filename:
            # Display heatmap
            heatmap_url = construct_report_url(heatmap_filename)
            f.write('                        <div class="p-4">\n')
            f.write(f'                            <img src="{heatmap_url}" alt="Monthly Returns Heatmap for {symbol}" style="width: 100%; height: auto; max-width: 800px; border-radius: 8px;">\n')
            f.write('                        </div>\n')
        else:
            # Fallback to text display if heatmap generation fails
            f.write('                        <div class="p-4">\n')
            f.write('                            <p class="text-red-600">Heatmap generation failed. Showing table instead.</p>\n')
            f.write('                        </div>\n')
        
        f.write('                    </div>\n')
        f.write('                </div>\n')
    
    # Add JavaScript for table toggle functionality
    f.write('        <script>\n')
    f.write('            function toggleMonthlyTable(symbol) {\n')
    f.write('                const table = document.getElementById("monthlyTable_" + symbol);\n')
    f.write('                const button = document.getElementById("toggleTable_" + symbol);\n')
    f.write('                \n')
    f.write('                if (table.style.display === "none" || table.style.display === "") {\n')
    f.write('                    table.style.display = "block";\n')
    f.write('                    button.innerHTML = `\n')
    f.write('                        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">\n')
    f.write('                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>\n')
    f.write('                        </svg>\n')
    f.write('                        Hide Monthly Return Table\n')
    f.write('                    `;\n')
    f.write('                } else {\n')
    f.write('                    table.style.display = "none";\n')
    f.write('                    button.innerHTML = `\n')
    f.write('                        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">\n')
    f.write('                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 6h18m-9 8h9m-9 4h9m-9-8V6a2 2 0 012-2h14a2 2 0 012 2v12a2 2 0 01-2-2V10z"></path>\n')
    f.write('                        </svg>\n')
    f.write('                        View Monthly Return Table\n')
    f.write('                    `;\n')
    f.write('                }\n')
    f.write('            }\n')
    f.write('        </script>\n')


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
    f.write('                        <a href="https://app.tigzig.com" target="_blank" rel="noopener noreferrer"\n')
    f.write('                           style="color: #4338ca; text-decoration: none; font-weight: normal;">\n')
    f.write('                            app.tigzig.com\n')
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
    """Write the custom performance metrics section with max drawdown metrics."""
    f.write('                <div class="mb-12">\n')
    f.write('                    <h2 class="text-2xl mb-4 section-header">Overall Returns and Risk Measures (NEW)</h2>\n')
    f.write('                    <div class="bg-white rounded-lg shadow overflow-x-auto">\n')
    
    # Get performance metrics from data processor
    rf_decimal = risk_free_rate / 100.0  # Convert percentage to decimal
    metrics = data_processor.get_performance_metrics(risk_free_rate=rf_decimal)
    
    # Get the raw data for drawdown calculations
    raw_data = data_processor.raw_data
    
    if metrics:
        symbols = list(metrics.keys())
        
        # Calculate max drawdown metrics using FFN for each symbol
        import ffn
        drawdown_metrics = {}
        for symbol in symbols:
            try:
                # Calculate drawdown series using FFN
                drawdown_series = ffn.to_drawdown_series(raw_data[symbol])
                
                # Get maximum drawdown (most negative value)
                max_dd = drawdown_series.min()
                
                # Get date of maximum drawdown
                max_dd_date = drawdown_series.idxmin()
                
                # Get drawdown details to find max duration
                drawdown_details = ffn.drawdown_details(drawdown_series)
                max_duration = 0
                if drawdown_details is not None and len(drawdown_details) > 0:
                    max_duration = drawdown_details['Length'].max()
                
                drawdown_metrics[symbol] = {
                    'max_drawdown': max_dd,
                    'max_drawdown_date': max_dd_date,
                    'max_drawdown_duration': max_duration
                }
                
            except Exception as e:
                logger.error(f"Error calculating drawdown metrics for {symbol}: {str(e)}")
                drawdown_metrics[symbol] = {
                    'max_drawdown': np.nan,
                    'max_drawdown_date': None,
                    'max_drawdown_duration': np.nan
                }
        
        # Start HTML table with increased width
        f.write('                        <table class="table-base performance-metrics-table" style="max-width: 1000px;">\n')
        
        # Header row
        f.write('                            <tr class="table-header-base">\n')
        f.write('                                <th class="table-header-base" style="width: 140px;">Metric</th>\n')
        
        # Asset columns with increased width
        for asset in symbols:
            f.write(f'                                <th class="table-header-base" style="width: 110px;">{asset}</th>\n')
        
        f.write('                            </tr>\n')
        
        # Define metrics with correct keys that match data processor output
        metric_definitions = [
            ('Total Return', 'Total Return', lambda x: f"{x:.2%}"),
            ('CAGR', 'CAGR', lambda x: f"{x:.2%}"),
            ('Sharpe Ratio', 'Sharpe Ratio', lambda x: f"{x:.2f}"),
            ('Sortino Ratio', 'Sortino Ratio', lambda x: f"{x:.2f}"),
            ('Max Drawdown %', 'max_drawdown', lambda x: f"{x:.2%}"),
            ('Max Drawdown Date', 'max_drawdown_date', lambda x: x.strftime('%d-%b-%Y') if hasattr(x, 'strftime') else str(x)),
            ('Max DD Duration', 'max_drawdown_duration', lambda x: f"{int(x)} days" if not pd.isna(x) else 'N/A')
        ]
        
        # Data rows
        for row_index, (metric_name, metric_key, formatter) in enumerate(metric_definitions):
            # Apply alternating row styling
            row_class = "table-row-alt" if row_index % 2 == 1 else ""
            f.write(f'                            <tr class="{row_class}">\n')
            f.write(f'                                <td class="table-cell-base metrics-table-row-label">{metric_name}</td>\n')
            
            for asset in symbols:
                try:
                    # Check if it's a drawdown metric (use drawdown_metrics) or regular metric
                    if metric_key in ['max_drawdown', 'max_drawdown_date', 'max_drawdown_duration']:
                        if asset in drawdown_metrics and metric_key in drawdown_metrics[asset]:
                            value = drawdown_metrics[asset][metric_key]
                            if pd.isna(value) or value is None:
                                formatted_value = 'N/A'
                            else:
                                formatted_value = formatter(value)
                        else:
                            formatted_value = 'N/A'
                    else:
                        # Regular metrics from data processor
                        if asset in metrics and metric_key in metrics[asset]:
                            value = metrics[asset][metric_key]
                            if pd.isna(value) or value is None:
                                formatted_value = 'N/A'
                            else:
                                formatted_value = formatter(value)
                        else:
                            formatted_value = 'N/A'
                    
                    f.write(f'                                <td class="table-cell-base">{formatted_value}</td>\n')
                except Exception as e:
                    logger.error(f"Error formatting {metric_name} for {asset}: {str(e)}")
                    f.write(f'                                <td class="table-cell-base">N/A</td>\n')
            
            f.write('                            </tr>\n')
        
        f.write('                        </table>\n')
        
        # Add note about calculations
        f.write('                        <div style="padding: 12px; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb;">\n')
        f.write(f'                            <strong>Notes:</strong> Sharpe and Sortino ratios calculated using {risk_free_rate:.2f}% annual risk-free rate. ')
        f.write('                            Max drawdown metrics calculated using FFN library.\n')
        f.write('                        </div>\n')
    else:
        f.write('                        <div class="p-4 text-red-600">Error: Could not calculate performance metrics</div>\n')
    
    f.write('                    </div>\n')
    f.write('                </div>\n') 