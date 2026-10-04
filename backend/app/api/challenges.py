from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.challenge import PvpChallengeCreate, PvpChallengeRead
from app.schemas.pvp import PvpMatchRead
from app.services.challenge_service import (
    ChallengeError,
    create_challenge,
    get_challenge,
    get_player_challenges,
    get_player_matches,
    resolve_challenge,
)

router = APIRouter(prefix="/pvp", tags=["pvp"])


@router.get("/players/{player_id}/challenges", response_model=list[PvpChallengeRead])
async def read_player_challenges(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PvpChallengeRead]:
    challenges = await get_player_challenges(session, player_id)
    return [PvpChallengeRead.from_model(challenge) for challenge in challenges]


@router.get("/players/{player_id}/matches", response_model=list[PvpMatchRead])
async def read_player_matches(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PvpMatchRead]:
    matches = await get_player_matches(session, player_id)
    return [PvpMatchRead.from_model(match) for match in matches]


@router.post("/challenges", response_model=PvpChallengeRead, status_code=201)
async def create_pvp_challenge(
    payload: PvpChallengeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PvpChallengeRead:
    try:
        challenge = await create_challenge(
            session,
            payload.challenger_id,
            challenged_player_id=payload.challenged_player_id,
            challenged_username=payload.challenged_username,
        )
    except ChallengeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    await session.commit()
    return PvpChallengeRead.from_model(challenge)


@router.get("/challenges/{challenge_id}", response_model=PvpChallengeRead)
async def read_pvp_challenge(
    challenge_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PvpChallengeRead:
    challenge = await get_challenge(session, challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="challenge not found")
    return PvpChallengeRead.from_model(challenge)


@router.post("/challenges/{challenge_id}/resolve", response_model=PvpMatchRead)
async def resolve_pvp_challenge(
    challenge_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PvpMatchRead:
    match = await resolve_challenge(session, challenge_id)
    if match is None:
        raise HTTPException(status_code=404, detail="challenge not found")
    await session.commit()
    return PvpMatchRead.from_model(match)


@router.get("/challenges/{challenge_id}/match", response_model=PvpMatchRead)
async def read_pvp_match(
    challenge_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PvpMatchRead:
    from app.services.challenge_service import get_match

    match = await get_match(session, challenge_id)
    if match is None:
        raise HTTPException(status_code=404, detail="match not found")
    return PvpMatchRead.from_model(match)
