from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.config import get_settings
from app.routers import admin_artwork, admin_catalog, admin_content, auth, catalog_public, health
from app.storage import get_storage

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _humanize_validation(err: dict) -> str:
    loc = [str(part) for part in err.get("loc", ()) if part not in ("body", "query", "path")]
    where = " → ".join(loc)
    msg = err.get("msg", "This value isn’t valid.")
    if msg.startswith("Value error, "):
        msg = msg[len("Value error, ") :]
    return f"{where}: {msg}" if where else msg


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    parts = [_humanize_validation(e) for e in exc.errors()]
    detail = "Please check the form. " + " ".join(parts) if parts else "Please check the form and try again."
    return JSONResponse(status_code=422, content={"detail": detail})

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(catalog_public.router)
app.include_router(admin_content.router)
app.include_router(admin_artwork.router)
app.include_router(admin_catalog.router)


@app.get("/media/{key:path}")
def media(key: str) -> Response:
    storage = get_storage()
    if not storage.exists(key):
        raise HTTPException(404, "Picture not found.")
    data = storage.get(key)
    content_type = "application/json" if key.endswith(".json") else "image/jpeg"
    if key.endswith(".png"):
        content_type = "image/png"
    return Response(content=data, media_type=content_type, headers={"Cache-Control": "public, max-age=3600"})
