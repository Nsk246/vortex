import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from .config import get_settings
from .database import create_tables
from .routers import auth, cases, websocket


settings = get_settings()
settings.validate_production()

app = FastAPI(title="VORTEX API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.on_event("startup")
def startup() -> None:
    create_tables()


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4())[:12])
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["x-process-time-ms"] = str(round((time.perf_counter() - start) * 1000))
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error"})


@app.get("/health")
def health():
    return {"status": "ok", "service": "vortex-api", "env": settings.app_env}


app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(websocket.router)
