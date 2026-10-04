from __future__ import annotations

import secrets

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.build import BuildSnapshot
from app.models.challenge import PvpChallenge
from app.models.player import Player
from app.models.pvp import PvpMatch
from app.services.battle_service import resolve_battle


class ChallengeError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _build_load_options():
    return selectinload(PvpChallenge.challenger_build), selectinload(PvpChallenge.challenged_build)


async def create_challenge(
    session: AsyncSession,
    challenger_id: str,
    *,
    challenged_player_id: str | None = None,
    challenged_username: str | None = None,
) -> PvpChallenge:
    challenger = await session.get(Player, challenger_id)
    if challenger is None:
        raise ChallengeError("challenger not found", 404)

    if challenged_player_id is not None:
        challenged = await session.get(Player, challenged_player_id)
    else:
        challenged = await session.scalar(
            select(Player).where(Player.username == challenged_username)
        )
    if challenged is None:
        raise ChallengeError("challenged player not found", 404)
    if challenged.id == challenger.id:
        raise ChallengeError("a player cannot challenge themself", 400)

    builds = await session.execute(
        select(BuildSnapshot).where(
            BuildSnapshot.player_id.in_([challenger.id, challenged.id]),
            BuildSnapshot.is_current.is_(True),
        )
    )
    current_builds = {build.player_id: build for build in builds.scalars()}
    challenger_build = current_builds.get(challenger.id)
    challenged_build = current_builds.get(challenged.id)
    if challenger_build is None:
        raise ChallengeError("challenger has no published build", 409)
    if challenged_build is None:
        raise ChallengeError("challenged player has no published build", 409)

    challenge = PvpChallenge(
        challenger_id=challenger.id,
        challenged_id=challenged.id,
        challenger_build_id=challenger_build.id,
        challenged_build_id=challenged_build.id,
        status="pending",
    )
    session.add(challenge)
    await session.flush()
    await session.refresh(challenge, attribute_names=["challenger_build", "challenged_build"])
    return challenge


async def get_challenge(session: AsyncSession, challenge_id: str) -> PvpChallenge | None:
    result = await session.execute(
        select(PvpChallenge)
        .options(*_build_load_options())
        .where(PvpChallenge.id == challenge_id)
    )
    return result.scalar_one_or_none()


async def resolve_challenge(
    session: AsyncSession,
    challenge_id: str,
    *,
    seed: int | None = None,
) -> PvpMatch | None:
    result = await session.execute(
        select(PvpChallenge)
        .options(*_build_load_options(), selectinload(PvpChallenge.match))
        .where(PvpChallenge.id == challenge_id)
        .with_for_update()
    )
    challenge = result.scalar_one_or_none()
    if challenge is None:
        return None
    if challenge.match is not None:
        return challenge.match

    battle_seed = seed if seed is not None else secrets.randbits(63)
    result_name, events = resolve_battle(
        challenge.challenger_build.cat_snapshot,
        challenge.challenged_build.cat_snapshot,
        battle_seed,
    )
    match = PvpMatch(
        challenge_id=challenge.id,
        challenger_id=challenge.challenger_id,
        challenged_id=challenge.challenged_id,
        seed=battle_seed,
        status="completed",
        result="challenger" if result_name == "player" else "challenged",
        challenger_snapshot=challenge.challenger_build.cat_snapshot,
        challenged_snapshot=challenge.challenged_build.cat_snapshot,
        events=events,
        turn_count=sum(event["event_type"] == "attack" for event in events),
    )
    challenge.status = "completed"
    session.add(match)
    await session.flush()
    return match


async def get_match(session: AsyncSession, challenge_id: str) -> PvpMatch | None:
    result = await session.execute(
        select(PvpMatch).where(PvpMatch.challenge_id == challenge_id)
    )
    return result.scalar_one_or_none()


async def get_player_challenges(
    session: AsyncSession,
    player_id: str,
) -> list[PvpChallenge]:
    result = await session.execute(
        select(PvpChallenge)
        .options(*_build_load_options())
        .where(
            or_(
                PvpChallenge.challenger_id == player_id,
                PvpChallenge.challenged_id == player_id,
            )
        )
        .order_by(PvpChallenge.created_at.desc())
    )
    return list(result.scalars().all())


async def get_player_matches(session: AsyncSession, player_id: str) -> list[PvpMatch]:
    result = await session.execute(
        select(PvpMatch)
        .where(
            or_(
                PvpMatch.challenger_id == player_id,
                PvpMatch.challenged_id == player_id,
            )
        )
        .order_by(PvpMatch.created_at.desc())
    )
    return list(result.scalars().all())
