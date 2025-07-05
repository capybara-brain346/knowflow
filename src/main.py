from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging import logger
from routes import auth_routes, search_routes

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up KnowFlow API")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down KnowFlow API")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENV,
    }


@app.get("/health/detailed")
async def detailed_health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENV,
        "database": "connected",
        "api_version": "v1",
    }


app.include_router(
    auth_routes.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"]
)

app.include_router(
    search_routes.router, prefix=f"{settings.API_V1_PREFIX}/search", tags=["Search"]
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
    )
