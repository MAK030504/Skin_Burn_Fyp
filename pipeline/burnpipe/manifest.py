"""Build a reproducible image-level manifest from a folder or CSV of labels.

The trainer only reads this manifest. Swapping the public folder labels for a
clinician-reviewed folder or CSV is a config change, not a code change.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from burnpipe.config import REPO_ROOT, resolve_repo_path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
MANIFEST_FIELDS = [
    "image_path",
    "label",
    "source_label",
    "split",
    "width",
    "height",
    "content_md5",
    "source",
]


def build_manifest(config: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    classes = [str(label) for label in config["classes"]]
    rows, skipped = collect_rows(config, classes)
    if not rows:
        raise SystemExit("No usable images found for this config.")

    counts = {label: sum(row["label"] == label for row in rows) for label in classes}
    missing = [label for label, count in counts.items() if count == 0]
    if missing:
        raise SystemExit(
            "These classes have no images after filtering: " + ", ".join(missing)
        )

    seed = int(config.get("seed", 42))
    ratios = _split_ratios(config)
    assign_splits(rows, classes, ratios, seed)

    manifest_path = out_dir / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: (item["split"], item["label"], item["image_path"])):
            writer.writerow(row)

    skipped_path = out_dir / "skipped.csv"
    with skipped_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image_path", "source_label", "reason"])
        writer.writeheader()
        writer.writerows(skipped)

    split_counts: dict[str, dict[str, int]] = {}
    for split in ("train", "val", "test"):
        split_counts[split] = {
            label: sum(row["split"] == split and row["label"] == label for row in rows)
            for label in classes
        }

    meta = {
        "source_name": config["name"],
        "config_path": config.get("_config_path"),
        "label_note": str(config.get("label_note", "")).strip(),
        "classes": classes,
        "seed": seed,
        "split_ratios": {"train": ratios[0], "val": ratios[1], "test": ratios[2]},
        "n_images": len(rows),
        "n_skipped": len(skipped),
        "class_counts": counts,
        "split_counts": split_counts,
    }
    (out_dir / "manifest_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return manifest_path


def collect_rows(config: dict, classes: list[str]) -> tuple[list[dict], list[dict]]:
    source = config["source"]
    kind = source.get("kind", "folder")
    if kind == "folder":
        return collect_folder(config, classes)
    if kind == "csv":
        return collect_csv(config, classes)
    raise SystemExit(f"Unknown source.kind: {kind!r}. Use 'folder' or 'csv'.")


def collect_folder(config: dict, classes: list[str]) -> tuple[list[dict], list[dict]]:
    source = config["source"]
    root = resolve_repo_path(source["root"])
    if not root.is_dir():
        raise SystemExit(f"Label folder not found: {root}")

    label_map = source.get("label_map") or {label: label for label in classes}
    label_map = {str(key): str(value) for key, value in label_map.items()}
    unknown_targets = sorted({value for value in label_map.values() if value not in classes})
    if unknown_targets:
        raise SystemExit(
            "label_map points at classes that are not in config.classes: "
            + ", ".join(unknown_targets)
        )

    present = {path.name for path in root.iterdir() if path.is_dir()}
    missing_folders = [name for name in label_map if name not in present]
    if missing_folders:
        raise SystemExit(
            f"Missing label folders under {root}: " + ", ".join(missing_folders)
        )
    extra = sorted(present - set(label_map))
    if extra:
        print("Ignoring unlabeled folders: " + ", ".join(extra))

    min_side = int(config.get("image", {}).get("min_short_side", 0))
    rows: list[dict] = []
    skipped: list[dict] = []
    seen: dict[str, tuple[str, str]] = {}

    for source_label, label in label_map.items():
        folder = root / source_label
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            rel = _relative(path)
            try:
                digest, width, height = inspect_image(path)
            except (OSError, UnidentifiedImageError, ValueError) as exc:
                skipped.append(
                    {"image_path": rel, "source_label": source_label, "reason": f"unreadable: {exc}"}
                )
                continue
            if min(width, height) < min_side:
                skipped.append(
                    {
                        "image_path": rel,
                        "source_label": source_label,
                        "reason": f"short_side {min(width, height)} < {min_side}",
                    }
                )
                continue
            if digest in seen:
                previous_label, previous_path = seen[digest]
                reason = (
                    "duplicate_same_label"
                    if previous_label == label
                    else f"duplicate_label_conflict with {previous_path} ({previous_label})"
                )
                skipped.append({"image_path": rel, "source_label": source_label, "reason": reason})
                continue
            seen[digest] = (label, rel)
            rows.append(
                {
                    "image_path": rel,
                    "label": label,
                    "source_label": source_label,
                    "split": "",
                    "width": str(width),
                    "height": str(height),
                    "content_md5": digest,
                    "source": config["name"],
                }
            )
    return rows, skipped


def collect_csv(config: dict, classes: list[str]) -> tuple[list[dict], list[dict]]:
    source = config["source"]
    csv_path = resolve_repo_path(source["path"])
    if not csv_path.is_file():
        raise SystemExit(f"Label CSV not found: {csv_path}")

    min_side = int(config.get("image", {}).get("min_short_side", 0))
    rows: list[dict] = []
    skipped: list[dict] = []
    seen: dict[str, tuple[str, str]] = {}
    allowed = set(classes)

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise SystemExit(f"Label CSV has no header: {csv_path}")
        fields = {name.strip().lower(): name for name in reader.fieldnames}
        path_key = fields.get("image_path") or fields.get("path")
        label_key = fields.get("degree") or fields.get("label") or fields.get("class")
        if path_key is None or label_key is None:
            raise SystemExit("Label CSV needs columns image_path and degree (or label).")

        for record in reader:
            raw_path = (record.get(path_key) or "").strip()
            label = (record.get(label_key) or "").strip().lower()
            if not raw_path:
                continue
            image_path = _resolve_image(raw_path, csv_path.parent)
            rel = _relative(image_path)
            if label not in allowed:
                skipped.append(
                    {"image_path": rel, "source_label": label, "reason": "label not in config.classes"}
                )
                continue
            if not image_path.is_file():
                skipped.append({"image_path": rel, "source_label": label, "reason": "file missing"})
                continue
            try:
                digest, width, height = inspect_image(image_path)
            except (OSError, UnidentifiedImageError, ValueError) as exc:
                skipped.append(
                    {"image_path": rel, "source_label": label, "reason": f"unreadable: {exc}"}
                )
                continue
            if min(width, height) < min_side:
                skipped.append(
                    {
                        "image_path": rel,
                        "source_label": label,
                        "reason": f"short_side {min(width, height)} < {min_side}",
                    }
                )
                continue
            if digest in seen:
                previous_label, previous_path = seen[digest]
                reason = (
                    "duplicate_same_label"
                    if previous_label == label
                    else f"duplicate_label_conflict with {previous_path} ({previous_label})"
                )
                skipped.append({"image_path": rel, "source_label": label, "reason": reason})
                continue
            seen[digest] = (label, rel)
            rows.append(
                {
                    "image_path": rel,
                    "label": label,
                    "source_label": label,
                    "split": "",
                    "width": str(width),
                    "height": str(height),
                    "content_md5": digest,
                    "source": config["name"],
                }
            )
    return rows, skipped


def assign_splits(rows: list[dict], classes: list[str], ratios: tuple[float, float, float], seed: int) -> None:
    by_label: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_label[row["label"]].append(row)

    for index, label in enumerate(classes):
        items = by_label[label]
        rng = random.Random(seed + index)
        rng.shuffle(items)
        n_train, n_val, n_test = _split_counts(len(items), ratios)
        for row in items[:n_train]:
            row["split"] = "train"
        for row in items[n_train : n_train + n_val]:
            row["split"] = "val"
        for row in items[n_train + n_val :]:
            row["split"] = "test"
        if n_test != len(items) - n_train - n_val:
            raise RuntimeError(f"Split counts do not add up for class {label}")


def read_manifest(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def inspect_image(path: Path) -> tuple[str, int, int]:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    with Image.open(path) as image:
        image.load()
        width, height = image.size
    if width < 1 or height < 1:
        raise ValueError("empty image")
    return digest.hexdigest(), width, height


def _split_ratios(config: dict) -> tuple[float, float, float]:
    split = config.get("split") or {}
    ratios = (
        float(split.get("train", 0.70)),
        float(split.get("val", 0.15)),
        float(split.get("test", 0.15)),
    )
    if any(value <= 0 for value in ratios):
        raise SystemExit("train, val, and test split ratios must all be > 0.")
    total = sum(ratios)
    if abs(total - 1.0) > 0.02:
        raise SystemExit(f"Split ratios must sum to 1 (got {total:.3f}).")
    return ratios


def _split_counts(n: int, ratios: tuple[float, float, float]) -> tuple[int, int, int]:
    counts = [int(n * ratio) for ratio in ratios]
    while sum(counts) < n:
        counts[0] += 1
    while sum(counts) > n:
        for index in (2, 1, 0):
            if counts[index] > 0:
                counts[index] -= 1
                break
    if n >= 10:
        for index in (1, 2):
            if counts[index] == 0 and counts[0] > 1:
                counts[index] += 1
                counts[0] -= 1
    return counts[0], counts[1], counts[2]


def _resolve_image(raw_path: str, csv_dir: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    from_repo = (REPO_ROOT / path).resolve()
    if from_repo.exists():
        return from_repo
    return (csv_dir / path).resolve()


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()
