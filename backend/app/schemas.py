from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


class JobResponse(BaseModel):
    model_config = {"str_to_lower": False}

    id: str = Field(..., min_length=1, description="Stable job identifier")
    title: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., min_length=1, max_length=120)
    location: str = Field(..., min_length=1, max_length=120)
    url: str = Field(..., pattern=r"^https?://", description="Direct application URL")
    posted_at: str = Field(..., description="ISO-8601 datetime string")
    source: str = Field(..., min_length=1, max_length=40)
    job_type: str = Field(..., min_length=1, max_length=40)
    tags: List[str] = Field(default_factory=list, description="Skill tags")

    @field_validator("url", mode="before")
    @classmethod
    def _ensure_url_scheme(cls, value: str) -> str:
        value = str(value)
        if not value.startswith(("http://", "https://")):
            return f"https://{value}"
        return value

    @field_validator("title", "company", "location", mode="before")
    @classmethod
    def _strip_whitespace(cls, value: str) -> str:
        return str(value).strip()


class JobSearchQuery(BaseModel):
    q: Optional[str] = Field(None, min_length=1, max_length=120)
    location: Optional[str] = Field(None, min_length=1, max_length=120)
    job_type: Optional[str] = Field(None, min_length=1, max_length=40)
    source: Optional[str] = Field(None, min_length=1, max_length=40)


class CreateJobAlert(BaseModel):
    query: JobSearchQuery
    channel: str = Field(..., pattern=r"^(email|webhook|slack)$")
