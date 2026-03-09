from datetime import datetime, UTC

from fastapi import APIRouter, Depends, Form, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from .db import get_session
from .models import ClickEvent, Link
from .security import create_session, require_admin, clear_session
from .settings import settings

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")


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


@router.get("/")
def root():
    return RedirectResponse("/admin/login", status_code=302)


@router.get("/r/{code}")
def redirect(code: str, request: Request, session: Session = Depends(get_session)):
    link = session.exec(select(Link).where(Link.code == code)).first()
    if not link or link.deleted_at is not None or link.is_blocked or is_link_expired(link):
        return Response(status_code=404)

    link.clicks += 1
    session.add(link)
    session.commit()
    session.refresh(link)

    event = ClickEvent(
        link_id=link.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )
    session.add(event)
    session.commit()

    return RedirectResponse(url=link.target_url, status_code=302)


@router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/admin/login")
def admin_login(username: str = Form(...), password: str = Form(...)):
    if username == settings.admin_username and password == settings.admin_password:
        sid = create_session(username)
        resp = RedirectResponse("/admin/links", status_code=303)
        resp.set_cookie(settings.session_cookie_name, sid, httponly=True)
        return resp
    return HTMLResponse(content="Invalid credentials", status_code=401)


@router.post("/admin/logout")
def admin_logout(request: Request):
    sid = request.cookies.get(settings.session_cookie_name)
    resp = RedirectResponse("/admin/login", status_code=303)
    clear_session(resp, sid)
    return resp


@router.get("/admin/links", response_class=HTMLResponse)
def admin_links(
    request: Request,
    q: str | None = None,
    blocked: str | None = None,
    expired: str | None = None,
    include_deleted: str | None = None,
    sort: str = Query(default="clicks_desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=100),
    session: Session = Depends(get_session),
):
    require_admin(request)

    links = session.exec(select(Link)).all()

    if include_deleted != "yes":
        links = [l for l in links if l.deleted_at is None]

    if q:
        q_lower = q.lower()
        links = [
            l for l in links
            if q_lower in l.target_url.lower() or q_lower in l.code.lower()
        ]

    if blocked in {"yes", "no"}:
        blocked_bool = blocked == "yes"
        links = [l for l in links if l.is_blocked == blocked_bool]

    if expired in {"yes", "no"}:
        expired_bool = expired == "yes"
        links = [l for l in links if is_link_expired(l) == expired_bool]

    if sort == "clicks_asc":
        links.sort(key=lambda x: x.clicks)
    elif sort == "created_desc":
        links.sort(key=lambda x: x.created_at, reverse=True)
    elif sort == "created_asc":
        links.sort(key=lambda x: x.created_at)
    else:
        links.sort(key=lambda x: x.clicks, reverse=True)

    total = len(links)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    links = links[start:end]

    enriched_links = [
        {
            "code": l.code,
            "target_url": l.target_url,
            "clicks": l.clicks,
            "is_blocked": l.is_blocked,
            "expires_at": l.expires_at,
            "max_clicks": l.max_clicks,
            "is_expired": is_link_expired(l),
            "is_deleted": l.deleted_at is not None,
        }
        for l in links
    ]

    return templates.TemplateResponse(
        request,
        "admin_links.html",
        {
            "links": enriched_links,
            "q": q or "",
            "blocked": blocked or "",
            "expired": expired or "",
            "include_deleted": include_deleted or "",
            "sort": sort,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.post("/admin/links/{code}/toggle")
def toggle_block(code: str, request: Request, session: Session = Depends(get_session)):
    require_admin(request)
    link = session.exec(select(Link).where(Link.code == code)).first()
    if not link or link.deleted_at is not None:
        return Response(status_code=404)
    link.is_blocked = not link.is_blocked
    session.add(link)
    session.commit()
    return RedirectResponse("/admin/links", status_code=303)


@router.post("/admin/links/{code}/delete")
def admin_delete_link(code: str, request: Request, session: Session = Depends(get_session)):
    require_admin(request)
    link = session.exec(select(Link).where(Link.code == code)).first()
    if not link or link.deleted_at is not None:
        return Response(status_code=404)

    link.deleted_at = datetime.now(UTC)
    session.add(link)
    session.commit()
    return RedirectResponse("/admin/links?include_deleted=yes", status_code=303)


@router.get("/admin/links/{code}", response_class=HTMLResponse)
def admin_link_detail(code: str, request: Request, session: Session = Depends(get_session)):
    require_admin(request)

    link = session.exec(select(Link).where(Link.code == code)).first()
    if not link:
        return Response(status_code=404)

    events = session.exec(
        select(ClickEvent)
        .where(ClickEvent.link_id == link.id)
        .order_by(ClickEvent.clicked_at.desc())
    ).all()

    return templates.TemplateResponse(
        request,
        "link_detail.html",
        {
            "link": {
                "code": link.code,
                "target_url": link.target_url,
                "clicks": link.clicks,
                "is_blocked": link.is_blocked,
                "expires_at": link.expires_at,
                "max_clicks": link.max_clicks,
                "is_expired": is_link_expired(link),
                "is_deleted": link.deleted_at is not None,
            },
            "events": events,
        },
    )