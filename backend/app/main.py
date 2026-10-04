from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import check_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        database_connected = await check_database()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc

    if not database_connected:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")

    return {"status": "ok", "database": "connected"}
