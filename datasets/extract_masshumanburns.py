"""Extract MassHumanBurns .7z archives into huggingface/MassHumanBurns/."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "huggingface" / "MassHumanBurns"
ARCHIVES = ("burn_masks.7z", "full_masks.7z", "images.7z")
SEVENZR = Path(__file__).resolve().parent.parent / "tools" / "7zip" / "7zr.exe"


def main() -> None:
    if not SEVENZR.is_file():
        sys.exit(f"Missing {SEVENZR} — download from https://www.7-zip.org/a/7zr.exe")
    ROOT.mkdir(parents=True, exist_ok=True)
    for name in ARCHIVES:
        archive = ROOT / name
        if not archive.is_file():
            raise FileNotFoundError(archive)
        print(f"\n=== Extracting {name} -> {ROOT} ===", flush=True)
        subprocess.check_call(
            [str(SEVENZR), "x", str(archive), f"-o{ROOT}", "-y"],
        )
        print(f"OK {name}", flush=True)
    print("\nAll archives extracted.", flush=True)


if __name__ == "__main__":
    main()
