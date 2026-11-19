from io import BytesIO

import torch

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.main import app

client = TestClient(app)


def test_home_contains_embedded_styles_and_versioned_script():
    response = client.get("/")
    assert response.status_code == 200
    assert "--green-dark" in response.text
    assert "PapilAlert" in response.text
    assert "app.js?v=0.2.1" in response.text
    assert response.headers.get("cache-control", "").startswith("no-store")


def test_static_assets_are_served():
    css = client.get("/static/styles.css")
    js = client.get("/static/app.js")
    assert css.status_code == 200 and "--green-dark" in css.text
    assert js.status_code == 200 and "setEvidenceImage" in js.text


def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    body = response.json()
    assert body["clinical_status"].startswith("research demonstrator")


def test_analyze_endpoint_quality_only():
    image = Image.new("RGB", (320, 320), (80, 80, 80))
    draw = ImageDraw.Draw(image)
    draw.ellipse((50, 50, 270, 270), outline=(220, 160, 100), width=4)
    stream = BytesIO()
    image.save(stream, format="JPEG")
    response = client.post("/api/analyze", files={"file": ("sample.jpg", stream.getvalue(), "image/jpeg")})
    assert response.status_code == 200
    body = response.json()
    assert "quality" in body
    assert "important_notice" in body
    assert body["prediction"] is None or isinstance(body["prediction"], dict)


def test_rejects_non_image_content_type():
    response = client.post("/api/analyze", files={"file": ("notes.txt", b"not an image", "text/plain")})
    assert response.status_code == 415


def test_metrics_endpoint_reports_dataset_and_caveats():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["primary"]["n"] == 640
    assert body["primary"]["positives"] == 17
    assert body["primary"]["sensitivity"] == 0.7058823529411765
    assert body["external"]["n_matched"] == 170
    assert body["external"]["positives"] == 4


def test_gradcam_overlay_returns_data_url():
    import numpy as np
    from PIL import Image
    from app.model import ModelBundle, build_model

    torch_model = build_model(num_classes=2, pretrained=False)
    bundle = ModelBundle(
        model=torch_model,
        classes=["no_ode", "optic_disc_edema"],
        image_size=224,
        device="cpu",
        metadata={},
    )
    pixels = np.random.default_rng(42).integers(0, 256, (320, 320, 3), dtype=np.uint8)
    image = Image.fromarray(pixels, mode="RGB")
    overlay = bundle.gradcam_overlay(image)
    assert overlay is not None
    assert overlay.startswith("data:image/png;base64,")


def test_analyze_includes_gradcam_when_model_available(monkeypatch):
    import numpy as np
    from PIL import Image
    from app import main as main_module
    from app.model import ModelBundle, build_model

    torch.manual_seed(7)
    bundle = ModelBundle(
        model=build_model(num_classes=2, pretrained=False),
        classes=["no_ode", "optic_disc_edema"],
        image_size=224,
        device="cpu",
        metadata={},
    )
    monkeypatch.setattr(main_module, "MODEL", bundle)

    pixels = np.random.default_rng(7).integers(20, 235, (320, 320, 3), dtype=np.uint8)
    image = Image.fromarray(pixels, mode="RGB")
    stream = BytesIO()
    image.save(stream, format="PNG")

    response = client.post(
        "/api/analyze",
        files={"file": ("fundus.png", stream.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] is not None
    assert body["explanation"] is not None
    assert body["explanation"]["method"] == "Grad-CAM"
    assert body["explanation"]["overlay_data_url"].startswith("data:image/png;base64,")
    assert body["explanation"]["original_data_url"].startswith("data:image/jpeg;base64,")
    assert "not a lesion segmentation" in body["explanation"]["note"]
