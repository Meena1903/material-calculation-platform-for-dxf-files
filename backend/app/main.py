"""FastAPI Application Entrypoint for BuildIQ Pile Takeoff Engine."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.api.endpoints import router as api_router

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

# Mount outputs / crops directory for image preview in frontend
crops_dir = os.path.join(settings.OUTPUT_DIR, "crops")
os.makedirs(crops_dir, exist_ok=True)
app.mount("/crops", StaticFiles(directory=crops_dir), name="crops")


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "health": "/api/health",
        "sample": "/api/takeoff/sample",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
