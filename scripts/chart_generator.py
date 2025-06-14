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
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cumulative Return (%)', fontsize=12)
        
        # Format y-axis as percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}%'))
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        
        # Add horizontal line at 0%
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.8)
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Enhanced legend positioning for better handling of multiple series
        num_series = len(cumulative_returns.columns)
        if num_series <= 4:
            # Single column legend for few series
            ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
        elif num_series <= 8:
            # Two column legend for medium number of series
            ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True, ncol=2)
        else:
            # Compact legend outside plot area for many series
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, 
                     fancybox=True, shadow=True, ncol=1)
        
        # Add title inside chart area, centered at the top
        ax.text(0.5, 0.95, 'Cumulative Returns', transform=ax.transAxes, 
                fontsize=12, fontweight='bold', ha='center', va='top')
        
        # Tight layout with padding adjustment for legend
        if num_series > 8:
            plt.tight_layout(rect=[0, 0, 0.85, 1])  # Leave space for external legend
        else:
            plt.tight_layout()
        
        # Save the chart with high DPI for crisp quality
        chart_filename = f"{report_filename_base}_cumulative_returns.png"
        chart_path = os.path.join(REPORTS_DIR, chart_filename)
        plt.savefig(chart_path, dpi=200, bbox_inches='tight', facecolor='white')
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
            
            # Prepare trace parameters (simplified - lines only, no markers)
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
                'mode': 'lines'  # Include markers when specified
            }
            
            # Add marker parameters if applicable
            if style['marker'] is not None:
                # Calculate marker spacing (similar to matplotlib's markevery)
                total_points = len(cumulative_returns)
                marker_every = max(total_points // 15, 1)  # Same spacing as matplotlib
                
                # Create marker data with spacing
                marker_indices = list(range(0, total_points, marker_every))
                marker_x = [cumulative_returns.index[i] for i in marker_indices]
                marker_y = [cumulative_returns[column].iloc[i] * 100 for i in marker_indices]
                
                # Add a separate trace for markers only
                marker_trace = go.Scatter(
                    x=marker_x,
                    y=marker_y,
                    mode='markers',
                    marker=dict(
                        symbol=style['marker'],
                        color=style['marker_color'],
                        size=style['marker_size'],
                        line=dict(width=1, color=style['marker_color'])
                    ),
                    showlegend=False,  # Don't show in legend (already shown by line)
                    hoverinfo='skip',  # Don't show hover for markers
                    name=f"{column}_markers"
                )
                fig.add_trace(marker_trace)
                
                # Update main trace to lines only
                trace_params['mode'] = 'lines'
            else:
                trace_params['mode'] = 'lines'
            
            fig.add_trace(go.Scatter(**trace_params))
        
        # Configure layout to match matplotlib styling
        fig.update_layout(
            title={
                'text': 'Cumulative Returns',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 14, 'color': '#000000'}
            },
            xaxis_title='',  # Remove "Date" text
            yaxis_title='Cumulative Return (%)',
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
                bordercolor='rgba(128,128,128,0.3)',  # Lighter border
                borderwidth=0.5,  # Thinner border
                font=dict(size=9),  # Smaller font for iframe mode to prevent truncation
                itemsizing='constant',  # Ensure consistent sizing
                itemwidth=30  # Compact legend items
            ),
            margin=dict(l=50, r=20, t=50, b=50)  # Reduced margins to remove white space
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
            showline=True,
            linewidth=1,
            linecolor='black',
            ticksuffix='%'
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
                            'legend.bordercolor': 'gray',
                            'legend.borderwidth': 1
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
        plt.tight_layout(pad=2.0)
        
        # Save the chart with high DPI for crisp quality
        chart_filename = f"{report_filename_base}_cagr_chart.png"
        chart_path = os.path.join(REPORTS_DIR, chart_filename)
        plt.savefig(chart_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()  # Important: close the figure to free memory
        
        return chart_filename
        
    except Exception as e:
        logger.error(f"Error generating CAGR bar chart: {str(e)}")
        plt.close()  # Ensure figure is closed even on error
        return None 