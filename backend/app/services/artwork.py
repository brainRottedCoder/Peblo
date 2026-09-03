from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.reference import artwork_specs

MAX_BYTES = 200 * 1024
ASPECT_TOLERANCE = 0.05
MIN_DIM_RATIO = 0.8


@dataclass
class ArtworkOk:
    width: int
    height: int
    content_type: str


class ArtworkError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def _friendly_kind(kind: str) -> str:
    return {"poster": "poster", "banner": "banner", "thumbnail": "thumbnail"}[kind]


def validate_artwork(kind: str, data: bytes) -> ArtworkOk:
    specs = artwork_specs()[kind]
    target_w, target_h = specs["target_px"]
    expected_aspect = target_w / target_h
    label = _friendly_kind(kind)

    if len(data) > MAX_BYTES:
        kb = round(len(data) / 1024)
        raise ArtworkError(
            f"This file is {kb} KB. {label.capitalize()}s must be 200 KB or smaller. "
            "Export it again at a lower quality, or shrink the image, then try once more."
        )

    try:
        image = Image.open(BytesIO(data))
        image.load()
    except UnidentifiedImageError as exc:
        raise ArtworkError(
            "We couldn't open that file as an image. Please upload a JPG or PNG."
        ) from exc

    width, height = image.size
    if width < 1 or height < 1:
        raise ArtworkError("That image has no width or height. Please upload a different file.")

    actual_aspect = width / height
    if abs(actual_aspect - expected_aspect) > expected_aspect * ASPECT_TOLERANCE:
        raise ArtworkError(
            f"This {label} is {width}×{height} pixels "
            f"({_ratio_label(width, height)}). "
            f"{label.capitalize()}s need to be {specs['aspect']} — about {target_w}×{target_h} pixels. "
            "Crop or export a new image in that shape."
        )

    if width < target_w * MIN_DIM_RATIO or height < target_h * MIN_DIM_RATIO:
        raise ArtworkError(
            f"This {label} is {width}×{height} pixels — too small. "
            f"Please upload one closer to {target_w}×{target_h} pixels so it stays sharp on a TV."
        )

    fmt = (image.format or "").upper()
    content_type = "image/png" if fmt == "PNG" else "image/jpeg"
    return ArtworkOk(width=width, height=height, content_type=content_type)


def _ratio_label(width: int, height: int) -> str:
    # Reduce to a short ratio so editors see "4:3" not "1.333".
    a, b = width, height
    while b:
        a, b = b, a % b
    g = a or 1
    return f"{width // g}:{height // g}"
