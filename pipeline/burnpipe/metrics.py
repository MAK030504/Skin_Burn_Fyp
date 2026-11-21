"""Classification metrics without an extra dependency."""

from __future__ import annotations


def classification_metrics(y_true: list[int], y_pred: list[int], classes: list[str]) -> dict:
    size = len(classes)
    matrix = [[0 for _ in range(size)] for _ in range(size)]
    for truth, pred in zip(y_true, y_pred):
        matrix[truth][pred] += 1

    per_class = {}
    f1_scores = []
    for index, name in enumerate(classes):
        true_positive = matrix[index][index]
        predicted_positive = sum(matrix[row][index] for row in range(size))
        actual_positive = sum(matrix[index])
        false_positive = predicted_positive - true_positive
        false_negative = actual_positive - true_positive
        precision = true_positive / (true_positive + false_positive) if predicted_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if actual_positive else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        per_class[name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": actual_positive,
        }
        f1_scores.append(f1)

    correct = sum(matrix[index][index] for index in range(size))
    total = max(len(y_true), 1)
    return {
        "accuracy": correct / total,
        "macro_f1": sum(f1_scores) / size,
        "per_class": per_class,
        "confusion_matrix": matrix,
        "classes": list(classes),
        "n": len(y_true),
    }


def format_metrics(metrics: dict) -> str:
    classes = metrics["classes"]
    header = "class".ljust(12) + "precision".rjust(10) + "recall".rjust(10) + "f1".rjust(10) + "support".rjust(10)
    lines = [
        f"n={metrics['n']}  accuracy={metrics['accuracy']:.4f}  macro_f1={metrics['macro_f1']:.4f}",
        header,
    ]
    for name in classes:
        row = metrics["per_class"][name]
        lines.append(
            name.ljust(12)
            + f"{row['precision']:.4f}".rjust(10)
            + f"{row['recall']:.4f}".rjust(10)
            + f"{row['f1']:.4f}".rjust(10)
            + f"{row['support']}".rjust(10)
        )
    name_width = max(len(name) for name in classes)
    pred_header = "true\\pred".ljust(name_width) + "".join(name.rjust(name_width + 2) for name in classes)
    lines.append(pred_header)
    for index, name in enumerate(classes):
        counts = "".join(str(value).rjust(name_width + 2) for value in metrics["confusion_matrix"][index])
        lines.append(name.ljust(name_width) + counts)
    return "\n".join(lines)
