---
name: competition-setup
description: This skill should be used when the user asks to "setup competition", "setup infra", "GCP setup", "GCPセットアップ", "初期セットアップ", "コンペのセットアップ", "インフラ構築", "データダウンロード", "download competition data", "setup environment", "環境構築", or wants to initialize infrastructure and download competition data for a new competition project.
---

# Competition Setup

End-to-end setup workflow for a competition project: GCP infrastructure provisioning, Docker image build, and competition data download to both local and GCS.

## Step 0: Ask the User About Their Competition

Before proceeding, ask the user:

1. **Competition platform**: Which platform is the competition on? (Kaggle / Other)
2. **Competition name**: What is the competition name (slug)?

Use the `AskUserQuestion` tool to gather this information.

- If the platform is **Kaggle**: Proceed with all phases below (including automated data download).
- If the platform is **other** (e.g., AtCoder, signate, etc.): Skip Phase 0 (Kaggle credentials) and Phase 3 (automated data download). Instead, inform the user:
  > このプラットフォームでは自動データダウンロードに対応していません。手動でデータをダウンロードして `data/input/{COMPETITION_NAME}/` に配置してください。GCS へのアップロードは `task push-data` で行えます。

Infrastructure setup (Phase 1 & 2) is common across all platforms.

## Prerequisites

Before starting, ensure the following are configured:

- **GCP authentication**: `gcloud auth application-default login` and `gcloud auth login`
- **`.env` file**: Copy from `.env.example` and fill in required values (`PROJECT_ID`, `REGION`, `COMPETITION_NAME`)
  - For Kaggle competitions, also set `KAGGLE_USERNAME` and `KAGGLE_KEY`
- **Tools installed**: `gcloud`, `terraform`, `task` (Taskfile), `uv`

## Setup Workflow

Execute the following phases in order. Each phase depends on the previous one completing successfully.

### Phase 0: Setup Kaggle Credentials (Kaggle only)

```bash
bash scripts/setup_kaggle_json.sh
```

This reads `KAGGLE_USERNAME` and `KAGGLE_KEY` from `.env` and generates `~/.kaggle/kaggle.json` (chmod 600). If the file already exists, it is force-overwritten.

**Skip this phase for non-Kaggle competitions.**

### Phase 1: Initialize Terraform Backend

```bash
task init-infra
```

This creates:

- A GCS bucket for Terraform state (`{PROJECT_ID}-terraform-state`)
- Initializes Terraform with the GCS backend

Only required once per project. Skip if `terraform/environments/dev/.terraform/` already exists.

### Phase 2: Apply Infrastructure and Build Docker Image

```bash
task setup-infra
```

This provisions:

- **GCS bucket** for data and model artifacts (`{COMPETITION_NAME}`)
- **Artifact Registry** repository for training Docker images (`training-images`)
- **Service account** for Vertex AI training jobs with IAM roles
- **Vertex AI API** enablement
- **Docker image** built and pushed to Artifact Registry via Cloud Build

### Phase 3: Download Competition Data (Kaggle only)

Run both downloads in parallel — they are independent:

```bash
task dl-kaggle-comp         # Download to local ./data/input/{COMPETITION_NAME}/
task dl-kaggle-comp-gcs     # Download to GCS via Vertex AI job
```

- **Local download** (`dl-kaggle-comp`): Downloads directly to `data/input/` using Kaggle API
- **GCS download** (`dl-kaggle-comp-gcs`): Submits a Vertex AI custom job that downloads data directly to `gs://{BUCKET_NAME}/data/input/`

**Skip this phase for non-Kaggle competitions.** Instead, manually download data and place it in `data/input/{COMPETITION_NAME}/`, then run `task push-data` to sync to GCS.

### Phase 4: Initialize Backlog (Project Management)

```bash
backlog init {COMPETITION_NAME} --integration-mode none --defaults
```

This creates a `.backlog/` directory for tracking tasks, milestones, documents, and decisions throughout the competition. Skip if `.backlog/` already exists.

After initialization, create a milestone for the competition deadline if known:

```bash
backlog milestone create "Competition Deadline" --due {DEADLINE_DATE}
```

## Troubleshooting

### Common Issues

| Issue                                                    | Cause                             | Fix                                                                               |
| -------------------------------------------------------- | --------------------------------- | --------------------------------------------------------------------------------- |
| `terraform init` fails                                   | Missing GCP auth                  | Run `task auth`                                                                   |
| `build-image` fails with `externally managed`            | Ubuntu 24.04 PEP 668              | Add `--break-system-packages` to `uv pip install` in Dockerfile and entrypoint.sh |
| `dl-kaggle-comp-gcs` fails with unsupported machine type | `e2-*` not supported on Vertex AI | Use `n1-*` or `n2-*` machine types in `vertex.py`                                 |
| `terraform apply` permission error                       | Insufficient IAM roles            | Ensure the authenticated account has `roles/editor` or equivalent                 |

### Verifying Setup

After completing all phases, verify:

```bash
# Check Terraform resources
task tf-plan                    # Should show no changes

# Check Docker image in Artifact Registry
gcloud artifacts docker images list {REGION}-docker.pkg.dev/{PROJECT_ID}/training-images

# Check local data
ls data/input/{COMPETITION_NAME}/

# Check GCS data
gcloud storage ls gs://{BUCKET_NAME}/data/input/{COMPETITION_NAME}/
```

## Key Files

| File                                             | Purpose                     |
| ------------------------------------------------ | --------------------------- |
| `terraform/environments/dev/`                    | Terraform configuration     |
| `docker/Dockerfile.training`                     | Training container image    |
| `docker/entrypoint.sh`                           | Container entrypoint script |
| `docker/cloudbuild.yaml`                         | Cloud Build configuration   |
| `src/kaggle_ops/vertex.py`                       | Vertex AI job submission    |
| `src/kaggle_ops/scripts/download_competition.py` | GCS download script         |
| `.backlog/`                                      | Project management (Backlog) |
