from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.items import router as items_router
from app.api.players import router as players_router
from app.config import get_settings
from app.db import check_database, get_session
from app.schemas.player import PlayerWithDetails
from app.services.player_service import get_or_create_development_player

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
app.include_router(players_router)
app.include_router(items_router)


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        database_connected = await check_database()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc

    if not database_connected:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")

    return {"status": "ok", "database": "connected"}


@app.post("/dev/player", response_model=PlayerWithDetails, include_in_schema=False)
@app.post("/dev/players", response_model=PlayerWithDetails, include_in_schema=False)
async def create_dev_player_alias(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlayerWithDetails:
    player = await get_or_create_development_player(session)
    await session.commit()
    return PlayerWithDetails.model_validate(player)
