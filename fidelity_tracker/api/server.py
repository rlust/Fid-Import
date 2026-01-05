"""
FastAPI REST API Server
Provides HTTP endpoints for portfolio data access
"""

from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from fidelity_tracker.database import DatabaseManager
from fidelity_tracker.transactions import TransactionManager, CostBasisCalculator, FidelityCSVImporter, TransactionInferenceEngine
from fidelity_tracker.benchmarks import BenchmarkFetcher
from fidelity_tracker.analytics import PerformanceAnalytics, AttributionAnalytics, RiskAnalytics, PortfolioOptimizer
from fidelity_tracker.utils.config import Config

# Initialize FastAPI app
app = FastAPI(
    title="Fidelity Portfolio Tracker API",
    description="REST API for accessing portfolio data",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
def get_db():
    """Get database connection"""
    config = Config()
    db_path = config.get('database.path', 'fidelity_portfolio.db')
    return DatabaseManager(db_path)

def get_transaction_manager():
    """Get transaction manager"""
    config = Config()
    db_path = config.get('database.path', 'fidelity_portfolio.db')
    return TransactionManager(db_path)

def get_cost_basis_calculator():
    """Get cost basis calculator"""
    config = Config()
    db_path = config.get('database.path', 'fidelity_portfolio.db')
    return CostBasisCalculator(db_path)

def get_benchmark_fetcher():
    """Get benchmark fetcher"""
    config = Config()
    db_path = config.get('database.path', 'fidelity_portfolio.db')
    return BenchmarkFetcher(db_path)

def get_performance_analytics():
    """Get performance analytics"""
    config = Config()
    db_path = config.get('database.path', 'fidelity_portfolio.db')
    return PerformanceAnalytics(db_path)

def get_attribution_analytics():
    """Get attribution analytics"""
    config = Config()
    db_path = config.get('database.path', 'fidelity_portfolio.db')
    return AttributionAnalytics(db_path)

def get_risk_analytics():
    """Get risk analytics"""
    config = Config()
    db_path = config.get('database.path', 'fidelity_portfolio.db')
    return RiskAnalytics(db_path)

def get_portfolio_optimizer():
    """Get portfolio optimizer"""
    config = Config()
    db_path = config.get('database.path', 'fidelity_portfolio.db')
    return PortfolioOptimizer(db_path)


def map_holding_fields(holding: Dict[str, Any]) -> Dict[str, Any]:
    """Map database fields to API response fields"""
    mapped = holding.copy()
    # Map ticker to symbol for API consistency
    if 'ticker' in mapped:
        mapped['symbol'] = mapped.pop('ticker')
    return mapped


# Pydantic models
class SnapshotResponse(BaseModel):
    id: int
    timestamp: str
    total_value: float


class HoldingResponse(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    quantity: float
    last_price: float
    value: float
    cost_basis: Optional[float] = None
    gain_loss: Optional[float] = None
    gain_loss_percent: Optional[float] = None
    portfolio_weight: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None


class PortfolioSummary(BaseModel):
    total_value: float
    total_holdings: int
    total_gain_loss: Optional[float] = None
    total_return_percent: Optional[float] = None
    last_updated: str


class SectorAllocation(BaseModel):
    sector: str
    value: float
    percentage: float


class TransactionCreate(BaseModel):
    account_id: str
    ticker: str
    transaction_type: str
    transaction_date: str
    quantity: float
    total_amount: float
    price_per_share: Optional[float] = None
    fees: float = 0.0
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    account_id: str
    ticker: str
    transaction_type: str
    transaction_date: str
    quantity: float
    price_per_share: Optional[float]
    total_amount: float
    fees: float
    notes: Optional[str]
    source: str
    created_at: str
    updated_at: str


class BenchmarkResponse(BaseModel):
    id: int
    name: str
    ticker: str
    description: Optional[str]
    is_active: bool


class BenchmarkDataResponse(BaseModel):
    date: str
    close_price: float
    open_price: Optional[float]
    high_price: Optional[float]
    low_price: Optional[float]
    volume: Optional[float]


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Portfolio endpoints
@app.get("/api/v1/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(db: DatabaseManager = Depends(get_db)):
    """Get portfolio summary"""
    latest = db.get_latest_snapshot()

    if not latest:
        raise HTTPException(status_code=404, detail="No portfolio data found")

    holdings = db.get_holdings(latest['id'])

    # Note: gain_loss and cost_basis are not stored in current schema
    # These would need to be calculated from historical data or added to schema
    total_gain_loss = sum(h.get('gain_loss', 0) for h in holdings if h.get('gain_loss'))
    total_cost = sum(h.get('cost_basis', 0) for h in holdings if h.get('cost_basis'))
    total_return_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else None

    return PortfolioSummary(
        total_value=latest['total_value'],
        total_holdings=len(holdings),
        total_gain_loss=total_gain_loss if total_gain_loss > 0 else None,
        total_return_percent=total_return_percent,
        last_updated=latest['timestamp']
    )


@app.get("/api/v1/portfolio/holdings", response_model=List[HoldingResponse])
async def get_holdings(
    limit: int = Query(None, description="Limit number of holdings returned"),
    db: DatabaseManager = Depends(get_db)
):
    """Get current portfolio holdings"""
    latest = db.get_latest_snapshot()

    if not latest:
        raise HTTPException(status_code=404, detail="No portfolio data found")

    holdings = db.get_holdings(latest['id'])

    if limit:
        holdings = holdings[:limit]

    return [HoldingResponse(**map_holding_fields(h)) for h in holdings]


@app.get("/api/v1/portfolio/sectors", response_model=List[SectorAllocation])
async def get_sector_allocation(db: DatabaseManager = Depends(get_db)):
    """Get portfolio sector allocation"""
    latest = db.get_latest_snapshot()

    if not latest:
        raise HTTPException(status_code=404, detail="No portfolio data found")

    holdings = db.get_holdings(latest['id'])

    # Calculate sector allocations
    sectors: Dict[str, float] = {}
    for holding in holdings:
        sector = holding.get('sector', 'Unknown')
        # Include all sectors (Unknown, Cash, etc.) for transparency
        if sector:  # Only skip empty/null sectors
            sectors[sector] = sectors.get(sector, 0) + holding.get('value', 0)

    total_value = latest['total_value']
    allocations = [
        SectorAllocation(
            sector=sector,
            value=value,
            percentage=(value / total_value * 100) if total_value > 0 else 0
        )
        for sector, value in sorted(sectors.items(), key=lambda x: x[1], reverse=True)
    ]

    return allocations


@app.get("/api/v1/portfolio/top-holdings", response_model=List[HoldingResponse])
async def get_top_holdings(
    limit: int = Query(10, description="Number of top holdings to return"),
    db: DatabaseManager = Depends(get_db)
):
    """Get top holdings by value"""
    latest = db.get_latest_snapshot()

    if not latest:
        raise HTTPException(status_code=404, detail="No portfolio data found")

    holdings = db.get_holdings(latest['id'])
    top_holdings = sorted(holdings, key=lambda h: h.get('value', 0), reverse=True)[:limit]

    return [HoldingResponse(**map_holding_fields(h)) for h in top_holdings]


@app.get("/api/v1/snapshots", response_model=List[SnapshotResponse])
async def get_snapshots(
    limit: int = Query(10, description="Number of snapshots to return"),
    days: int = Query(None, description="Get snapshots from last N days"),
    db: DatabaseManager = Depends(get_db)
):
    """Get historical snapshots"""
    if days:
        snapshots = db.get_portfolio_history(days)
    else:
        snapshots = db.get_snapshots(limit)

    return [SnapshotResponse(**s) for s in snapshots]


@app.get("/api/v1/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: int,
    db: DatabaseManager = Depends(get_db)
):
    """Get specific snapshot by ID"""
    # This would need to be implemented in DatabaseManager
    snapshots = db.get_snapshots(1000)  # Get many to search
    snapshot = next((s for s in snapshots if s['id'] == snapshot_id), None)

    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

    return SnapshotResponse(**snapshot)


@app.get("/api/v1/snapshots/{snapshot_id}/holdings", response_model=List[HoldingResponse])
async def get_snapshot_holdings(
    snapshot_id: int,
    db: DatabaseManager = Depends(get_db)
):
    """Get holdings for a specific snapshot"""
    holdings = db.get_holdings(snapshot_id)

    if not holdings:
        raise HTTPException(status_code=404, detail=f"No holdings found for snapshot {snapshot_id}")

    return [HoldingResponse(**map_holding_fields(h)) for h in holdings]


@app.get("/api/v1/portfolio/history")
async def get_portfolio_history(
    days: int = Query(90, description="Number of days of history"),
    db: DatabaseManager = Depends(get_db)
):
    """Get portfolio value history"""
    history = db.get_portfolio_history(days)

    return {
        "data": [
            {
                "timestamp": timestamp,
                "total_value": total_value
            }
            for timestamp, total_value in history
        ],
        "period_days": days,
        "data_points": len(history)
    }


# Transaction endpoints
@app.post("/api/v1/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    transaction: TransactionCreate,
    txn_mgr: TransactionManager = Depends(get_transaction_manager)
):
    """Create a new transaction"""
    try:
        transaction_id = txn_mgr.create_transaction(
            account_id=transaction.account_id,
            ticker=transaction.ticker,
            transaction_type=transaction.transaction_type,
            transaction_date=transaction.transaction_date,
            quantity=transaction.quantity,
            total_amount=transaction.total_amount,
            price_per_share=transaction.price_per_share,
            fees=transaction.fees,
            notes=transaction.notes
        )

        txn = txn_mgr.get_transaction(transaction_id)
        return TransactionResponse(**txn)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create transaction: {str(e)}")


@app.get("/api/v1/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    account_id: Optional[str] = Query(None),
    ticker: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    txn_mgr: TransactionManager = Depends(get_transaction_manager)
):
    """Get transactions with optional filters"""
    transactions = txn_mgr.get_transactions(
        account_id=account_id,
        ticker=ticker,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

    return [TransactionResponse(**txn) for txn in transactions]


@app.get("/api/v1/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    txn_mgr: TransactionManager = Depends(get_transaction_manager)
):
    """Get transaction by ID"""
    txn = txn_mgr.get_transaction(transaction_id)

    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    return TransactionResponse(**txn)


@app.put("/api/v1/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    updates: Dict[str, Any],
    txn_mgr: TransactionManager = Depends(get_transaction_manager)
):
    """Update transaction"""
    success = txn_mgr.update_transaction(transaction_id, **updates)

    if not success:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    txn = txn_mgr.get_transaction(transaction_id)
    return TransactionResponse(**txn)


@app.delete("/api/v1/transactions/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    txn_mgr: TransactionManager = Depends(get_transaction_manager)
):
    """Delete transaction"""
    success = txn_mgr.delete_transaction(transaction_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")


@app.get("/api/v1/transactions/summary")
async def get_transactions_summary(
    account_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    txn_mgr: TransactionManager = Depends(get_transaction_manager)
):
    """Get transaction summary statistics"""
    return txn_mgr.get_transactions_summary(
        account_id=account_id,
        start_date=start_date,
        end_date=end_date
    )


@app.post("/api/v1/transactions/import")
async def import_transactions_csv(
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="Preview only, don't save to database")
):
    """
    Import transactions from CSV file

    Supports Fidelity transaction export format with automatic column detection.
    Set dry_run=false to actually import the transactions.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Parse CSV
        config = Config()
        db_path = config.get('database.path', 'fidelity_portfolio.db')
        importer = FidelityCSVImporter(db_path)

        transactions, parse_errors = importer.parse_csv(temp_path)

        # Validate transactions
        valid_transactions, validation_errors = importer.validate_transactions(transactions)

        all_errors = parse_errors + validation_errors

        # If not dry run and no errors, import to database
        imported_count = 0
        if not dry_run and not all_errors:
            txn_mgr = TransactionManager(db_path)
            for txn in valid_transactions:
                try:
                    txn_mgr.create_transaction(**txn)
                    imported_count += 1
                except Exception as e:
                    all_errors.append(f"Failed to import {txn.get('ticker', 'unknown')}: {str(e)}")

        # Clean up temp file
        os.unlink(temp_path)

        return {
            "success": len(all_errors) == 0,
            "dry_run": dry_run,
            "total_rows": len(transactions),
            "valid_transactions": len(valid_transactions),
            "imported": imported_count,
            "errors": all_errors,
            "preview": valid_transactions[:10] if dry_run else None  # Show first 10 for preview
        }

    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@app.post("/api/v1/transactions/infer")
async def infer_transactions_from_snapshots(
    save: bool = Query(False, description="Save inferred transactions to database"),
    skip_existing: bool = Query(True, description="Skip dates with existing inferred transactions")
):
    """
    Infer transactions by comparing consecutive portfolio snapshots.

    Automatically detects buys, sells, and quantity changes by analyzing
    differences between daily holdings snapshots.

    Args:
        save: If True, save inferred transactions to database
        skip_existing: If True, skip inference for dates that already have transactions

    Returns:
        Summary of inferred transactions with details
    """
    try:
        config = Config()
        db_path = config.get('database.path', 'fidelity_portfolio.db')
        engine = TransactionInferenceEngine(db_path)

        # Run inference
        result = engine.infer_all_transactions(skip_existing=skip_existing)

        # Save if requested
        saved_count = 0
        if save and result['transactions']:
            saved_count = engine.save_inferred_transactions(result['transactions'])

        return {
            "success": result['errors'] == 0,
            "inferred_count": result['inferred'],
            "saved_count": saved_count if save else 0,
            "skipped_dates": result['skipped'],
            "errors": result['errors'],
            "error_details": result.get('error_details', []),
            "message": result.get('message', ''),
            "preview": result['transactions'][:20] if not save else None,  # Show first 20 if preview
            "save_mode": save
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.get("/api/v1/transactions/infer/preview")
async def preview_inferred_transactions(
    limit: int = Query(50, description="Maximum number of transactions to preview")
):
    """
    Preview what transactions would be inferred from snapshots without saving.

    Returns a sample of inferred transactions for review.
    """
    try:
        config = Config()
        db_path = config.get('database.path', 'fidelity_portfolio.db')
        engine = TransactionInferenceEngine(db_path)

        # Run inference without saving
        result = engine.infer_all_transactions(skip_existing=False)

        transactions = result['transactions'][:limit]

        # Group by date for easier review
        by_date = {}
        for tx in transactions:
            date = tx['date']
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(tx)

        return {
            "total_inferred": result['inferred'],
            "preview_count": len(transactions),
            "errors": result['errors'],
            "error_details": result.get('error_details', []),
            "transactions": transactions,
            "grouped_by_date": by_date
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


# Benchmark endpoints
@app.get("/api/v1/benchmarks", response_model=List[BenchmarkResponse])
async def get_benchmarks(
    fetcher: BenchmarkFetcher = Depends(get_benchmark_fetcher)
):
    """Get all active benchmarks"""
    benchmarks = fetcher.get_active_benchmarks()
    return [BenchmarkResponse(**b) for b in benchmarks]


@app.get("/api/v1/benchmarks/{ticker}", response_model=BenchmarkResponse)
async def get_benchmark(
    ticker: str,
    fetcher: BenchmarkFetcher = Depends(get_benchmark_fetcher)
):
    """Get benchmark by ticker"""
    benchmark = fetcher.get_benchmark_by_ticker(ticker)

    if not benchmark:
        raise HTTPException(status_code=404, detail=f"Benchmark {ticker} not found")

    return BenchmarkResponse(**benchmark)


@app.get("/api/v1/benchmarks/{ticker}/data", response_model=List[BenchmarkDataResponse])
async def get_benchmark_data(
    ticker: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    days: Optional[int] = Query(None),
    fetcher: BenchmarkFetcher = Depends(get_benchmark_fetcher)
):
    """Get benchmark historical data"""
    try:
        data = fetcher.get_benchmark_history(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            days=days
        )

        return [BenchmarkDataResponse(**record) for record in data]

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/benchmarks/{ticker}/sync")
async def sync_benchmark(
    ticker: str,
    days: int = Query(365, le=3650),
    replace: bool = Query(False),
    fetcher: BenchmarkFetcher = Depends(get_benchmark_fetcher)
):
    """Sync benchmark data from Yahoo Finance"""
    try:
        saved = fetcher.sync_benchmark(ticker, days=days, replace=replace)

        return {
            "ticker": ticker,
            "records_saved": saved,
            "days": days,
            "replaced": replace
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync benchmark: {str(e)}")


@app.get("/api/v1/benchmarks/{ticker}/returns")
async def get_benchmark_returns(
    ticker: str,
    days: int = Query(30, le=3650),
    fetcher: BenchmarkFetcher = Depends(get_benchmark_fetcher)
):
    """Calculate benchmark returns"""
    try:
        return fetcher.calculate_returns(ticker, days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate returns: {str(e)}")


# Performance Analytics endpoints
@app.get("/api/v1/analytics/performance")
async def get_performance_metrics(
    days: int = Query(365, le=3650, description="Number of days for analysis"),
    analytics: PerformanceAnalytics = Depends(get_performance_analytics)
):
    """Get comprehensive performance metrics including TWR, MWR, and returns"""
    try:
        return analytics.calculate_portfolio_returns(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate performance: {str(e)}")


@app.get("/api/v1/analytics/performance/history")
async def get_performance_history(
    days: int = Query(365, le=3650, description="Number of days of history"),
    db: DatabaseManager = Depends(get_db)
):
    """
    Get historical portfolio performance data for charting.

    Returns time-series data of portfolio value, gains, and cumulative returns.
    """
    try:
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Get snapshots
        history = db.get_portfolio_history(days)

        if len(history) < 2:
            return {
                "error": "Insufficient data",
                "message": f"Need at least 2 snapshots, found {len(history)}"
            }

        # Calculate cumulative returns from first snapshot
        first_value = history[0][1]  # (timestamp, total_value)

        data_points = []
        for timestamp, total_value in history:
            cumulative_return = ((total_value - first_value) / first_value * 100) if first_value > 0 else 0
            data_points.append({
                "timestamp": timestamp,
                "total_value": total_value,
                "cumulative_return_percent": cumulative_return
            })

        return {
            "period_days": days,
            "data_points": len(data_points),
            "start_value": first_value,
            "end_value": history[-1][1],
            "total_return_percent": data_points[-1]["cumulative_return_percent"],
            "history": data_points
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance history: {str(e)}")


@app.get("/api/v1/analytics/performance/holding/{ticker}")
async def get_holding_performance(
    ticker: str,
    days: int = Query(365, le=3650),
    analytics: PerformanceAnalytics = Depends(get_performance_analytics)
):
    """Get performance metrics for a specific holding"""
    try:
        return analytics.calculate_holding_performance(ticker, days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate holding performance: {str(e)}")


@app.get("/api/v1/analytics/attribution")
async def get_performance_attribution(
    days: int = Query(30, le=365),
    analytics: AttributionAnalytics = Depends(get_attribution_analytics)
):
    """Get performance attribution by holding"""
    try:
        return analytics.calculate_holding_attribution(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate attribution: {str(e)}")


@app.get("/api/v1/analytics/attribution/sector")
async def get_sector_attribution(
    days: int = Query(30, le=365),
    analytics: AttributionAnalytics = Depends(get_attribution_analytics)
):
    """Get performance attribution by sector"""
    try:
        return analytics.calculate_sector_attribution(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate sector attribution: {str(e)}")


@app.get("/api/v1/analytics/contributors")
async def get_top_contributors(
    days: int = Query(30, le=365),
    limit: int = Query(10, le=50),
    analytics: AttributionAnalytics = Depends(get_attribution_analytics)
):
    """Get top contributors and detractors to performance"""
    try:
        return analytics.get_top_contributors(days=days, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contributors: {str(e)}")


# Risk Analytics Endpoints
@app.get("/api/v1/risk/comprehensive")
async def get_comprehensive_risk(
    days: int = Query(365, le=1095),
    risk: RiskAnalytics = Depends(get_risk_analytics)
):
    """Get comprehensive risk analysis report"""
    try:
        return risk.get_comprehensive_risk_report(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get risk report: {str(e)}")


@app.get("/api/v1/risk/volatility")
async def get_volatility(
    days: int = Query(365, le=1095),
    risk: RiskAnalytics = Depends(get_risk_analytics)
):
    """Get portfolio volatility metrics"""
    try:
        return risk.calculate_volatility(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate volatility: {str(e)}")


@app.get("/api/v1/risk/sharpe")
async def get_sharpe_ratio(
    days: int = Query(365, le=1095),
    risk: RiskAnalytics = Depends(get_risk_analytics)
):
    """Get Sharpe ratio (risk-adjusted return)"""
    try:
        return risk.calculate_sharpe_ratio(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate Sharpe ratio: {str(e)}")


@app.get("/api/v1/risk/beta")
async def get_beta(
    days: int = Query(365, le=1095),
    benchmark: str = Query('^GSPC', description="Benchmark symbol"),
    risk: RiskAnalytics = Depends(get_risk_analytics)
):
    """Get portfolio beta vs benchmark"""
    try:
        return risk.calculate_beta(days=days, benchmark=benchmark)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate beta: {str(e)}")


@app.get("/api/v1/risk/var")
async def get_value_at_risk(
    days: int = Query(365, le=1095),
    confidence: float = Query(0.95, ge=0.9, le=0.99),
    risk: RiskAnalytics = Depends(get_risk_analytics)
):
    """Get Value at Risk (VaR)"""
    try:
        return risk.calculate_value_at_risk(days=days, confidence=confidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate VaR: {str(e)}")


@app.get("/api/v1/risk/drawdown")
async def get_max_drawdown(
    days: int = Query(365, le=1095),
    risk: RiskAnalytics = Depends(get_risk_analytics)
):
    """Get maximum drawdown analysis"""
    try:
        return risk.calculate_max_drawdown(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate drawdown: {str(e)}")


@app.get("/api/v1/risk/correlation")
async def get_correlation_matrix(
    days: int = Query(365, le=1095),
    min_holdings: int = Query(5, ge=2, le=20),
    risk: RiskAnalytics = Depends(get_risk_analytics)
):
    """Get correlation matrix between top holdings"""
    try:
        return risk.calculate_correlation_matrix(days=days, min_holdings=min_holdings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate correlation: {str(e)}")


# Portfolio Optimization Endpoints
@app.get("/api/v1/optimize/sharpe")
async def optimize_sharpe(
    days: int = Query(365, le=1095),
    min_holdings: int = Query(5, ge=2, le=20),
    optimizer: PortfolioOptimizer = Depends(get_portfolio_optimizer)
):
    """Get portfolio with maximum Sharpe ratio"""
    try:
        return optimizer.optimize_sharpe(days=days, min_holdings=min_holdings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@app.get("/api/v1/optimize/min-volatility")
async def optimize_min_volatility(
    days: int = Query(365, le=1095),
    min_holdings: int = Query(5, ge=2, le=20),
    optimizer: PortfolioOptimizer = Depends(get_portfolio_optimizer)
):
    """Get portfolio with minimum volatility"""
    try:
        return optimizer.optimize_min_volatility(days=days, min_holdings=min_holdings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@app.get("/api/v1/optimize/efficient-frontier")
async def get_efficient_frontier(
    days: int = Query(365, le=1095),
    min_holdings: int = Query(5, ge=2, le=20),
    num_points: int = Query(50, ge=10, le=100),
    optimizer: PortfolioOptimizer = Depends(get_portfolio_optimizer)
):
    """Calculate efficient frontier"""
    try:
        return optimizer.calculate_efficient_frontier(days=days, min_holdings=min_holdings, num_points=num_points)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate frontier: {str(e)}")


@app.get("/api/v1/optimize/monte-carlo")
async def run_monte_carlo(
    days: int = Query(365, le=1095),
    min_holdings: int = Query(5, ge=2, le=20),
    num_simulations: int = Query(10000, ge=1000, le=50000),
    time_horizon: int = Query(252, ge=30, le=1260),
    optimizer: PortfolioOptimizer = Depends(get_portfolio_optimizer)
):
    """Run Monte Carlo simulation"""
    try:
        return optimizer.monte_carlo_simulation(
            days=days,
            min_holdings=min_holdings,
            num_simulations=num_simulations,
            time_horizon=time_horizon
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@app.get("/api/v1/optimize/rebalance")
async def get_rebalancing_recommendations(
    days: int = Query(365, le=1095),
    min_holdings: int = Query(5, ge=2, le=20),
    optimizer: PortfolioOptimizer = Depends(get_portfolio_optimizer)
):
    """Get rebalancing recommendations"""
    try:
        return optimizer.get_rebalancing_recommendations(days=days, min_holdings=min_holdings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


# Sync/Update endpoints
@app.get("/api/v1/sync/status")
async def get_sync_status(db: DatabaseManager = Depends(get_db)):
    """Get sync schedule and status information"""
    try:
        from datetime import datetime, time as datetime_time
        import subprocess

        # Get latest snapshot to determine last sync
        latest = db.get_latest_snapshot()
        last_sync = latest['timestamp'] if latest else None

        # Calculate next scheduled sync (6 PM daily)
        now = datetime.now()
        next_sync_time = datetime.combine(now.date(), datetime_time(18, 0))
        if now.time() >= datetime_time(18, 0):
            # If it's after 6 PM today, next sync is tomorrow at 6 PM
            next_sync_time = datetime.combine(now.date() + timedelta(days=1), datetime_time(18, 0))

        # Check launchd agent status
        try:
            result = subprocess.run(
                ['launchctl', 'list', 'com.portfolio.sync'],
                capture_output=True,
                text=True,
                timeout=5
            )
            agent_running = result.returncode == 0
        except:
            agent_running = False

        return {
            "last_sync": last_sync,
            "next_scheduled_sync": next_sync_time.isoformat(),
            "schedule": "Daily at 6:00 PM",
            "agent_active": agent_running,
            "sync_command": "portfolio-tracker sync"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@app.post("/api/v1/sync/trigger")
async def trigger_manual_sync():
    """Manually trigger a portfolio sync"""
    try:
        import subprocess
        from datetime import datetime

        # Run sync command in background
        result = subprocess.Popen(
            ['python3', '-m', 'fidelity_tracker.cli.commands', 'sync'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='/Users/randylust/grok'
        )

        return {
            "status": "started",
            "message": "Portfolio sync initiated",
            "started_at": datetime.now().isoformat(),
            "note": "Sync is running in background. Check /api/v1/sync/status for latest data."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger sync: {str(e)}")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc)}
    )


@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )


# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fidelity_tracker.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
