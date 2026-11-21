"""Train, evaluate, and run one image through a saved degree classifier."""

from __future__ import annotations

import csv
import json
import random
import shutil
from datetime import datetime
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image

from burnpipe.config import REPO_ROOT, load_config
from burnpipe.data import build_transforms, class_weights, make_loader
from burnpipe.manifest import build_manifest, read_manifest
from burnpipe.metrics import classification_metrics, format_metrics
from burnpipe.model import build_model


def prepare(config_path: str, out_dir: str | None) -> Path:
    config = load_config(config_path)
    destination = Path(out_dir) if out_dir else _preview_dir(config)
    if not destination.is_absolute():
        destination = (REPO_ROOT / destination).resolve()
    manifest = build_manifest(config, destination)
    _print_manifest_summary(destination)
    return manifest


def train(config_path: str, epochs: int | None, max_steps: int | None, run_dir: str | None) -> Path:
    config = load_config(config_path)
    destination = Path(run_dir) if run_dir else _new_run_dir(config)
    if not destination.is_absolute():
        destination = (REPO_ROOT / destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    log = _Logger(destination / "train.log")

    shutil.copyfile(config["_config_path"], destination / "config.snapshot.yaml")
    manifest_path = build_manifest(config, destination)
    rows = read_manifest(manifest_path)
    classes = [str(label) for label in config["classes"]]
    _print_manifest_summary(destination, log)

    note = str(config.get("label_note", "")).strip()
    if note:
        log(note)

    train_rows = [row for row in rows if row["split"] == "train"]
    val_rows = [row for row in rows if row["split"] == "val"]
    test_rows = [row for row in rows if row["split"] == "test"]
    for split_name, split_rows in ("train", train_rows), ("val", val_rows), ("test", test_rows):
        if not split_rows:
            raise SystemExit(f"{split_name} split is empty. Check the manifest.")

    train_cfg = config["train"]
    image_size = int(config["image"]["size"])
    batch_size = int(train_cfg.get("batch_size", 32))
    num_workers = int(train_cfg.get("num_workers", 0))
    epoch_count = int(epochs if epochs is not None else train_cfg.get("epochs", 8))
    patience = int(train_cfg.get("patience", 3))
    seed = int(config.get("seed", 42))
    _set_seed(seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log(f"device={device}  backbone={train_cfg.get('backbone', 'resnet18')}  epochs={epoch_count}")
    if device.type == "cpu":
        torch.set_num_threads(min(8, os_cpu_count()))

    model = build_model(
        str(train_cfg.get("backbone", "resnet18")),
        num_classes=len(classes),
        pretrained=bool(train_cfg.get("pretrained", True)),
    ).to(device)
    weights = class_weights(train_rows, classes).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(train_cfg.get("lr", 3e-4)),
        weight_decay=float(train_cfg.get("weight_decay", 1e-4)),
    )

    train_loader = make_loader(train_rows, classes, image_size, batch_size, True, num_workers, seed)
    val_loader = make_loader(val_rows, classes, image_size, batch_size, False, num_workers, seed)

    history_path = destination / "history.csv"
    with history_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["epoch", "train_loss", "val_loss", "val_accuracy", "val_macro_f1"],
        )
        writer.writeheader()

        best_f1 = -1.0
        stale = 0
        for epoch in range(1, epoch_count + 1):
            train_loss = _train_one_epoch(
                model, train_loader, criterion, optimizer, device, max_steps, log, epoch
            )
            val_metrics = _run_split(model, val_loader, criterion, device, classes)
            val_metrics["split"] = "val"
            log(
                f"epoch {epoch}/{epoch_count}  train_loss={train_loss:.4f}  "
                f"val_loss={val_metrics['loss']:.4f}  val_acc={val_metrics['accuracy']:.4f}  "
                f"val_macro_f1={val_metrics['macro_f1']:.4f}"
            )
            writer.writerow(
                {
                    "epoch": epoch,
                    "train_loss": f"{train_loss:.6f}",
                    "val_loss": f"{val_metrics['loss']:.6f}",
                    "val_accuracy": f"{val_metrics['accuracy']:.6f}",
                    "val_macro_f1": f"{val_metrics['macro_f1']:.6f}",
                }
            )
            handle.flush()
            _save_checkpoint(destination / "last.pt", model, config, classes, image_size, epoch)
            if val_metrics["macro_f1"] > best_f1:
                best_f1 = val_metrics["macro_f1"]
                stale = 0
                _save_checkpoint(destination / "best.pt", model, config, classes, image_size, epoch)
                log(f"saved best.pt  val_macro_f1={best_f1:.4f}")
            else:
                stale += 1
                if stale >= patience:
                    log(f"early stop after {patience} epochs without val macro-F1 improvement")
                    break
            if max_steps is not None:
                log("max-steps is set, so this run stops after one short epoch")
                break

    if max_steps is None:
        _load_weights(model, destination / "best.pt", device)
        test_loader = make_loader(test_rows, classes, image_size, batch_size, False, num_workers, seed)
        test_metrics = _run_split(model, test_loader, criterion, device, classes)
        test_metrics["split"] = "test"
        test_metrics["checkpoint"] = "best.pt"
        _write_metrics(destination / "metrics.json", test_metrics)
        log("test split (best.pt, not used for model selection)")
        log(format_metrics(test_metrics))
    else:
        log("skipped the test split because this was a smoke run")

    _write_latest_pointer(config, destination)
    log(f"run directory: {destination}")
    return destination


