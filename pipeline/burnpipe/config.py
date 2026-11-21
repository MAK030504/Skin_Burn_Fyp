"""Load pipeline YAML and resolve paths from the repository root."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_repo_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def resolve_cli_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    from_cwd = (Path.cwd() / path).resolve()
    if from_cwd.exists():
        return from_cwd
    return (REPO_ROOT / path).resolve()


def load_config(path_str: str) -> dict:
    path = resolve_cli_path(path_str)
    if not path.is_file():
        raise SystemExit(f"Config not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"Config must be a YAML mapping: {path}")
    data["_config_path"] = str(path)
    required = ["name", "classes", "source", "train", "image"]
    missing = [key for key in required if key not in data]
    if missing:
        raise SystemExit(f"Config is missing keys: {', '.join(missing)}")
    if not isinstance(data["classes"], list) or len(data["classes"]) < 2:
        raise SystemExit("Config classes must be a list of at least two labels.")
    return data
