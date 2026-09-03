"""Public demo clips so the viewer can actually play something.

These are Google's hosted sample MP4s (the same set used in Chrome's video demos).
They stand in for Peblo episode files — we do not ship licensed kids' shows.
"""

import hashlib

_BASE = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/"

SHOW_VIDEO = {
    "motis-many-lives": f"{_BASE}BigBuckBunny.mp4",
    "tiny-tales-banyan-dadi": f"{_BASE}ElephantsDream.mp4",
    "discover-india-with-moti": f"{_BASE}ForBiggerEscapes.mp4",
    "peblo-songs": f"{_BASE}ForBiggerJoyrides.mp4",
    "peblo-songs-lyrical": f"{_BASE}ForBiggerFun.mp4",
    "curious-cubs": f"{_BASE}Sintel.mp4",
    "number-nest": f"{_BASE}ForBiggerMeltdowns.mp4",
    "rhyme-rangers": f"{_BASE}ForBiggerBlazes.mp4",
}

_CLIPS = [
    f"{_BASE}BigBuckBunny.mp4",
    f"{_BASE}ElephantsDream.mp4",
    f"{_BASE}Sintel.mp4",
    f"{_BASE}TearsOfSteel.mp4",
    f"{_BASE}ForBiggerJoyrides.mp4",
    f"{_BASE}ForBiggerEscapes.mp4",
    f"{_BASE}ForBiggerFun.mp4",
    f"{_BASE}ForBiggerMeltdowns.mp4",
    f"{_BASE}ForBiggerBlazes.mp4",
    f"{_BASE}SubaruOutbackOnStreetAndDirt.mp4",
]


def video_for_show(slug: str) -> str:
    return SHOW_VIDEO.get(slug, _CLIPS[0])


def video_for_episode(content_group: str) -> str:
    idx = int(hashlib.md5(content_group.encode()).hexdigest(), 16) % len(_CLIPS)
    return _CLIPS[idx]
