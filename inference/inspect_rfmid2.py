
from pathlib import Path
import pandas as pd

PRED_PATH = Path("results/rfmid2_test_predictions.csv")
TRUTH_PATH = Path(r"Test_set_2\RFMiD_2_Testing_labels.csv")
IMAGE_ROOT = Path("Test_set_2")


def normalize_id(value):
    if pd.isna(value):
        return None

    stem = Path(str(value).strip()).stem

    if stem.isdigit():
        return str(int(stem))

    return stem.lower()


pred = pd.read_csv(PRED_PATH)
truth = pd.read_csv(TRUTH_PATH, encoding="utf-8-sig")

pred["key"] = pred["ID"].map(normalize_id)
truth["key"] = truth["ID"].map(normalize_id)

truth["ODE"] = pd.to_numeric(truth["ODE"], errors="coerce")

# Index the actual images.
image_index = {}

for p in IMAGE_ROOT.rglob("*"):
    if p.is_file() and p.suffix.lower() in {
        ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"
    }:
        image_index.setdefault(normalize_id(p.stem), []).append(p)

pred_keys = set(pred["key"])
truth_keys = set(truth["key"])

unmatched_pred = pred[~pred["key"].isin(truth_keys)]
unmatched_truth = truth[~truth["key"].isin(pred_keys)]

print("=" * 60)
print("UNMATCHED PREDICTIONS")
print("=" * 60)

for _, row in unmatched_pred.iterrows():
    print(
        f"Image ID: {row['ID']} | "
        f"Prediction: {row['ODE']} | "
        f"Probability: {row['ODE_PROB']}"
    )

    for p in image_index.get(row["key"], []):
        print("  Image:", p)
        print("  File size:", p.stat().st_size, "bytes")


print("\n" + "=" * 60)
print("UNMATCHED GROUND-TRUTH LABELS")
print("=" * 60)

print(
    unmatched_truth[["ID", "ODE"]].to_string(index=False)
)

print(
    "\nUnmatched ground-truth ODE-positive count:",
    int((unmatched_truth["ODE"] == 1).sum())
)

print(
    "Total ODE positives in original test CSV:",
    int((truth["ODE"] == 1).sum())
)

print("\n" + "=" * 60)
print("DATASET INTEGRITY")
print("=" * 60)

print("Image files:", sum(map(len, image_index.values())))
print("Prediction rows:", len(pred))
print("Ground-truth rows:", len(truth))
print("Duplicate image IDs:", pred["key"].duplicated().sum())
print("Duplicate label IDs:", truth["key"].duplicated().sum())
print("Matched IDs:", len(pred_keys & truth_keys))
