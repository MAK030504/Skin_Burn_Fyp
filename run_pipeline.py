"""Run the burn pipeline from the repository root.

Examples:
    python run_pipeline.py prepare --config pipeline/configs/classify_last_databurn.yaml
    python run_pipeline.py train --config pipeline/configs/classify_last_databurn.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "pipeline"))

from burnpipe.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
