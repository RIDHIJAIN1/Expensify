import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, budgets, categories, export, insights, summary, transactions, uploads
from app.config import settings
from app.schemas.common import HealthOut
from app.services.errors import ServiceError

app = FastAPI(title="Expense Classification API", version="1.0.0")


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(summary.router)
app.include_router(budgets.router)
app.include_router(insights.router)
app.include_router(export.router)


@app.get("/api/health", response_model=HealthOut)
def health():
    return HealthOut(status="ok")


# Serve the built React SPA in production (when static/ exists)
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", settings.STATIC_DIR))
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        candidate = os.path.abspath(os.path.join(STATIC_DIR, full_path))
        if full_path and os.path.isfile(candidate) and candidate.startswith(STATIC_DIR):
            return FileResponse(candidate)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
