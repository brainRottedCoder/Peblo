from fastapi import APIRouter, HTTPException, Query

from app.services.catalog import read_live_catalogue, search_catalogue

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def get_catalog() -> dict:
    return read_live_catalogue()


@router.get("/catalog/search")
def search_catalog(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    language: str | None = Query(default=None),
    section: str | None = Query(default=None),
) -> dict:
    catalogue = read_live_catalogue()
    if not catalogue.get("run_id"):
        raise HTTPException(404, "No catalogue has been published yet.")
    return search_catalogue(catalogue, q=q, category=category, language=language, section=section)
