from __future__ import annotations

import base64
import logging
from io import BytesIO
from pathlib import Path

from PIL import Image

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .image_checks import decode_image, inspect_image
from .model import load_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("papilalert")

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}

# Reproduced on the RFMiD 1.0 held-out test partition (640 images).
# These are dataset-level evaluation metrics, not guarantees for a new upload.
PERFORMANCE = {
    "primary": {
        "dataset": "RFMiD 1.0",
        "partition": "held-out test set",
        "n": 640,
        "positives": 17,
        "auroc": 0.9671419129449532,
        "auprc": 0.7849151665328137,
        "sensitivity": 0.7058823529411765,
        "specificity": 0.9983948635634029,
        "threshold": 0.5,
        "confusion_matrix": {"tn": 622, "fp": 1, "fn": 5, "tp": 12},
        "note": "Single held-out dataset evaluation; only 17 ODE-positive test images. Not clinical validation.",
    },
    "external": {
        "dataset": "RFMiD 2.0",
        "partition": "exploratory external test subset",
        "n_matched": 170,
        "positives": 4,
        "unmatched_predictions": 4,
        "unmatched_labels": 4,
        "auroc": 0.8810240963855421,
        "auprc": 0.15600613154960982,
        "sensitivity": 0.0,
        "specificity": 1.0,
        "threshold": 0.5,
        "note": "Exploratory only: four positive cases, four unmatched records, and zero true-positive detections at threshold 0.5. Estimates are highly uncertain.",
    },
}

app = FastAPI(
    title="PapilAlert Research Prototype",
    version="0.2.1",
    description="Optic-disc image workflow demonstrator. Not a medical device or diagnostic tool.",
)
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
MODEL, MODEL_MESSAGE = load_model()


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    # Return the page with embedded CSS. This avoids unstyled rendering when a
    # browser, reverse proxy, or cached deployment fails to load /static CSS.
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "no-store, max-age=0", "Pragma": "no-cache"},
    )


def make_preview_data_url(image: Image.Image, max_dimension: int = 1400) -> str:
    """Create a compact browser-safe preview of the uploaded image in memory."""
    preview = image.convert("RGB").copy()
    preview.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    preview.save(buffer, format="JPEG", quality=88, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


@app.get("/api/status")
def status() -> dict:
    return {
        "app": "PapilAlert Research Prototype",
        "version": "0.2.1",
        "model_loaded": MODEL is not None,
        "model_message": MODEL_MESSAGE,
        "model_name": MODEL.metadata.get("model_name", "MobileNetV3-Small") if MODEL else None,
        "clinical_status": "research demonstrator; not clinically validated; not for patient-care decisions",
        "explanation_method": "Grad-CAM for the optic_disc_edema output class" if MODEL else None,
        "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
    }


@app.get("/api/metrics")
def metrics() -> dict:
    return PERFORMANCE


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, WEBP or BMP still image.")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Maximum upload size is 12 MB.")
    try:
        image = decode_image(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    quality = inspect_image(image, len(raw)).to_dict()
    response = {
        "status": "quality_only",
        "quality": quality,
        "prediction": None,
        "explanation": None,
        "message": MODEL_MESSAGE,
        "important_notice": "This prototype cannot diagnose papilledema or measure intracranial pressure. A fundus photograph alone cannot establish either diagnosis.",
    }

    if quality["gate"] == "reacquire":
        response["status"] = "reacquire"
        response["message"] = "The image failed a basic technical check. Retake or select a better image."
        return response

    if MODEL is not None:
        response["prediction"] = MODEL.predict(image)
        try:
            overlay = MODEL.gradcam_overlay(image, target_class="optic_disc_edema")
        except Exception as exc:  # Explanation failure must not block prediction.
            logger.exception("Grad-CAM generation failed: %s", exc)
            overlay = None
        if overlay:
            response["explanation"] = {
                "method": "Grad-CAM",
                "target_class": "optic_disc_edema",
                "overlay_data_url": overlay,
                "title": "Model attention for the ODE output",
                "original_data_url": make_preview_data_url(image),
                "note": "Warm regions indicate image areas that contributed more to this model's ODE-class score. This is a coarse model-attention map—not a lesion segmentation, anatomical boundary, proof of edema, or clinical explanation.",
            }
        response["status"] = "research_model_output"
        response["message"] = "Research-model output only. It requires qualified clinical interpretation and independent validation."

    return response
