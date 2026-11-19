from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_label(folder: str) -> str:
    raw = folder.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "healthy": "normal",
        "control": "normal",
        "controls": "normal",
        "normal_control": "normal",
        "ppe": "pseudopapilledema",
        "pseudo_papilledema": "pseudopapilledema",
        "pseudopapilledema": "pseudopapilledema",
        "optic_neuropathies": "optic_neuropathy_mixed",
        "optic_neuropathy": "optic_neuropathy_mixed",
        "other_optic_disc_abnormality": "optic_neuropathy_mixed",
    }
    return aliases.get(raw, raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a de-duplicated image manifest from class folders.")
    parser.add_argument("--input", required=True, help="Root directory containing one folder per class")
    parser.add_argument("--output", default="data/manifest.csv")
    parser.add_argument("--patient-map", default=None, help="Optional CSV with columns filename,patient_id")
    parser.add_argument("--source-name", default="unspecified dataset")
    parser.add_argument("--license-status", choices=["verified", "unknown", "restricted"], default="unknown")
    parser.add_argument("--label-note", default="Labels follow source dataset folders; not independently adjudicated by PapilAlert.")
    args = parser.parse_args()

    input_root = Path(args.input).resolve()
    if not input_root.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_root}")

    patient_lookup: dict[str, str] = {}
    if args.patient_map:
        patient_df = pd.read_csv(args.patient_map)
        required = {"filename", "patient_id"}
        if not required.issubset(patient_df.columns):
            raise SystemExit("--patient-map must contain filename and patient_id columns.")
        patient_lookup = dict(zip(patient_df["filename"].astype(str), patient_df["patient_id"].astype(str)))

    rows = []
    seen_hashes: dict[str, str] = {}
    duplicates = []
    invalid = []

    for class_dir in sorted(p for p in input_root.iterdir() if p.is_dir()):
        label = normalize_label(class_dir.name)
        for path in sorted(class_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
                continue
            try:
                with Image.open(path) as im:
                    im.verify()
                digest = sha256(path)
            except Exception as exc:
                invalid.append({"path": str(path), "reason": str(exc)})
                continue
            if digest in seen_hashes:
                duplicates.append({"duplicate_path": str(path), "same_as": seen_hashes[digest], "sha256": digest})
                continue
            seen_hashes[digest] = str(path)
            rows.append({
                "image_path": str(path.relative_to(input_root)).replace("\\", "/"),
                "label": label,
                "patient_id": patient_lookup.get(path.name, ""),
                "sha256": digest,
                "source_name": args.source_name,
                "license_status": args.license_status,
            })

    if not rows:
        raise SystemExit("No readable images found. Expected <input>/<class_name>/<image-file>.")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    dup_path = out.with_name(out.stem + "_duplicates.csv")
    pd.DataFrame(duplicates, columns=["duplicate_path", "same_as", "sha256"]).to_csv(dup_path, index=False)
    invalid_path = out.with_name(out.stem + "_invalid.csv")
    pd.DataFrame(invalid, columns=["path", "reason"]).to_csv(invalid_path, index=False)

    summary = {
        "source_name": args.source_name,
        "license_status": args.license_status,
        "label_note": args.label_note,
        "images_kept": len(rows),
        "exact_duplicates_removed": len(duplicates),
        "unreadable_images": len(invalid),
        "patient_ids_present": sum(bool(r["patient_id"]) for r in rows),
        "class_counts": pd.Series([r["label"] for r in rows]).value_counts().to_dict(),
        "warning": "The script verifies file readability and exact duplicates only. It does not verify clinical labels, patient independence, licensing, or image provenance.",
    }
    out.with_name(out.stem + "_audit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if summary["patient_ids_present"] == 0:
        print("WARNING: no patient IDs found. Patient-independent validation is impossible. Training will require an explicit --allow-image-level-split flag.")


if __name__ == "__main__":
    main()
