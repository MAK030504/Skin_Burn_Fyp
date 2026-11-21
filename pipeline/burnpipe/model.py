"""Classification backbones. The saved checkpoint records which one was used."""

from __future__ import annotations

import torch.nn as nn
from torchvision.models import (
    EfficientNet_B0_Weights,
    ResNet18_Weights,
    efficientnet_b0,
    resnet18,
)


def build_model(backbone: str, num_classes: int, pretrained: bool) -> nn.Module:
    if backbone == "resnet18":
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        model = resnet18(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model
    if backbone == "efficientnet_b0":
        weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = efficientnet_b0(weights=weights)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
        return model
    raise SystemExit(
        f"Unknown backbone {backbone!r}. Use 'resnet18' or 'efficientnet_b0'."
    )
