from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.model_selection import StratifiedGroupKFold, train_test_split
from sklearn.utils.class_weight import compute_class_weight
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from app.model import IMAGENET_MEAN, IMAGENET_STD, build_model


class FundusDataset(Dataset):
    def __init__(self, frame: pd.DataFrame, data_root: Path, class_to_idx: dict[str, int], train: bool, image_size: int = 224):
        self.frame = frame.reset_index(drop=True)
        self.data_root = data_root
        self.class_to_idx = class_to_idx
        if train:
            self.transform = transforms.Compose([
                transforms.Resize((256, 256)),
                transforms.RandomResizedCrop(image_size, scale=(0.88, 1.0), ratio=(0.95, 1.05)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=7),
                transforms.ColorJitter(brightness=0.07, contrast=0.07, saturation=0.04, hue=0.01),
                transforms.ToTensor(),
                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ])

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, index: int):
        row = self.frame.iloc[index]
        path = self.data_root / str(row["image_path"])
        with Image.open(path) as im:
            image = im.convert("RGB")
        return self.transform(image), self.class_to_idx[str(row["label"])]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_splits(frame: pd.DataFrame, seed: int, allow_image_split: bool) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    y = frame["label"].astype(str).to_numpy()
    has_group = "patient_id" in frame.columns and frame["patient_id"].fillna("").astype(str).str.strip().ne("").all()

    if has_group:
        groups = frame["patient_id"].astype(str).to_numpy()
        outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
        rem_idx, test_idx = next(outer.split(np.zeros(len(frame)), y, groups))
        remaining = frame.iloc[rem_idx].reset_index(drop=True)
        y_rem = remaining["label"].astype(str).to_numpy()
        groups_rem = remaining["patient_id"].astype(str).to_numpy()
        inner = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=seed + 1)
        train_idx_local, val_idx_local = next(inner.split(np.zeros(len(remaining)), y_rem, groups_rem))
        train_df = remaining.iloc[train_idx_local].copy()
        val_df = remaining.iloc[val_idx_local].copy()
        test_df = frame.iloc[test_idx].copy()
        split_type = "patient_grouped_stratified"
    else:
        if not allow_image_split:
            raise ValueError(
                "Patient IDs are missing. This dataset cannot support patient-independent validation. "
                "For a clearly labelled exploratory image-level experiment only, pass --allow-image-level-split."
            )
        train_val, test_df = train_test_split(frame, test_size=0.15, random_state=seed, stratify=y)
        y_train_val = train_val["label"].astype(str).to_numpy()
        train_df, val_df = train_test_split(train_val, test_size=0.1765, random_state=seed + 1, stratify=y_train_val)
        split_type = "IMAGE_LEVEL_ONLY_NOT_PATIENT_INDEPENDENT"

    expected = set(frame["label"].astype(str).unique())
    for name, part in (("train", train_df), ("validation", val_df), ("test", test_df)):
        present = set(part["label"].astype(str).unique())
        if present != expected:
            raise ValueError(f"{name} split does not contain all classes. Present={sorted(present)}, expected={sorted(expected)}. Add more patients per class or revise the split plan.")
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True), split_type


