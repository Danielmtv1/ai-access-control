from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.security import RateLimitMiddleware, SecurityHeadersMiddleware

def add_security_middleware(app: FastAPI):
    """Agrega middlewares de seguridad a la aplicación."""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción, especificar dominios permitidos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # Rate Limiting - Excluir rutas de documentación
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        window_size=60,
        exclude_paths=["/docs", "/redoc", "/openapi.json", "/metrics"]  # ← Sin / final
    )
    
    # Security Headers - CSP permisiva para ReDoc
    app.add_middleware(
        SecurityHeadersMiddleware,
        content_security_policy=(
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https: blob:; "
            "worker-src 'self' blob:; "  # ← Esto es clave para ReDoc
            "img-src 'self' data: https:; "
            "font-src 'self' https: data:;"
        )
    )