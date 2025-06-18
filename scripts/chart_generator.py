"""
Chart Generation Module for FFN Portfolio Analysis

This module contains all chart generation functions including:
- Matplotlib cumulative returns charts
- Interactive Plotly charts  
- CAGR bar charts
- Chart styling functions
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import seaborn as sns
import plotly.graph_objects as go
import plotly.offline as pyo
import logging

# Get logger
logger = logging.getLogger(__name__)

# Reports directory (will be imported from main)
REPORTS_DIR = os.path.join('static', 'reports')


def get_series_style(series_index, cumulative_returns_length):
    """Get styling for a specific series based on the simplified alternating pattern."""
    if series_index < 10:
        # Special case for series 5 (NVDA) - thin with black circle marker
        if series_index == 4:  # Series 5 (0-indexed as 4)
            return {
                'linestyle': '-',
                'linewidth': 1.0,
                'marker': 'o',  # Circle
                'marker_color': '#1e3a8a',  # Navy blue instead of black
                'markevery': max(cumulative_returns_length // 15, 1),
                'markersize': 5
            }
        
        # Simplified pattern: Thick solid (no marker) alternating with Thin solid (with marker)
        is_even = series_index % 2 == 0
        
        if is_even:  # Series 0, 2, 4, 6, 8: Thick solid, no marker (except series 4 handled above)
            return {
                'linestyle': '-',
                'linewidth': 2.5,
                'marker': None,
                'marker_color': None,
                'markevery': None,
                'markersize': None
            }
        else:  # Series 1, 3, 5, 7, 9: Thin solid with alternating markers
            # Alternate between diamond and cross markers
            marker_type = 'D' if (series_index // 2) % 2 == 0 else 'x'
            # Use black for cross markers, navy blue for others
            marker_color = 'black' if marker_type == 'x' else '#1e3a8a'
            
            return {
                'linestyle': '-',
                'linewidth': 1.0,
                'marker': marker_type,
                'marker_color': marker_color,
                'markevery': max(cumulative_returns_length // 15, 1),
                'markersize': 5 if marker_type == 'D' else 6
            }
    else:
        # Fallback for series 11+: Simple solid lines, medium width, no markers, slight transparency
        return {
            'linestyle': '-',
            'linewidth': 2.0,
            'marker': None,
            'marker_color': None,
            'markevery': None,
            'markersize': None,
            'alpha': 0.7  # Slightly transparent for overflow series
        }


def get_plotly_series_style(series_index):
    """Get styling for Plotly series - simplified thick/thin alternating pattern with markers."""
    if series_index < 10:
        # Special case for series 5 (NVDA) - keep it thin for distinction
        if series_index == 4:  # Series 5 (0-indexed as 4)
            return {
                'line_width': 1.5,  # Slightly thicker than normal thin
                'dash': None,  # Solid line
                'marker': 'circle',
                'marker_color': '#1e3a8a',  # Navy blue
                'marker_size': 5
            }
        
        # Simplified pattern: Thick solid alternating with Thin solid (WITH MARKERS)
        is_even = series_index % 2 == 0
        
        if is_even:  # Series 0, 2, 4, 6, 8: Thick solid (except series 4 handled above)
            return {
                'line_width': 3.0,  # Slightly thicker for web display
                'dash': None,  # Solid line
                'marker': None,
                'marker_color': None,
                'marker_size': None
            }
        else:  # Series 1, 3, 5, 7, 9: Thin solid with markers
            # Alternate between diamond and cross markers
            marker_type = 'diamond' if (series_index // 2) % 2 == 0 else 'x'
            # Use black for cross markers, navy blue for others
            marker_color = 'black' if marker_type == 'x' else '#1e3a8a'
            marker_size = 5 if marker_type == 'diamond' else 7
            
            return {
                'line_width': 1.5,  # Medium thin for web visibility
                'dash': None,  # Solid line
                'marker': marker_type,
                'marker_color': marker_color,
                'marker_size': marker_size
            }
    else:
        # Fallback for series 11+
        return {
            'line_width': 2.0,
            'dash': None,
            'marker': None,
            'marker_color': None,
            'marker_size': None
        }


def generate_cumulative_returns_chart(data, report_filename_base):
    """Generate a cumulative returns chart and save it as PNG."""
    try:
        # Set up the style for a professional look
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create figure and axis - keep original size for quality, control display size in CSS
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Calculate cumulative returns (rebase to start at 0%)
        returns_data = data.pct_change().fillna(0)
        cumulative_returns = (1 + returns_data).cumprod() - 1
        
        # Same color palette as matplotlib version
        colors = [
            '#1f77b4',  # blue
            '#ff7f0e',  # orange  
            '#2ca02c',  # green
            '#d62728',  # red
            '#ff69b4',  # hot pink (replaced dark red/maroon for better contrast with red and navy blue)
            '#000080',  # navy blue (replaced deep pink for better contrast)
            '#00ffff',  # cyan
            '#ffa500',  # dark orange
            '#8b4513',  # saddle brown
            '#32cd32'   # lime green
        ]
        
        # Plot each series with enhanced differentiation
        for i, column in enumerate(cumulative_returns.columns):
            color = colors[i % len(colors)]
            style = get_series_style(i, len(cumulative_returns))
            
            # Prepare plot parameters
            plot_params = {
                'label': column,
                'color': color,
                'linestyle': style['linestyle'],
                'linewidth': style['linewidth'],
                'alpha': style.get('alpha', 0.9)
            }
            
            # Add marker parameters if applicable
            if style['marker'] is not None:
                plot_params.update({
                    'marker': style['marker'],
                    'markerfacecolor': style['marker_color'],
                    'markeredgecolor': style['marker_color'],
                    'markevery': style['markevery'],
                    'markersize': style['markersize']
                })
            
            # Plot the series
            ax.plot(cumulative_returns.index, cumulative_returns[column] * 100, **plot_params)
        
        # Formatting - remove external title, will add inside chart
        # Use same soft color as CAGR chart for consistency
        soft_text_color = '#4A5568'  # Same as compound performance chart
        ax.set_xlabel('')  # Remove "Date" label - it's obvious from the year tickers
        ax.set_ylabel('')  # Remove Y-axis label since title already indicates what chart shows
        
        # Format y-axis as percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}%'))
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        
        # Add horizontal line at 0% for reference
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.8)
        
        # Remove grid for cleaner look
        ax.grid(False)
        
        # Configure axes - remove top, right, and left borders, keep bottom only
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)   # Remove Y-axis line (vertical line)
        ax.spines['bottom'].set_visible(True)  # Keep X-axis line (horizontal line)
        
        # Move Y-axis labels to the right side
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position('right')
        
        # Enhanced legend positioning for better handling of multiple series - remove borders
        num_series = len(cumulative_returns.columns)
        if num_series <= 4:
            # Single column legend for few series
            ax.legend(loc='upper left', frameon=False)
        elif num_series <= 8:
            # Two column legend for medium number of series
            ax.legend(loc='upper left', frameon=False, ncol=2)
        else:
            # Compact legend outside plot area for many series
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False, ncol=1)
        
        # Add title inside chart area, centered at the top - match CAGR chart styling
        ax.text(0.5, 0.95, 'Cumulative Returns (%)', transform=ax.transAxes, 
                fontsize=16, fontweight='bold', ha='center', va='top', color=soft_text_color)
        
        # Tight layout with minimal padding for mobile responsiveness
        if num_series > 8:
            plt.tight_layout(rect=[0, 0, 0.85, 1], pad=0)  # Leave space for external legend, no padding
        else:
            plt.tight_layout(pad=0)  # Remove all padding
        
        # Save the chart with high DPI and minimal margins for mobile
        chart_filename = f"{report_filename_base}_cumulative_returns.png"
        chart_path = os.path.join(REPORTS_DIR, chart_filename)
        plt.savefig(chart_path, dpi=200, bbox_inches='tight', pad_inches=0, facecolor='white')
        plt.close()  # Important: close the figure to free memory
        
        return chart_filename
        
    except Exception as e:
        logger.error(f"Error generating cumulative returns chart: {str(e)}")
        plt.close()  # Ensure figure is closed even on error
        return None


def generate_plotly_cumulative_returns_chart(data, report_filename_base):
    """Generate an interactive Plotly cumulative returns chart and save as HTML."""
    try:
        # Calculate cumulative returns (rebase to start at 0%)
        returns_data = data.pct_change().fillna(0)
        cumulative_returns = (1 + returns_data).cumprod() - 1
        
        # Same color palette as matplotlib version
        colors = [
            '#1f77b4',  # blue
            '#ff7f0e',  # orange  
            '#2ca02c',  # green
            '#d62728',  # red
            '#ff69b4',  # hot pink (replaced dark red/maroon for better contrast with red and navy blue)
            '#000080',  # navy blue (replaced deep pink for better contrast)
            '#00ffff',  # cyan
            '#ffa500',  # dark orange
            '#8b4513',  # saddle brown
            '#32cd32'   # lime green
        ]
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add traces for each series
        for i, column in enumerate(cumulative_returns.columns):
            color = colors[i % len(colors)]
            style = get_plotly_series_style(i)
            
            # Get the actual prices for this series (for hover display)
            actual_prices = data[column]
            
            # Prepare trace parameters
            trace_params = {
                'x': cumulative_returns.index,
                'y': cumulative_returns[column] * 100,  # Convert to percentage
                'name': column,
                'line': dict(
                    color=color, 
                    width=style['line_width'],
                    dash=style['dash']
                ),
                'hovertemplate': f'<span style="font-size:14px"><b>{column}</b>: %{{y:.1f}}% (%{{customdata:.1f}})</span>' +
                               '<extra></extra>',
                'customdata': actual_prices,  # Add actual prices as custom data
                'mode': 'lines'
            }
            
            # Add marker parameters if applicable and show them in legend
            if style['marker'] is not None:
                # Calculate marker spacing (similar to matplotlib's markevery)
                total_points = len(cumulative_returns)
                marker_every = max(total_points // 15, 1)  # Same spacing as matplotlib
                
                # Update main trace to include markers AND show in legend
                trace_params['mode'] = 'lines+markers'
                trace_params['marker'] = dict(
                    symbol=style['marker'],
                    color=style['marker_color'],
                    size=style['marker_size'],
                    line=dict(width=1, color=style['marker_color'])
                )
                # Show only subset of markers for cleaner display
                trace_params['marker']['maxdisplayed'] = max(total_points // 15, 5)
            else:
                trace_params['mode'] = 'lines'
            
            fig.add_trace(go.Scatter(**trace_params))
        
        # Configure layout to match matplotlib styling
        # Use same soft color as other charts for consistency
        soft_text_color = '#4A5568'
        
        fig.update_layout(
            title={
                'text': 'Cumulative Returns (%)',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16, 'color': soft_text_color}  # Match other charts
            },
            xaxis_title='',  # Remove "Date" text
            yaxis_title='',  # Remove Y-axis title since chart title already indicates what it shows
            width=780,  # Reduced from 1000 to fit better in iframe without scroll bars
            height=420,  # Reduced from 600 to fit better in iframe 
            plot_bgcolor='white',
            paper_bgcolor='white',
            font={'family': 'Arial, sans-serif', 'size': 11, 'color': '#000000'},
            hovermode='x unified',  # Show all series values on hover
            legend=dict(
                orientation='v',
                yanchor='top',
                y=0.98,  # Moved higher to prevent truncation
                xanchor='left',
                x=0.02,  # Slightly more margin from left edge
                bgcolor='rgba(255,255,255,0.9)',  # More transparent to blend better
                bordercolor='rgba(255,255,255,0)',  # Transparent border (no border)
                borderwidth=0,  # No border width
                font=dict(size=9),  # Smaller font for iframe mode to prevent truncation
                itemsizing='constant',  # Ensure consistent sizing
                itemwidth=30  # Compact legend items
            ),
            margin=dict(l=20, r=60, t=50, b=50)  # Adjusted margins: reduced left, increased right for Y-axis labels
        )
        
        # Configure axes
        fig.update_xaxes(
            gridcolor='lightgray',
            gridwidth=0.5,
            showgrid=False,  # Remove grid lines
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor='black'
        )
        
        fig.update_yaxes(
            gridcolor='lightgray',
            gridwidth=0.5,
            showgrid=False,  # Remove grid lines
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=0.8,
            showline=False,  # Remove Y-axis line
            side='right',    # Move Y-axis labels to the right side
            ticksuffix='%',
            title_font=dict(size=12, color=soft_text_color)  # Match other charts
        )
        
        # Update hover styling with larger fonts
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                bordercolor="gray",
                font_size=16,  # Larger font for all hover text including date
                font_family="Arial"
            )
        )
        
        # Generate HTML content
        chart_html = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')
        
        # Save as HTML file
        chart_filename = f"{report_filename_base}_cumulative_returns_plotly.html"
        chart_path = os.path.join(REPORTS_DIR, chart_filename)
        
        with open(chart_path, 'w') as f:
            f.write(f'''
<!DOCTYPE html>
<html>
<head>
    <title>Cumulative Returns - Interactive Chart</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ 
            margin: 0; 
            padding: 8px; 
            font-family: Arial, sans-serif; 
            background-color: white;
            overflow: hidden;  /* Prevent any scroll bars */
        }}
        
        /* Default: Embedded in iframe (fixed size) */
        .chart-container {{ 
            width: 100%; 
            height: 100vh; 
            display: flex;
            justify-content: center;
            align-items: center;
            box-sizing: border-box;
        }}
        .chart-wrapper {{
            background: white;
            padding: 0;
            width: 100%;
            max-width: 800px;
            height: auto;
            overflow: hidden;
        }}
        
        /* Standalone mode: Opened in new window (responsive/full-size) */
        @media all {{
            /* Detect if we're NOT in an iframe (standalone mode) */
            body:not([data-iframe]) .chart-container {{
                width: 100vw;
                height: 100vh;
                padding: 10px;
            }}
            body:not([data-iframe]) .chart-wrapper {{
                max-width: none;
                width: 95vw;
                height: 90vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            body:not([data-iframe]) .plotly-graph-div {{
                width: 95vw !important;
                height: 85vh !important;
            }}
        }}
        
        /* Ensure plotly chart container doesn't overflow */
        .plotly-graph-div {{
            margin: 0 !important;
            padding: 0 !important;
        }}
    </style>
    <script>
        // Detect if we're in standalone mode (not in iframe)
        function isStandalone() {{
            try {{
                return window.self === window.top;
            }} catch (e) {{
                return false;
            }}
        }}
        
        // Apply responsive sizing for standalone mode
        function applyStandaloneMode() {{
            if (isStandalone()) {{
                // Remove iframe data attribute to trigger CSS
                document.body.removeAttribute('data-iframe');
                
                // Wait for Plotly to load, then resize
                function resizeChart() {{
                    const plotlyDiv = document.querySelector('.plotly-graph-div');
                    if (plotlyDiv && window.Plotly) {{
                        // Full-screen layout with better legend
                        window.Plotly.relayout(plotlyDiv, {{
                            'width': window.innerWidth * 0.95,
                            'height': window.innerHeight * 0.85,
                            'legend.font.size': 12,  // Larger font for full-screen
                            'legend.itemwidth': 50,  // More space for legend items
                            'legend.y': 0.95,       // Optimal positioning for full-screen
                            'legend.x': 0.01,       // Back to original position
                            'legend.bgcolor': 'rgba(255,255,255,0.95)',  // More opaque for full-screen
                            'legend.bordercolor': 'rgba(255,255,255,0)',  // Keep transparent border
                            'legend.borderwidth': 0  // No border even in full-screen
                        }});
                    }}
                }}
                
                // Resize on load and window resize
                setTimeout(resizeChart, 500);
                window.addEventListener('resize', resizeChart);
            }} else {{
                // Mark as iframe mode - keep compact legend settings
                document.body.setAttribute('data-iframe', 'true');
            }}
        }}
        
        // Run on DOM ready
        document.addEventListener('DOMContentLoaded', applyStandaloneMode);
    </script>
</head>
<body data-iframe="true">
    <div class="chart-container">
        <div class="chart-wrapper">
            {chart_html}
        </div>
    </div>
</body>
</html>
            ''')

        return chart_filename

    except Exception as e:
        logger.error(f"Error generating Plotly cumulative returns chart: {str(e)}")
        return None


def generate_cagr_bar_chart(data, report_filename_base):
    """Generate a CAGR bar chart for all securities."""
    try:
        # Set up the style for a professional look
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create figure and axis - same size as cumulative returns chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Calculate CAGR for each security
        years = (data.index[-1] - data.index[0]).days / 365.25
        cagr_data = {}
        
        for column in data.columns:
            total_return = (data[column].iloc[-1] / data[column].iloc[0]) - 1
            cagr = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
            cagr_data[column] = cagr * 100  # Convert to percentage
        
        # Create bar chart
        securities = list(cagr_data.keys())
        cagr_values = list(cagr_data.values())
        
        # Use same enhanced color palette as cumulative returns chart for consistency
        colors = [
            '#1f77b4',  # blue
            '#ff7f0e',  # orange  
            '#2ca02c',  # green
            '#d62728',  # red
            '#ff69b4',  # hot pink (replaced dark red/maroon for better contrast with red and navy blue)
            '#000080',  # navy blue (replaced deep pink for better contrast)
            '#00ffff',  # cyan
            '#ffa500',  # dark orange
            '#8b4513',  # saddle brown
            '#32cd32'   # lime green
        ]
        bar_colors = [colors[i % len(colors)] for i in range(len(securities))]
        
        bars = ax.bar(securities, cagr_values, color=bar_colors, alpha=0.8, edgecolor='white', linewidth=1)
        
        # Formatting
        ax.set_ylabel('CAGR (%)', fontsize=12)
        ax.set_xlabel('Securities', fontsize=12)
        
        # Format y-axis as percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1f}%'))
        
        # Add horizontal line at 0%
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.8)
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, axis='y')
        
        # Add value labels on bars with better spacing
        max_value = max(cagr_values) if cagr_values else 0
        min_value = min(cagr_values) if cagr_values else 0
        value_range = max_value - min_value
        label_offset = value_range * 0.02 if value_range > 0 else 0.5  # Dynamic offset based on data range
        
        for bar, value in zip(bars, cagr_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + (label_offset if height > 0 else -label_offset),
                   f'{value:.1f}%', ha='center', va='bottom' if height > 0 else 'top', 
                   fontsize=12, fontweight='bold')
        
        # Add title inside chart area, but with more spacing from top
        ax.text(0.5, 0.92, 'Compound Annual Growth Rate (CAGR)', transform=ax.transAxes, 
                fontsize=16, fontweight='bold', ha='center', va='top')
        
        # Adjust y-axis limits to provide more space at the top for title and value labels
        current_ylim = ax.get_ylim()
        y_range = current_ylim[1] - current_ylim[0]
        # Add 15% extra space at the top for title and labels
        ax.set_ylim(current_ylim[0], current_ylim[1] + y_range * 0.15)
        
        # Tight layout with padding
        plt.tight_layout(pad=0)  # Minimize padding for mobile responsiveness
        
        # Save the chart with high DPI and minimal margins for mobile
        chart_filename = f"{report_filename_base}_cagr_chart.png"
        chart_path = os.path.join(REPORTS_DIR, chart_filename)
        plt.savefig(chart_path, dpi=200, bbox_inches='tight', pad_inches=0, facecolor='white')
        plt.close()  # Important: close the figure to free memory
        
        return chart_filename
        
    except Exception as e:
        logger.error(f"Error generating CAGR bar chart: {str(e)}")
        plt.close()  # Ensure figure is closed even on error
        return None 


def generate_compound_performance_chart(data, data_processor, risk_free_rate, report_filename_base):
    """
    Generate a compound performance chart with CAGR, Sharpe/Sortino ratios, and drawdown metrics.
    
    This chart includes:
    - Top subplot: CAGR bars with Sharpe/Sortino ratio lines
    - Middle subplot: Maximum drawdown bars (sticking to CAGR bars)
    - Bottom subplot: Maximum drawdown duration (lollipop chart)
    """
    try:
        import ffn
        
        # Set up the style for a professional look
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Get performance metrics and drawdown data
        performance_metrics = data_processor.get_performance_metrics(risk_free_rate / 100.0)
        
        # Calculate drawdown metrics using FFN for each symbol
        drawdown_metrics = {}
        for symbol in data.columns:
            try:
                # Calculate drawdown series using FFN
                drawdown_series = ffn.to_drawdown_series(data[symbol])
                
                # Get maximum drawdown (most negative value)
                max_dd = drawdown_series.min()
                
                # Get drawdown details to find max duration
                drawdown_details = ffn.drawdown_details(drawdown_series)
                
                if drawdown_details is not None and len(drawdown_details) > 0:
                    max_duration = drawdown_details['Length'].max()
                else:
                    max_duration = 0
                
                drawdown_metrics[symbol] = {
                    'max_drawdown': max_dd,
                    'max_drawdown_duration': max_duration
                }
            except Exception as e:
                logger.error(f"Error calculating drawdown metrics for {symbol}: {str(e)}")
                drawdown_metrics[symbol] = {
                    'max_drawdown': 0.0,
                    'max_drawdown_duration': 0
                }
        
        # Prepare data for plotting
        securities = list(performance_metrics.keys())
        n_securities = len(securities)
        
        # Extract data for plotting
        cagr_values = [performance_metrics[symbol]['CAGR'] * 100 for symbol in securities]  # Convert to percentage
        sharpe_values = [performance_metrics[symbol]['Sharpe Ratio'] for symbol in securities]
        sortino_values = [performance_metrics[symbol]['Sortino Ratio'] for symbol in securities]
        drawdown_values = [drawdown_metrics[symbol]['max_drawdown'] * 100 for symbol in securities]  # Convert to percentage
        drawdown_durations = [drawdown_metrics[symbol]['max_drawdown_duration'] for symbol in securities]
        
        # Create x-axis positions
        x = np.arange(n_securities)
        width = 0.65
        
        # Create figure with 3 subplots using gridspec for proper spacing
        fig = plt.figure(figsize=(10, 9))
        gs = fig.add_gridspec(3, 1, height_ratios=[3, 0.8, 1.6], hspace=0)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1], sharex=ax1)  # Share x-axis with ax1 for proper alignment
        ax3 = fig.add_subplot(gs[2], sharex=ax1)  # Share x-axis with ax1 for proper alignment
        
        # Fine-tune spacing to eliminate white gap and create seamless connection
        plt.tight_layout(pad=0)
        
        # Create tight connection between CAGR and drawdown bars, space before lollipop
        pos1 = ax1.get_position()
        pos2 = ax2.get_position()
        pos3 = ax3.get_position()
        
        # Move ax2 slightly up to eliminate white gap with ax1 (negative overlap)
        ax2.set_position([pos2.x0, pos2.y0 + 0.008, pos2.width, pos2.height])
        # Move ax3 down to create space for drawdown labels
        ax3.set_position([pos3.x0, pos3.y0 - 0.03, pos3.width, pos3.height])
        
        # Completely remove borders between subplots - hide all horizontal lines and x-axis lines
        ax1.spines['bottom'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
        ax3.spines['top'].set_visible(False)
        
        # Also remove x-axis lines that might be showing
        ax1.axhline(y=0, color='none')
        ax2.axhline(y=0, color='none')
        ax3.axhline(y=0, color='none')
        
        # Turn off x-axis for middle subplot completely
        ax2.set_xticks([])
        ax2.tick_params(axis='x', which='both', bottom=False, top=False)
        
        # Use same enhanced color palette as other charts for consistency
        colors = [
            '#1f77b4',  # blue
            '#ff7f0e',  # orange  
            '#2ca02c',  # green
            '#d62728',  # red
            '#ff69b4',  # hot pink
            '#000080',  # navy blue
            '#00ffff',  # cyan
            '#ffa500',  # dark orange
            '#8b4513',  # saddle brown
            '#32cd32'   # lime green
        ]
        bar_colors = [colors[i % len(colors)] for i in range(n_securities)]
        
        # Define a softer text color for all labels (even softer than before)
        soft_text_color = '#4A5568'  # Lighter blue-gray, very soft and easy on eyes
        
        # TOP SUBPLOT: CAGR bars with Sharpe/Sortino ratio lines
        bars = ax1.bar(x, cagr_values, width, color=bar_colors, alpha=0.8, edgecolor='white', linewidth=1, zorder=3)
        ax1.set_ylabel('CAGR (%)', fontsize=12, fontweight='bold', color=soft_text_color)
        ax1.set_title('CAGR with Sharpe, Sortino Ratios and Drawdown Metrics', pad=40, fontsize=16, fontweight='bold', color=soft_text_color)
        
        # Set y-axis limits for CAGR with some headroom
        if cagr_values:
            max_cagr = max(cagr_values)
            min_cagr = min(cagr_values)
            cagr_range = max_cagr - min_cagr
            ax1.set_ylim(min(min_cagr - cagr_range * 0.1, 0), max_cagr + cagr_range * 0.3)
        
        # IMMEDIATELY remove ax1 styling after setup
        ax1.spines['bottom'].set_visible(False)
        ax1.spines['top'].set_visible(False)
        ax1.spines['left'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.tick_params(axis='y', which='both', left=False, right=False, labelleft=False, labelright=False)
        ax1.set_yticklabels([])  # Remove Y-axis numbers completely
        ax1.grid(False)
        
        # Annotate CAGR bars with values inside at bottom with background boxes
        for i, val in enumerate(cagr_values):
            # Value label inside the bar at the bottom
            y_pos = max(cagr_values) * 0.05 if val > 0 else val + abs(val) * 0.05  # Small offset from bottom
            
            # Add rounded background box behind the text
            from matplotlib.patches import FancyBboxPatch
            
            # Create a semi-transparent rounded rectangle behind the text
            bbox_props = dict(
                boxstyle="round,pad=0.3",  # Rounded corners with padding
                facecolor='white',         # White/off-white background
                alpha=0.8,                 # Semi-transparent
                edgecolor='none'           # No border
            )
            
            ax1.text(i, y_pos, f'{val:.1f}%', ha='center', va='bottom', 
                    fontsize=10, fontweight='bold', color=soft_text_color,
                    bbox=bbox_props)
        
        # Add Sharpe and Sortino ratios on secondary y-axis
        ax4 = ax1.twinx()
        line1 = ax4.plot(x, sharpe_values, marker='o', label='Sharpe Ratio', linewidth=2, markersize=8, color='#8B4513', zorder=4)
        line2 = ax4.plot(x, sortino_values, marker='x', label='Sortino Ratio', linewidth=2, markersize=10, color='#800080', zorder=4)
        
        # Add data value labels for Sharpe and Sortino ratios
        for i, (sharpe_val, sortino_val) in enumerate(zip(sharpe_values, sortino_values)):
            # Sharpe ratio label above the point
            ax4.text(i, sharpe_val + 0.05, f'{sharpe_val:.2f}', ha='center', va='bottom', 
                    fontsize=10, fontweight='bold', color='#8B4513')
            # Sortino ratio label above the point
            ax4.text(i, sortino_val + 0.05, f'{sortino_val:.2f}', ha='center', va='bottom', 
                    fontsize=10, fontweight='bold', color='#800080')
        
        # Set appropriate limits for ratios
        if sharpe_values and sortino_values:
            all_ratios = sharpe_values + sortino_values
            max_ratio = max(all_ratios)
            min_ratio = min(all_ratios)
            ratio_range = max_ratio - min_ratio
            ax4.set_ylim(min(min_ratio - ratio_range * 0.1, 0), max_ratio + ratio_range * 0.2)
        
        # IMMEDIATELY hide ax4 axis elements after setting limits
        for spine in ax4.spines.values():
            spine.set_visible(False)
        ax4.tick_params(axis='y', which='both', left=False, right=False, labelleft=False, labelright=False)
        ax4.set_ylabel('')
        
        # Create legend at the top of the first plot but below the title - positioned higher to avoid overlap
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax4.get_legend_handles_labels()
        fig.legend(lines1 + lines2, labels1 + labels2,
                   loc='upper left', bbox_to_anchor=(0.05, 1.025), ncol=2, frameon=False, fontsize=11)
        
        # MIDDLE SUBPLOT: Maximum Drawdown bars (50% width to look like pipes coming from below)
        drawdown_bars = ax2.bar(x, drawdown_values, width * 0.5, 
                               color=[colors[i % len(colors)] for i in range(n_securities)], 
                               alpha=0.8, zorder=3)
        ax2.set_ylabel('Max Drawdown (%)', fontsize=12, fontweight='bold', color=soft_text_color)
        
        # Set appropriate limits for drawdowns - increased bottom space for labels
        if drawdown_values:
            min_drawdown = min(drawdown_values)
            max_drawdown = max(drawdown_values)
            dd_range = abs(max_drawdown - min_drawdown)
            ax2.set_ylim(min_drawdown - dd_range * 0.5, max(max_drawdown * 0.1, 0))  # Increased from 0.3 to 0.5
        
        # IMMEDIATELY remove ax2 styling after setup
        for spine in ax2.spines.values():
            spine.set_visible(False)
        ax2.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        ax2.tick_params(axis='y', which='both', left=False, right=False, labelleft=False, labelright=False)
        ax2.set_yticklabels([])  # Remove Y-axis numbers completely
        ax2.grid(False)
        
        # Annotate drawdown bars - add labels outside the bars at the bottom
        for i, val in enumerate(drawdown_values):
            # Position label below the bar (since drawdowns are negative values)
            y_pos = val - abs(val) * 0.15  # Slightly below the end of the bar
            ax2.text(i, y_pos, f'{val:.1f}%', ha='center', va='top', 
                    fontsize=10, fontweight='bold', color=soft_text_color)
        
        # BOTTOM SUBPLOT: Maximum Drawdown Duration (lollipop chart)
        # Start vlines slightly above 0 to avoid horizontal line at y=0
        ax3.vlines(x, max(drawdown_durations) * 0.01, drawdown_durations, linewidth=6, colors=[colors[i % len(colors)] for i in range(n_securities)])
        scatter = ax3.scatter(x, drawdown_durations, s=250, zorder=3, marker='o', 
                            c=[colors[i % len(colors)] for i in range(n_securities)])
        ax3.set_ylabel('Max DD Days', fontsize=12, fontweight='bold', color=soft_text_color)
        # Remove x-axis label for cleaner look since we have data labels
        
        # Set appropriate limits for duration - start slightly above 0
        if drawdown_durations:
            max_duration = max(drawdown_durations)
            ax3.set_ylim(max_duration * 0.01, max_duration + max_duration * 0.2)
        
        # Add symbol labels below the bottom chart (like working sample)
        ax3.set_xticks(x)
        ax3.set_xticklabels(securities, fontsize=12, fontweight='bold', color=soft_text_color)
        
        # IMMEDIATELY remove ax3 styling after setup
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.spines['bottom'].set_visible(True)
        ax3.spines['left'].set_visible(False)
        ax3.tick_params(axis='y', which='both', left=False, right=False, labelleft=False, labelright=False)
        ax3.set_yticklabels([])  # Remove Y-axis numbers completely
        ax3.grid(False)
        
        # Annotate duration bubbles
        for i, val in enumerate(drawdown_durations):
            ax3.text(i, val + max(drawdown_durations) * 0.05, f'{int(val)} days', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold', color=soft_text_color)
        
        # Final cleanup - remove zero lines and set background
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_facecolor('white')
            # Remove all zero lines
            ax.axhline(y=0, visible=False)
            ax.axvline(x=0, visible=False)
            # Ensure no grid lines
            ax.grid(False)
        
        # Set white background for the figure
        fig.patch.set_facecolor('white')
        
        # Force all spines and ticks to be invisible - prevent any conflicting calls
        # Top subplot (ax1)
        for spine in ax1.spines.values():
            spine.set_visible(False)
        ax1.tick_params(axis='both', which='both', left=False, right=False, top=False, bottom=False, 
                       labelleft=False, labelright=False, labeltop=False, labelbottom=False)
        
        # Middle subplot (ax2) 
        for spine in ax2.spines.values():
            spine.set_visible(False)
        ax2.tick_params(axis='both', which='both', left=False, right=False, top=False, bottom=False, 
                       labelleft=False, labelright=False, labeltop=False, labelbottom=False)
        
        # Bottom subplot (ax3) - keep only bottom spine and x-labels
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False) 
        ax3.spines['left'].set_visible(False)
        ax3.spines['bottom'].set_visible(True)
        ax3.tick_params(axis='y', which='both', left=False, right=False, labelleft=False, labelright=False)
        
        # Secondary axis (ax4) - completely hidden
        for spine in ax4.spines.values():
            spine.set_visible(False)
        ax4.tick_params(axis='both', which='both', left=False, right=False, top=False, bottom=False, 
                       labelleft=False, labelright=False, labeltop=False, labelbottom=False)
        
        # Don't call tight_layout again as it will override our spacing fix
        
        # Save the chart with high DPI and minimal margins for mobile responsiveness
        chart_filename = f"{report_filename_base}_compound_performance_chart.png"
        chart_path = os.path.join(REPORTS_DIR, chart_filename)
        plt.savefig(chart_path, dpi=200, bbox_inches='tight', pad_inches=0, facecolor='white')
        plt.close()  # Important: close the figure to free memory
        
        logger.info(f"Generated compound performance chart: {chart_filename}")
        return chart_filename
        
    except Exception as e:
        logger.error(f"Error generating compound performance chart: {str(e)}")
        plt.close()  # Ensure figure is closed even on error
        return None 