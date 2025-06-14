#!/usr/bin/env python3
"""
Markdown to HTML Converter for Documentation
Converts the SPR_QS_METHODOLOGY.md file to HTML with custom styling
for serving via FastAPI static files.
"""

import os
import sys
import markdown
from datetime import datetime
import shutil

def ensure_directories():
    """Create necessary directories for documentation output."""
    directories = [
        'static/docs',
        'static/docs/assets'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Directory ensured: {directory}")

def get_custom_css():
    """Generate custom CSS for the documentation."""
    css_content = """
/* QuantStats Methodology Documentation Styles */
* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background-color: #fafafa;
}

/* Header Styles */
h1 {
    color: #2c3e50;
    border-bottom: 3px solid #3498db;
    padding-bottom: 10px;
    margin-bottom: 30px;
    font-size: 2.2em;
}

h2 {
    color: #34495e;
    border-left: 4px solid #3498db;
    padding-left: 15px;
    margin-top: 40px;
    margin-bottom: 20px;
    font-size: 1.6em;
}

h3 {
    color: #2c3e50;
    margin-top: 30px;
    margin-bottom: 15px;
    font-size: 1.3em;
}

h4 {
    color: #34495e;
    margin-top: 25px;
    margin-bottom: 12px;
    font-size: 1.1em;
}

/* Code Blocks */
pre {
    background-color: #2d3748;
    color: #e2e8f0;
    padding: 20px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 20px 0;
    border-left: 4px solid #3498db;
}

code {
    background-color: #f1f3f4;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 0.9em;
    color: #e74c3c;
}

pre code {
    background-color: transparent;
    padding: 0;
    color: #e2e8f0;
}

/* Tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 20px 0;
    background-color: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

th, td {
    border: 1px solid #ddd;
    padding: 12px 15px;
    text-align: left;
}

th {
    background-color: #3498db;
    color: white;
    font-weight: 600;
}

tr:nth-child(even) {
    background-color: #f8f9fa;
}

tr:hover {
    background-color: #e8f4fd;
}

/* Lists */
ul, ol {
    margin: 15px 0;
    padding-left: 30px;
}

li {
    margin-bottom: 8px;
}

/* Blockquotes */
blockquote {
    border-left: 4px solid #95a5a6;
    margin: 20px 0;
    padding: 10px 20px;
    background-color: #ecf0f1;
    border-radius: 0 8px 8px 0;
}

/* Status Indicators */
.status-success {
    color: #27ae60;
    font-weight: bold;
}

.status-warning {
    color: #f39c12;
    font-weight: bold;
}

.status-error {
    color: #e74c3c;
    font-weight: bold;
}

/* Mathematical Formulas */
.math-block {
    background-color: #f8f9fa;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    margin: 20px 0;
    font-family: 'Times New Roman', serif;
    text-align: center;
}

/* Responsive Design */
@media (max-width: 768px) {
    body {
        padding: 10px;
        font-size: 14px;
    }
    
    h1 {
        font-size: 1.8em;
    }
    
    h2 {
        font-size: 1.4em;
    }
    
    table {
        font-size: 12px;
    }
    
    pre {
        padding: 15px;
        font-size: 12px;
    }
}

/* Remove old doc-header styles since we're using inline styles from FFN reports */

/* Emoji support */
.emoji {
    font-style: normal;
    font-size: 1.2em;
}

/* Highlight boxes */
.highlight-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
}

.highlight-box h3 {
    color: white;
    margin-top: 0;
}
"""
    return css_content

def get_html_template():
    """Generate HTML template with metadata."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="QuantStats vs SPR Methodology Validation and Comparison Documentation">
    <meta name="keywords" content="QuantStats, Portfolio Analysis, Financial Metrics, CAGR, Sharpe Ratio">
    <meta name="author" content="SPR Analytics Team">
    <title>QuantStats vs SPR: Methodology Documentation</title>
    <link rel="stylesheet" href="assets/docs.css">
    <link href="https://cdn.tailwindcss.com" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50">
    <!-- Header Section (same as FFN reports) -->
    <header style="
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: white;
        padding: 6px 0;
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 16px;
    ">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 12px; font-size: 16px; font-weight: 600;">
                <!-- Icons first -->
                <div style="display: flex; align-items: center; gap: 3px; font-size: 18px;">
                    <span style="font-family: 'Times New Roman', serif; font-style: italic; font-weight: 600;">f(x)</span>
                    <span style="font-family: monospace; font-weight: 600; letter-spacing: -1px;">&lt;/&gt;</span>
                </div>
                <!-- REX text with full hyperlink -->
                <a href="https://rex.tigzig.com" target="_blank" rel="noopener noreferrer" style="color: #fbbf24; text-decoration: none; font-weight: 600;">
                    REX <span style="color: #ffffff; font-weight: 600;">: AI Co-Analyst</span>
                </a>
                <span style="color: #ffffff; font-weight: 500;">- Documentation</span>
            </div>
        </div>
    </header>

    <!-- Main Content Area -->
    <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px 32px 24px;">
        
        <!-- Document Title Section -->
        <div class="mb-6">
            <h1 class="text-4xl font-bold text-blue-900 mb-2">QuantStats Vs. SPR (Security Performance Report)</h1>
            <h2 class="text-2xl font-medium text-blue-700 mb-3">Methodology Validation, Reconciliation & Comparisons</h2>
                         <p style="font-size: 14px; color: #6b7280; margin-bottom: 8px; line-height: 1.4; margin-top: 0;">
                 For any questions, drop a note at 
                 <a href="mailto:amar@harolikar.com" style="color: #1d4ed8; text-decoration: none; font-weight: 500;">amar@harolikar.com</a>
             </p>
        </div>
        
        {content}
        
                 <!-- Last Updated Info -->
         <div style="
             font-size: 0.9em;
             color: #7f8c8d;
             text-align: right;
             margin-top: 30px;
             padding-top: 20px;
             border-top: 1px solid #ecf0f1;
         ">
             <p><strong>Last Updated:</strong> {timestamp}</p>
         </div>
        
                 <!-- Note Disclaimer Box -->
         <div style="
             background: rgba(255,248,220,0.8);
             border: 1px solid #fbbf24;
             border-radius: 6px;
             padding: 12px;
             margin: 24px 0 16px 0;
             font-size: 13px;
             color: #92400e;
             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
             line-height: 1.5;
         ">
             <strong style="font-weight: bold !important;">Note:</strong> This documentation is for informational purposes only and should not be considered as investment advice. The methodologies described here compare QuantStats-Lumi and Security Performance Report (SPR) implementations. SPR uses custom calculations as well as FFN package for some of the metrics. While some of the calculations metrics have been validated for consistency, users are encouraged to refer to 
             <a href="https://github.com/amararun/shared-fastapi-mcp-ffn" target="_blank" rel="noopener noreferrer" style="color: #1d4ed8; text-decoration: none; font-weight: 500;">GitHub Repo for SPR</a>, the 
             <a href="https://github.com/pmorissette/ffn" target="_blank" rel="noopener noreferrer" style="color: #1d4ed8; text-decoration: none; font-weight: 500;">official documentation for FFN</a> and 
             <a href="https://github.com/Lumiwealth/quantstats_lumi" target="_blank" rel="noopener noreferrer" style="color: #1d4ed8; text-decoration: none; font-weight: 500;">QuantStats documentation</a>
             for full methodology details. Always validate outputs and interpret results in light of your specific analytical objectives.
         </div>
        
        <!-- Footer (same as FFN reports) -->
        <footer style="
            background: rgba(255,255,255,0.5);
            border-top: 1px solid #e0e7ff;
            padding: 8px 0;
            margin-top: 20px;
            font-size: 12px;
            color: #1e1b4b;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-weight: normal;
        ">
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px;">
                    <div style="font-size: 12px; color: rgba(30, 27, 75, 0.7); font-weight: normal;">
                        Amar Harolikar <span style="margin: 0 6px; color: #c7d2fe;">•</span>
                        Specialist - Decision Sciences & Applied Generative AI <span style="margin: 0 6px; color: #c7d2fe;">•</span>
                        <a href="mailto:amar@harolikar.com" style="color: #4338ca; text-decoration: none; font-weight: normal;">amar@harolikar.com</a>
                    </div>
                    <div style="display: flex; align-items: center; gap: 16px; font-size: 12px;">
                        <a href="https://www.linkedin.com/in/amarharolikar" target="_blank" rel="noopener noreferrer"
                           style="color: #4338ca; text-decoration: none; font-weight: normal;">
                            LinkedIn
                        </a>
                        <a href="https://github.com/amararun" target="_blank" rel="noopener noreferrer"
                           style="color: #4338ca; text-decoration: none; font-weight: normal;">
                            GitHub
                        </a>
                        <a href="https://rex.tigzig.com" target="_blank" rel="noopener noreferrer"
                           style="color: #4338ca; text-decoration: none; font-weight: normal;">
                            rex.tigzig.com
                        </a>
                        <a href="https://tigzig.com" target="_blank" rel="noopener noreferrer"
                           style="color: #4338ca; text-decoration: none; font-weight: normal;">
                            tigzig.com
                        </a>
                    </div>
                </div>
            </div>
        </footer>
        
    </div>
    
    <script>
        // Add some basic interactivity for tables
        document.addEventListener('DOMContentLoaded', function() {
            // Add click-to-highlight for code blocks
            const codeBlocks = document.querySelectorAll('pre');
            codeBlocks.forEach(block => {
                block.addEventListener('click', function() {
                    if (window.getSelection) {
                        const selection = window.getSelection();
                        const range = document.createRange();
                        range.selectNodeContents(this);
                        selection.removeAllRanges();
                        selection.addRange(range);
                    }
                });
                block.style.cursor = 'pointer';
                block.title = 'Click to select all code';
            });
        });
    </script>
</body>
</html>"""

def convert_markdown_to_html(md_file_path, output_dir):
    """Convert markdown file to HTML with custom styling."""
    
    # Check if markdown file exists
    if not os.path.exists(md_file_path):
        print(f"Error: Markdown file not found: {md_file_path}")
        return False
    
    try:
        # Read markdown content
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Remove the first main header since we have our own HTML header
        lines = md_content.split('\n')
        filtered_lines = []
        skip_first_header = True
        
        for line in lines:
            # Skip the first level 1 header (starts with # but not ##)
            if skip_first_header and line.startswith('# ') and not line.startswith('## '):
                skip_first_header = False
                continue
            filtered_lines.append(line)
        
        md_content = '\n'.join(filtered_lines)
        
        # Configure markdown with extensions
        md = markdown.Markdown(extensions=[
            'extra',           # Tables, fenced code blocks, etc.
            'codehilite',      # Syntax highlighting
            'toc',             # Table of contents
            'sane_lists',      # Better list handling
            'smarty'           # Smart quotes and dashes
        ])
        
        # Convert markdown to HTML
        html_content = md.convert(md_content)
        
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Generate complete HTML with template
        template = get_html_template()
        full_html = template.replace('{content}', html_content).replace('{timestamp}', timestamp)
        
        # Write HTML file
        html_file_path = os.path.join(output_dir, 'SPR_QS_METHODOLOGY.html')
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        # Write CSS file
        css_file_path = os.path.join(output_dir, 'assets', 'docs.css')
        with open(css_file_path, 'w', encoding='utf-8') as f:
            f.write(get_custom_css())
        
        print(f"Successfully converted markdown to HTML")
        print(f"   HTML: {html_file_path}")
        print(f"   CSS: {css_file_path}")
        
        return True
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        return False

def main():
    """Main function to run the conversion."""
    print("Starting Markdown to HTML conversion...")
    print("=" * 50)
    
    # Define paths
    md_file_path = 'docs/SPR_QS_METHODOLOY.md'
    output_dir = 'static/docs'
    
    # Ensure directories exist
    ensure_directories()
    
    # Convert markdown to HTML
    success = convert_markdown_to_html(md_file_path, output_dir)
    
    if success:
        print("=" * 50)
        print("Conversion completed successfully!")
        print("\nGenerated files:")
        print(f"   - static/docs/SPR_QS_METHODOLOGY.html")
        print(f"   - static/docs/assets/docs.css")
        print("\nAccess URLs (when server is running):")
        print(f"   - Local: http://localhost:8000/static/docs/SPR_QS_METHODOLOGY.html")
        print(f"   - Remote: https://your-app.com/static/docs/SPR_QS_METHODOLOGY.html")
        print("\nFrontend Integration Examples:")
        print("   - Direct Link: <a href='URL' target='_blank'>View Docs</a>")
        print("   - Iframe: <iframe src='URL' width='100%' height='600px'></iframe>")
        print("   - Fetch: fetch('URL').then(res => res.text())")
        
    else:
        print("Conversion failed. Please check error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 