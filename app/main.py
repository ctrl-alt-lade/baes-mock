import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Core router imports
from app.routers.auth import router as auth_router
from app.routers.exam import router as exam_router
from app.routers.admin import router as admin_router

BASE_DIR = Path(__file__).resolve().parent.parent

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
    @app.get("/api/health", tags=["Health"])
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok", "message": "FastAPI is live"}

    # Mount API routers (both /api/ and bare prefix fallbacks)
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(exam_router, prefix="/api/exam", tags=["Exam"])
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
    app.include_router(auth_router, prefix="/auth", tags=["Auth Fallback"])
    app.include_router(exam_router, prefix="/exam", tags=["Exam Fallback"])
    app.include_router(admin_router, prefix="/admin", tags=["Admin Fallback"])

    # Serve the main HTML pages directly from Python
    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_path = BASE_DIR / "index.html"
        if not index_path.exists():
            index_path = BASE_DIR / "cbt-frontend" / "index.html"
        return FileResponse(str(index_path))

    @app.get("/{page}.html", include_in_schema=False)
    async def serve_html_pages(page: str):
        # Handles exam.html, results.html, admin.html
        page_path = BASE_DIR / f"{page}.html"
        if not page_path.exists():
            page_path = BASE_DIR / "cbt-frontend" / f"{page}.html"
        if page_path.exists():
            return FileResponse(str(page_path))
        return FileResponse(str(BASE_DIR / "index.html"))

    # Mount static assets (js, css, images) if they exist
    for folder in ["js", "css", "assets", "images"]:
        f_path = BASE_DIR / folder
        if not f_path.exists():
            f_path = BASE_DIR / "cbt-frontend" / folder
        if f_path.exists():
            app.mount(f"/{folder}", StaticFiles(directory=str(f_path)), name=folder)

    return app

app = create_app()