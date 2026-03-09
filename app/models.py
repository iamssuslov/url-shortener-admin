from datetime import datetime, UTC
from typing import Optional
from sqlmodel import SQLModel, Field


class Link(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    target_url: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    clicks: int = 0
    is_blocked: bool = False

    expires_at: Optional[datetime] = None
    max_clicks: Optional[int] = None

    deleted_at: Optional[datetime] = Field(default=None, index=True)


class ClickEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    link_id: int = Field(index=True, foreign_key="link.id")
    clicked_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None


class ApiKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))