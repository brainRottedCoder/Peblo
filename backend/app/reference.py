from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.config import get_settings

SECTIONS = ("featured", "series", "minisodes", "songs")
CATEGORIES = (
    "adventure",
    "folk",
    "friendship",
    "india",
    "language",
    "learning",
    "maths",
    "music",
    "nature",
    "reading",
    "science",
    "singalong",
    "stories",
    "travel",
    "values",
)
LANGUAGES = ("en", "hi")
ARTWORK_KINDS = ("poster", "banner", "thumbnail")
STATUSES = ("draft", "published")
TRAILER_SEASON = 0

SECTION_LABELS = {
    "featured": "Featured",
    "series": "Series",
    "minisodes": "Minisodes",
    "songs": "Songs",
}

LANGUAGE_LABELS = {"en": "English", "hi": "Hindi"}


@lru_cache
def load_reference() -> dict:
    path = Path(get_settings().data_dir) / "reference.json"
    return json.loads(path.read_text(encoding="utf-8"))


def artwork_specs() -> dict:
    return load_reference()["artwork_specs"]
