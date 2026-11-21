"""Command line for the degree-classification pipeline.

From the repository root:

    python run_pipeline.py prepare --config pipeline/configs/classify_last_databurn.yaml
    python run_pipeline.py train --config pipeline/configs/classify_last_databurn.yaml
    python run_pipeline.py evaluate --run-dir runs/classify/last_databurn_degree/<stamp>
    python run_pipeline.py predict --run-dir <stamp> --image path\\to\\burn.jpg
"""

from __future__ import annotations

import argparse

from burnpipe.engine import evaluate, predict, prepare, train


def main() -> int:
    parser = argparse.ArgumentParser(prog="burnpipe")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare_parser = sub.add_parser("prepare", help="Write a train/val/test manifest and stop.")
    prepare_parser.add_argument("--config", required=True)
    prepare_parser.add_argument("--out", default=None, help="Directory for manifest.csv")

    train_parser = sub.add_parser("train", help="Build the manifest, train, and score the test split.")
    train_parser.add_argument("--config", required=True)
    train_parser.add_argument("--epochs", type=int, default=None)
    train_parser.add_argument("--max-steps", type=int, default=None, help="Smoke test: stop the first epoch early.")
    train_parser.add_argument("--run-dir", default=None)

    eval_parser = sub.add_parser("evaluate", help="Score best.pt on the test rows stored in a run.")
    eval_parser.add_argument("--run-dir", required=True)

    predict_parser = sub.add_parser("predict", help="Print class probabilities for one image.")
    predict_parser.add_argument("--run-dir", required=True)
    predict_parser.add_argument("--image", required=True)

    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.config, args.out)
    elif args.command == "train":
        train(args.config, args.epochs, args.max_steps, args.run_dir)
    elif args.command == "evaluate":
        evaluate(args.run_dir)
    elif args.command == "predict":
        predict(args.run_dir, args.image)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
