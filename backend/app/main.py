from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import jobs

app = FastAPI(title="JobHunter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api", tags=["jobs"])

@app.get("/health")
async def health():
    return {"status": "ok"}
