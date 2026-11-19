# PapilAlert
### Optic-Disc Edema Workflow Research Prototype

PapilAlert is a browser-based research prototype for reviewing retinal fundus photographs. It uses an image-classification model to estimate whether an image may show optic-disc edema (ODE), and provides a visual explanation of the regions that influenced the model's output.

**Project status:** Working web prototype and training/evaluation pipeline  
**Intended use:** Software demonstration and supervised research only  
**Clinical status:** Not clinically validated. Not intended for diagnosis, screening decisions, triage, or patient care.

---

## The problem

The optic disc is the point at the back of the eye where the optic nerve exits the retina. Swelling of this region is called optic-disc edema. It can be associated with several ocular or neurological conditions and may require further clinical assessment.

Reviewing retinal images requires appropriate imaging equipment and trained clinical interpretation. PapilAlert explores whether an image-classification model can help flag photographs for further review by an eye-care professional.

ODE is not synonymous with papilledema. Papilledema refers specifically to optic-disc swelling associated with raised intracranial pressure. PapilAlert does not determine the cause of swelling, diagnose papilledema, or estimate intracranial pressure.

## What has been built

The prototype combines a web interface, a FastAPI backend, image checks, a MobileNetV3-Small classifier, and a Grad-CAM explanation view.

A user can:

- Upload and view a retinal fundus photograph.
- Receive basic image-quality checks for resolution, illumination, clipping, and a blur proxy.
- Run a compatible MobileNetV3-Small checkpoint to obtain an ODE classification score.
- See an abstention state when the configured prototype score or top-two score-margin thresholds are not met.
- View the original image beside a Grad-CAM overlay for the ODE output class.
- Review the model's dataset-level evaluation metrics and known limitations.

Grad-CAM indicates image regions that contributed to the model's output. It is a coarse model-attention visualisation—not an ODE lesion mask, optic-disc segmentation, confirmed anatomical abnormality, or proof that ODE is present.

The prototype does not call a third-party large language model. Uploaded images are processed in memory; the application does not intentionally persist them as part of its normal inference workflow.

## How it works

1. **Image upload:** A retinal fundus photograph is submitted through the browser interface.
2. **Image checks:** The backend measures basic technical properties such as image dimensions, illumination, clipping, and a blur proxy.
3. **Preprocessing:** The image is converted and resized to the input format expected by the compatible model checkpoint.
4. **Classification:** MobileNetV3-Small produces scores for two classes: `no_ode` and `optic_disc_edema`.
5. **Abstention:** Configured prototype thresholds determine whether the output is shown as a model prediction or an abstention.
6. **Explanation:** Grad-CAM generates a coarse attention overlay for the ODE output class.

The model score is uncalibrated. It should not be interpreted as a patient's clinical probability or as a measure of disease severity.

## Model and evaluation

The classifier is based on **MobileNetV3-Small** and was trained as a two-class image classifier using the RFMiD 1.0 retinal fundus dataset. Evaluation uses a held-out test partition.

### RFMiD 1.0 held-out test results

| Metric | Result |
|---|---:|
| Test images | 640 |
| ODE-positive images | 17 |
| AUROC | 0.96714 |
| AUPRC | 0.78492 |
| Sensitivity at threshold 0.50 | 70.59% (12/17) |
| Specificity at threshold 0.50 | 99.84% (622/623) |

Confusion matrix (rows: ground truth; columns: prediction):

|  | Predicted no ODE | Predicted ODE |
|---|---:|---:|
| Actual no ODE | 622 | 1 |
| Actual ODE | 5 | 12 |

The 17 positive cases make the sensitivity estimate imprecise. These results describe performance on this dataset split only; they do not establish clinical performance or performance on other cameras, populations, or settings.

### Exploratory RFMiD 2.0 external evaluation

| Metric | Result |
|---|---:|
| Matched images | 170 |
| Matched ODE-positive images | 4 |
| AUROC | 0.8810 |
| AUPRC | 0.1560 |
| Sensitivity at threshold 0.50 | 0% (0/4) |
| Specificity at threshold 0.50 | 100% (166/166) |

Four prediction IDs and four ground-truth IDs were unmatched. All four unmatched ground-truth records were labelled no ODE; all four positive cases were among the matched images. The small number of positive cases means this external evaluation is exploratory and cannot establish reliable external generalisation.

The RFMiD 2.0 results also show that a high AUROC alone does not guarantee a useful operating threshold. At the 0.50 threshold, the model missed all four matched positive cases. Threshold changes must be selected using a separate validation set, not by tuning against the external test labels.

## Data and responsible use

- **Primary dataset:** RFMiD 1.0 retinal fundus images and associated labels.
- **External evaluation:** RFMiD 2.0 test images and labels, used for an exploratory comparison.
- **Data handling:** Dataset files are not included in this repository. Users should obtain them from their original sources and review the applicable terms before use or redistribution.
- **Privacy:** Use public, de-identified research images for demonstrations. Do not upload identifiable patient images to an unapproved deployment.
- **Label integrity:** ODE labels must not be treated as labels for papilledema or raised intracranial pressure.

## Limitations and safeguards

PapilAlert is an early-stage research prototype. It has not undergone prospective clinical validation, external multi-centre validation, reader studies, or regulatory review. Its image-quality checks are engineering checks, not clinically validated image-acceptance criteria. Its model scores are uncalibrated. Grad-CAM is not lesion localisation and may highlight features that are not clinically relevant.

A normal smartphone selfie camera cannot photograph the retina. Retinal imaging requires a fundus camera or a compatible optical attachment. The prototype should only be demonstrated with suitable retinal fundus photographs.

The application must not be used to make diagnosis, referral, treatment, screening, or urgency decisions. Any future clinical evaluation would require ophthalmologist oversight, appropriate datasets and patient-level data governance, prospective validation, device-specific testing, and relevant regulatory review.

## Run the web prototype

**Environment:** Python 3.11

From the project root on Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000> in a browser.

A compatible trained checkpoint is required for model inference. The source distribution does **not** bundle trained clinical model weights. To enable the classifier, place a compatible MobileNetV3-Small checkpoint at:

```text
models/papilalert_mobilenet_v3_small.pt
```

Then restart the application. Without a compatible checkpoint, the interface may still be used to inspect the workflow, but it cannot provide a trained-model prediction.

## Training and evaluation

The repository includes scripts for dataset manifest preparation, model training, and held-out evaluation. The pipeline records dataset and split information and supports patient-grouped splitting when patient identifiers are available. Patient-level separation should be used to reduce leakage between training and evaluation. Image-level splits are exploratory only and should not be presented as patient-independent performance.

See the training instructions and validation documentation in `docs/` before preparing a new dataset. Confirm image provenance, label definitions, licences, and permissions before use. Do not treat a mixed optic-neuropathy category as a papilledema class.

## Project structure

```text
app/                  FastAPI backend, image checks, model loading
app/static/           Browser interface, styles, metrics and image views
training/             Dataset preparation, training and evaluation scripts
data/                 Dataset location and manifest template
models/               Location for a separately supplied compatible checkpoint
docs/                 Model card, dataset audit, references and validation notes
presentation/         Project presentation
runs/                 Local training outputs (not committed)
tests/                Automated tests
```

## Further information

Project documentation is available in `docs/`, including the dataset audit, model card, validation protocol, technical explanation, references, and demonstration guide.

---

**PapilAlert is a research workflow prototype. Its outputs require expert review and must not be used as clinical advice.**
