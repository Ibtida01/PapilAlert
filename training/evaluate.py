from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import classification_report, confusion_matrix, f1_score, roc_auc_score
from torch.utils.data import DataLoader

from app.model import build_model
from training.train import FundusDataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a saved model on the held-out test split.")
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--data-root", default="data/images")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output-dir", default="runs/evaluation")
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    out = Path(args.output_dir).resolve(); out.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(args.split_manifest)
    if "split" not in frame.columns:
        raise SystemExit("Split manifest must contain a split column.")
    test_df = frame[frame["split"] == "test"].copy()
    if test_df.empty:
        raise SystemExit("No rows marked split=test.")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    classes = ckpt["classes"]
    class_to_idx = {c: i for i, c in enumerate(classes)}
    test_data = FundusDataset(test_df, Path(args.data_root).resolve(), class_to_idx, False, int(ckpt.get("image_size", 224)))
    loader = DataLoader(test_data, batch_size=args.batch_size, shuffle=False, num_workers=0)
    model = build_model(len(classes), pretrained=False).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    ys, preds, probs_all = [], [], []
    with torch.inference_mode():
        for images, labels in loader:
            logits = model(images.to(device))
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            preds.extend(probs.argmax(axis=1).tolist())
            ys.extend(labels.numpy().tolist())
            probs_all.extend(probs.tolist())

    report = classification_report(ys, preds, labels=list(range(len(classes))), target_names=classes, output_dict=True, zero_division=0)
    cm = confusion_matrix(ys, preds, labels=list(range(len(classes))))
    try:
        auc = float(roc_auc_score(ys, np.asarray(probs_all), multi_class="ovr", average="macro", labels=list(range(len(classes)))))
    except Exception:
        auc = None

    summary = {
        "n_test_images": len(ys),
        "classes": classes,
        "accuracy": float(np.mean(np.asarray(ys) == np.asarray(preds))),
        "macro_f1": float(f1_score(ys, preds, average="macro", zero_division=0)),
        "macro_ovr_auc": auc,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "split_type": ckpt.get("metadata", {}).get("split_type", "unknown"),
        "interpretation": ("Exploratory image-level holdout only; patient-level leakage cannot be ruled out. " if ckpt.get("metadata", {}).get("split_type") == "IMAGE_LEVEL_ONLY_NOT_PATIENT_INDEPENDENT" else "Exploratory patient-grouped internal holdout; external clinical generalization is unproven. ") + "Not clinical validation.",
    }
    (out / "evaluation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, interpolation="nearest")
    ax.set_title("Held-out test confusion matrix")
    fig.colorbar(im, ax=ax)
    ticks = np.arange(len(classes))
    ax.set_xticks(ticks, classes, rotation=35, ha="right")
    ax.set_yticks(ticks, classes)
    ax.set_ylabel("True label")
    ax.set_xlabel("Predicted label")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center")
    fig.tight_layout()
    fig.savefig(out / "confusion_matrix.png", dpi=180)
    plt.close(fig)
    print(json.dumps({k: v for k, v in summary.items() if k != "classification_report"}, indent=2))
    print("Saved detailed evaluation to", out)


if __name__ == "__main__":
    main()
