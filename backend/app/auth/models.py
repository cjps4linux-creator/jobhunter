from __future__ import annotations

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str = Field(..., description="Subject/user [lorem]")
    exp: int = Field(..., description="Expiry as UTC epoch seconds")
    iat: int = Field(..., description="Issued at as UTC epoch seconds")
    type: str = Field(..., description="Token discriminator: access|refresh")
    jti: str | None = Field(default=None, description="JWT [lorem] for refresh rotation")
