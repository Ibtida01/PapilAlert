from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
from typing import Any

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    cv2 = None


@dataclass
class ImageQuality:
    width: int
    height: int
    format: str | None
    file_size_bytes: int
    blur_score: float | None
    mean_luminance: float
    dark_pixel_fraction: float
    clipped_pixel_fraction: float
    quality_score: int
    flags: list[str]
    gate: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def decode_image(raw: bytes) -> Image.Image:
    """Decode a still image safely and apply EXIF orientation."""
    try:
        with Image.open(BytesIO(raw)) as src:
            if getattr(src, "n_frames", 1) != 1:
                raise ValueError("Animated images are not supported. Upload a still photograph.")
            image = ImageOps.exif_transpose(src).convert("RGB")
            image.load()
            return image
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The uploaded file is not a readable image.") from exc


def inspect_image(image: Image.Image, file_size_bytes: int = 0) -> ImageQuality:
    """Compute generic engineering checks; these are NOT clinically validated.

    A low score means the file may be hard for a model to process. This function
    does not identify papilledema, disease, or patient risk.
    """
    image = image.convert("RGB")
    width, height = image.size
    arr = np.asarray(image, dtype=np.uint8)
    gray = np.asarray(image.convert("L"), dtype=np.uint8)

    mean_luminance = float(gray.mean() / 255.0)
    dark_fraction = float(np.mean(gray < 12))
    clipped_fraction = float(np.mean((gray < 3) | (gray > 252)))

    blur_score: float | None = None
    if cv2 is not None:
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    flags: list[str] = []
    score = 100

    if min(width, height) < 192:
        flags.append("Low image resolution: shortest side is below 192 pixels.")
        score -= 35
    if mean_luminance < 0.06:
        flags.append("Image is very dark; recapture with more even illumination.")
        score -= 25
    elif mean_luminance > 0.94:
        flags.append("Image is very bright; highlights may obscure detail.")
        score -= 20
    if dark_fraction > 0.70:
        flags.append("Most pixels are near black; verify framing and illumination.")
        score -= 20
    if clipped_fraction > 0.50:
        flags.append("Large clipped regions detected; fine detail may be lost.")
        score -= 15
    if blur_score is not None and blur_score < 8.0:
        flags.append("Low edge detail detected; image may be blurred.")
        score -= 20

    if not flags:
        flags.append("No gross technical issue detected by these basic checks.")

    score = max(0, min(100, score))
    # Only hard-fail obviously unusable technical input. Thresholds are heuristic.
    gate = "reacquire" if min(width, height) < 96 or mean_luminance < 0.015 or mean_luminance > 0.99 else "pass_with_caveats"

    return ImageQuality(
        width=width,
        height=height,
        format="decoded-image",
        file_size_bytes=int(file_size_bytes),
        blur_score=blur_score,
        mean_luminance=round(mean_luminance, 4),
        dark_pixel_fraction=round(dark_fraction, 4),
        clipped_pixel_fraction=round(clipped_fraction, 4),
        quality_score=score,
        flags=flags,
        gate=gate,
    )
