from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.health import router as health_router
from app.metrics import MetricsMiddleware
from app.metrics import router as metrics_router
from app.observability import CorrelationMiddleware
from app.routers import jobs

app = FastAPI(title="JobHunter API")

app.add_middleware(MetricsMiddleware)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(auth_router)
