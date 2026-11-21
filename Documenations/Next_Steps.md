# Next steps

Working order from where the repo is now. The 14-week roadmap in `Documenations/FYP_Roadmap.pdf` still stands. This file is the order we will actually build in, and the definition of done for each step.

Roles from the scope document:

- **Mustafa Avais** — classification, segmentation, severity, VLM, integration.
- **Abdur Rehman** — dataset cleaning, the reviewed label set, recovery pairs, UI, evaluation write-up.

Either person can pick up a step. The name is the default owner, not a lock.

Git rule for every step: branch from `dev`, open a pull request back into `dev`. See `CONTRIBUTING.md`. Do not push to `main`.

---

## 1. Finish the public-label classification baseline

**Owner:** Mustafa. **Already started** on this machine (CPU, ResNet-18, Kaggle `last-databurn`).

The trainer is `python run_pipeline.py train --config pipeline/configs/classify_last_databurn.yaml`. It writes a frozen split and `metrics.json` under `runs/classify/last_databurn_degree/<timestamp>/`.

**Done when:**

- The run finishes and `metrics.json` has test accuracy, macro-F1, and the confusion matrix.
- The note in that folder still says these are folder labels, not a clinician review.
- The number is copied into a short results note: dataset name, split seed 42, 70/15/15, backbone, and the test scores. No sentence that calls it clinical accuracy.

## 2. Land the pipeline on `dev`

**Owner:** whoever ran step 1.

Commit only the pipeline code, `requirements.txt`, `run_pipeline.py`, and the docs. Leave `datasets/` and `runs/` untracked. Open a pull request into `dev`.

**Done when:** `dev` contains the trainer, and a teammate can repeat the command from `pipeline/README.md`.

## 3. Audit masks before training segmentation

**Owner:** Mustafa, with Abdur checking image quality.

Degree classification does not need a mask. Area and severity do. The Roboflow sets are not interchangeable:

- `pfa` and `skin-burn-ankzs` have named degrees, including a fourth degree, and polygon masks.
- `burn-segmentation` and `skin-burns` are large, but the class names are `0/1/2`.
- `last-databurn` has no masks. Do not invent them.

**Done when:** a short note picks one source for the first mask model, with a count of usable masks and a decision: binary burn / not-burn, or keep the dataset's own classes. Prefer a binary burn mask if the degree tags on the polygons are unreliable. Degree stays with the classifier from step 1.

## 4. Segmentation pipeline, same shape as classification

**Owner:** Mustafa.

New config, new manifest, train, Dice and IoU on a held-out split. Same rule as classification: the split is written into the run folder and the test split is scored once.

**Done when:** `best` weights plus a metrics file exist, and a single image can be turned into a mask and a pixel-area count.

## 5. Degree on the wound, then a severity score

**Owner:** Mustafa. Abdur checks that the score is explainable.

Run order at inference time:

1. Mask the burn.
2. Classify degree from that region (the step 1 model, until the reviewed labels replace it).
3. Severity is a written formula of degree plus mask area. Keep the formula in the repo so a panel can see it.

**Done when:** one command or function returns degree, mask area, and the severity score for a photo, and the formula is documented next to the code.

## 6. Retrain when the reviewed labels arrive

**Owner:** Abdur prepares the files. Mustafa reruns training.

This is a new experiment, not a continuation of step 1. Put images in `datasets/gold/first|second|third/` or a CSV with `image_path,degree`, then:

```powershell
python run_pipeline.py train --config pipeline/configs/classify_gold.example.yaml
```

**Done when:** the gold run has its own `metrics.json`, and the write-up quotes step 1 and step 6 as separate results. The 50-image labeling folder stays unused until `degree` is filled in.

## 7. Recovery only with the same wound twice

**Owner:** Abdur.

Most public sets are single photos. Do not report a recovery score on them. Recovery starts when Nowshera (or any other approved source) has two dates for one wound, or when we deliberately build pairs and say they are constructed.

**Done when:** a comparison takes two masks of the same wound and reports area change, and the evaluation says whether the pairs are real visits or constructed.

## 8. Report from the structured fields

**Owner:** Mustafa.

The draft text is allowed to use only the fields we computed: degree, area, severity, and recovery trend if step 7 ran. A clinician still reviews it. No free-form diagnosis.

**Done when:** a sample image produces a filled field list and a short paragraph that matches those fields.

## 9. A small interface over the same functions

**Owner:** Abdur for the screens, Mustafa for the API.

Upload one image, show mask, degree, area, severity. If a previous visit is stored, show the step 7 comparison. Keep it a research prototype.

**Done when:** a second person can run it locally and complete that path without editing code.

## 10. Write the results the way the viva will ask

**Owner:** Abdur, checked by Mustafa.

For every number: dataset, task, split, and limitation in the same paragraph. Component metrics first (macro-F1, Dice/IoU), then the joined pipeline. State what is out of scope: hospital deployment, EMR, regulatory validation, outcome claims.

**Done when:** the results section can be read out loud without adding a claim the repo cannot support.

---

## Not in this sequence

- Mixing BIP_US graft-style labels into the three degree classes.
- Training on Hugging Face HSR synthetic renders as if they were patients.
- A recovery accuracy number on unpaired images.
- Replacing the doctor.
