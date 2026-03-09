import secrets

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from .db import get_session
from .models import ApiKey


def generate_api_key() -> str:
    return f"sk_{secrets.token_urlsafe(24)}"


def require_api_key(
    x_api_key: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> ApiKey:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    api_key = session.exec(
        select(ApiKey).where(ApiKey.key == x_api_key)
    ).first()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not api_key.is_active:
        raise HTTPException(status_code=403, detail="API key is inactive")

    return api_key