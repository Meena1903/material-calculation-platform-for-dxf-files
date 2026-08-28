"""FastAPI Application Entrypoint for BuildIQ Pile Takeoff Engine."""

import os
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.logging_config import app_logger
from backend.app.core.langfuse_client import get_langfuse, flush as langfuse_flush
from backend.app.api.endpoints import router as api_router

app_logger.info("=" * 80)
app_logger.info(f"[APP STARTUP] Initializing {settings.APP_NAME}")
app_logger.info(f"  - Environment: {settings.APP_ENV}")
app_logger.info(f"  - Host: {settings.HOST}:{settings.PORT}")
app_logger.info(f"  - Debug Mode: {settings.DEBUG}")
app_logger.info(f"  - Max Upload Size: {settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.0f} MB")
app_logger.info(f"  - CORS Origins: {settings.CORS_ORIGINS}")
app_logger.info(
    f"  - Langfuse Observability: "
    f"{'ENABLED — ' + settings.LANGFUSE_BASE_URL if settings.LANGFUSE_SECRET_KEY else 'DISABLED (keys not set)'}"
)
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

@app.on_event("shutdown")
async def on_shutdown():
    """Flush any buffered Langfuse events before the server exits."""
    app_logger.info("[APP SHUTDOWN] Flushing Langfuse event buffer...")
    langfuse_flush()
    app_logger.info("[APP SHUTDOWN] Langfuse flush complete. Goodbye.")


# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured JSON response and error logging."""
    app_logger.warning(f"[HTTP EXCEPTION] {request.method} {request.url.path} -> {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "detail": exc.detail,
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request schema validation errors."""
    app_logger.warning(f"[VALIDATION ERROR] {request.method} {request.url.path} -> {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "status_code": 422,
            "message": "Request payload validation failed.",
            "detail": exc.errors(),
            "details": exc.errors(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled server exceptions."""
    app_logger.error(f"[UNHANDLED EXCEPTION] {request.method} {request.url.path} -> {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "message": "An unexpected internal server error occurred.",
            "detail": str(exc) if settings.DEBUG else "Internal server error.",
            "path": request.url.path,
        },
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
