from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.exam import router as exam_router
from app.routers.admin import router as admin_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="CBT Application API",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/api/health")
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    # Mount auth router under all possible path prefixes
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
    app.include_router(auth_router, prefix="/api", tags=["Auth"])
    app.include_router(auth_router, prefix="", tags=["Auth"])

    # Mount admin router under all possible path prefixes
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
    app.include_router(admin_router, prefix="/admin", tags=["Admin"])
    app.include_router(admin_router, prefix="/api", tags=["Admin"])
    app.include_router(admin_router, prefix="", tags=["Admin"])

    # Mount exam router
    app.include_router(exam_router, prefix="/api/exam", tags=["Exam"])
    app.include_router(exam_router, prefix="/exam", tags=["Exam"])
    app.include_router(exam_router, prefix="/api", tags=["Exam"])
    app.include_router(exam_router, prefix="", tags=["Exam"])

    # --- VERCEL DEBUG TRAP ---
    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def catch_all(request: Request, full_path: str):
        return {
            "detail": "Trap Triggered",
            "received_path": full_path,
            "actual_url": str(request.url),
            "headers": dict(request.headers)
        }

    return app


app = create_app()