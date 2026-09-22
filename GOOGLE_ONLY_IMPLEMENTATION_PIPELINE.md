# Google-Only Implementation Pipeline (Redesign)

## 1) Purpose

This document redesigns the burn assessment prototype pipeline using only Google products.
It keeps the same research scope (classification, segmentation, severity estimation, recovery monitoring, and report drafting) while replacing all implementation components with Google-native services.

This remains a research prototype and decision-support workflow, not a clinical diagnostic device.

---

## 2) Target Google stack (only)

### Core platform
- **Google Cloud Platform (GCP)** as the full backend and MLOps environment.
- **Vertex AI** for training, pipelines, model registry, deployment, and monitoring.
- **Gemini on Vertex AI** for structured clinical-style report drafting.

### Data and storage
- **Cloud Storage (GCS)** for raw images, curated datasets, splits, masks, and model artifacts.
- **BigQuery** for dataset metadata, experiment logs, prediction records, and analytics.
- **Firestore** for application records (patient case timeline, wound visit history, UI state).

### App and APIs
- **Cloud Run** for backend API services (inference orchestration, business logic).
- **API Gateway** in front of Cloud Run for managed API exposure.
- **Firebase Hosting** for the web frontend.
- **Firebase Authentication** for clinician/research-user identity and access.

### Security and operations
- **IAM** for least-privilege access control.
- **Secret Manager** for API keys and runtime secrets.
- **Cloud KMS** for key management.
- **Cloud Logging + Cloud Monitoring + Error Reporting** for observability.
- **Cloud Audit Logs** for traceability of sensitive data access.

### CI/CD and artifacts
- **Cloud Build** for CI pipelines.
- **Artifact Registry** for container images.
- **Cloud Deploy** (optional) for controlled multi-environment rollout.

---

## 3) End-to-end implementation pipeline

## Phase A: Data intake and governance
1. Upload source datasets to **GCS raw bucket** (`gs://.../raw/`).
2. Normalize image formats and naming with a **Vertex AI Pipeline** preprocessing step.
3. Store metadata (source, label schema, split, image quality flags) in **BigQuery**.
4. Store de-identified case linkage fields in **Firestore** (if longitudinal tracking is used).
5. Enforce bucket-level IAM and encryption (KMS-backed) for medical images.

**Outputs:** versioned curated dataset in GCS + metadata tables in BigQuery.

## Phase B: Data preparation and labeling harmonization
1. Run preprocessing job (resize, color normalization, quality checks) in **Vertex AI Custom Job**.
2. Convert label taxonomies into a common schema (degree classes, mask classes, visit IDs).
3. Create reproducible train/validation/test splits and persist split manifests to GCS + BigQuery.
4. Optional manual corrections via **Vertex AI Data Labeling** (if extra mask refinement is needed).

**Outputs:** training-ready tensors/files + split manifests + label mapping spec.

## Phase C: Model training (modular)
Train separate components in Vertex AI:
1. **Classification model** (burn degree/type) via Vertex AI Custom Training.
2. **Segmentation model** (burn region masks) via Vertex AI Custom Training.
3. **Severity module** as a deterministic or learned fusion step:
   - combines class probabilities + segmented area features,
   - writes interpretable intermediate metrics into BigQuery.
4. **Recovery module** compares same-wound visits (mask area change + appearance features).

Track parameters and metrics with Vertex Experiments and persist final artifacts to GCS.

**Outputs:** trained model artifacts + experiment metrics + chosen model versions.

## Phase D: Evaluation and model registration
1. Compute classification metrics (accuracy, macro-F1, per-class recall).
2. Compute segmentation metrics (Dice, IoU).
3. Compute recovery metrics on actual longitudinal subsets only.
4. Register approved model versions in **Vertex AI Model Registry**.
5. Gate production promotion on explicit metric thresholds in Cloud Build/Cloud Deploy policy.

**Outputs:** registered, versioned candidate models ready for deployment.

