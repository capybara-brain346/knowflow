from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.core.config import settings
from src.routes import (
    auth_routes,
    chat_routes,
    graph_routes,
    document_routes,
    session_routes,
)
from src.core.middleware import setup_middleware
from src.core.database import init_db
from src.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

setup_middleware(app)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENV,
    }


@app.get("/health/detailed", tags=["Health"])
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
    chat_routes.router, prefix=f"{settings.API_V1_PREFIX}/chat", tags=["Chat"]
)

app.include_router(
    document_routes.router,
    prefix=f"{settings.API_V1_PREFIX}/document",
    tags=["Documents"],
)

app.include_router(
    graph_routes.router, prefix=f"{settings.API_V1_PREFIX}/graph", tags=["Graph"]
)

app.include_router(
    session_routes.router,
    prefix=f"{settings.API_V1_PREFIX}/sessions",
    tags=["Sessions"],
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
