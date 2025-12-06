"""
Cyprus Dam Water Levels API

An application that visualizes real-time dam water levels across Cyprus
and provides predictive insights on future capacity.

Data source: https://cyprus-water.appspot.com
License: CC BY 2.0
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import summary, dams, trend, risk, forecast, narrative, dam_detail

# Initialize FastAPI app
app = FastAPI(
    title="Cyprus Dam Water Levels API",
    description="Real-time dam water levels and predictive insights for Cyprus",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(summary.router)
app.include_router(dams.router)
app.include_router(dam_detail.router)
app.include_router(trend.router)
app.include_router(risk.router)
app.include_router(forecast.router)
app.include_router(narrative.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/")
def read_root():
    """Root endpoint with API info."""
    return {
        "name": "Cyprus Dam Water Levels API",
        "version": "1.0.0",
        "description": "Real-time dam water levels and predictive insights for Cyprus",
        "data_source": "https://cyprus-water.appspot.com",
        "endpoints": {
            "summary": "/api/summary",
            "dams": "/api/dams",
            "dam_detail": "/api/dam?name={dam_name}",
            "trend": "/api/trend",
            "risk": "/api/risk",
            "forecast": "/api/forecast",
            "narrative": "/api/narrative",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
