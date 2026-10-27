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

    # --- VERCEL PATH RECOVERY ---
    @app.middleware("http")
    async def fix_vercel_routing(request: Request, call_next):
        # Read the true path we injected via vercel.json
        vercel_path = request.query_params.get("__vercel_path")
        if vercel_path:
            request.scope["path"] = vercel_path
        return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    # Mount routers
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
    app.include_router(auth_router, prefix="/api", tags=["Auth"])
    app.include_router(auth_router, prefix="", tags=["Auth"])

    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
    app.include_router(admin_router, prefix="/admin", tags=["Admin"])
    app.include_router(admin_router, prefix="/api", tags=["Admin"])
    app.include_router(admin_router, prefix="", tags=["Admin"])

    app.include_router(exam_router, prefix="/api/exam", tags=["Exam"])
    app.include_router(exam_router, prefix="/exam", tags=["Exam"])
    app.include_router(exam_router, prefix="/api", tags=["Exam"])
    app.include_router(exam_router, prefix="", tags=["Exam"])

    return app

app = create_app()