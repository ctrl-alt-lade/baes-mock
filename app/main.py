from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core router imports
from app.routers.auth import router as auth_router
from app.routers.exam import router as exam_router
from app.routers.admin import router as admin_router


def create_app() -> FastAPI:
    """FastAPI application factory for Vercel Serverless & Local Execution."""
    app = FastAPI(
        title="CBT Application API",
        description="Computer-Based Testing (CBT) web app backend with FastAPI and Firebase Firestore.",
        version="1.0.0",
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

    # 2. Health check endpoints (Both /api/health and /health so neither fails)
    @app.get("/api/health", tags=["Health Check"])
    @app.get("/health", tags=["Health Check"])
    @app.get("/api/ping", tags=["Health Check"])
    @app.get("/ping", tags=["Health Check"])
    async def health_check():
        """Health check endpoint to verify serverless backend is running."""
        return {"status": "ok", "message": "FastAPI is live on Vercel"}

    # 3. Mount standard /api routes
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(exam_router, prefix="/api/exam", tags=["Exam"])
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

    # 4. Mount route fallbacks in case Vercel rewrites strip the /api prefix
    app.include_router(auth_router, prefix="/auth", tags=["Auth Fallback"])
    app.include_router(exam_router, prefix="/exam", tags=["Exam Fallback"])
    app.include_router(admin_router, prefix="/admin", tags=["Admin Fallback"])

    return app


app = create_app()git add .
git commit -m "refactor: flatten frontend to root, set single api rewrite, and add route fallbacks"
git push origin main