"""Image datasets and transforms for degree classification."""

from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms as T

from burnpipe.config import REPO_ROOT

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def build_transforms(image_size: int, train: bool) -> T.Compose:
    # Resize the full frame. A random crop can drop the wound, which is the
    # only region the degree label refers to.
    if train:
        return T.Compose(
            [
                T.Resize((image_size, image_size)),
                T.RandomHorizontalFlip(),
                T.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.08),
                T.ToTensor(),
                T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ]
        )
    return T.Compose(
        [
            T.Resize((image_size, image_size)),
            T.ToTensor(),
            T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


class BurnImageDataset(Dataset):
    def __init__(self, rows: list[dict], classes: list[str], transform) -> None:
        self.rows = rows
        self.class_to_index = {label: index for index, label in enumerate(classes)}
        self.transform = transform

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        path = _image_path(row["image_path"])
        with Image.open(path) as image:
            image = image.convert("RGB")
            tensor = self.transform(image)
        target = self.class_to_index[row["label"]]
        return tensor, target


def make_loader(rows: list[dict], classes: list[str], image_size: int, batch_size: int, train: bool, num_workers: int, seed: int):
    dataset = BurnImageDataset(rows, classes, build_transforms(image_size, train=train))
    generator = torch.Generator()
    generator.manual_seed(seed)
    return torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=train,
        num_workers=num_workers,
        generator=generator if train else None,
        pin_memory=torch.cuda.is_available(),
    )


def class_weights(rows: list[dict], classes: list[str]) -> torch.Tensor:
    counts = [sum(row["label"] == label for row in rows) for label in classes]
    weights = [sum(counts) / max(count, 1) for count in counts]
    tensor = torch.tensor(weights, dtype=torch.float32)
    return tensor / tensor.sum() * len(classes)


def _image_path(stored: str) -> Path:
    path = Path(stored)
    if path.is_absolute():
        return path
    return REPO_ROOT / path
