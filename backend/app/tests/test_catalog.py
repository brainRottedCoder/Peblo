import json
from pathlib import Path

from app.services.catalog import search_catalogue
from app.storage.local import LocalDiskStorage


def _show(title, section="series", categories=None, languages=None, episodes=None):
    return {
        "id": title,
        "slug": title.lower().replace(" ", "-"),
        "title": title,
        "synopsis": "",
        "categories": categories or ["stories"],
        "section": section,
        "artwork": {},
        "seasons": [
            {
                "number": 1,
                "episodes": episodes
                or [
                    {
                        "content_group": f"{title}-e1",
                        "title": "The Lost Kite",
                        "episode_number": 1,
                        "duration_seconds": 400,
                        "languages": languages or ["en"],
                        "artwork": {},
                    }
                ],
            }
        ],
        "trailers": [],
    }


def _catalogue():
    return {
        "run_id": "test",
        "sections": [
            {"id": "featured", "title": "Featured", "shows": [_show("Moti", "featured", ["adventure"], ["en", "hi"])]},
            {"id": "series", "title": "Series", "shows": [_show("Tiny Tales", "series", ["stories", "folk"], ["en"])]},
            {"id": "songs", "title": "Songs", "shows": [_show("Peblo Songs", "songs", ["music"], ["hi"])]},
        ],
    }


def test_search_matches_show_title():
    result = search_catalogue(_catalogue(), q="moti")
    assert [s["title"] for s in result["results"]] == ["Moti"]


def test_search_matches_episode_title():
    result = search_catalogue(_catalogue(), q="lost kite")
    assert len(result["results"]) == 3


def test_search_matches_category():
    result = search_catalogue(_catalogue(), q="folk")
    assert [s["title"] for s in result["results"]] == ["Tiny Tales"]


def test_filters_compose():
    result = search_catalogue(_catalogue(), q="kite", language="hi", section="songs")
    assert [s["title"] for s in result["results"]] == ["Peblo Songs"]


def test_language_filter_excludes():
    result = search_catalogue(_catalogue(), language="hi", section="series")
    assert result["results"] == []


def test_empty_query_returns_filtered_shows():
    result = search_catalogue(_catalogue(), category="music")
    assert [s["title"] for s in result["results"]] == ["Peblo Songs"]


def test_put_atomic_replaces_without_partial_read(tmp_path):
    storage = LocalDiskStorage(tmp_path, "http://localhost")
    storage.put_atomic("catalogues/catalogue.json", b'{"v":1}', "application/json")
    assert json.loads(storage.get("catalogues/catalogue.json")) == {"v": 1}
    storage.put_atomic("catalogues/catalogue.json", b'{"v":2}', "application/json")
    assert json.loads(storage.get("catalogues/catalogue.json")) == {"v": 2}
    leftovers = list(Path(tmp_path).rglob("*.tmp"))
    assert leftovers == []


def test_search_matches_language_specific_title():
    show = _show("Moti")
    show["seasons"][0]["episodes"][0]["titles_by_language"] = {"en": "The Lost Kite", "hi": "पतंग"}
    catalogue = {"run_id": "test", "sections": [{"id": "series", "title": "Series", "shows": [show]}]}
    result = search_catalogue(catalogue, q="पतंग")
    assert [s["title"] for s in result["results"]] == ["Moti"]
