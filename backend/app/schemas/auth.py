from pydantic import BaseModel, Field

from app.schemas.player import PlayerWithDetails


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class AuthResponse(PlayerWithDetails):
    pass
