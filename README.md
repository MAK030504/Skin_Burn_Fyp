# AI-Based Burn Severity Assessment and Recovery Monitoring System

**Undergraduate Final Year Project (FYP)**  
Faculty of Computer Science and Engineering (FCSE)  
Ghulam Ishaq Khan Institute of Engineering Sciences and Technology (GIKI)  
Bachelor of Science in Computer Engineering (2023–2027)

This README is the **single source of truth** for the project. Later documents (slides, scope, papers, code) should be read *through* this file, not instead of it.

---

## 1. One-paragraph summary

Burn severity and healing are still assessed largely by **eye**. That judgment is important, but it is also subjective, hard to document consistently across visits, and harder still where specialist burn care is scarce. This FYP proposes a **prototype AI-assisted decision-support system** that, from photographs of a burn, (1) classifies burn type, (2) localizes / segments the affected region, (3) estimates severity from those visual findings, (4) compares follow-up images of the same wound to track recovery, and (5) drafts a structured clinical-style summary using a vision-language model (VLM).

The contribution is **integration of an end-to-end workflow**, not a claim that we invented every underlying model. The system is a **research prototype**. It is **not** a medical device, **not** clinically validated, and **not** a replacement for a doctor.

---

## 2. Project identity

| Item | Detail |
|---|---|
| Full title | AI-Based Burn Severity Assessment and Recovery Monitoring System |
| Students | Abdur Rehman (2023054), Mustafa Avais (2023564) |
| Supervisor | Dr. Asad Mehmood |
| Co-supervisor | Dr. Hanif |
| Programme | BS Computer Engineering, FCSE, GIKI |
| Planned start | 23 June 2026 |
| Planned duration | 14 weeks (see [Roadmap](#12-execution-roadmap)) |
| Intended users | Clinicians / students evaluating a research prototype — not patients using a product |

**Division of work (from the official scope document):**

- **Mustafa Avais** — classification and severity models, segmentation, VLM integration, system integration and testing.
- **Abdur Rehman** — dataset collection and preprocessing, longitudinal recovery analysis, user interface, performance evaluation.

---

## 3. Why this problem exists (the topic)

### 3.1 What a “burn assessment” actually involves

A useful assessment is more than “how bad does this look?” Clinically, severity depends on several interacting factors:

- **Depth** — how far through the skin the injury goes (epidermis only vs into dermis vs full thickness).
- **Extent** — how much body surface is involved (often discussed as % TBSA, total body surface area).
- **Location** — face, hands, joints, and airway-adjacent burns change management even at the same depth.
- **Progression** — a wound on day 0 is not the same wound on day 14. Superficial injuries often heal; deeper injuries may require grafting. Healing itself is evidence.

Undergraduate readers (and panels) should remember: **depth, area, location, and time** are all part of the problem. An image classifier that only outputs “2nd degree” is solving one piece.

### 3.2 Why visual assessment is difficult

Standard practice is still **visual inspection plus clinical experience**. That is the right clinical gold standard in many settings, but it has well-known practical issues:

- Non-specialists are less consistent than burn specialists.
- The same wound can look different under different lighting, cameras, dressings, and skin tones.
- Early assessment is especially uncertain; depth can declare itself over days.
- Follow-up visits produce photographs that are rarely **compared quantitatively** (area change, colour change, texture change).

Specialist tools such as laser Doppler imaging exist, but they are expensive and uncommon in low- and middle-income settings — including much of Pakistan, and particularly first-contact care in regions such as Khyber Pakhtunkhwa.

### 3.3 What this project is *not* claiming

Do **not** describe this FYP as:

- a replacement for clinicians,
- a clinically validated diagnostic,
- a hospital-ready product,
- a system proven to improve patient outcomes.

The honest framing is: **an engineered prototype that can support consistent image-based documentation and structured summaries, with a human in the loop.**

---

## 4. Motivation vs justification

These two ideas are related but different. Use them that way in reports and vivas.

**Motivation — why anyone should care**

1. Burn assessment is clinically hard (depth, area, location, progression).
2. Specialist access is uneven, especially in resource-constrained settings.
3. Visual assessment is subjective, so documentation and visit-to-visit comparison suffer.
4. A single snapshot does not describe healing; longitudinal images might.
5. Computer vision and multimodal AI can *assist* with consistent measurements and structured text.

**Justification — why *this* FYP is a reasonable Computer Engineering project**

- **Clinical relevance:** severity and healing documentation matter in burn care; consistent records support follow-up.
- **Technical relevance:** the problem combines classification, segmentation, temporal analysis, software systems, and VLMs.
- **Research gap:** published work usually solves *one* of those tasks; integrated assessment + localization + severity + recovery monitoring is still an open *practical* challenge.
- **Local relevance:** data collection, skin-tone diversity, and clinical workflow constraints in Pakistani settings are part of the design problem.
- **Feasibility:** modern CNNs/U-Nets/VLMs make a prototype tractable; components can be evaluated separately then combined.

---

## 5. Proposed system

### 5.1 Capabilities (what “done” looks like)

One platform, four visual capabilities, plus reporting:

| # | Capability | Meaning in this project |
|---|---|---|
| 1 | **Classify** | Estimate burn type / degree from the image (prototype target: first / second / third degree, subject to the labels actually available in the datasets). |
| 2 | **Segment** | Localize the burn region at pixel level (mask), rather than classifying the whole photo blindly. |
| 3 | **Score** | Estimate severity using the *segmented* region (depth-related class + area-related measures), not a single opaque whole-image score. |
| 4 | **Monitor** | Compare sequential images of the *same* wound (area, visual appearance) and produce a recovery trend. |
| 5 | **Report** | A VLM turns those structured outputs into a clinical-style summary for a human to review. |

### 5.2 Intended data flow

```
Burn image (and optional follow-up images of the same wound)
        │
        ▼
Preprocessing (resize, colour normalisation, quality checks)
        │
        ├──► Classification model  ──► burn type / degree
        ├──► Segmentation model    ──► burn mask + area proxy
        └──► Severity module       ──► combined visual severity estimate
        │
        ▼
If a prior visit exists: longitudinal comparison (area / appearance change)
        │
        ▼
VLM + templates  ──► structured report (for clinician review)
        │
        ▼
Store image + outputs against a patient/wound history (prototype database)
```

Software architecture (how those models sit in a real system):

```
User / Clinician
        ▼
Frontend / Interface
        ▼
Backend API
        ▼
AI processing pipeline
   ├── Vision models (classify / segment / compare)
   └── VLM / reporting
        ▼
Database / wound history
        ▼
Results and longitudinal monitoring
```

### 5.3 Business / academic objectives (from the scope document)

| ID | Objective |
|---|---|
| BO-1 | Classify burn types from images. |
| BO-2 | Estimate severity from visual features. |
| BO-3 | Segment / localise the affected region. |
| BO-4 | Monitor healing across sequential images. |
| BO-5 | Use a VLM for structured clinical-style descriptions. |
| BO-6 | Produce reports with scores, area measures, and recovery analysis. |
| BO-7 | Keep the prototype efficient and usable as *assistance*, not automation of care. |

---

## 6. In scope / out of scope

**In scope**

- Prototype-level system (web or similar interface).
- Pre-collected and publicly available image datasets (plus any ethically obtained clinical images if they become available).
- Image-based classification, segmentation, severity estimation.
- Longitudinal comparison of follow-up photographs.
- VLM-assisted structured reporting.
- Software engineering of a modular pipeline (API, storage, logging, tests), not a one-off notebook.

**Out of scope**

- Real-time clinical deployment in a hospital.
- Integration with hospital information systems / EMR.
- Regulatory or medical-device validation.
- Replacing clinical judgment.
- Guaranteeing improved clinical outcomes.

If a later milestone *does* involve clinicians, it is still **human-in-the-loop evaluation**, not certification.

---

## 7. Research gap (how to talk about prior work)

Existing papers have already shown that CNNs can classify burn images, that segmentation networks can outline wounds, and that a few prototypes can track a wound over time. That is useful. It is **not** the same as an integrated, practical system.

Typical limitations in the literature (often several at once):

- small or single-centre datasets
- limited skin-tone / demographic diversity
- controlled cameras (not ordinary smartphones)
- classification *or* segmentation, rarely both plus follow-up
- no longitudinal recovery module
- no structured reporting layer
- little external or real-world clinical validation
- heavy dependence on expert pixel labels

**The sentence to remember:**  
existing work largely addresses *individual components*; an integrated system for **assessment + localization + severity estimation + longitudinal recovery monitoring** remains an open practical challenge.

This FYP’s primary contribution is that **integration**, plus recovery tracking and reporting, implemented as software — not a claim of superior accuracy over every published model.

Verified papers used in the title-defence literature review:

| # | Paper | Link | What it did | Limitation relative to this FYP |
|---|---|---|---|---|
| [1] | Yadav et al., IEEE JTEHM, 2019 | [doi](https://doi.org/10.1109/JTEHM.2019.2923628) · [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6605086/) | SVM on BIP_US; graft vs non-graft; **82.43%** on 74 test images | Binary task; small set; no localisation or follow-up |
| [2] | Cirillo et al., *J. Burn Care Res.*, 2019 | [doi](https://doi.org/10.1093/jbcr/irz103) | CNNs on TiVi images; ResNet-101 10-fold avg. **81.66%** | Small specialised-camera set; classification only |
| [3] | Chauhan & Goyal, *Burns*, 2020 (BPBSAM) | [doi](https://doi.org/10.1016/j.burns.2020.03.007) | Body-part-specific severity; BI acc. **84.85%** / F1 **77.8%**; UBI acc. **91.53%** / F1 **87.2%** | Limited labelled set (partly web images); no segmentation or tracking |
| [4] | Liu et al., *Comput. Math. Methods Med.*, 2021 | [doi](https://doi.org/10.1155/2021/5514224) · [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8046560/) | Area + multi-depth segmentation; IoU **0.8467** (binary), **0.5144** (multi-depth) | Single-centre; modest multi-depth IoU; no recovery tracking |
| [5] | Boissin et al., *Sci. Rep.*, 2023 | [doi](https://doi.org/10.1038/s41598-023-28164-4) · [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9889389/) | Wound identifier + surgery-need classifier; **87.2%** area detected; AUC **0.885** | Acute burns ≤48 h only; no recovery tracking |
| [6] | Ethier et al., *J. Burn Care Res.*, 2024 (SATA) | [doi](https://doi.org/10.1093/jbcr/irad197) · [preprint](https://www.medrxiv.org/content/10.1101/2022.12.15.22283475v1) | Healing tracking with EfficientNetB7 + BAM; single-patient 6+2 week PoC; area *r* = **0.87** | Single-case prototype; not an integrated reporting workflow |

Do not invent extra accuracies. If a number is not in the paper, do not put it on a slide.

---

## 8. Technical approach (planned)

Exact architectures are **Week 2** decisions on the roadmap. The working families (from the title defence) are:

| Layer | Planned family | Role |
|---|---|---|
| Classification | CNN / transfer learning (ResNet, EfficientNet, or similar) | Burn type / degree |
| Segmentation | Encoder–decoder (U-Net family or similar) | Mask and area proxy |
| Severity | Combination of class + segmented region statistics (not a black-box whole-image score) | Interpretable-enough prototype metric |
| Recovery | Visit-to-visit comparison of masks and appearance (area change, visual indicators) | Trend, not a medical prognosis |
| Reporting | VLM (BLIP-family or a later equivalent) + structured fields | Draft text for a clinician |
| Product shell | Frontend + backend API + database | Upload, history, results |

**Engineering goal:** a modular, testable, reproducible *system* (requirements, data versioning, train/val/test splits, APIs, logging, privacy of medical images), not a single trained `.pt` file.

Privacy: treat all medical images as sensitive. No public upload of identifiable patient photos. Prefer de-identified public sets; any hospital data needs proper ethics/consent via supervisors.

---

## 9. Datasets

Public and research datasets already collected under `datasets/`. Details and download commands live in [`datasets/README.md`](datasets/README.md).

**Currently on disk (high level):**

| Dataset | Path | Notes |
|---|---|---|
| BIP_US (Univ. of Seville) | `datasets/bip_us/` | Small clinical set; ~94 images; superficial / deep dermal / full thickness — same family of data used by Yadav [1] |
| Kaggle Skin Burn Dataset | `datasets/kaggle/skin-burn-dataset/` | ~1.3k images + YOLO labels (1st/2nd/3rd) |
| Kaggle last-databurn | `datasets/kaggle/last-databurn/` | ~1.3k images in degree folders |
| Kaggle human-skin-burns | `datasets/kaggle/human-skin-burns/` | Larger hospital-style collection |
| HuggingFace HSR_Burns | `datasets/huggingface/HSR_Burns/` | Synthetic TBSA-style renders — use with caution; not real wounds |
| HuggingFace MassHumanBurns | `datasets/huggingface/MassHumanBurns/` | Archives; unpack via `python datasets/extract_masshumanburns.py` |
| Roboflow collections | `datasets/roboflow/` | Several YOLO exports for detection/segmentation |

**Not automatically available (and should not be pretended otherwise):**

- EBIS — request from the authors ([VEDAs-Lab/EBIS](https://github.com/VEDAs-Lab/EBIS)).
- Private hospital sets used in papers (e.g. Alberta, Hangzhou) — not public.
- Any local Pakistani clinical set — only if collected with supervisor-approved ethics/consent.

**Primary project constraint (roadmap):** dataset availability, diversity, and labelling quality will dominate accuracy and timeline. Web-scraped or mixed-quality images can inflate numbers and fail to generalise. Always report *which* set, *which* split, and *what* the labels actually mean (degree vs graft/non-graft vs surgery-need are different tasks).

Re-download public sets:

```powershell
python datasets/download_all.py
```

---

## 10. How we will evaluate (so claims stay honest)

Evaluate **components first**, then the pipeline:

| Component | Typical metrics | Notes |
|---|---|---|
| Classification | accuracy, macro-F1, per-class recall | Report class imbalance. |
| Segmentation | Dice / IoU | Pixel labels may be noisy. |
| Severity | agreement with the label definition you actually used | Do not mix “degree” with “needs graft” without saying so. |
| Recovery | correlation of area/trend with a defined reference on paired visits | Needs *same-wound* sequences; most public sets are not longitudinal. |
| Report | qualitative review + whether required fields are present | A fluent paragraph is not a clinical diagnosis. |
| System | inference time, failure modes, missing-image behaviour | Prototype, not production SLA. |

If a dataset has no follow-up images, **do not claim recovery-monitoring accuracy on that set**. Simulate or collect paired visits separately.

---

## 11. Current repository status

This is still early. At the time this README was written:

- Title-defence slides and official roadmap exist under `Documenations/`.
- Scope document exists (`SDP - Scope Document .docx`).
- Public datasets have been downloaded into `datasets/`.
- Application code (training pipeline, API, UI) is **not** the main body of the repo yet — that is Weeks 4–12 of the roadmap.

If you clone this repo and expect a running web app immediately, you will not find one until those milestones land.

---

## 12. Execution roadmap

Official plan: **14 weeks from 23 June 2026**. Dataset quality is the named primary constraint.

| Week | Phase | What “done” means |
|---|---|---|
| 1 | Literature review | Limitations, datasets, architecture shortlist |
| 1–2 | Dataset collection | Public sets + outreach via Dr. Hanif / external contacts |
| 2 | Technology selection | Freeze DL / CV / VLM / backend / frontend / DB / deploy stack |
| 3 | Data preparation | Clean, annotate/align labels, train/val/test, augmentation pipeline |
| 4 | Burn classification | Trained CNN for the agreed degree / type labels |
| 5 | Burn segmentation | Masks + area calculation |
| 6 | Severity assessment | Combined depth + area module; clinician consultation on definitions |
| 7–8 | Recovery monitoring | Sequential comparison, healing graphs / scores |
| 9–10 | VLM reporting | Fields inspired by real report structure; generated draft text |
| 11–12 | Full-stack | Frontend + backend wiring model APIs |
| 13 | Testing | Integration, metrics, edge cases |
| 14 | Deployment | End-to-end web/mobile prototype for *evaluation*, not hospital go-live |

---

## 13. Repository layout

```
Skin_Burn_Fyp/
├── README.md                 ← you are here
├── .gitignore
├── datasets/                 ← images and download scripts (gitignored contents)
│   ├── README.md
│   ├── download_all.py
│   ├── extract_masshumanburns.py
│   ├── bip_us/
│   ├── kaggle/
│   ├── huggingface/
│   ├── roboflow/
│   └── zenodo_skin_burn/
├── Documenations/            ← official FYP documents (folder name is historical)
│   ├── FYP_Title_Defence.pptx
│   ├── FYP_Roadmap.pdf
│   └── SDP - Scope Document .docx
└── tools/                    ← local utilities (e.g. 7zip for large archives)
```

Large image archives are listed in `.gitignore` (`datasets/`) so they are not committed.

---

## 14. Related documents

| Document | Path | Use it for |
|---|---|---|
| This README | `README.md` | Orientation and ground truth |
| Title defence | `Documenations/FYP_Title_Defence.pptx` | Panel narrative and diagrams |
| Roadmap | `Documenations/FYP_Roadmap.pdf` | Week-by-week plan |
| Scope | `Documenations/SDP - Scope Document .docx` | Formal objectives and roles |
| Dataset inventory | `datasets/README.md` | What was downloaded and how |

If the scope document and this README disagree on **clinical claims**, prefer this README’s conservative wording (prototype, decision support, no outcome claims). If they disagree on **dates or deliverables**, prefer the official roadmap PDF.

---

## 15. Glossary

| Term | Meaning here |
|---|---|
| **TBSA** | Total body surface area; fraction of the body that is burned. |
| **Depth / degree** | How deep the injury is (roughly: 1st = epidermis, 2nd = into dermis, 3rd = full thickness). Labels in datasets are often coarse. |
| **Graft vs non-graft** | A *clinical decision* label used in some papers (e.g. BIP_US), not the same as three-class degree. |
| **Segmentation mask** | Per-pixel map of “this is burn” (sometimes also depth subclasses). |
| **Longitudinal / recovery monitoring** | Comparing the *same wound* across dates, not classifying unrelated photos. |
| **VLM** | Vision-language model: takes images (and/or structured fields) and produces text. |
| **Human-in-the-loop** | A clinician reviews outputs; the model does not discharge, prescribe, or triage alone. |
| **Prototype** | Demonstrates feasibility on held-out images. Not a deployed medical product. |

---

## 16. How a new reader should start

1. Read Sections 1, 3, 5, and 6 of this file.
2. Skim the title-defence slides for diagrams.
3. Inspect `datasets/README.md` before training anything.
4. Treat Week 2 (stack freeze) and Week 3 (clean splits) as the real start of modelling.
5. When writing results, name the dataset, the task, and the limitation in the same sentence.
