import time
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.config import settings
from src.core.logging import logger
from src.core.exceptions import AppException, RateLimitException


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()

        try:
            response = await call_next(request)
            return self.add_response_headers(request, response)
        except AppException as e:
            logger.error(
                f"Application error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "error_type": e.__class__.__name__,
                    "status_code": e.status_code,
                    **e.extra,
                },
            )
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.message, "request_id": request_id, **e.extra},
            )
        except Exception as e:
            logger.exception(
                f"Unhandled error: {str(e)}", extra={"request_id": request_id}
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
            )

    def add_response_headers(self, request: Request, response: Response) -> Response:
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Process-Time"] = str(time.time() - request.state.start_time)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": process_time,
            },
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        calls: int = 100,
        period: int = 60,
        excluded_paths: set[str] = {"/health", "/health/detailed"},
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
        self.excluded_paths = excluded_paths

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        client_ip = request.client.host

        if not self._is_allowed(client_ip):
            raise RateLimitException(
                message="Too many requests",
                extra={
                    "client_ip": client_ip,
                    "limit": self.calls,
                    "period": f"{self.period} seconds",
                },
            )

        return await call_next(request)

    def _is_allowed(self, client_ip: str) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        if client_ip not in self.clients:
            self.clients[client_ip] = [(now, 1)]
            return True

        requests = self.clients[client_ip]
        while requests and now - requests[0][0] > self.period:
            requests.pop(0)

        total_requests = sum(count for _, count in requests)
        if total_requests >= self.calls:
            return False

        requests.append((now, 1))
        return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


def setup_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestContextMiddleware)

    app.add_middleware(LoggingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.ENV == "production":
        app.add_middleware(
            RateLimitMiddleware,
            calls=settings.RATE_LIMIT_CALLS,
            period=settings.RATE_LIMIT_PERIOD,
            excluded_paths=settings.RATE_LIMIT_EXCLUDED_PATHS,
        )

    app.add_middleware(SecurityHeadersMiddleware)
