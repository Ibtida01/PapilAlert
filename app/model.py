from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "papilalert_mobilenet_v3_small.pt"


def build_model(num_classes: int, pretrained: bool = False) -> torch.nn.Module:
    weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
    net = models.mobilenet_v3_small(weights=weights)
    in_features = net.classifier[3].in_features
    net.classifier[3] = torch.nn.Linear(in_features, num_classes)
    return net


def inference_transform(image_size: int = 224) -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


class ModelBundle:
    def __init__(self, model: torch.nn.Module, classes: list[str], image_size: int, device: str, metadata: dict[str, Any]):
        self.model = model.eval()
        self.classes = classes
        self.image_size = image_size
        self.device = device
        self.metadata = metadata
        self.transform = inference_transform(image_size)
        # MobileNetV3-Small's final feature block is the last spatial feature map
        # before global pooling/classification. Grad-CAM uses this layer.
        self.gradcam_layer = self.model.features[-1]

    @torch.inference_mode()
    def predict(self, image: Image.Image) -> dict[str, Any]:
        tensor = self.transform(image.convert("RGB")).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        scores = torch.softmax(logits, dim=1)[0].detach().cpu().tolist()
        ranked = sorted(zip(self.classes, scores), key=lambda item: item[1], reverse=True)
        top_label, top_score = ranked[0]
        margin = float(ranked[0][1] - ranked[1][1]) if len(ranked) > 1 else float(ranked[0][1])
        min_score = float(self.metadata.get("abstain_score_threshold", 0.60))
        min_margin = float(self.metadata.get("abstain_margin_threshold", 0.15))
        abstain = top_score < min_score or margin < min_margin
        return {
            "top_class": None if abstain else top_label,
            "top_score": round(float(top_score), 4),
            "margin": round(margin, 4),
            "abstain": abstain,
            "abstain_reason": "Model score or top-two margin is below the prototype's configured threshold." if abstain else None,
            "class_scores": [{"class": label, "score": round(float(score), 4)} for label, score in ranked],
            "score_interpretation": "Uncalibrated model score; not a clinical probability.",
            "model_name": self.metadata.get("model_name", "MobileNetV3-Small"),
            "model_version": self.metadata.get("model_version", "unversioned"),
        }

    def gradcam_overlay(self, image: Image.Image, target_class: str = "optic_disc_edema") -> str | None:
        """Return a Grad-CAM overlay as a PNG data URL, or None if unavailable.

        This is a model-attention visualisation, not a lesion segmentation or
        clinically validated anatomical localisation.
        """
        if target_class not in self.classes:
            return None

        captured: dict[str, torch.Tensor] = {}

        def save_activation(_module, _inputs, output):
            captured["activation"] = output

        handle = self.gradcam_layer.register_forward_hook(save_activation)
        try:
            self.model.eval()
            self.model.zero_grad(set_to_none=True)
            tensor = self.transform(image.convert("RGB")).unsqueeze(0).to(self.device)

            with torch.enable_grad():
                logits = self.model(tensor)
                activation = captured.get("activation")
                if activation is None or not activation.requires_grad:
                    return None
                class_index = self.classes.index(target_class)
                score = logits[:, class_index].sum()
                gradients = torch.autograd.grad(score, activation, retain_graph=False, create_graph=False)[0]

            weights = gradients.mean(dim=(2, 3), keepdim=True)
            cam = torch.relu((weights * activation).sum(dim=1, keepdim=True))
            # Keep the returned evidence image lightweight for the browser.
            scale = min(1.0, 1280.0 / max(image.width, image.height))
            display_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
            cam = F.interpolate(cam, size=(display_size[1], display_size[0]), mode="bilinear", align_corners=False)
            cam = cam[0, 0].detach().float().cpu().numpy()
            cam -= float(cam.min())
            max_value = float(cam.max())
            if max_value > 1e-15:
                cam /= max_value
            else:
                return None

            # A restrained, semi-transparent heatmap: cool areas are low
            # relative activation; warm areas are higher relative activation.
            heat = np.zeros((cam.shape[0], cam.shape[1], 3), dtype=np.float32)
            heat[..., 0] = np.clip(1.5 - np.abs(4.0 * cam - 3.0), 0, 1)
            heat[..., 1] = np.clip(1.5 - np.abs(4.0 * cam - 2.0), 0, 1)
            heat[..., 2] = np.clip(1.5 - np.abs(4.0 * cam - 1.0), 0, 1)

            base_image = image.convert("RGB").resize(display_size, Image.Resampling.LANCZOS)
            base = np.asarray(base_image, dtype=np.float32) / 255.0
            alpha = (np.clip(cam, 0, 1) ** 0.8 * 0.48)[..., None]
            # Blend mostly where Grad-CAM activation is present.
            overlay = np.clip(base * (1.0 - alpha) + heat * alpha, 0, 1)
            output = Image.fromarray((overlay * 255).astype(np.uint8), mode="RGB")

            buffer = BytesIO()
            output.save(buffer, format="PNG", optimize=True)
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
        finally:
            handle.remove()
            self.model.zero_grad(set_to_none=True)


def load_model(path: str | Path = DEFAULT_MODEL_PATH) -> tuple[ModelBundle | None, str]:
    path = Path(path)
    if not path.exists():
        return None, f"No trained checkpoint found at {path}. The app is in image-quality-only mode."
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        checkpoint = torch.load(path, map_location=device, weights_only=False)
        classes = checkpoint.get("classes")
        if not isinstance(classes, list) or len(classes) < 2:
            raise ValueError("Checkpoint must contain a 'classes' list with at least two classes.")
        image_size = int(checkpoint.get("image_size", 224))
        model = build_model(len(classes), pretrained=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(device)
        bundle = ModelBundle(model, classes, image_size, device, checkpoint.get("metadata", {}))
        warning = "Research checkpoint loaded. Its outputs are not clinically validated."
        return bundle, warning
    except Exception as exc:
        return None, f"Checkpoint could not be loaded: {type(exc).__name__}: {exc}"
