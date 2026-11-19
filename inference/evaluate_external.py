
import argparse
from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
)


def normalize_id(value):
    if pd.isna(value):
        return None

    value = str(value).strip()
    stem = Path(value).stem

    if stem.endswith(".0"):
        stem = stem[:-2]

    if stem.isdigit():
        return str(int(stem))

    return stem.lower()


def read_labels(path):
    for encoding in ["utf-8-sig", "cp1252", "latin1"]:
        try:
            df = pd.read_csv(path, encoding=encoding)
            print("CSV encoding:", encoding)
            return df
        except UnicodeDecodeError:
            continue

    raise ValueError("Could not decode ground-truth CSV.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred", required=True)
    parser.add_argument("--truth", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    # Load files
    pred = pd.read_csv(args.pred)
    truth = read_labels(args.truth)

    # Clean column names
    pred.columns = (
        pred.columns.astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    truth.columns = (
        truth.columns.astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    print("\nPrediction columns:", list(pred.columns))
    print("Ground-truth columns:", list(truth.columns))

    # Validate required columns
    if not {"ID", "ODE_PROB"}.issubset(pred.columns):
        raise ValueError(
            "Prediction CSV must contain ID and ODE_PROB."
        )

    if "ID" not in truth.columns or "ODE" not in truth.columns:
        raise ValueError(
            "Ground-truth CSV must contain ID and ODE."
        )

    # Explicitly rename to avoid Pandas merge suffix ambiguity
    pred = pred.rename(columns={"ODE": "ODE_PRED"})
    truth = truth.rename(columns={"ODE": "ODE_TRUE"})

    # Normalize image IDs
    pred["key"] = pred["ID"].map(normalize_id)
    truth["key"] = truth["ID"].map(normalize_id)

    # Convert values
    pred["ODE_PROB"] = pd.to_numeric(
        pred["ODE_PROB"], errors="coerce"
    )

    truth["ODE_TRUE"] = pd.to_numeric(
        truth["ODE_TRUE"], errors="coerce"
    )

    pred = pred.dropna(
        subset=["key", "ODE_PROB"]
    )

    truth = truth.dropna(
        subset=["key", "ODE_TRUE"]
    )

    # Verify labels are binary
    if not set(truth["ODE_TRUE"].unique()).issubset({0, 1}):
        raise ValueError("Ground-truth ODE contains non-binary labels.")

    # Ensure unique IDs
    if pred["key"].duplicated().any():
        raise ValueError("Duplicate prediction IDs found.")

    if truth["key"].duplicated().any():
        raise ValueError("Duplicate ground-truth IDs found.")

    # Merge using normalized image IDs
    merged = pred.merge(
        truth[["key", "ODE_TRUE"]],
        on="key",
        how="inner",
        validate="one_to_one"
    )

    print("\nMerged columns:", list(merged.columns))
    print("\nMatched images:", len(merged))
    print("Unmatched predictions:", len(pred) - len(merged))
    print("Unmatched labels:", len(truth) - len(merged))

    if merged.empty:
        raise ValueError("No matching image IDs found.")

    # Ground truth and continuous model scores
    y_true = merged["ODE_TRUE"].astype(int)
    scores = merged["ODE_PROB"].astype(float)

    # Recalculate predictions from probabilities
    y_pred = (scores >= args.threshold).astype(int)

    if "ODE_PRED" in merged.columns:
        saved_predictions = merged["ODE_PRED"].astype(int)
        disagreements = int((saved_predictions != y_pred).sum())
        print("Saved prediction / threshold disagreements:", disagreements)

    # Metrics
    print("\nGround-truth distribution:")
    print(y_true.value_counts())

    print("\nProbability statistics:")
    print(scores.describe(
        percentiles=[0.5, 0.9, 0.95, 0.99]
    ))

    print("\nThreshold:", args.threshold)
    print("Predicted ODE-positive:", int(y_pred.sum()))

    print("\nConfusion matrix [rows=true, cols=pred]:")
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    print(cm)

    print("\nClassification report:")
    print(
        classification_report(
            y_true,
            y_pred,
            labels=[0, 1],
            target_names=["no_ode", "optic_disc_edema"],
            zero_division=0
        )
    )

    if y_true.nunique() == 2:
        print("AUROC:", roc_auc_score(y_true, scores))
        print("AUPRC:", average_precision_score(y_true, scores))

        tn, fp, fn, tp = cm.ravel()

        sensitivity = tp / (tp + fn) if tp + fn else 0
        specificity = tn / (tn + fp) if tn + fp else 0

        print("Sensitivity:", sensitivity)
        print("Specificity:", specificity)

    else:
        print("AUROC/AUPRC unavailable: only one ground-truth class.")


if __name__ == "__main__":
    main()
