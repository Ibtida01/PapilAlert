# Changelog

## 0.2.1 — 2026-11-19

- Refined the interface with a more polished responsive clinical-research layout, improved typography, spacing, navigation and image cards.
- Embedded the primary CSS in the HTML response so the page remains styled if the browser cannot load the separate stylesheet; added no-cache response headers and versioned JS asset URL.
- Fixed broken explanation-view images by returning a compact original-image data URL from the API instead of relying only on a temporary browser object URL.
- Added image-load fallbacks so missing original/overlay assets show a useful message instead of broken-image icons.
- Added explicit tests for embedded styling, static assets and original-image preview data URL.
- Preserved all research-performance caveats and the distinction between Grad-CAM model attention and lesion localisation.

## 0.2.0 — 2026-11-19

- Reworked the browser UI to use a restrained clinical-research visual style.
- Added RFMiD 1.0 held-out evaluation metrics and confusion matrix.
- Added transparent exploratory RFMiD 2.0 external results with small-sample and unmatched-record caveats.
- Added Grad-CAM for the `optic_disc_edema` model output and a side-by-side original/overlay evidence view.
- Explicitly labelled Grad-CAM as model attention, not lesion segmentation or proof of ODE.
- Added `/api/metrics` and updated `/api/status` metadata.
- Kept the app's non-diagnostic and human-review safeguards.

## 0.1.0

- Initial upload, image quality-check and optional classifier workflow.
