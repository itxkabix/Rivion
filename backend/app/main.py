from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.config import settings
from app.routes import search, health
from app.utils.logger import setup_logger
from app.services.db_init import init_db, get_db_status
from app.services.image_storage import cleanup_old_sessions

# Setup logging
logger = setup_logger(__name__)

# Startup/Shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # ========== STARTUP ==========
    logger.info("=" * 60)
    logger.info("🚀 RIVION Face Emotion Detection API Starting...")
    logger.info("=" * 60)
    
    # Initialize Database
    try:
        logger.info("📊 Initializing database...")
        init_db()
        db_status = get_db_status()
        logger.info(f"✅ Database Status: {db_status['status']}")
        logger.info(f"   Tables: {db_status.get('count', 0)} tables found")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Log configuration
    logger.info(f"🗂️  Storage Directory: {settings.STORAGE_DIR}")
    logger.info(f"📝 Log Level: {settings.LOG_LEVEL}")
    logger.info(f"🔗 Allowed CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"⏰ Session Expiry: {settings.SESSION_EXPIRY_HOURS} hours")
    
    logger.info("✅ Application Ready!")
    logger.info("=" * 60)
    
    yield
    
    # ========== SHUTDOWN ==========
    logger.info("=" * 60)
    logger.info("🛑 RIVION API Shutting Down...")
    
    # Cleanup old sessions
    try:
        deleted = await cleanup_old_sessions(hours=settings.SESSION_EXPIRY_HOURS)
        logger.info(f"🧹 Cleanup: Deleted {deleted} old sessions")
    except Exception as e:
        logger.warning(f"⚠️ Cleanup failed: {e}")
    
    logger.info("✅ Shutdown Complete")
    logger.info("=" * 60)

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
    """Root endpoint - shows API info"""
    return {
        "name": "Face Emotion Detection API",
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "endpoints": {
            "docs": "/docs",
            "health": "/api/health",
            "search": "/api/v1/search",
        },
        "database": get_db_status(),
    }

# Status endpoint
@app.get("/api/v1/status")
async def status():
    """Get system status"""
    return {
        "status": "running",
        "database": get_db_status(),
        "storage": {
            "type": settings.STORAGE_TYPE,
            "directory": settings.STORAGE_DIR,
        },
        "session_expiry_hours": settings.SESSION_EXPIRY_HOURS,
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
