from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import logger
from src.routes import auth_routes, search_routes
from src.core.middleware import setup_middleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
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
