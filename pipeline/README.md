# Classification pipeline

Image-level burn degree classifier. The first source is the Kaggle `last-databurn` folders (`1st degree`, `2nd degree`, `3nd degree`). Those names are public labels, not a clinician review.

The trainer does not care which folder the pictures came from. It reads a manifest of `image_path` + `degree`. When the reviewed labels are ready, point a new config at that folder or CSV and run the same command. Keep the two runs separate. They are not the same experiment.

## Train the current labeled set

From the repository root:

```powershell
python run_pipeline.py train --config pipeline/configs/classify_last_databurn.yaml
```

That builds a stratified 70/15/15 split (seed 42), fine-tunes ImageNet ResNet-18, keeps the checkpoint with the best validation macro-F1, and scores the test split once. Outputs land in `runs/classify/last_databurn_degree/<timestamp>/`:

| File | What it is |
|---|---|
| `manifest.csv` | Frozen split used for this run |
| `manifest_meta.json` | Class counts and the label warning |
| `skipped.csv` | Unreadable files and exact-byte duplicates |
| `best.pt` | Weights selected on validation macro-F1 |
| `history.csv` | Loss and validation scores per epoch |
| `metrics.json` | Test accuracy, macro-F1, per-class scores, confusion matrix |
| `config.snapshot.yaml` | Config copied into the run |

A short look at the split, without training:

```powershell
python run_pipeline.py prepare --config pipeline/configs/classify_last_databurn.yaml
```

Smoke test (a few steps, no test-set score):

```powershell
python run_pipeline.py train --config pipeline/configs/classify_last_databurn.yaml --max-steps 2
```

Score a finished run again, or classify one photo:

```powershell
python run_pipeline.py evaluate --run-dir runs/classify/last_databurn_degree/<timestamp>
python run_pipeline.py predict --run-dir runs/classify/last_databurn_degree/<timestamp> --image path\to\burn.jpg
```

This machine build uses CPU PyTorch. Eight epochs is the default. `--epochs 3` is enough to confirm the loop if you do not want a full baseline yet.

## Train again on better labels

Put reviewed images in class folders:

```text
datasets/gold/first/
datasets/gold/second/
datasets/gold/third/
```

or write `datasets/gold/labels.csv` with columns `image_path,degree`. Then:

```powershell
python run_pipeline.py train --config pipeline/configs/classify_gold.example.yaml
```

Edit that file first if the folder or CSV path differs. `degree` must be `first`, `second`, or `third`.

`efficientnet_b0` is the other backbone. Set `train.backbone` in the config.

## What this run is not

- Not a clinical accuracy number. Say which dataset and that the labels are folder names.
- Not segmentation, severity, or recovery. Those need masks and paired visits. Degree classification is the first module on the roadmap.
- Not mixed with BIP_US. That set uses superficial / deep dermal / full thickness, which is a different label scheme.
- Roboflow exports are not in this config. Several of them use unnamed classes `0/1/2` or add a fourth degree, so they are not the same three-class task.
