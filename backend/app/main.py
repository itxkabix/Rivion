# TODO: implement FastAPI app here
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio
from pinecone import Pinecone


from app.config import settings
from app.routes import search, health
from app.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Startup/Shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Application starting...")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"S3 Bucket: {settings.AWS_S3_BUCKET}")
    
    # Background tasks can be started here
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Face Emotion Detection API",
        "version": settings.API_VERSION,
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
