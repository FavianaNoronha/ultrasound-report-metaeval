# EchoCheck research demo

A local web interface for two research workflows:

1. Upload one breast, thyroid, or fetal-head ultrasound image to generate an experimental report draft with the repository's local MedGemma 1.5 4B MLX-VLM conversion.
2. Compare an existing or generated candidate report with a reference report using the Step 46 rule/extractor preview.

The current scorer requires a reference report. It does not score image-report agreement, run the holistic Gemma judge, or apply the tuned test threshold. It reports discrepancies found by the number checker and extractor v5, with the Step 46 severity penalties. A score of 1.0 means only that these enabled checks did not find a discrepancy; it is not evidence of clinical correctness.

## Run locally

From the repository root:

```sh
.venv/bin/python usmeta/demo/app.py
```

Then open <http://127.0.0.1:8765>.

Image-to-report generation requires the local MLX-VLM environment and converted model already used by `usmeta.medgemma`:

- Python executable: `~/venvs/mlx312/bin/python`
- Model directory: `~/.cache/usmeta/medgemma-1.5-4b-it-4bit`

To point the server at another Python 3.12 environment, set `USMETA_MLX_VLM_PY` before launch. The extractor/scorer uses the repository `.venv` and its local Qwen MLX model. The first run can take several minutes while the models load.

The server binds to `127.0.0.1` by default. Uploaded images are held in a temporary directory and removed after generation. Report text is not stored by the UI; the existing extractor writes its model response cache under `~/.cache/usmeta/demo_extractor_v5.jsonl`.

## Scope and safety

This is a research demonstration, not a medical device, diagnostic service, or clinically validated score. Do not use it for patient care or enter identifiable patient information. The image model sees one frame, not a complete ultrasound examination. Image-only scoring is not implemented: the scorer needs a reference report, and even then uses a limited research rule preview.

## How the larger project should grow

Keep one shared scoring engine and define a versioned fact schema for each organ. The engine owns extraction, normalization, reference comparison, severity penalties, and explanations. The breast schema carries fields such as BI-RADS, side, shape, margin, and size; thyroid carries TI-RADS, composition, foci, and size; fetal head carries scan plane and head circumference. Organ-specific fields do not require three separate scoring products.

Suggested order:

1. Finish Step 46 and use its held-out results to decide which scorer checks are reliable enough to expose.
2. Connect the demo to the complete frozen UScore pipeline, with confidence/abstention and visible field-level evidence.
3. Have clinicians review each schema and error-severity mapping; test by organ and dataset.
4. Add image-grounded report checking only after a separate validation set and reference annotations exist.
5. Consider fine-tuning a small extractor only if measured extraction failures justify it and independently labeled training data are available. It is not a prerequisite for the scorer or the first demo.

The research contribution remains the controlled scorer evaluation. The web interface is a demonstration layer around that work.
