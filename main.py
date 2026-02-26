from fastapi import FastAPI, Request, Query, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import ffn
import os
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, date, timedelta
import logging
import warnings
from dotenv import load_dotenv
import io
from contextlib import redirect_stdout, asynccontextmanager
import asyncio
import requests
from fastapi_mcp import FastApiMCP
import traceback
import httpx
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import seaborn as sns
import plotly.graph_objects as go
import plotly.offline as pyo
from plotly.subplots import make_subplots

# Import chart generation functions
from scripts.chart_generator import (
    generate_cumulative_returns_chart,
    generate_plotly_cumulative_returns_chart,
    generate_cagr_bar_chart,
    generate_compound_performance_chart
)

# Import report generation functions
from scripts.report_generator import (
    generate_perf_report,
    generate_csv_exports,
    construct_report_url,
    set_environment_config
)

# Import data fetching functions
from scripts.data_fetcher import (
    get_stock_data,
    validate_symbols,
    validate_date_range
)

# Load environment variables
load_dotenv()

# Get environment variables for URL handling with multiple fallback checks
IS_LOCAL_DEVELOPMENT_RAW = os.getenv('IS_LOCAL_DEVELOPMENT', '0')
# Check for various truthy values
IS_LOCAL_DEVELOPMENT = IS_LOCAL_DEVELOPMENT_RAW.lower() in ['1', 'true', 'yes', 'on']
BASE_URL_FOR_REPORTS = os.getenv('BASE_URL_FOR_REPORTS')

# Configure logging (must be before any logger usage)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# If no .env file exists, default to local development for localhost
if not IS_LOCAL_DEVELOPMENT and not BASE_URL_FOR_REPORTS:
    logger.warning("No .env file found and no environment variables set. Defaulting to local development mode.")
    IS_LOCAL_DEVELOPMENT = True

# Configuration from environment variables
RATE_LIMIT = os.getenv("RATE_LIMIT", "30/minute")
MAX_CONCURRENT_PER_IP = int(os.getenv("MAX_CONCURRENT_PER_IP", "3"))
MAX_CONCURRENT_GLOBAL = int(os.getenv("MAX_CONCURRENT_GLOBAL", "6"))


