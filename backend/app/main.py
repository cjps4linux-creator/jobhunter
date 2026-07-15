from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import jobs
from app.auth.router import router as auth_router

app = FastAPI(title="JobHunter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(auth_router)

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
