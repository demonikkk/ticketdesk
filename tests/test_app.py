from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_protected_route_redirects_to_login(client):
    r = client.get("/tickets", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_register_rejects_short_password(client):
    r = client.post("/register", data={"username": "bob", "password": "short"})
    assert r.status_code == 400


def test_login_wrong_password(client):
    client.post("/register", data={"username": "bob", "password": "password123"})
    r = client.post("/login", data={"username": "bob", "password": "wrongpass1"})
    assert r.status_code == 401


def test_create_and_view_ticket(auth_client):
    r = auth_client.post("/tickets/new", data={
        "title": "Printer broken", "description": "Floor 2", "priority": "High"})
    assert r.status_code == 200
    assert "Printer broken" in r.text
    assert "Printer broken" in auth_client.get("/tickets").text


def test_admin_status_flow_and_invalid_status(admin_client):
    admin_client.post("/tickets/new", data={"title": "T1", "priority": "Low"})
    for s in ["In Progress", "Resolved", "Closed"]:
        r = admin_client.post("/tickets/1/status", data={"status": s})
        assert r.status_code == 200 and s in r.text
    assert admin_client.post("/tickets/1/status", data={"status": "Nope"}).status_code == 400


def test_user_cannot_change_status(auth_client):
    auth_client.post("/tickets/new", data={"title": "Mine", "priority": "Low"})
    r = auth_client.post("/tickets/1/status", data={"status": "Closed"})
    assert r.status_code == 403


def test_user_cannot_see_other_users_ticket(auth_client):
    auth_client.post("/tickets/new", data={"title": "Alice only", "priority": "Low"})
    other = TestClient(app)
    other.post("/register", data={"username": "bob", "password": "password123"})
    other.post("/login", data={"username": "bob", "password": "password123"})
    assert other.get("/tickets/1").status_code == 404
    assert "Alice only" not in other.get("/tickets").text


def test_admin_sees_all_tickets(auth_client, admin_client):
    auth_client.post("/tickets/new", data={"title": "From alice", "priority": "Low"})
    assert "From alice" in admin_client.get("/tickets").text


def test_dashboard_counts(admin_client):
    admin_client.post("/tickets/new", data={"title": "A", "priority": "Low"})
    admin_client.post("/tickets/new", data={"title": "B", "priority": "High"})
    admin_client.post("/tickets/2/status", data={"status": "Closed"})
    assert "<b>2</b>" in admin_client.get("/dashboard").text


def test_upload_attachment_calls_storage(auth_client):
    auth_client.post("/tickets/new", data={"title": "With file", "priority": "Low"})
    with patch("app.main.storage.upload_file") as up:
        r = auth_client.post("/tickets/1/attachments",
                             files={"file": ("shot.txt", b"hello", "text/plain")})
    assert r.status_code == 200
    assert "shot.txt" in r.text
    key = up.call_args[0][0]
    assert key.startswith("tickets/1/") and key.endswith("shot.txt")


def test_upload_rejects_bad_extension(auth_client):
    auth_client.post("/tickets/new", data={"title": "X", "priority": "Low"})
    with patch("app.main.storage.upload_file") as up:
        r = auth_client.post("/tickets/1/attachments",
                             files={"file": ("evil.exe", b"x", "application/octet-stream")})
    assert r.status_code == 400
    up.assert_not_called()