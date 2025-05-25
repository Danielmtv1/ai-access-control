from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from typing import Dict, Tuple, List
from collections import defaultdict
import asyncio

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        window_size: int = 60,
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = window_size
        self.exclude_paths = exclude_paths or []
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
            
        client_ip = request.client.host
        
        async with self.lock:
            current_time = time.time()
            
            # Limpiar solicitudes antiguas
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < self.window_size
            ]
            
            # Verificar límite
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                return Response(
                    content="Too Many Requests",
                    status_code=429
                )
            
            # Registrar nueva solicitud
            self.requests[client_ip].append(current_time)
        
        return await call_next(request)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        content_security_policy: str = None
    ):
        super().__init__(app)
        self.content_security_policy = content_security_policy

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Agregar headers de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP personalizado si se proporciona
        if self.content_security_policy:
            response.headers["Content-Security-Policy"] = self.content_security_policy
        else:
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response 