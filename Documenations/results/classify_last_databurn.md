# Last-databurn degree classification

These labels are the Kaggle `faresabbasai2022/last-databurn` folder names (`1st degree`, `2nd degree`, `3nd degree`). They are public folder names, not a clinician review. This is not a clinical accuracy number.

| Item | Value |
|---|---|
| Dataset | Kaggle last-databurn |
| Config | `pipeline/configs/classify_last_databurn.yaml` |
| Task | first / second / third degree |
| Seed | 42 |
| Split | 70% train, 15% validation, 15% test |
| Images after exact-byte dedup | 1,219 kept, 138 skipped |
| Train counts | first 355, second 300, third 200 |
| Validation counts | first 76, second 64, third 42 |
| Test counts | first 76, second 64, third 42 |
| Backbone | ResNet-18, ImageNet initialization |
| Where it ran | Google Colab, Tesla T4, PyTorch 2.14.1+cu130 |
| Checkpoint used for the score | `best.pt` on validation macro-F1 |

Test split, scored once:

| | |
|---|---|
| Accuracy | 0.632 |
| Macro-F1 | 0.616 |
| Test images | 182 |
| Test loss | 1.493 |

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| first | 0.718 | 0.737 | 0.727 | 76 |
| second | 0.667 | 0.406 | 0.505 | 64 |
| third | 0.508 | 0.786 | 0.617 | 42 |

Confusion matrix. Rows are the folder label. Columns are the prediction, in the order first, second, third.

| True \ predicted | first | second | third |
|---|---:|---:|---:|
| first | 56 | 10 | 10 |
| second | 16 | 26 | 22 |
| third | 6 | 3 | 33 |

Second degree is the weak class: recall 0.406. Third degree is often predicted when the folder label is second. A later run on clinician-reviewed labels is a separate experiment and is not this number.
