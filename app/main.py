import os
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from . import config, storage
from .database import Base, engine, get_db, SessionLocal
from .models import User, Ticket, Attachment
from .security import hash_password, verify_password

STATUSES = ["Open", "In Progress", "Resolved", "Closed"]
PRIORITIES = ["Low", "Medium", "High"]
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".pdf", ".txt"}

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def seed_admin():
    if not (config.ADMIN_USERNAME and config.ADMIN_PASSWORD):
        return
    with SessionLocal() as db:
        if not db.query(User).filter_by(username=config.ADMIN_USERNAME).first():
            db.add(User(username=config.ADMIN_USERNAME,
                        password_hash=hash_password(config.ADMIN_PASSWORD),
                        role="admin"))
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    seed_admin()
    storage.init()
    yield


app = FastAPI(title="TicketDesk", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY, same_site="lax")


# ---------- auth helpers ----------
class NotAuthenticated(Exception):
    pass


@app.exception_handler(NotAuthenticated)
async def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    uid = request.session.get("user_id")
    user = db.get(User, uid) if uid else None
    if not user:
        raise NotAuthenticated()
    return user


# ---------- upload helpers ----------
async def read_upload(file: UploadFile | None):
    if file is None or not file.filename:
        return None
    name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(file.filename))
    if os.path.splitext(name)[1].lower() not in ALLOWED_EXT:
        raise HTTPException(400, "File type not allowed")
    data = await file.read()
    if len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, "File too large")
    return name, data, file.content_type


def store_attachment(db: Session, ticket: Ticket, payload):
    name, data, ctype = payload
    key = f"tickets/{ticket.id}/{uuid.uuid4().hex}-{name}"
    storage.upload_file(key, data, ctype)
    db.add(Attachment(ticket_id=ticket.id, filename=name, s3_key=key, content_type=ctype))
    db.commit()

def is_admin(user: User) -> bool:
    return user.role == "admin"


def get_ticket_for(db: Session, tid: int, user: User) -> Ticket:
    ticket = db.get(Ticket, tid)
    if not ticket or (not is_admin(user) and ticket.created_by != user.id):
        raise HTTPException(404, "Ticket not found")
    return ticket


# ---------- public routes ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return RedirectResponse("/tickets", status_code=303)


@app.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse(request, "register.html", {"error": None})


@app.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...),
             db: Session = Depends(get_db)):
    username = username.strip()
    error = None
    if len(username) < 3:
        error = "Username must be at least 3 characters"
    elif len(password) < 8:
        error = "Password must be at least 8 characters"
    elif db.query(User).filter_by(username=username).first():
        error = "Username already taken"
    if error:
        return templates.TemplateResponse(request, "register.html", {"error": error}, status_code=400)
    db.add(User(username=username, password_hash=hash_password(password)))
    db.commit()
    return RedirectResponse("/login", status_code=303)


@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...),
          db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username.strip()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request, "login.html",
                                          {"error": "Invalid username or password"}, status_code=401)
    request.session["user_id"] = user.id
    return RedirectResponse("/tickets", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# ---------- protected routes ----------
@app.get("/tickets")
def list_tickets(request: Request, status: str | None = None,
                 db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = db.query(Ticket).order_by(Ticket.created_at.desc())
    if not is_admin(user):
        q = q.filter(Ticket.created_by == user.id)
    if status in STATUSES:
        q = q.filter(Ticket.status == status)
    return templates.TemplateResponse(request, "tickets.html",
                                      {"user": user, "tickets": q.all(), "statuses": STATUSES})


@app.get("/tickets/new")
def new_ticket_form(request: Request, user: User = Depends(current_user)):
    return templates.TemplateResponse(request, "new.html", {"user": user, "priorities": PRIORITIES})


@app.post("/tickets/new")
async def create_ticket(title: str = Form(...), description: str = Form(""),
                        priority: str = Form("Medium"),
                        file: UploadFile | None = File(None),
                        db: Session = Depends(get_db), user: User = Depends(current_user)):
    if priority not in PRIORITIES:
        raise HTTPException(400, "Invalid priority")
    payload = await read_upload(file)  # validate before creating anything
    ticket = Ticket(title=title.strip(), description=description, priority=priority,
                    created_by=user.id)
    db.add(ticket)
    db.commit()
    if payload:
        store_attachment(db, ticket, payload)
    return RedirectResponse(f"/tickets/{ticket.id}", status_code=303)


@app.get("/tickets/{tid}")
def ticket_detail(tid: int, request: Request, db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    ticket = get_ticket_for(db, tid, user)
    return templates.TemplateResponse(request, "detail.html",
                                      {"user": user, "t": ticket, "statuses": STATUSES})


@app.post("/tickets/{tid}/status")
def update_status(tid: int, status: str = Form(...), db: Session = Depends(get_db),
                  user: User = Depends(current_user)):
    if not is_admin(user):
        raise HTTPException(403, "Only support staff can change ticket status")
    ticket = get_ticket_for(db, tid, user)
    if status not in STATUSES:
        raise HTTPException(400, "Invalid status")
    ticket.status = status
    db.commit()
    return RedirectResponse(f"/tickets/{tid}", status_code=303)


@app.post("/tickets/{tid}/attachments")
async def add_attachment(tid: int, file: UploadFile = File(...), db: Session = Depends(get_db),
                         user: User = Depends(current_user)):
    ticket = get_ticket_for(db, tid, user)
    payload = await read_upload(file)
    if not payload:
        raise HTTPException(400, "No file provided")
    store_attachment(db, ticket, payload)
    return RedirectResponse(f"/tickets/{tid}", status_code=303)


@app.get("/attachments/{aid}")
def download_attachment(aid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    att = db.get(Attachment, aid)
    if not att or (not is_admin(user) and att.ticket.created_by != user.id):
        raise HTTPException(404, "Attachment not found")
    return StreamingResponse(
        storage.stream(att.s3_key),
        media_type=att.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{att.filename}"'},
    )


@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    def counts(col):
        q = db.query(col, func.count(Ticket.id))
        if not is_admin(user):
            q = q.filter(Ticket.created_by == user.id)
        return dict(q.group_by(col).all())

    s_rows, p_rows = counts(Ticket.status), counts(Ticket.priority)
    by_status = {s: s_rows.get(s, 0) for s in STATUSES}
    by_priority = {p: p_rows.get(p, 0) for p in PRIORITIES}
    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user, "total": sum(by_status.values()),
        "by_status": by_status, "by_priority": by_priority,
    })
