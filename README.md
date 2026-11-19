# PapilAlert — Optic-Disc Workflow Research Prototype

**Version:** 0.2.1  
**Status:** Working web prototype + training/evaluation pipeline. **No trained clinical model is bundled.**  
**Intended use:** Software demonstration and supervised research only. Not a medical device. Not for diagnosis, screening decisions, triage, or patient care.

## The honest scope

PapilAlert is a browser-based workflow demonstrator for fundus photographs. It currently provides:

1. Still-image upload and display.
2. Basic engineering checks for resolution, illumination, clipping, and a blur proxy.
3. A local MobileNetV3-Small ODE classifier when the compatible checkpoint is installed.
4. Abstention when a model score or top-two score margin falls below configured prototype thresholds.
5. A Grad-CAM overlay for the ODE output class, clearly labelled as coarse model attention rather than lesion localisation.
6. Dataset-level RFMiD 1.0 metrics and exploratory RFMiD 2.0 results, including limitations.
7. No third-party LLM call and no intentional server-side image persistence.
8. A responsive clinical-research interface with a dataset-metrics section and side-by-side original/Grad-CAM image evidence view. The upload endpoint returns a compact in-memory image preview data URL so the result panel does not depend on a temporary browser blob URL.

The project **does not** presently provide validated papilledema detection, intracranial-pressure estimation, clinical urgency prediction, or a diagnosis. A normal smartphone selfie camera cannot photograph the retina; a fundus camera or compatible optical attachment is required.

### Critical dataset correction

The frequently cited 1,369-image dataset associated with Ahn et al. (2019) has 779 normal images, 295 pseudopapilledema images, and 295 **mixed optic-neuropathy** images. The paper says the mixed group contains 177 ischemic optic neuropathy, 48 optic neuritis, 17 diabetic optic neuropathy, **22 papilledema**, and 31 retinal-disorder cases. It is therefore incorrect to describe all 295 abnormal images as papilledema. On 2 November 2026, the publisher issued an Editorial Expression of Concern because the authors had not responded to requests for access to the dataset. See `docs/DATASET_AUDIT.md`.

For these reasons, this repository does not download, redistribute, or bundle that dataset, does not ship weights trained on it, and does not present it as a clean papilledema benchmark. The training pipeline is intentionally generic and should be used only with image data whose provenance, labels, licensing, and patient-level identifiers have been checked.

## Current model evidence (important)

The current checkpoint's RFMiD 1.0 held-out test results were reproduced locally on all 640 test images: AUROC 0.96714, AUPRC 0.78492, sensitivity 70.59% (12/17), and specificity 99.84% (622/623) at threshold 0.50. The confusion matrix is TN=622, FP=1, FN=5, TP=12. There were only 17 ODE-positive test images, so sensitivity is imprecise.

An exploratory RFMiD 2.0 external evaluation matched 170 images including four ODE-positive cases. It produced AUROC 0.8810, AUPRC 0.1560, sensitivity 0% and specificity 100% at threshold 0.50. Four image IDs and four ground-truth IDs were unmatched. These data are too limited to establish external generalisation.

The interface's Grad-CAM overlay shows coarse image regions that contributed to the model's ODE-class score. It is not an ODE lesion mask, optic-disc segmentation, anatomical boundary, or proof of disease. It is not clinically validated.

## 1.1 Web interface update (0.2.1)

The page embeds its main stylesheet directly in `index.html`, uses a versioned JavaScript asset URL, and returns the original uploaded image as a compact preview data URL alongside Grad-CAM. These changes avoid an unstyled page when an external CSS request is stale or unavailable and avoid broken original-image previews caused by temporary browser object URLs. The stylesheet is also retained at `app/static/styles.css` for maintainability.

After replacing the `app/` folder, stop the old server, restart it, and hard-refresh the browser with `Ctrl+F5`. The app is still a local research prototype, not a production or clinical service.

## 1. Run the web prototype (Windows 11)

Use Python 3.11. From PowerShell in this folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>.

Alternatively run `run_windows.bat`. The first installation of PyTorch can take time. For GPU training, install the PyTorch build appropriate for your NVIDIA driver/CUDA from the official PyTorch installation selector before installing the remaining requirements.

## 2. Expected dataset layout