def get_client_ip(request: Request) -> str:
    for header in ("x-original-client-ip", "cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
        val = request.headers.get(header)
        if val:
            return val.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# Rate limiter setup
limiter = Limiter(key_func=get_client_ip)
_concurrency_lock = asyncio.Lock()
_ip_concurrency: dict[str, int] = {}
_global_concurrency = 0


async def check_concurrency(client_ip: str):
    """Check and increment concurrency counters. Raises HTTPException if limits exceeded."""
    global _global_concurrency
    async with _concurrency_lock:
        if _global_concurrency >= MAX_CONCURRENT_GLOBAL:
            raise HTTPException(status_code=503, detail="Server busy. Please try again shortly.")
        ip_count = _ip_concurrency.get(client_ip, 0)
        if ip_count >= MAX_CONCURRENT_PER_IP:
            raise HTTPException(status_code=429, detail="Too many concurrent requests. Please wait.")
        _global_concurrency += 1
        _ip_concurrency[client_ip] = ip_count + 1


async def release_concurrency(client_ip: str):
    """Decrement concurrency counters."""
    global _global_concurrency
    async with _concurrency_lock:
        _global_concurrency = max(0, _global_concurrency - 1)
        ip_count = _ip_concurrency.get(client_ip, 1)
        if ip_count <= 1:
            _ip_concurrency.pop(client_ip, None)
        else:
            _ip_concurrency[client_ip] = ip_count - 1

# Debug: Log environment variable values
logger.info(f"Environment Variables:")
logger.info(f"IS_LOCAL_DEVELOPMENT (raw): '{IS_LOCAL_DEVELOPMENT_RAW}'")
logger.info(f"IS_LOCAL_DEVELOPMENT (processed): {IS_LOCAL_DEVELOPMENT}")
logger.info(f"BASE_URL_FOR_REPORTS: '{BASE_URL_FOR_REPORTS}'")

# Suppress warnings
warnings.filterwarnings('ignore')

# Patch numpy for older FFN versions
np.Inf = np.inf

# Ensure reports directory exists
REPORTS_DIR = os.path.join('static', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# Configure the report generator module with environment settings
set_environment_config(IS_LOCAL_DEVELOPMENT, BASE_URL_FOR_REPORTS, REPORTS_DIR)

# Simple file cleanup function for startup
def cleanup_old_reports(max_age_hours: int = 72) -> dict:
    """
    Clean up old report files from the reports directory on server startup.
    
    Args:
        max_age_hours: Maximum age of files in hours before deletion (default: 72 hours = 3 days)
        
    Returns:
        Dictionary with cleanup statistics
    """
    try:
        logger.info(f"Starting file cleanup (max age: {max_age_hours} hours)")
        stats = {
            "total_removed": 0,
            "html_removed": 0,
            "csv_removed": 0,
            "png_removed": 0,
            "errors": 0
        }
        
        # Calculate cutoff time
        now = datetime.now()
        cutoff_time = now - timedelta(hours=max_age_hours)
        logger.info(f"Cutoff time for file cleanup: {cutoff_time}")
        
        # Check if reports directory exists
        if not os.path.exists(REPORTS_DIR):
            logger.info(f"Reports directory does not exist: {REPORTS_DIR}")
            return stats
        
        # Process all files in the reports directory
        for filename in os.listdir(REPORTS_DIR):
            file_path = os.path.join(REPORTS_DIR, filename)
            
            # Skip directories, only process files
            if os.path.isdir(file_path):
                continue
            
            try:
                # Get file modification time
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Check if file is older than cutoff
                if file_time < cutoff_time:
                    # Determine file type and update stats
                    if filename.endswith('.html'):
                        stats["html_removed"] += 1
                    elif filename.endswith('.csv'):
                        stats["csv_removed"] += 1
                    elif filename.endswith('.png'):
                        stats["png_removed"] += 1
                    
                    # Remove the file
                    os.remove(file_path)
                    logger.info(f"Removed old file: {filename}")
                    stats["total_removed"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                stats["errors"] += 1
        
        logger.info(f"File cleanup complete. Stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")
        return {"error": str(e), "total_removed": 0}

# Define lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("=" * 40)
    logger.info("FastAPI server with MCP integration is starting!")
    logger.info("MCP endpoint is available at: /mcp")
    logger.info("Using custom httpx client with 3-minute (180 second) timeout")
    
    # Run file cleanup on startup (keep files from last 3 days)
    logger.info("Running startup file cleanup...")
    cleanup_stats = cleanup_old_reports(max_age_hours=72)  # 3 days
    logger.info(f"Startup cleanup completed: {cleanup_stats}")
    
    # Log all available routes and their operation IDs
    logger.info("Available routes and operation IDs in FastAPI app:")
    fastapi_operations = []
    for route in app.routes:
        if hasattr(route, "operation_id"):
            logger.info(f"Route: {route.path}, Operation ID: {route.operation_id}")
            fastapi_operations.append(route.operation_id)
    
    yield  # This is where the FastAPI app runs
    
    # Shutdown code
    logger.info("=" * 40)
    logger.info("FastAPI server is shutting down")
    logger.info("=" * 40)

# Create a middleware for request logging
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log the request
        client_host = get_client_ip(request)
        logger.info(f"Request [{request_id}]: {request.method} {request.url.path} from {client_host}")
        
        # Try to log query parameters if any
        if request.query_params:
            logger.info(f"Request [{request_id}] params: {dict(request.query_params)}")
        
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log the response
            logger.info(f"Response [{request_id}]: {response.status_code} (took {process_time:.4f}s)")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request [{request_id}] failed after {process_time:.4f}s: {str(e)}")
            logger.error(traceback.format_exc())
            raise

# Initialize FastAPI app - minimal configuration
app = FastAPI(
    title="Security Performance Review (SPR) API",
    description="API for generating SPR portfolio analysis reports using custom calculations and FFN metrics",
    version="1.0.0",
    lifespan=lifespan
)

# Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"detail": "Rate limit exceeded. Please try again later."}
))
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# Configure CORS - wildcard origins, no credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add the logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add API Monitor middleware for centralized logging
from tigzig_api_monitor import APIMonitorMiddleware
app.add_middleware(
    APIMonitorMiddleware,
    app_name="MCP_FFN",
    include_prefixes=("/api/", "/analyze"),
)

# Simple request logging without custom middleware to avoid ASGI conflicts
import logging
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.disabled = False

# Mount static files
static_dir = os.path.join(os.getcwd(), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Define the request model
class PortfolioAnalysisRequest(BaseModel):
    """Request model for SPR (Security Performance Review) portfolio analysis generation."""
    symbols: str = Field(
        description="Stock symbols to analyze, comma-separated (e.g., 'AAPL,GOOG,MSFT'). Must be valid Yahoo Finance ticker symbols. Supports multiple symbols for SPR portfolio analysis using custom calculations and FFN metrics.",
        example="AAPL,MSFT,GOOG"
    )
    start_date: date = Field(
        description="Start date for SPR analysis. Should be at least 6 months before end_date for meaningful analysis. Format: YYYY-MM-DD",
        example="2023-01-01"
    )
    end_date: date = Field(
        description="End date for SPR analysis. Must be after start_date and not in the future. Format: YYYY-MM-DD",
        example="2023-12-31"
    )
    risk_free_rate: float = Field(
        default=0.0,
        description="Risk-free rate as annual percentage (e.g., 5.0 for 5%). Used in SPR custom Sharpe ratio and other risk-adjusted return calculations. Default is 0.0% if not provided.",
        example=5.0,
        ge=0.0,
        le=100.0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "symbols": "AAPL,MSFT,GOOG",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "risk_free_rate": 5.0
            }
        }

# Define the response model
class PortfolioAnalysisResponse(BaseModel):
    """Response model for SPR (Security Performance Review) portfolio analysis."""
    html_report_ffn_url: str = Field(
        description="URL to access the SPR HTML report with portfolio analysis and visualizations using custom calculations and FFN metrics"
    )
    input_price_data_csv_url: str = Field(
        description="URL to download the processed price data CSV file used in SPR analysis"
    )
    cumulative_returns_csv_url: str = Field(
        description="URL to download the cumulative returns data CSV file from SPR analysis"
    )
    success: str = Field(
        description="Success message indicating SPR report generation status"
    )

@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request,
    error: str = Query(None, description="Error message to display"),
    success: str = Query(None, description="Success message to display"),
    report_path: str = Query(None, description="Path to generated report")
):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "error": error,
            "success": success,
            "report_path": report_path,
            "report_generated": bool(report_path)
        }
    )

