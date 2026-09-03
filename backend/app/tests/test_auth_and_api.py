from fastapi.testclient import TestClient

from app.main import app
from app.security import hash_password, verify_password


def test_password_roundtrip():
    stored = hash_password("admin-password")
    assert verify_password("admin-password", stored)
    assert not verify_password("nope", stored)


def test_health_does_not_need_auth():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}


def test_catalog_is_public():
    client = TestClient(app)
    res = client.get("/catalog")
    assert res.status_code == 200
    body = res.json()
    assert "sections" in body


def test_admin_requires_auth():
    client = TestClient(app)
    assert client.get("/admin/shows").status_code == 401
    assert client.get("/admin/validation-report").status_code == 401
    assert client.post("/admin/catalog/publish").status_code == 401


def test_publish_forbidden_message_for_editor_role_decode():
    from fastapi import HTTPException

    from app.deps import require_admin

    class Dummy:
        role = "editor"

    try:
        require_admin(Dummy())  # type: ignore[arg-type]
        raise AssertionError("editor must not publish")
    except HTTPException as exc:
        assert exc.status_code == 403
        assert "admin" in exc.detail.lower()


def test_editor_passes_editor_guard():
    from app.deps import require_editor

    class Dummy:
        role = "editor"

    assert require_editor(Dummy()) is not None  # type: ignore[arg-type]


def test_admin_passes_admin_guard():
    from app.deps import require_admin

    class Dummy:
        role = "admin"

    assert require_admin(Dummy()) is not None  # type: ignore[arg-type]