## Phase E: Deployment and online inference
1. Deploy models to **Vertex AI Endpoints** (separate endpoints per component or unified endpoint).
2. Backend **Cloud Run API** orchestrates:
   - image upload and retrieval from GCS,
   - calls to classification and segmentation endpoints,
   - severity and recovery calculations,
   - Gemini report generation on Vertex AI.
3. Persist prediction outputs and report drafts to Firestore/BigQuery.
4. Return structured response to frontend (scores, masks, trend chart payload, draft report).

**Outputs:** usable inference API for the web application.

## Phase F: Frontend and workflow
1. Host UI on **Firebase Hosting**.
2. Use **Firebase Auth** for sign-in and role-based route protection.
3. Present:
   - single-visit assessment,
   - longitudinal view by wound/case ID,
   - generated report draft with mandatory human review checkbox.
4. Store review actions and edits in Firestore for audit and quality analysis.

**Outputs:** clinician/research-facing interface on Google-managed frontend stack.

## Phase G: Monitoring, drift, and continuous improvement
1. Enable **Vertex Model Monitoring** for prediction skew/drift.
2. Route runtime logs to **Cloud Logging**; set alerts in **Cloud Monitoring**.
3. Build quality dashboards in **Looker Studio** from BigQuery.
4. Trigger periodic retraining pipelines with **Cloud Scheduler + Vertex Pipelines**.
5. Keep immutable model/version lineage for reproducibility.

**Outputs:** stable operations loop with retraining triggers and quality visibility.

---

## 4) Reference architecture (logical)

1. User uploads burn image(s) in web app (Firebase Hosting + Auth).
2. Cloud Run API stores images in GCS and writes request metadata to BigQuery.
3. Cloud Run invokes Vertex AI endpoints for classification + segmentation.
4. Cloud Run computes severity/recovery features and stores results.
5. Cloud Run calls Gemini on Vertex AI to produce structured draft summary.
6. API returns outputs to UI; clinician reviews/edits; final report state saved in Firestore.
7. Monitoring and analytics are centralized in Cloud Monitoring/Logging + BigQuery dashboards.

---

## 5) Service-to-capability mapping

| Project capability | Google product(s) |
|---|---|
| Dataset storage and versioning | Cloud Storage |
| Metadata and analytics | BigQuery |
| Data preprocessing pipeline | Vertex AI Pipelines + Custom Jobs |
| Classification training | Vertex AI Custom Training |
| Segmentation training | Vertex AI Custom Training |
| Model registry/versioning | Vertex AI Model Registry |
| Online inference | Vertex AI Endpoints |
| Structured report generation | Gemini on Vertex AI |
| Backend orchestration | Cloud Run + API Gateway |
| Frontend hosting and identity | Firebase Hosting + Firebase Auth |
| Case timeline persistence | Firestore |
| CI/CD | Cloud Build + Artifact Registry (+ Cloud Deploy optional) |
| Observability | Cloud Logging, Monitoring, Error Reporting |
| Security and compliance controls | IAM, Secret Manager, KMS, Audit Logs |

---

## 6) Implementation milestones (aligned to existing FYP flow)

1. **Environment foundation:** project setup, IAM, buckets, BigQuery datasets, Artifact Registry.
2. **Data pipeline:** ingestion + preprocessing + split manifests.
3. **Model pipeline:** classification and segmentation training in Vertex AI.
4. **Fusion and recovery logic:** severity + longitudinal comparison services.
5. **Inference API:** Cloud Run orchestration with Vertex endpoints.
6. **Report module:** Gemini prompt template + structured output schema.
7. **UI integration:** Firebase frontend with history view and report review flow.
8. **Monitoring and hardening:** drift alerts, dashboards, audit logs, retraining schedule.

---

## 7) Guardrails and constraints

- The system must keep a **human in the loop** for any clinical interpretation.
- Generated text from Gemini is a **draft summary**, never an autonomous diagnosis.
- Recovery metrics must be reported only for genuine same-wound follow-up data.
- Every reported metric must identify dataset, split, and label definition.