def run_epoch(model, loader, criterion, optimizer, device, train: bool):
    model.train(train)
    total_loss = 0.0
    correct = 0
    total = 0
    all_y, all_pred = [], []
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        if train:
            optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(train):
            logits = model(images)
            loss = criterion(logits, labels)
            if train:
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 2.0)
                optimizer.step()
        preds = logits.argmax(dim=1)
        total_loss += float(loss.item()) * labels.size(0)
        correct += int((preds == labels).sum().item())
        total += int(labels.size(0))
        all_y.extend(labels.detach().cpu().tolist())
        all_pred.extend(preds.detach().cpu().tolist())
    from sklearn.metrics import f1_score
    return {
        "loss": total_loss / max(total, 1),
        "accuracy": correct / max(total, 1),
        "macro_f1": float(f1_score(all_y, all_pred, average="macro", zero_division=0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train an exploratory optic-disc classifier.")
    parser.add_argument("--manifest", default="data/manifest.csv")
    parser.add_argument("--data-root", default="data/images")
    parser.add_argument("--output-dir", default="runs/latest")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--allow-image-level-split", action="store_true")
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--patience", type=int, default=5)
    args = parser.parse_args()

    set_seed(args.seed)
    manifest_path = Path(args.manifest).resolve()
    data_root = Path(args.data_root).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")
    frame = pd.read_csv(manifest_path)
    required = {"image_path", "label"}
    if not required.issubset(frame.columns):
        raise SystemExit("Manifest needs image_path,label columns.")
    frame = frame.dropna(subset=["image_path", "label"]).copy()
    frame["label"] = frame["label"].astype(str)
    frame["image_path"] = frame["image_path"].astype(str)
    for rel in frame["image_path"]:
        if not (data_root / rel).is_file():
            raise SystemExit(f"Missing image: {data_root / rel}")
    counts = frame["label"].value_counts()
    if len(counts) < 2 or counts.min() < 5:
        raise SystemExit(f"Need at least 2 classes and 5 images per class for an exploratory run. Counts: {counts.to_dict()}")

    train_df, val_df, test_df, split_type = make_splits(frame, args.seed, args.allow_image_level_split)
    class_names = sorted(frame["label"].unique().tolist())
    class_to_idx = {name: i for i, name in enumerate(class_names)}
    train_df = train_df.copy(); train_df["split"] = "train"
    val_df = val_df.copy(); val_df["split"] = "validation"
    test_df = test_df.copy(); test_df["split"] = "test"
    split_frame = pd.concat([train_df, val_df, test_df], ignore_index=True)
    split_frame.to_csv(out_dir / "split_manifest.csv", index=False)

    train_data = FundusDataset(train_df, data_root, class_to_idx, True, args.image_size)
    val_data = FundusDataset(val_df, data_root, class_to_idx, False, args.image_size)
    train_loader = DataLoader(train_data, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, pin_memory=torch.cuda.is_available())
    val_loader = DataLoader(val_data, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, pin_memory=torch.cuda.is_available())

    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        model = build_model(len(class_names), pretrained=not args.no_pretrained)
    except Exception as exc:
        print(f"Could not load ImageNet weights ({exc}); falling back to randomly initialized MobileNetV3-Small.")
        model = build_model(len(class_names), pretrained=False)
    model.to(device)

    class_weights = compute_class_weight(class_weight="balanced", classes=np.array(class_names), y=train_df["label"].to_numpy())
    weights_tensor = torch.tensor(class_weights, dtype=torch.float32, device=device)
    criterion = nn.CrossEntropyLoss(weight=weights_tensor)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)

    best_f1 = -1.0
    best_epoch = 0
    stale = 0
    history = []
    best_path = out_dir / "best_checkpoint.pt"
    for epoch in range(1, args.epochs + 1):
        tr = run_epoch(model, train_loader, criterion, optimizer, device, True)
        va = run_epoch(model, val_loader, criterion, optimizer, device, False)
        scheduler.step(va["macro_f1"])
        record = {"epoch": epoch, "train": tr, "validation": va, "lr": optimizer.param_groups[0]["lr"]}
        history.append(record)
        print(f"Epoch {epoch:02d}/{args.epochs} | train loss {tr['loss']:.4f} F1 {tr['macro_f1']:.3f} | val loss {va['loss']:.4f} F1 {va['macro_f1']:.3f}")
        if va["macro_f1"] > best_f1:
            best_f1 = va["macro_f1"]
            best_epoch = epoch
            stale = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "classes": class_names,
                "image_size": args.image_size,
                "metadata": {
                    "model_name": "MobileNetV3-Small",
                    "model_version": "0.1-research",
                    "trained_at_utc": datetime.now(timezone.utc).isoformat(),
                    "split_type": split_type,
                    "best_validation_macro_f1": best_f1,
                    "best_epoch": best_epoch,
                    "seed": args.seed,
                    "warning": "Not clinically validated. Scores are uncalibrated. Do not use for diagnosis or care decisions.",
                    "data_provenance": "See dataset audit and model card; provenance and licensing must be independently verified.",
                },
                "abstain_score_threshold": 0.60,
                "abstain_margin_threshold": 0.15,
            }, best_path)
        else:
            stale += 1
        if stale >= args.patience:
            print(f"Early stopping after {epoch} epochs; best epoch was {best_epoch}.")
            break

    (out_dir / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    summary = {
        "split_type": split_type,
        "classes": class_names,
        "image_counts": {"train": len(train_df), "validation": len(val_df), "test": len(test_df)},
        "class_counts": frame["label"].value_counts().to_dict(),
        "best_validation_macro_f1": best_f1,
        "best_epoch": best_epoch,
        "checkpoint": str(best_path),
        "clinical_validity": "NOT ESTABLISHED",
        "warning": ("Image-level split: patient-independent performance cannot be established. " if split_type == "IMAGE_LEVEL_ONLY_NOT_PATIENT_INDEPENDENT" else "Patient-grouped internal split: external clinical generalization is still unproven. ") + "No clinical validity is implied.",
    }
    (out_dir / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("Next: run training/evaluate.py against this run's split_manifest.csv and best_checkpoint.pt")


if __name__ == "__main__":
    main()
