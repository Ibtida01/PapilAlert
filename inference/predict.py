
import argparse
import sys
from pathlib import Path

import torch
import pandas as pd
from PIL import Image
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.model import build_model, inference_transform


def load_checkpoint(checkpoint_path, device):
    checkpoint = torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=False
    )

    classes = checkpoint["classes"]
    model_name = checkpoint.get("model_name", "mobilenet_v3_small")

    model = build_model(
        num_classes=len(classes),
        pretrained=False
    )

    state_dict = checkpoint.get("model_state_dict", checkpoint.get("state_dict"))

    if state_dict is None:
        raise ValueError("No model state dictionary found in checkpoint.")

    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    print("Model:", model_name)
    print("Classes:", classes)

    return model, classes


def predict_image(image_path, model, transform, device, classes):
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(image)
        probabilities = torch.softmax(logits, dim=1)[0]

    ode_index = classes.index("optic_disc_edema")

    ode_probability = probabilities[ode_index].item()
    predicted_index = probabilities.argmax().item()

    return int(classes[predicted_index] == "optic_disc_edema"), ode_probability


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--folder", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", default="predictions.csv")
    parser.add_argument("--threshold", type=float, default=0.5)

    args = parser.parse_args()

    folder = Path(args.folder)
    checkpoint_path = Path(args.checkpoint)

    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")

    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Device:", device)

    model, classes = load_checkpoint(checkpoint_path, device)
    transform = inference_transform()

    image_paths = sorted(
        p for p in folder.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {
            ".jpg", ".jpeg", ".png", ".bmp",
            ".tif", ".tiff", ".webp"
        }
    )

    if not image_paths:
        raise RuntimeError("No JPG/JPEG/PNG images found in the folder.")

    results = []

    for image_path in tqdm(image_paths, desc="Predicting"):
        try:
            predicted, probability = predict_image(
                image_path,
                model,
                transform,
                device,
                classes
            )

            # Apply requested threshold to ODE probability.
            predicted = int(probability >= args.threshold)

            results.append({
                "ID": image_path.stem,
                "ODE": predicted,
                "ODE_PROB": float(probability)
            })

        except Exception as e:
            print(f"\nError processing {image_path.name}: {e}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
    results,
    columns=["ID", "ODE", "ODE_PROB"]
)
    df.to_csv(output_path, index=False)
    if not df.empty:
        print("\nODE probability statistics:")
        print(df["ODE_PROB"].describe(
            percentiles=[0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
        ))

        print("\nMaximum ODE probability:", df["ODE_PROB"].max())
        print("Minimum ODE probability:", df["ODE_PROB"].min())

        print(
            "Images above threshold:",
            (df["ODE_PROB"] >= args.threshold).sum()
        )

        print(
            "Images above 0.1:",
            (df["ODE_PROB"] >= 0.1).sum()
        )

        print(
            "Images above 0.2:",
            (df["ODE_PROB"] >= 0.2).sum()
        )

        print(
            "Images above 0.3:",
            (df["ODE_PROB"] >= 0.3).sum()
        )

    print("\nInference completed.")
    print("Images predicted:", len(df))
    print("ODE predicted:", int(df["ODE"].sum()))
    print("No ODE predicted:", int((df["ODE"] == 0).sum()))
    print("CSV saved:", output_path.resolve())


if __name__ == "__main__":
    main()
