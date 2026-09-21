"""Download publicly available skin-burn datasets into this folder."""
from __future__ import annotations

import shutil
import traceback
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS: list[tuple[str, str, str]] = []


def log(msg: str) -> None:
    print(msg, flush=True)


def copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        for item in src.iterdir():
            target = dst / item.name
            if item.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
    else:
        shutil.copy2(src, dst / src.name)


def unzip_if_needed(zip_path: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)


def download_kaggle() -> None:
    try:
        import kagglehub
    except Exception as e:
        RESULTS.append(("kagglehub", "FAIL", str(e)))
        return

    datasets = [
        ("shubhambaid/skin-burn-dataset", ROOT / "kaggle" / "skin-burn-dataset"),
        ("faresabbasai2022/last-databurn", ROOT / "kaggle" / "last-databurn"),
        ("brendarangelolvera/human-skin-burns", ROOT / "kaggle" / "human-skin-burns"),
    ]
    for slug, dest in datasets:
        log(f"\n=== Kaggle: {slug} ===")
        try:
            path = Path(kagglehub.dataset_download(slug))
            log(f"cache path: {path}")
            copy_tree(path, dest)
            RESULTS.append((slug, "OK", str(dest)))
        except Exception as e:
            log(f"FAILED: {e}")
            traceback.print_exc()
            RESULTS.append((slug, "FAIL", str(e)))


def download_huggingface() -> None:
    try:
        from huggingface_hub import snapshot_download
    except Exception as e:
        RESULTS.append(("huggingface_hub", "FAIL", str(e)))
        return

    datasets = [
        ("HLSS/HSR_Burns", ROOT / "huggingface" / "HSR_Burns"),
        ("HLSS/MassHumanBurns", ROOT / "huggingface" / "MassHumanBurns"),
    ]
    for repo, dest in datasets:
        log(f"\n=== HuggingFace: {repo} ===")
        try:
            path = snapshot_download(
                repo_id=repo,
                repo_type="dataset",
                local_dir=str(dest),
            )
            RESULTS.append((repo, "OK", path))
        except Exception as e:
            log(f"FAILED: {e}")
            traceback.print_exc()
            RESULTS.append((repo, "FAIL", str(e)))


def extract_bip_us() -> None:
    zip_path = ROOT / "bip_us" / "Burns_BIP_US_database.zip"
    dest = ROOT / "bip_us" / "extracted"
    log("\n=== Extract BIP_US ===")
    if not zip_path.exists():
        RESULTS.append(("BIP_US", "FAIL", "zip missing"))
        return
    try:
        if dest.exists():
            shutil.rmtree(dest)
        unzip_if_needed(zip_path, dest)
        RESULTS.append(("BIP_US", "OK", str(dest)))
        log(f"extracted to {dest}")
    except Exception as e:
        RESULTS.append(("BIP_US", "FAIL", str(e)))
        traceback.print_exc()


def try_roboflow() -> None:
    """Roboflow public export usually needs an API key; attempt package if present."""
    log("\n=== Roboflow ===")
    try:
        import os
        from roboflow import Roboflow
    except Exception as e:
        RESULTS.append(
            (
                "roboflow",
                "SKIP",
                f"package/import issue ({e}). Need ROBOFLOW_API_KEY for universe downloads.",
            )
        )
        return

    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        RESULTS.append(
            (
                "roboflow",
                "SKIP",
                "Set ROBOFLOW_API_KEY env var, then re-run for universe datasets.",
            )
        )
        return

    projects = [
        ("aibuildersclub", "skin-burns-4yoo2", 1, ROOT / "roboflow" / "skin-burns"),
        ("pelukbakar", "pb-tkjgx", 1, ROOT / "roboflow" / "pb"),
        ("burndegree", "pfa-hfzdi", 1, ROOT / "roboflow" / "pfa"),
    ]
    rf = Roboflow(api_key=api_key)
    for workspace, project, version, dest in projects:
        name = f"{workspace}/{project}"
        log(f"Roboflow: {name}")
        try:
            dest.mkdir(parents=True, exist_ok=True)
            proj = rf.workspace(workspace).project(project)
            # version may vary; try latest if specific fails
            try:
                ver = proj.version(version)
            except Exception:
                ver = proj.version(proj.versions()[0].version if hasattr(proj, "versions") else version)
            dataset = ver.download("yolov8", location=str(dest))
            RESULTS.append((name, "OK", str(dataset.location if hasattr(dataset, "location") else dest)))
        except Exception as e:
            log(f"FAILED: {e}")
            traceback.print_exc()
            RESULTS.append((name, "FAIL", str(e)))


def write_readme() -> None:
    lines = [
        "# Skin Burn Datasets",
        "",
        "Auto-download status:",
        "",
        "| Dataset | Status | Path / note |",
        "|---|---|---|",
    ]
    for name, status, note in RESULTS:
        safe = note.replace("|", "/")
        lines.append(f"| `{name}` | {status} | `{safe}` |")
    lines += [
        "",
        "## Not auto-downloadable",
        "",
        "- **EBIS** ([VEDAs-Lab/EBIS](https://github.com/VEDAs-Lab/EBIS)): email `vedas.cs@gmail.com` with signed commitment form.",
        "- **Zenodo 15101082**: metadata/PDF only, not the image archive.",
        "- Hospital/private sets cited in papers (Alberta, Hangzhou, Michael-OvO private) are not public.",
        "",
        "## Manual steps if needed",
        "",
        "1. Kaggle: put `kaggle.json` in `%USERPROFILE%\\.kaggle\\` then re-run `python download_all.py`.",
        "2. Roboflow: set `ROBOFLOW_API_KEY` and re-run.",
        "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    extract_bip_us()
    download_kaggle()
    download_huggingface()
    try_roboflow()
    write_readme()
    log("\n=== FINAL SUMMARY ===")
    for row in RESULTS:
        log(f"{row[0]} -> {row[1]} :: {row[2]}")


if __name__ == "__main__":
    main()
