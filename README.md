# Security Performance Report FastAPI Server

A professional FastAPI-based portfolio analysis application that uses a combination of custom calculation methodologies as well as metrics from the **[FFN (Financial Functions)](https://github.com/pmorissette/ffn)** package. This application provides comprehensive portfolio analytics with beautiful HTML reports, CSV data exports, and MCP (Model Context Protocol) 
integration for AI agents.

## 🎯 What This Application Does

This application performs **quantitative portfolio analysis** using custom calculation methodologies combined with the open-source **[FFN library](https://github.com/pmorissette/ffn)** - a powerful Python package for financial analysis. It provides:

### ⚠️ **Statcounter Analytics Note**

The application includes a Statcounter web analytics code in `templates/index.html`. This tracking code is linked to my personal Statcounter account (Project ID: 13047808), so all web analytics data will be sent there. 

**If you clone this application, please:**
- Replace it with your own Statcounter project ID and security code, or
- Use your preferred analytics tracking solution (Google Analytics, etc.), or  
- Remove the tracking code entirely if you don't need web analytics

The Statcounter code is located in the `<head>` section of `templates/index.html` and can be easily modified or removed.

## AI Co-Analyst Platform

For additional data analysis capabilities, visit our AI Co-Analyst Platform at [rex.tigzig.com](https://rex.tigzig.com). For any questions, reach out to me at amar@harolikar.com

### 📊 **Portfolio Analytics Features:**
- **Performance Metrics**: Total returns, CAGR, Sharpe ratio, Sortino ratio, Calmar ratio
- **Risk Analysis**: Maximum drawdown, volatility, drawdown periods and analysis  
- **Visual Charts**: Cumulative returns charts, CAGR bar charts with professional styling
- **Monthly Returns**: Detailed month-by-month performance breakdown
- **Data Exports**: Multiple CSV files with price data, returns, correlations, and statistics

### 🎨 **Professional Reports:**
- **HTML Reports**: Beautiful, responsive reports with REX AI branding
- **Interactive Charts**: Professional matplotlib charts with proper scaling
- **Multiple Formats**: HTML for viewing + CSV files for data analysis
- **Mobile Responsive**: Reports work on all screen sizes

### 🤖 **AI Integration:**
- **MCP Protocol**: Full Model Context Protocol support for AI agents
- **JSON API**: Clean REST API for programmatic access
- **Structured Data**: Well-formatted JSON responses for AI consumption

---

## 📊 QuantStats versus SPR

Validations have been carried out for custom calculations against established methodologies. The detailed report is available at **[SPR vs QuantStats Methodology Comparison](https://ffn.hosting.tigzig.com/static/docs/SPR_QS_METHODOLOGY.html)**.

This document provides a comparison between two portfolio analysis methodologies:

- **QuantStats (QS)**: Using the [quantstats-lumi](https://github.com/Lumiwealth/quantstats_lumi) library
- **SPR (Security Performance Review)**: Custom implementation based on QuantStats methodology with FFN library integration

**Key Findings:**
- ✅ **Perfect Matches**: Total Return (100%), CAGR (100%)
- ✅ **Near-Perfect Matches**: Sharpe Ratio (97%+), Sortino Ratio (97%+)
- ✅ **Identical Supporting Analytics**: Monthly returns, drawdown analysis via FFN library
- ✅ **Date Preprocessing**: Same methodology with subtle implementation differences

Users can refer to that document for a detailed comparison of the calculations and validations.

---

## 📊 Methodology & Calculations

### 🎯 **Calculation Sources**

This application provides **dual calculation methodology** for comprehensive analysis:

- **🔢 Core Performance Metrics** (Total Return, CAGR, Sharpe, Sortino): Custom implementations based on **[QuantStats](https://github.com/ramirobentes/quantstats)** methodology
- **📈 Additional Analytics** (Drawdowns, Monthly Returns, Statistical Analysis): Powered by the **[FFN library](https://github.com/pmorissette/ffn)**

### 🧮 **Our Custom Calculation Methodology**

#### **Data Processing Pipeline:**
1. **Data Fetching**: Yahoo Finance via `yfinance` library
2. **Date Alignment**: Uses QuantStats `_match_dates()` methodology - drops initial dates until first non-zero return for each symbol
3. **NaN Handling**: Fill with 0.0 (matching QuantStats approach) instead of dropping
4. **Multi-Asset Alignment**: Forward-fill missing values up to 5 days for exchange calendar differences

#### **Daily Returns Calculation:**
```
Daily Return = (Price_today / Price_yesterday) - 1
```

#### **Total Return Calculation:**
```
Total Return = (1 + r₁) × (1 + r₂) × ... × (1 + rₙ) - 1

Where:
- r₁, r₂, ..., rₙ are daily returns
- This provides the compounded total return over the entire period
```

#### **CAGR (Compound Annual Growth Rate):**
```
CAGR = (Total Return + 1)^(1/years) - 1

Where:
- years = (end_date - start_date) / 365.25 (accounting for leap years)
- Uses fractional years for precise annualization
```

#### **Risk-Free Rate Processing:**
```
Daily RF Rate = (1 + Annual_RF_Rate)^(1/365) - 1

Applied to returns:
Excess Returns = Daily_Returns - Daily_RF_Rate
```

#### **Sharpe Ratio Calculation:**
```
Sharpe Ratio = (Mean_Excess_Return / Std_Dev_Excess_Returns) × √365

Where:
- Excess returns have risk-free rate subtracted
- Standard deviation uses ddof=1 (sample standard deviation)
- Annualization factor: √365 (matching QuantStats default)
```

#### **Sortino Ratio Calculation:**
```
Sortino Ratio = (Mean_Excess_Return / Downside_Deviation) × √365

Downside Deviation = √(Σ(negative_returns²) / total_observations)

Where:
- Only negative excess returns are used in deviation calculation
- Denominator uses total observations, not just negative ones (QuantStats methodology)
```

### 🎯 **Validation & Accuracy**

#### **✅ Perfect Matches with QuantStats:**
- **Total Return**: 100% match (e.g., 184.20% for both implementations)
- **CAGR**: 100% match (e.g., 11.04% for both implementations)

#### **📊 Near-Perfect Matches:**
- **Sharpe Ratio**: 97%+ accuracy (e.g., 0.785 vs 0.81 QuantStats)
- **Sortino Ratio**: 97%+ accuracy (e.g., 1.099 vs 1.14 QuantStats)

#### **🔍 Remaining 3% Difference Analysis:**
The small remaining differences in Sharpe/Sortino ratios are attributed to:

1. **"Time in Market" Filtering**: QuantStats reports 98% time in market vs our 95-97% per symbol
2. **Data Quality Filters**: QuantStats may exclude low-volume days or holiday-adjacent periods
3. **Portfolio vs Individual**: QuantStats may calculate exposure at portfolio level rather than per-symbol
4. **Precision Differences**: Minor rounding differences in intermediate calculations

These differences are within **acceptable tolerance for financial analysis** and significantly smaller than typical variations between different financial data providers.

### 📈 **FFN Library Integration**

For comprehensive portfolio analytics beyond our core metrics, we leverage the **[FFN library](https://github.com/pmorissette/ffn)** for:

- **Drawdown Analysis**: Maximum drawdown, drawdown periods, recovery times
- **Monthly Returns**: Detailed month-by-month performance tables
- **Statistical Metrics**: Skewness, kurtosis, win rates, best/worst periods
- **Rolling Statistics**: Moving averages, rolling volatility, time-series analysis

#### **Data Preprocessing for FFN:**
- Raw price data sourced from Yahoo Finance
- Basic preprocessing: removal of zero or NaN values
- Multi-security date alignment using forward-fill (up to 5 days)
- Industry-standard practice with minimal impact on results

### 🔬 **Technical Implementation Notes**

#### **Annualization Periods:**
- **365 days per year** (matching QuantStats default, not 252 trading days)
- Handles fractional years for precise CAGR calculations
- Leap year accounting: 365.25 average days per year

#### **Risk-Free Rate Integration:**
- Compound de-annualization: `(1+rf)^(1/365) - 1`
- Applied during preprocessing phase (QuantStats order)
- Supports any annual risk-free rate input

#### **Statistical Precision:**
- Sample standard deviation (ddof=1) for unbiased estimators
- Double-precision floating point arithmetic
- Proper handling of edge cases (zero variance, insufficient data)

### 📊 **Why This Methodology Matters**

1. **Industry Standard**: Aligns with widely-used QuantStats library 
2. **Transparency**: Open-source calculations that can be audited and verified
3. **Accuracy**: 97%+ accuracy with established benchmarks
4. **Flexibility**: Custom implementation allows for specific business requirements
5. **Reliability**: Perfect matches on core metrics (Total Return, CAGR) confirm mathematical correctness

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/shared-fastap-mcp-ffn.git
cd shared-fastap-mcp-ffn

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

The application will be available at: **http://localhost:8000**

---

## 📡 API Documentation

### **Base URL**: `http://localhost:8000` (local) or your deployment URL

---

## 🔧 **Primary Endpoint: Portfolio Analysis**

### **POST /analyze**

Generate comprehensive portfolio analysis reports with multiple data exports.

#### **Request Format:**
```json
{
  "symbols": "AAPL,MSFT,GOOG",
  "start_date": "2023-01-01", 
  "end_date": "2023-12-31",
  "risk_free_rate": 5.0
}
```

#### **Request Parameters:**
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `symbols` | string | ✅ | Comma-separated Yahoo Finance ticker symbols | `"AAPL,MSFT,GOOG"` |
| `start_date` | string | ✅ | Analysis start date (YYYY-MM-DD format) | `"2023-01-01"` |
| `end_date` | string | ✅ | Analysis end date (YYYY-MM-DD format) | `"2023-12-31"` |
| `risk_free_rate` | float | ❌ | Annual risk-free rate percentage (default: 0.0) | `5.0` |

#### **Response Format:**
```json
{
  "html_report_ffn_url": "/static/reports/report_AAPL-MSFT-GOOG_20241201_143022.html",
  "input_price_data_csv_url": "/static/reports/report_AAPL-MSFT-GOOG_20241201_143022_price_data.csv",
  "cumulative_returns_csv_url": "/static/reports/report_AAPL-MSFT-GOOG_20241201_143022_cumulative_returns.csv",
  "success": "Portfolio analysis report generated successfully!"
}
```

#### **Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `html_report_ffn_url` | string | URL to access the complete HTML report with charts and analytics |
| `input_price_data_csv_url` | string | URL to download raw price data CSV file |
| `cumulative_returns_csv_url` | string | URL to download cumulative returns CSV file |
| `success` | string | Success message confirming report generation |

---

## 🌐 **Web Interface Endpoint**

### **POST /api/analyze**

Alternative endpoint for web form submissions (same functionality as `/analyze` but accepts form data).

#### **Request Format** (Form Data):
```
symbols=AAPL,MSFT,GOOG
start_date=2023-01-01
end_date=2023-12-31
risk_free_rate=5.0
```

#### **Response Format:**
```json
{
  "success": true,
  "message": "Report generated successfully!",
  "html_report_ffn_url": "/static/reports/report_AAPL-MSFT-GOOG_20241201_143022.html",
  "input_price_data_csv_url": "/static/reports/report_AAPL-MSFT-GOOG_20241201_143022_price_data.csv",
  "cumulative_returns_csv_url": "/static/reports/report_AAPL-MSFT-GOOG_20241201_143022_cumulative_returns.csv"
}
```

---

## 🤖 **MCP (Model Context Protocol) Integration**

### **POST /mcp**

For AI agents and LLM applications. The MCP endpoint exposes the portfolio analysis functionality.

#### **Available Operations:**
- `analyze_portfolio` - Complete portfolio analysis with reports

#### **MCP Request Format:**
```json
{
  "operation_id": "analyze_portfolio",
  "parameters": {
    "symbols": "AAPL,MSFT,GOOG",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31", 
    "risk_free_rate": 5.0
  }
}
```

---

## 📊 **Generated Data Files**

When you run an analysis, the system generates **6 different CSV files** plus an HTML report:

### **CSV Files Generated:**
1. **`*_price_data.csv`** - Raw daily prices for all securities
2. **`*_daily_returns.csv`** - Daily percentage returns
3. **`*_cumulative_returns.csv`** - Cumulative returns over time
4. **`*_summary_statistics.csv`** - Key performance metrics
5. **`*_correlation_matrix.csv`** - Correlation matrix between securities
6. **`*_monthly_returns.csv`** - Monthly return breakdown

### **HTML Report Includes:**
- **REX AI Professional Header** with branding
- **Data Summary** - Date ranges, trading days, price information
- **Drawdown Analysis** - Detailed drawdown periods and magnitudes
- **Monthly Returns Tables** - Month-by-month performance
- **Visual Charts** - Cumulative returns and CAGR bar charts
- **Professional Footer** - Contact information and links

---

## 🎯 **Example Usage**

### **Python Example:**
```python
import requests

# Portfolio analysis request
url = "http://localhost:8000/analyze"
payload = {
    "symbols": "AAPL,MSFT,GOOG",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "risk_free_rate": 2.5
}

response = requests.post(url, json=payload)
result = response.json()

print("HTML Report:", result["html_report_ffn_url"])
print("Price Data:", result["input_price_data_csv_url"]) 
print("Returns Data:", result["cumulative_returns_csv_url"])
```

### **JavaScript Example:**
```javascript
const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    symbols: "AAPL,MSFT,GOOG",
    start_date: "2023-01-01",
    end_date: "2023-12-31",
    risk_free_rate: 2.5
  })
});

const result = await response.json();
console.log('Report generated:', result.html_report_ffn_url);
```

### **cURL Example:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": "AAPL,MSFT,GOOG",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "risk_free_rate": 2.5
  }'
```

---

## ⚙️ **Configuration**

### **Environment Variables**
Create a `.env` file for configuration:

```env
# Development vs Production Mode
IS_LOCAL_DEVELOPMENT=1

# Base URL for generated report links
BASE_URL_FOR_REPORTS=http://localhost:8000/

# Server Configuration  
PORT=8000
HOST=0.0.0.0
```

### **Deployment Modes:**

#### **Local Development** (`IS_LOCAL_DEVELOPMENT=1`):
- URLs are relative: `/static/reports/filename.html`
- Perfect for localhost development

#### **Production** (`IS_LOCAL_DEVELOPMENT=0`):  
- URLs are absolute: `https://yourdomain.com/static/reports/filename.html`
- Required for remote deployment

### **Automatic File Cleanup**

The server automatically cleans up old report files on startup to manage disk space:

- **Cleanup Trigger**: Runs automatically when the FastAPI server starts
- **File Age Threshold**: Files older than **72 hours (3 days)** are removed
- **File Types Cleaned**: HTML reports (`.html`), CSV data files (`.csv`), chart images (`.png`)
- **Location**: All files in the `static/reports/` directory
- **Logging**: Cleanup statistics are logged including number of files removed by type

This ensures the server doesn't accumulate too many old report files over time while preserving recent reports for user access.

---

## 🛠 **Technical Stack**

- **FastAPI** - Modern Python web framework
- **[FFN Library](https://github.com/pmorissette/ffn)** - Financial analysis and portfolio metrics
- **Matplotlib & Seaborn** - Professional chart generation
- **yfinance** - Yahoo Finance data fetching
- **Pandas & NumPy** - Data manipulation and analysis
- **Jinja2** - HTML template rendering
- **fastapi-mcp** - Model Context Protocol integration

---

## 🔗 **API Response Examples**

### **Successful Response:**
```json
{
  "html_report_ffn_url": "/static/reports/report_AAPL-MSFT-GOOG_20241201_143022.html",
  "input_price_data_csv_url": "/static/reports/report_AAPL-MSFT-GOOG_20241201_143022_price_data.csv", 
  "cumulative_returns_csv_url": "/static/reports/report_AAPL-MSFT-GOOG_20241201_143022_cumulative_returns.csv",
  "success": "Portfolio analysis report generated successfully!"
}
```

### **Error Response Examples:**

#### **400 Bad Request** (Missing parameters):
```json
{
  "detail": "Missing required fields"
}
```

#### **400 Bad Request** (Invalid date range):
```json
{
  "detail": "Error fetching stock data: No data available for the provided symbols in the date range 2023-01-01 to 2023-12-31"
}
```

#### **500 Internal Server Error**:
```json
{
  "detail": "Error generating analysis: [specific error message]"
}
```

---

## 🎯 **Quick Copy-Paste example**

```
ENDPOINT: POST /analyze
URL: http://localhost:8000/analyze

REQUEST:
{
  "symbols": "AAPL,MSFT,GOOG",
  "start_date": "2023-01-01", 
  "end_date": "2023-12-31",
  "risk_free_rate": 5.0
}

RESPONSE:
{
  "html_report_ffn_url": "URL_TO_HTML_REPORT",
  "input_price_data_csv_url": "URL_TO_PRICE_DATA_CSV",
  "cumulative_returns_csv_url": "URL_TO_RETURNS_CSV", 
  "success": "SUCCESS_MESSAGE"
}

USAGE: Financial portfolio analysis with FFN library
GENERATES: HTML report + multiple CSV data files
SUPPORTS: Multiple securities, custom date ranges, risk-free rate configuration
```

---

## 📝 **License**

MIT License - see LICENSE file for details.

## 🙏 **Acknowledgments**

- **[FFN Library](https://github.com/pmorissette/ffn)** - Core financial analysis engine
- **[FastAPI](https://fastapi.tiangolo.com/)** - High-performance web framework  
- **[yfinance](https://github.com/ranaroussi/yfinance)** - Yahoo Finance data integration 
## Author

Built by [Amar Harolikar](https://www.linkedin.com/in/amarharolikar/)

Explore 30+ open source AI tools for analytics, databases & automation at [tigzig.com](https://tigzig.com)