The trainer expects class folders under `data/images/` or another directory you specify:

```text
data/
  images/
    normal/
      image_001.jpg
    pseudopapilledema/
      image_002.jpg
    optic_neuropathy_mixed/
      image_003.jpg
  manifest.csv
```

The exact class names are dataset-specific. Do not relabel a mixed `optic_neuropathy` folder as `papilledema`.

Create the manifest:

```powershell
python -m training.prepare_dataset --input data/images --output data/manifest.csv --source-name "YOUR DATASET NAME" --license-status verified --label-note "Describe exactly how the labels were assigned."
```

`--license-status verified` is a declaration you make only after checking the original data terms. The script does not verify permissions. It removes exact duplicate files by SHA-256 hash, records unreadable files and writes an audit JSON. It cannot detect near-duplicates or verify clinical truth.

If your source has a patient mapping file with columns `filename,patient_id`, provide it:

```powershell
python -m training.prepare_dataset --input data/images --output data/manifest.csv --patient-map data/patient_map.csv --source-name "YOUR DATASET" --license-status verified
```

Keep a patient map securely and do not include direct identifiers. Use coded pseudonymous IDs only where permitted.

## 3. Train

The trainer defaults to **patient-grouped splitting**. It will stop if patient IDs are missing. This is intentional: two eyes or repeated visits from the same person must not leak across train and test.

```powershell
python -m training.train --manifest data/manifest.csv --data-root data/images --output-dir runs/opticwatch --epochs 15 --batch-size 16
```

If patient IDs are unavailable, you can run an explicitly exploratory image-level split:

```powershell
python -m training.train --manifest data/manifest.csv --data-root data/images --output-dir runs/image-level-demo --epochs 8 --batch-size 8 --allow-image-level-split
```

**Do not present image-level results as patient-independent performance.** The checkpoint records the split type and the app labels its outputs as uncalibrated research scores.

If ImageNet weights cannot be downloaded, the script falls back to random initialization. For a small medical dataset this is usually a poor choice; prefer a network-enabled environment and confirm the training log says pretrained weights were loaded.

## 4. Evaluate the held-out test data

```powershell
python -m training.evaluate --split-manifest runs/opticwatch/split_manifest.csv --data-root data/images --checkpoint runs/opticwatch/best_checkpoint.pt --output-dir runs/opticwatch/evaluation
```

It saves `evaluation.json` and `confusion_matrix.png`. Report per-class sensitivity/recall, specificity where relevant, precision, macro-F1, confusion matrix, AUC (when defined), confidence intervals, and the exact split strategy. Accuracy alone is insufficient.

## 5. Enable a model in the app

Only after you have an appropriately licensed dataset and have completed the research checks, copy the selected checkpoint to:

```text
models/papilalert_mobilenet_v3_small.pt
```

Restart the server. The app will attempt to load it. Class labels are taken from the checkpoint. The top score is an **uncalibrated model score**, not a clinical probability. With a compatible MobileNetV3-Small checkpoint, the result view also attempts to generate a Grad-CAM overlay for the `optic_disc_edema` output class.

## 6. Tests

```powershell
pytest -q
```

## 7. Project structure

```text
app/                  FastAPI API, image QC and model loading
app/static/           Responsive browser UI, metric dashboard and Grad-CAM evidence view
training/             Dataset manifest, trainer and evaluator
data/                 Empty data location + manifest template
models/               Empty model location; no trained weights bundled
docs/                 Data audit, model card, validation, pitch and demo guides
presentation/         Pitch deck
runs/                 Training outputs (not committed)
tests/                Automated smoke tests
```

## 8. Competition warning

The public Future Health Digital Innovation Challenge page says a working prototype and technical documentation (including assumptions and limitations) are due 20 November 2026. It lists ten statements across fertility, population health and wellbeing. The publicly rendered page fully exposes the Male Reproductive Health statement, which is not a direct match for PapilAlert. Before submitting, confirm that the challenge portal provides a population-health or wellbeing statement that explicitly permits an ophthalmic early-identification workflow. Do not claim confirmed challenge alignment until this has been checked.

## 9. References

See `docs/REFERENCES.md` and `docs/DATASET_AUDIT.md` for the primary research and challenge sources.
