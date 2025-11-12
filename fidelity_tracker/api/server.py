"""
FastAPI REST API Server
Provides HTTP endpoints for portfolio data access
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fidelity_tracker.core.database import DatabaseManager
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

# Database dependency
def get_db():
    """Get database connection"""
    config = Config()
    db_path = config.get('database.path', 'fidelity_portfolio.db')
    return DatabaseManager(db_path)


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
        if sector not in ['Unknown', 'Cash']:
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
                "timestamp": h['timestamp'],
                "total_value": h['total_value']
            }
            for h in history
        ],
        "period_days": days,
        "data_points": len(history)
    }


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
