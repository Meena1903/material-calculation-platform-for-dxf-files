"""FastAPI Application Entrypoint for BuildIQ Pile Takeoff Engine."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.logging_config import app_logger
from backend.app.api.endpoints import router as api_router

app_logger.info("=" * 80)
app_logger.info(f"[APP STARTUP] Initializing {settings.APP_NAME}")
app_logger.info(f"  - Environment: {settings.APP_ENV}")
app_logger.info(f"  - Host: {settings.HOST}:{settings.PORT}")
app_logger.info(f"  - Debug Mode: {settings.DEBUG}")
app_logger.info(f"  - CORS Origins: {settings.CORS_ORIGINS}")
app_logger.info("=" * 80)

app = FastAPI(
    title=settings.APP_NAME,
    description="Automated Pile Foundation Takeoff Engine — Computer Vision, Multimodal LLMs, and CAD Geometry with 100% Native Python Engineering Calculations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)
app_logger.info("[APP ROUTES] Registered API router with endpoints (/api/health, /api/takeoff/*, /api/export/*)")

# Mount outputs / crops directory for image preview in frontend
crops_dir = os.path.join(settings.OUTPUT_DIR, "crops")
os.makedirs(crops_dir, exist_ok=True)
app.mount("/crops", StaticFiles(directory=crops_dir), name="crops")
app_logger.info(f"[APP MOUNT] Mounted static crops directory at '/crops' -> '{crops_dir}'")


@app.get("/")
def root():
    app_logger.info("[APP GET /] Root status check received")
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "health": "/api/health",
        "sample": "/api/takeoff/sample",
    }


if __name__ == "__main__":
    import uvicorn
    app_logger.info(f"[APP LAUNCH] Launching Uvicorn server on {settings.HOST}:{settings.PORT}")
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