@app.post("/api/analyze")
@limiter.limit(RATE_LIMIT)
async def analyze_api(request: Request):
    """API endpoint for JavaScript form submission - returns JSON response for SPR analysis using custom calculations and FFN metrics."""
    client_ip = get_client_ip(request)
    await check_concurrency(client_ip)
    try:
        # Get form data from request
        form_data = await request.form()
        symbols = form_data.get("symbols")
        start_date = form_data.get("start_date")
        end_date = form_data.get("end_date")
        risk_free_rate = float(form_data.get("risk_free_rate", 0.0))

        if not all([symbols, start_date, end_date]):
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required fields"}
            )

        # Get stock data
        data = get_stock_data(symbols, start_date, end_date)

        # Generate report (this now returns html_url and csv_urls)
        report_result = generate_perf_report(data, risk_free_rate)

        # Extract the URLs from the result
        if isinstance(report_result, tuple):
            html_url, csv_urls = report_result
        else:
            html_url = report_result
            csv_urls = {}

        # Return JSON response
        return JSONResponse(
            content={
                "success": True,
                "message": "Report generated successfully!",
                "html_report_ffn_url": html_url,
                "input_price_data_csv_url": csv_urls.get('price_data', ''),
                "cumulative_returns_csv_url": csv_urls.get('cumulative_returns', '')
            }
        )

    except ValueError as e:
        logger.error(f"Validation error in API: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": "Validation error occurred"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in API: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": "Analysis failed. Please try again."}
        )
    finally:
        await asyncio.shield(release_concurrency(client_ip))

