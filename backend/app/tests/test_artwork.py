from io import BytesIO

from PIL import Image

from app.services.artwork import ArtworkError, validate_artwork


def _jpeg(size: tuple[int, int], quality: int = 80) -> bytes:
    im = Image.new("RGB", size, (40, 80, 120))
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _noisy_png(size: tuple[int, int]) -> bytes:
    import random

    rng = random.Random(0)
    im = Image.new("RGB", size)
    pix = im.load()
    for y in range(size[1]):
        for x in range(0, size[0], 8):
            pix[x, y] = (rng.randrange(256), rng.randrange(256), rng.randrange(256))
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_good_poster_passes():
    ok = validate_artwork("poster", _jpeg((600, 900)))
    assert ok.width == 600
    assert ok.height == 900


def test_good_banner_passes():
    ok = validate_artwork("banner", _jpeg((1280, 720)))
    assert (ok.width, ok.height) == (1280, 720)


def test_good_thumbnail_passes():
    ok = validate_artwork("thumbnail", _jpeg((640, 360)))
    assert (ok.width, ok.height) == (640, 360)


def test_wrong_ratio_rejected():
    try:
        validate_artwork("poster", _jpeg((800, 600)))
        raise AssertionError("should have rejected")
    except ArtworkError as exc:
        assert "2:3" in exc.message
        assert "800" in exc.message


def test_too_small_rejected():
    try:
        validate_artwork("thumbnail", _jpeg((80, 45)))
        raise AssertionError("should have rejected")
    except ArtworkError as exc:
        assert "too small" in exc.message.lower()


def test_over_200kb_rejected():
    data = _noisy_png((1280, 720))
    assert len(data) > 200 * 1024
    try:
        validate_artwork("banner", data)
        raise AssertionError("should have rejected")
    except ArtworkError as exc:
        assert "200 KB" in exc.message


def test_not_an_image_rejected():
    try:
        validate_artwork("poster", b"not-an-image")
        raise AssertionError("should have rejected")
    except ArtworkError as exc:
        assert "JPG or PNG" in exc.message
