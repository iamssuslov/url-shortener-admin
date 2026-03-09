import csv
import io
import re
import secrets
from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl, field_validator
from sqlmodel import Session, select

from .auth_api import require_api_key
from .db import get_session
from .models import ApiKey, Link
from .rate_limit import is_rate_limited

router = APIRouter(prefix="/api/v1", tags=["api"])

CUSTOM_CODE_RE = re.compile(r"^[a-zA-Z0-9_-]{4,32}$")


class CreateLinkIn(BaseModel):
    target_url: HttpUrl
    custom_code: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_clicks: Optional[int] = None

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, value: Optional[str]):
        if value is None:
            return value
        if not CUSTOM_CODE_RE.fullmatch(value):
            raise ValueError(
                "custom_code must be 4-32 chars and contain only letters, numbers, underscore, hyphen"
            )
        return value

    @field_validator("max_clicks")
    @classmethod
    def validate_max_clicks(cls, value: Optional[int]):
        if value is not None and value < 1:
            raise ValueError("max_clicks must be >= 1")
        return value


class LinkOut(BaseModel):
    code: str
    target_url: str
    clicks: int
    is_blocked: bool
    expires_at: Optional[datetime] = None
    max_clicks: Optional[int] = None
    is_expired: bool
    is_deleted: bool


class LinkListOut(BaseModel):
    items: list[LinkOut]
    total: int
    page: int
    page_size: int


class HealthOut(BaseModel):
    status: str


def gen_code(n: int = 7) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))


def is_link_expired(link: Link) -> bool:
    now = datetime.now(UTC)

    if link.deleted_at is not None:
        return True

    if link.expires_at is not None:
        expires_at = link.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= now:
            return True

    if link.max_clicks is not None and link.clicks >= link.max_clicks:
        return True

    return False


def to_link_out(link: Link) -> LinkOut:
    return LinkOut(
        code=link.code,
        target_url=link.target_url,
        clicks=link.clicks,
        is_blocked=link.is_blocked,
        expires_at=link.expires_at,
        max_clicks=link.max_clicks,
        is_expired=is_link_expired(link),
        is_deleted=link.deleted_at is not None,
    )


@router.get("/health", response_model=HealthOut)
def healthcheck():
    return HealthOut(status="ok")


@router.post("/links", response_model=LinkOut, status_code=201)
def create_link(
    payload: CreateLinkIn,
    request: Request,
    session: Session = Depends(get_session),
    _: ApiKey = Depends(require_api_key),
):
    client_ip = request.client.host if request.client else "unknown"

    if is_rate_limited(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    if payload.custom_code:
        exists = session.exec(
            select(Link).where(Link.code == payload.custom_code)
        ).first()
        if exists and exists.deleted_at is None:
            raise HTTPException(status_code=409, detail="Custom code already exists")

        link = Link(
            code=payload.custom_code,
            target_url=str(payload.target_url),
            expires_at=payload.expires_at,
            max_clicks=payload.max_clicks,
        )
        session.add(link)
        session.commit()
        session.refresh(link)
        return to_link_out(link)

    for _ in range(10):
        code = gen_code()
        exists = session.exec(
            select(Link).where(Link.code == code, Link.deleted_at.is_(None))
        ).first()
        if not exists:
            link = Link(
                code=code,
                target_url=str(payload.target_url),
                expires_at=payload.expires_at,
                max_clicks=payload.max_clicks,
            )
            session.add(link)
            session.commit()
            session.refresh(link)
            return to_link_out(link)

    raise HTTPException(status_code=500, detail="Failed to generate code")


@router.get("/links", response_model=LinkListOut)
def list_links(
    session: Session = Depends(get_session),
    _: ApiKey = Depends(require_api_key),
    query: Optional[str] = None,
    blocked: Optional[bool] = None,
    expired: Optional[bool] = None,
    include_deleted: bool = False,
    sort: str = Query(default="created_desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
):
    links = session.exec(select(Link)).all()

    if not include_deleted:
        links = [l for l in links if l.deleted_at is None]

    if query:
        q = query.lower()
        links = [
            l for l in links
            if q in l.target_url.lower() or q in l.code.lower()
        ]

    if blocked is not None:
        links = [l for l in links if l.is_blocked == blocked]

    if expired is not None:
        links = [l for l in links if is_link_expired(l) == expired]

    if sort == "clicks_desc":
        links.sort(key=lambda x: x.clicks, reverse=True)
    elif sort == "clicks_asc":
        links.sort(key=lambda x: x.clicks)
    elif sort == "created_asc":
        links.sort(key=lambda x: x.created_at)
    else:
        links.sort(key=lambda x: x.created_at, reverse=True)

    total = len(links)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = links[start:end]

    return LinkListOut(
        items=[to_link_out(link) for link in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/links/export")
def export_links_csv(
    session: Session = Depends(get_session),
    _: ApiKey = Depends(require_api_key),
):
    links = session.exec(select(Link)).all()
    links = [l for l in links if l.deleted_at is None]
    links.sort(key=lambda x: x.created_at, reverse=True)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "code",
            "target_url",
            "clicks",
            "is_blocked",
            "expires_at",
            "max_clicks",
            "is_expired",
        ]
    )

    for link in links:
        writer.writerow([
            link.code,
            link.target_url,
            link.clicks,
            link.is_blocked,
            link.expires_at.isoformat() if link.expires_at else "",
            link.max_clicks if link.max_clicks is not None else "",
            is_link_expired(link),
        ])

    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=links.csv"},
    )


@router.get("/links/{code}", response_model=LinkOut)
def get_link(
    code: str,
    session: Session = Depends(get_session),
    _: ApiKey = Depends(require_api_key),
):
    link = session.exec(select(Link).where(Link.code == code)).first()
    if not link or link.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Not found")
    return to_link_out(link)


@router.delete("/links/{code}", status_code=204)
def soft_delete_link(
    code: str,
    session: Session = Depends(get_session),
    _: ApiKey = Depends(require_api_key),
):
    link = session.exec(select(Link).where(Link.code == code)).first()
    if not link or link.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Not found")

    link.deleted_at = datetime.now(UTC)
    session.add(link)
    session.commit()
    return None