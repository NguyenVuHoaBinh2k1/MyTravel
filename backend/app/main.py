"""
Vietnamese Travel Planning AI App - Main Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import router as api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    print("Starting Vietnamese Travel Planning AI App...")
    yield
    # Shutdown
    print("Shutting down Vietnamese Travel Planning AI App...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered travel planning assistant for Vietnam tourism",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "message": "Welcome to Vietnamese Travel Planning AI API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}
