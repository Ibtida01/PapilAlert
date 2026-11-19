from io import BytesIO

import numpy as np
from PIL import Image, ImageDraw

from app.image_checks import decode_image, inspect_image


def make_image(size=(320, 320), color=(70, 80, 90)):
    im = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(im)
    draw.ellipse((70, 70, 250, 250), outline=(190, 120, 80), width=5)
    draw.line((0, 160, 320, 160), fill=(220, 220, 220), width=3)
    return im


def test_decode_image_jpeg():
    buffer = BytesIO()
    make_image().save(buffer, format="JPEG")
    decoded = decode_image(buffer.getvalue())
    assert decoded.mode == "RGB"
    assert decoded.size == (320, 320)


def test_inspect_image_returns_heuristics():
    quality = inspect_image(make_image(), file_size_bytes=1234)
    assert quality.width == 320
    assert quality.height == 320
    assert 0 <= quality.quality_score <= 100
    assert quality.gate in {"pass_with_caveats", "reacquire"}
    assert quality.flags


def test_tiny_image_is_flagged():
    quality = inspect_image(Image.new("RGB", (64, 64), (100, 100, 100)))
    assert quality.gate == "reacquire"
    assert any("resolution" in flag.lower() for flag in quality.flags)