def evaluate(run_dir: str) -> dict:
    destination = _existing_run(run_dir)
    checkpoint = torch.load(destination / "best.pt", map_location="cpu", weights_only=False)
    classes = checkpoint["classes"]
    rows = [row for row in read_manifest(destination / "manifest.csv") if row["split"] == "test"]
    if not rows:
        raise SystemExit(f"No test rows in {destination / 'manifest.csv'}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(checkpoint["backbone"], len(classes), pretrained=False).to(device)
    model.load_state_dict(checkpoint["model_state"])
    loader = make_loader(
        rows,
        classes,
        int(checkpoint["image_size"]),
        batch_size=32,
        train=False,
        num_workers=0,
        seed=0,
    )
    metrics = _run_split(model, loader, nn.CrossEntropyLoss(), device, classes)
    metrics["split"] = "test"
    metrics["checkpoint"] = "best.pt"
    _write_metrics(destination / "metrics.json", metrics)
    print(format_metrics(metrics))
    return metrics


def predict(run_dir: str, image_path: str) -> dict:
    destination = _existing_run(run_dir)
    checkpoint = torch.load(destination / "best.pt", map_location="cpu", weights_only=False)
    classes = checkpoint["classes"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(checkpoint["backbone"], len(classes), pretrained=False).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    path = Path(image_path)
    if not path.is_file():
        candidate = REPO_ROOT / image_path
        if candidate.is_file():
            path = candidate
        else:
            raise SystemExit(f"Image not found: {image_path}")

    transform = build_transforms(int(checkpoint["image_size"]), train=False)
    with Image.open(path) as image:
        tensor = transform(image.convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        probabilities = torch.softmax(model(tensor), dim=1)[0].cpu()
    scores = {label: float(probabilities[index]) for index, label in enumerate(classes)}
    chosen = max(scores, key=scores.get)
    print(f"{chosen}  ({scores[chosen]:.3f})")
    for label, score in scores.items():
        print(f"  {label}: {score:.3f}")
    return {"label": chosen, "probabilities": scores, "image": str(path)}


def _train_one_epoch(model, loader, criterion, optimizer, device, max_steps, log, epoch) -> float:
    model.train()
    total_loss = 0.0
    total_n = 0
    for step, (images, targets) in enumerate(loader, start=1):
        images = images.to(device)
        targets = targets.to(device)
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(images), targets)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * targets.size(0)
        total_n += targets.size(0)
        if step == 1 or step % 20 == 0:
            log(f"  epoch {epoch} step {step}/{len(loader)}  loss={loss.item():.4f}")
        if max_steps is not None and step >= max_steps:
            break
    return total_loss / max(total_n, 1)


@torch.no_grad()
def _run_split(model, loader, criterion, device, classes) -> dict:
    model.eval()
    total_loss = 0.0
    truths: list[int] = []
    predictions: list[int] = []
    for images, targets in loader:
        images = images.to(device)
        targets = targets.to(device)
        logits = model(images)
        loss = criterion(logits, targets)
        total_loss += loss.item() * targets.size(0)
        truths.extend(targets.cpu().tolist())
        predictions.extend(logits.argmax(dim=1).cpu().tolist())
    metrics = classification_metrics(truths, predictions, classes)
    metrics["loss"] = total_loss / max(len(truths), 1)
    return metrics


def _save_checkpoint(path: Path, model, config: dict, classes: list[str], image_size: int, epoch: int) -> None:
    torch.save(
        {
            "model_state": model.state_dict(),
            "classes": classes,
            "backbone": str(config["train"].get("backbone", "resnet18")),
            "image_size": image_size,
            "epoch": epoch,
            "source_name": config["name"],
            "label_note": str(config.get("label_note", "")).strip(),
        },
        path,
    )


def _load_weights(model, path: Path, device) -> None:
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state"])


def _write_metrics(path: Path, metrics: dict) -> None:
    payload = json.loads(json.dumps(metrics))
    for key in ("accuracy", "macro_f1", "loss"):
        if key in payload:
            payload[key] = round(float(payload[key]), 6)
    for row in payload.get("per_class", {}).values():
        for key in ("precision", "recall", "f1"):
            row[key] = round(float(row[key]), 6)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _print_manifest_summary(out_dir: Path, log=print) -> None:
    meta = json.loads((out_dir / "manifest_meta.json").read_text(encoding="utf-8"))
    log(
        f"manifest: {meta['n_images']} images, {meta['n_skipped']} skipped  "
        f"classes={meta['class_counts']}"
    )
    for split, counts in meta["split_counts"].items():
        log(f"  {split}: {counts}")


def _new_run_dir(config: dict) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "runs" / "classify" / config["name"] / stamp


def _preview_dir(config: dict) -> Path:
    return REPO_ROOT / "runs" / "classify" / config["name"] / "preview"


def _write_latest_pointer(config: dict, run_dir: Path) -> None:
    pointer = REPO_ROOT / "runs" / "classify" / config["name"] / "LATEST.txt"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(run_dir), encoding="utf-8")


def _existing_run(run_dir: str) -> Path:
    path = Path(run_dir)
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    if not (path / "best.pt").is_file():
        raise SystemExit(f"No best.pt in {path}")
    return path


def _set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def os_cpu_count() -> int:
    import os

    return os.cpu_count() or 4


class _Logger:
    def __init__(self, path: Path) -> None:
        self.handle = path.open("a", encoding="utf-8")

    def __call__(self, message: str) -> None:
        print(message, flush=True)
        self.handle.write(message + "\n")
        self.handle.flush()