@app.post("/analyze", operation_id="analyze_portfolio", response_model=PortfolioAnalysisResponse)
@limiter.limit(RATE_LIMIT)
async def analyze(
    request: Request,
    analysis_request: PortfolioAnalysisRequest = Body(
        description="Portfolio analysis request parameters",
        example={
            "symbols": "AAPL,MSFT,GOOG",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "risk_free_rate": 5.0
        }
    )
):
    """
    Generates a comprehensive SPR (Security Performance Review) portfolio analysis report using custom calculations and FFN metrics.

    This endpoint performs detailed SPR portfolio analysis including:
    - Performance statistics using custom calculations (returns, volatility, Sharpe ratio, etc.)
    - Drawdown analysis using FFN library (maximum drawdown, drawdown periods)
    - Monthly returns breakdown by security via FFN

    Supports multiple stock symbols for SPR portfolio analysis. The risk-free rate is used in
    custom Sharpe ratio and other risk-adjusted return calculations.

    The SPR analysis is returned as an HTML report with:
    - Data summary with date ranges and price information
    - Comprehensive performance metrics table using custom calculations (including Sharpe ratios calculated with provided risk-free rate)
    - Detailed drawdown analysis for each security via FFN
    - Monthly return tables with color-coded performance via FFN

    Example request:
    {
        "symbols": "AAPL,MSFT,GOOG",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "risk_free_rate": 5.0
    }

    Parameters:
    - symbols: Comma-separated Yahoo Finance ticker symbols (e.g., 'AAPL,MSFT,GOOG'). Supports multiple symbols for SPR analysis.
    - start_date: SPR analysis start date (YYYY-MM-DD format)
    - end_date: SPR analysis end date (YYYY-MM-DD format)
    - risk_free_rate: Annual risk-free rate percentage (default: 0.0%). Used for custom Sharpe ratio calculations in SPR.

    Returns:
    - PortfolioAnalysisResponse with SPR HTML report URL and success message

    Raises:
    - HTTPException 400: Invalid parameters or insufficient data for SPR analysis
    - HTTPException 500: Data fetching or SPR processing errors

    Note: SPR analysis may take up to 2-3 minutes depending on date range and number of symbols.
    """
    client_ip = get_client_ip(request)
    await check_concurrency(client_ip)
    try:
        # Extract parameters from the request model
        symbols = analysis_request.symbols
        start_date = analysis_request.start_date.isoformat()
        end_date = analysis_request.end_date.isoformat()
        risk_free_rate = analysis_request.risk_free_rate

        logger.info(f"Processing SPR portfolio analysis request for symbols: {symbols}")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Risk-free rate: {risk_free_rate}%")

        # Get stock data
        data = get_stock_data(symbols, start_date, end_date)

        # Generate report (this now returns html_url and csv_urls)
        report_result = generate_perf_report(data, risk_free_rate)

        # Extract the URLs from the result
        if isinstance(report_result, tuple):
            html_url, csv_urls = report_result
        else:
            html_url = report_result
            csv_urls = {}

        # Return structured response with specific CSV URLs
        return PortfolioAnalysisResponse(
            html_report_ffn_url=html_url,
            input_price_data_csv_url=csv_urls.get('price_data', ''),
            cumulative_returns_csv_url=csv_urls.get('cumulative_returns', ''),
            success="SPR (Security Performance Review) portfolio analysis report generated successfully!"
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid parameters. Check symbols, dates, and risk-free rate.")
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")
    finally:
        await asyncio.shield(release_concurrency(client_ip))

# Create MCP server AFTER all endpoints are defined with proper configuration
# Use localhost to avoid Cloudflare overwriting cf-connecting-ip on external URLs
mcp = FastApiMCP(
    app,
    name="SPR (Security Performance Review) MCP API",
    description="MCP server for SPR portfolio analysis endpoints using custom calculations and FFN metrics. Note: SPR operations may take up to 3 minutes due to data fetching and analysis requirements.",
    include_operations=[
        "analyze_portfolio"
    ],
    describe_all_responses=True,
    describe_full_response_schema=True,
    http_client=httpx.AsyncClient(
        timeout=180.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        base_url="http://localhost:8000"
    )
)

# Mount the MCP server to the FastAPI app
mcp.mount()

# Log MCP operations
logger.info("Operations included in MCP server:")
for op in mcp._include_operations:
    logger.info(f"Operation '{op}' included in MCP")

logger.info("MCP server exposing SPR (Security Performance Review) portfolio analysis endpoints")
logger.info("=" * 40)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 