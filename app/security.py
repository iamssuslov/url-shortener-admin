import secrets
from fastapi import Request, Response, HTTPException
from .settings import settings

# В демо храним сессии в памяти процесса (для учебного проекта ок)
SESSIONS: dict[str, str] = {}

def create_session(username: str) -> str:
    sid = secrets.token_urlsafe(24)
    SESSIONS[sid] = username
    return sid

def require_admin(request: Request) -> str:
    sid = request.cookies.get(settings.session_cookie_name)
    if not sid or sid not in SESSIONS:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return SESSIONS[sid]

def clear_session(response: Response, sid: str | None) -> None:
    if sid and sid in SESSIONS:
        del SESSIONS[sid]
    response.delete_cookie(settings.session_cookie_name)