import json
import uuid

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import SessionLocal
from app.models import Artwork, Episode, Season, Show, User
from app.security import create_token, hash_password
from app.services.catalog import LIVE_KEY, POINTER_KEY, build_catalogue_payload, publish_catalogue
from app.storage import get_storage


def _user(role: str) -> tuple[User, dict[str, str]]:
    db = SessionLocal()
    try:
        email = f"{role}-{uuid.uuid4().hex[:10]}@test.local"
        user = User(email=email, password_hash=hash_password("test-password"), role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_token(str(user.id), user.email, user.role)
        return user, {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


def _cleanup_user(user_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        row = db.get(User, user_id)
        if row:
            db.delete(row)
            db.commit()
    finally:
        db.close()


def test_editor_jwt_cannot_publish(client: TestClient):
    user, headers = _user("editor")
    try:
        res = client.post("/admin/catalog/publish", headers=headers)
        assert res.status_code == 403
        assert "admin" in res.json()["detail"].lower()
    finally:
        _cleanup_user(user.id)


def test_admin_jwt_can_hit_publish(client: TestClient):
    user, headers = _user("admin")
    try:
        res = client.post("/admin/catalog/publish", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["outcome"] in {"success", "blocked", "failed"}
        assert body["actor_email"] == user.email
    finally:
        _cleanup_user(user.id)


def test_editor_can_list_shows(client: TestClient):
    user, headers = _user("editor")
    try:
        res = client.get("/admin/shows?page=1&page_size=5", headers=headers)
        assert res.status_code == 200
        assert "items" in res.json()
    finally:
        _cleanup_user(user.id)


def test_duplicate_content_group_language_rejected(client: TestClient):
    user, headers = _user("editor")
    try:
        slug = f"uniq-{uuid.uuid4().hex[:8]}"
        show = client.post(
            "/admin/shows",
            headers=headers,
            json={"title": "Unique Group", "slug": slug, "synopsis": "x", "section": "series", "status": "draft"},
        )
        assert show.status_code == 201
        show_id = show.json()["id"]
        season = client.post(f"/admin/shows/{show_id}/seasons", headers=headers, json={"number": 1})
        assert season.status_code == 201
        season_id = season.json()["id"]
        first = client.post(
            f"/admin/seasons/{season_id}/episodes",
            headers=headers,
            json={
                "title": "One",
                "number": 1,
                "language": "en",
                "content_group": f"{slug}-e1",
                "status": "draft",
            },
        )
        assert first.status_code == 201
        second = client.post(
            f"/admin/seasons/{season_id}/episodes",
            headers=headers,
            json={
                "title": "One again",
                "number": 2,
                "language": "en",
                "content_group": f"{slug}-e1",
                "status": "draft",
            },
        )
        assert second.status_code == 422
        assert "content group" in second.json()["detail"].lower()
        client.delete(f"/admin/shows/{show_id}", headers=headers)
    finally:
        _cleanup_user(user.id)


def test_artwork_upload_rejects_wrong_ratio_and_oversize(client: TestClient, assets_dir):
    user, headers = _user("editor")
    try:
        slug = f"art-{uuid.uuid4().hex[:8]}"
        show = client.post(
            "/admin/shows",
            headers=headers,
            json={"title": "Art Check", "slug": slug, "synopsis": "x", "status": "draft"},
        )
        show_id = show.json()["id"]
        bad_ratio = client.post(
            f"/admin/shows/{show_id}/artwork",
            headers=headers,
            data={"kind": "poster"},
            files={"file": ("poster_wrong_ratio.jpg", (assets_dir / "poster_wrong_ratio.jpg").read_bytes(), "image/jpeg")},
        )
        assert bad_ratio.status_code == 422
        detail = bad_ratio.json()["detail"]
        assert "2:3" in detail
        too_big = client.post(
            f"/admin/shows/{show_id}/artwork",
            headers=headers,
            data={"kind": "banner"},
            files={"file": ("banner_too_big.png", (assets_dir / "banner_too_big.png").read_bytes(), "image/png")},
        )
        assert too_big.status_code == 422
        assert "200 KB" in too_big.json()["detail"]
        good = client.post(
            f"/admin/shows/{show_id}/artwork",
            headers=headers,
            data={"kind": "poster"},
            files={"file": ("poster_good.jpg", (assets_dir / "poster_good.jpg").read_bytes(), "image/jpeg")},
        )
        assert good.status_code == 200
        assert good.json()["kind"] == "poster"
        client.delete(f"/admin/shows/{show_id}", headers=headers)
    finally:
        _cleanup_user(user.id)


def test_publish_blocked_leaves_live_file(client: TestClient, monkeypatch, tmp_path):
    from app.schemas import ValidationIssue, ValidationReport
    from app.services import catalog as cat

    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    get_settings.cache_clear()
    storage = get_storage()
    storage.put_atomic(LIVE_KEY, b'{"run_id":"keep-me","sections":[]}', "application/json")

    def blocked(_db):
        return ValidationReport(
            can_publish=False,
            blocking=[
                ValidationIssue(
                    severity="error",
                    code="test_block",
                    message="Blocked on purpose.",
                    how_to_fix="Nothing to fix — this is a test.",
                )
            ],
            warnings=[],
            groups={},
        )

    monkeypatch.setattr(cat, "build_validation_report", blocked)
    db = SessionLocal()
    try:
        run = publish_catalogue(db, "tester@test.local")
        assert run.outcome == "blocked"
        assert json.loads(storage.get(LIVE_KEY))["run_id"] == "keep-me"
    finally:
        db.close()
        get_settings.cache_clear()


def test_publish_atomic_and_idempotent(monkeypatch, tmp_path):
    from app.schemas import ValidationReport
    from app.services import catalog as cat

    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    get_settings.cache_clear()

    def ok(_db):
        return ValidationReport(can_publish=True, blocking=[], warnings=[], groups={})

    monkeypatch.setattr(cat, "build_validation_report", ok)
    monkeypatch.setattr(
        cat,
        "build_catalogue_payload",
        lambda db, run_id: ({"published_at": "t", "run_id": str(run_id), "sections": []}, 2, 4),
    )

    db = SessionLocal()
    try:
        first = publish_catalogue(db, "admin@test.local")
        assert first.outcome == "success"
        storage = get_storage()
        assert storage.exists(LIVE_KEY)
        assert storage.exists(POINTER_KEY)
        assert storage.exists(first.catalogue_key)
        live = json.loads(storage.get(LIVE_KEY))
        assert live["sections"] == []
        second = publish_catalogue(db, "admin@test.local")
        assert second.outcome == "success"
        assert (second.notes or {}).get("idempotent") is True
        assert second.catalogue_key == first.catalogue_key
    finally:
        db.close()
        get_settings.cache_clear()


def test_build_catalogue_groups_languages_and_lifts_season_zero():
    db = SessionLocal()
    slug = f"group-{uuid.uuid4().hex[:8]}"
    show = Show(
        title="Group Test",
        slug=slug,
        synopsis="x",
        section="series",
        categories=["stories"],
        status="published",
    )
    db.add(show)
    db.flush()
    s0 = Season(show_id=show.id, number=0)
    s1 = Season(show_id=show.id, number=1)
    db.add_all([s0, s1])
    db.flush()
    group = f"{slug}-e1"
    en = Episode(
        season_id=s1.id,
        show_id=show.id,
        title="The Kite",
        number=1,
        duration_seconds=120,
        language="en",
        content_group=group,
        status="published",
    )
    hi = Episode(
        season_id=s1.id,
        show_id=show.id,
        title="पतंग",
        number=1,
        duration_seconds=120,
        language="hi",
        content_group=group,
        status="published",
    )
    trailer = Episode(
        season_id=s0.id,
        show_id=show.id,
        title="Trailer",
        number=1,
        duration_seconds=30,
        language="en",
        content_group=f"{slug}-t1",
        status="published",
    )
    db.add_all([en, hi, trailer])
    db.flush()
    for ep in (en, hi, trailer):
        db.add(
            Artwork(
                kind="thumbnail",
                storage_key=f"artwork/episodes/{ep.id}/thumbnail.jpg",
                width=640,
                height=360,
                byte_size=12,
                content_type="image/jpeg",
                episode_id=ep.id,
            )
        )
    db.commit()
    try:
        payload, show_count, grouped = build_catalogue_payload(db, uuid.uuid4())
        found = None
        for section in payload["sections"]:
            for item in section["shows"]:
                if item["slug"] == slug:
                    found = item
        assert found is not None
        assert found["trailers"][0]["content_group"] == f"{slug}-t1"
        assert found["seasons"][0]["number"] == 1
        entry = found["seasons"][0]["episodes"][0]
        assert entry["languages"] == ["en", "hi"]
        assert entry["titles_by_language"]["en"] == "The Kite"
        assert entry["titles_by_language"]["hi"] == "पतंग"
        assert grouped >= 1
        assert show_count >= 1
    finally:
        db.delete(show)
        db.commit()
        db.close()
