# Skin Burn Datasets

Downloaded under `datasets/` for the Skin Burn FYP.

## Successfully downloaded

| Dataset | Path | What you get |
|---|---|---|
| **BIP_US** (clinical, Univ. of Seville) | `bip_us/extracted/` | ~94 hospital images; superficial / deep dermal / full thickness |
| **Kaggle Skin Burn Dataset** (Shubam) | `kaggle/skin-burn-dataset/` | ~1.3k images + YOLO labels (1st/2nd/3rd) |
| **Kaggle last-databurn** | `kaggle/last-databurn/` | ~1.3k images in `1st degree` / `2nd degree` / `3nd degree` folders |

## Also downloaded

| Dataset | Path | What you get |
|---|---|---|
| **HuggingFace HSR_Burns** | `huggingface/HSR_Burns/` | Synthetic TBSA validation renders (~204 MB) |
| **Kaggle human-skin-burns** | `kaggle/human-skin-burns/` | ~2.8k files (~791 MB archive); hospital-style burn images |
| **Roboflow Skin Burns** | `roboflow/skin-burns/` | YOLOv8 export (~1.1k images, classes 0/1/2) |
| **Roboflow PFA** | `roboflow/pfa/` | YOLOv8 export (~730 images) |
| **Roboflow Burn Segmentation** | `roboflow/burn-segmentation/` | YOLOv8 export (~9.6k images, classes 0/1/2) |
| **Roboflow skin-burn-ankzs** | `roboflow/skin-burn-ankzs/` | YOLOv8 export (~1.3k images) |
| **HuggingFace MassHumanBurns** | `huggingface/MassHumanBurns/` | Archives downloaded; unpack: `python datasets/extract_masshumanburns.py` (uses `tools/7zip/7zr.exe`) |

## Still need manual / credentials

| Dataset | Status | How to finish |
|---|---|---|
| **Roboflow PB** (`pelukbakar/pb-tkjgx`) | Permission / unavailable | Dataset may be private or removed on Universe |

## Not auto-downloadable

- **EBIS** — request via email: `vedas.cs@gmail.com` ([VEDAs-Lab/EBIS](https://github.com/VEDAs-Lab/EBIS))
- **Zenodo 15101082** — PDF/metadata only, no image archive
- Hospital private sets (Alberta, Hangzhou, Michael-OvO) — not public

## Re-run downloads

```powershell
python datasets/download_all.py
```
