from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core router imports
from app.routers.auth import router as auth_router
from app.routers.exam import router as exam_router
from app.routers.admin import router as admin_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="CBT Application API",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # 1. Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Health check endpoint
    @app.get("/api/health", tags=["Health"])
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok", "message": "FastAPI is live"}

    # 3. Mount API routers
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(exam_router, prefix="/api/exam", tags=["Exam"])
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

    # Fallback mounts without /api prefix
    app.include_router(auth_router, prefix="/auth", tags=["Auth Fallback"])
    app.include_router(exam_router, prefix="/exam", tags=["Exam Fallback"])
    app.include_router(admin_router, prefix="/admin", tags=["Admin Fallback"])

    return app


app = create_app()