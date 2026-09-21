"""Retry only datasets that previously failed."""
from __future__ import annotations

import os
import shutil
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def retry_kaggle_human_burns() -> None:
    import kagglehub

    slug = "brendarangelolvera/human-skin-burns"
    dest = ROOT / "kaggle" / "human-skin-burns"
    print(f"\n=== Kaggle: {slug} ===", flush=True)
    path = Path(kagglehub.dataset_download(slug))
    print(f"cache: {path}", flush=True)
    copy_tree(path, dest)
    print(f"OK -> {dest}", flush=True)


def retry_mass_human_burns() -> None:
    from huggingface_hub import hf_hub_download, snapshot_download

    repo = "HLSS/MassHumanBurns"
    dest = ROOT / "huggingface" / "MassHumanBurns"
    dest.mkdir(parents=True, exist_ok=True)
    print(f"\n=== HuggingFace: {repo} ===", flush=True)
    print("Warning: images.7z is ~23 GB; use hf_hub_download (curl -C - corrupts on HF CDN).", flush=True)

    snapshot_download(
        repo_id=repo,
        repo_type="dataset",
        local_dir=str(dest),
        allow_patterns=["*.md", "*.json", "*.npy", ".gitattributes", "burn_masks.7z", "full_masks.7z"],
    )
    images = dest / "images.7z"
    expected = 23_201_076_325
    path = hf_hub_download(
        repo_id=repo,
        filename="images.7z",
        repo_type="dataset",
        local_dir=str(dest),
    )
    size = Path(path).stat().st_size
    if size != expected:
        raise RuntimeError(f"images.7z size {size} != expected {expected}")
    size_gb = images.stat().st_size / 1e9
    print(f"OK images.7z -> {images} ({size_gb:.2f} GB)", flush=True)


def retry_roboflow() -> None:
    from roboflow import Roboflow

    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        print("\n=== Roboflow: SKIP (ROBOFLOW_API_KEY not set) ===", flush=True)
        return

    projects = [
        ("aibuildersclub", "skin-burns-4yoo2", ROOT / "roboflow" / "skin-burns"),
        ("pelukbakar", "pb-tkjgx", ROOT / "roboflow" / "pb"),
        ("burndegree", "pfa-hfzdi", ROOT / "roboflow" / "pfa"),
    ]
    rf = Roboflow(api_key=api_key)
    for workspace, project, dest in projects:
        name = f"{workspace}/{project}"
        print(f"\n=== Roboflow: {name} ===", flush=True)
        dest.mkdir(parents=True, exist_ok=True)
        proj = rf.workspace(workspace).project(project)
        versions = proj.versions()
        version_num = versions[0].version if versions else 1
        ver = proj.version(version_num)
        dataset = ver.download("yolov8", location=str(dest))
        loc = getattr(dataset, "location", dest)
        print(f"OK -> {loc}", flush=True)


def main() -> None:
    tasks = [
        ("human-skin-burns", retry_kaggle_human_burns),
        ("MassHumanBurns", retry_mass_human_burns),
        ("roboflow", retry_roboflow),
    ]
    for name, fn in tasks:
        try:
            fn()
        except Exception as e:
            print(f"\nFAIL [{name}]: {e}", flush=True)
            traceback.print_exc()


if __name__ == "__main__":
    main()
