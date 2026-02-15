"""
FastAPI Main Application
Entry point for the AlgoTradeX backend server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api import stocks, strategies, backtest


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events - runs on startup and shutdown"""
    # Startup
    print("🚀 Starting AlgoTradeX Backend...")
    print(f"📊 App Name: {settings.APP_NAME}")
    print(f"🔢 Version: {settings.APP_VERSION}")
    
    # Initialize database tables
    init_db()
    
    yield
    
    # Shutdown
    print("👋 Shutting down AlgoTradeX Backend...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Algorithmic Trading Platform for NSE Stocks",
    lifespan=lifespan
)

# CORS middleware - allows frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "AlgoTradeX API is live! 🚀"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": "2025-02-13T10:00:00Z"
    }


# Include API routers
app.include_router(stocks.router, prefix=f"{settings.API_V1_PREFIX}/stocks", tags=["Stocks"])
app.include_router(strategies.router, prefix=f"{settings.API_V1_PREFIX}/strategies", tags=["Strategies"])
app.include_router(backtest.router, prefix=f"{settings.API_V1_PREFIX}/backtest", tags=["Backtesting"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
