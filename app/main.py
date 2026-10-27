from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Core router imports
from app.routers.auth import router as auth_router
from app.routers.exam import router as exam_router
from app.routers.admin import router as admin_router


def create_app() -> FastAPI:
    """FastAPI application factory with CORS, modular routers, and mounted static frontend."""
    app = FastAPI(
        title="CBT Application API",
        description="Computer-Based Testing (CBT) web app backend with FastAPI and Firebase Firestore.",
        version="1.0.0",
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
    @app.get("/ping", tags=["Health Check"])
    async def ping():
        """Health check endpoint to verify server is running."""
        return {"status": "ok", "message": "pong"}

    # 3. Include API and Admin routers BEFORE mounting static files
    app.include_router(auth_router)
    app.include_router(exam_router)
    app.include_router(admin_router)

    # 4. Mount frontend static files at root AFTER all router declarations
    # Resolves path whether executed from root or sub-directories
    frontend_dir = Path(__file__).resolve().parent.parent / "cbt-frontend"
    if not frontend_dir.exists():
        frontend_dir = Path("cbt-frontend")

    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    return app


app = create_app()
