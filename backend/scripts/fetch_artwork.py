"""Download real photographs and pack them to Peblo artwork specs."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import urllib.request

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "data" / "show-art"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Real photographs (Unsplash + Wikimedia). Used as show posters/banners, not as people claiming to be staff.
SHOWS = {
    "motis-many-lives": {
        "poster": "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=900&h=1350&q=80",
        "banner": "https://images.unsplash.com/photo-1601758228041-f3b2795255f1?auto=format&fit=crop&w=1600&h=900&q=80",
    },
    "tiny-tales-banyan-dadi": {
        "poster": "https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?auto=format&fit=crop&w=900&h=1350&q=80",
        "banner": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1600&h=900&q=80",
    },
    "discover-india-with-moti": {
        "poster": "https://images.unsplash.com/photo-1477587458883-47145f2ee6c5?auto=format&fit=crop&w=900&h=1350&q=80",
        "banner": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1600&h=900&q=80",
    },
    "peblo-songs": {
        "poster": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=900&h=1350&q=80",
        "banner": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1600&h=900&q=80",
    },
    "peblo-songs-lyrical": {
        "poster": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=900&h=1350&q=80",
        "banner": "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?auto=format&fit=crop&w=1600&h=900&q=80",
    },
    "curious-cubs": {
        "poster": "https://images.unsplash.com/photo-1614027164847-1b28cfe1df60?auto=format&fit=crop&w=900&h=1350&q=80",
        "banner": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?auto=format&fit=crop&w=1600&h=900&q=80",
    },
    "number-nest": {
        "poster": "https://images.unsplash.com/photo-1596495578065-6e0763fa1178?auto=format&fit=crop&w=900&h=1350&q=80",
        "banner": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=1600&h=900&q=80",
    },
    "rhyme-rangers": {
        "poster": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=900&h=1350&q=80",
        "banner": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=1600&h=900&q=80",
    },
}

THUMBS = [
    "https://images.unsplash.com/photo-1587300003388-59208cc962cb?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1532375810709-75b1da00537c?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1474514012253-afca349867ca?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1477587458883-47145f2ee6c5?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=960&h=540&q=80",
    "https://images.unsplash.com/photo-1546182990-dffeafbe841d?auto=format&fit=crop&w=960&h=540&q=80",
]

SIZES = {"poster": (600, 900), "banner": (1280, 720), "thumbnail": (640, 360)}


def fetch(url: str) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/jpeg,image/webp,image/*"})
    data = urllib.request.urlopen(req, timeout=40).read()
    return Image.open(BytesIO(data)).convert("RGB")


def cover(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    tw, th = size
    scale = max(tw / im.width, th / im.height)
    nw, nh = int(im.width * scale), int(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def jpeg_under(im: Image.Image, limit: int = 190_000) -> bytes:
    for q in range(82, 40, -4):
        buf = BytesIO()
        im.save(buf, format="JPEG", quality=q, optimize=True)
        if buf.tell() <= limit:
            return buf.getvalue()
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=40, optimize=True)
    return buf.getvalue()


def save_kind(im: Image.Image, dest: Path, kind: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    packed = jpeg_under(cover(im, SIZES[kind]))
    dest.write_bytes(packed)
    print(f"  {dest.name} {len(packed)} bytes {SIZES[kind]}")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for slug, urls in SHOWS.items():
        print(slug)
        folder = ROOT / slug
        for kind, url in urls.items():
            im = fetch(url)
            save_kind(im, folder / f"{kind}.jpg", kind)
            if kind == "banner":
                save_kind(im, folder / "thumbnail.jpg", "thumbnail")
    thumbs = ROOT / "thumbs"
    thumbs.mkdir(exist_ok=True)
    for i, url in enumerate(THUMBS):
        print("thumb", i)
        im = fetch(url)
        save_kind(im, thumbs / f"{i:02d}.jpg", "thumbnail")
    print("done")


if __name__ == "__main__":
    main()
