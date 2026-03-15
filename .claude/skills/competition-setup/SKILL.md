---
name: competition-setup
description: This skill should be used when the user asks to "setup competition", "setup infra", "GCP setup", "GCPセットアップ", "初期セットアップ", "コンペのセットアップ", "インフラ構築", "データダウンロード", "download competition data", "setup environment", "環境構築", or wants to initialize infrastructure and download competition data for a new competition project.
---

# Competition Setup

End-to-end setup workflow for a competition project: GCP infrastructure provisioning, Docker image build, and competition data download to both local and GCS.

## Step 0: Gather Competition Info and Update project.yml

First, read `project.yml` to check if competition settings are already filled in. If not, ask the user:

1. **Competition platform**: Which platform is the competition on? (Kaggle / Other)
2. **Competition name**: What is the competition name (slug)?
3. **Competition URL**: What is the competition page URL?
4. **Is this a code competition?**: (Kaggle only) Does the competition require kernel submission?

Use the `AskUserQuestion` tool to gather missing information, then update `project.yml` accordingly:

```yaml
competition_name: "the-competition-slug"
competition_platform: kaggle
is_code_competition: false

metadata:
  url: "https://www.kaggle.com/competitions/the-competition-slug"
```

The `metadata` section is freeform — add any useful key-value pairs (e.g., `deadline`, `team_size_limit`, `submission_limit`).

- If the platform is **Kaggle**: Proceed with all phases below (including automated data download).
- If the platform is **other** (e.g., AtCoder, signate, etc.): Skip Phase 0 (Kaggle credentials) and Phase 3 (automated data download). Instead, inform the user:
  > このプラットフォームでは自動データダウンロードに対応していません。手動でデータをダウンロードして `data/input/{COMPETITION_NAME}/` に配置してください。GCS へのアップロードは `task push-data` で行えます。

Infrastructure setup (Phase 1 & 2) is common across all platforms.

## Prerequisites

Before starting, ensure the following are configured:

- **GCP authentication**: `gcloud auth application-default login` and `gcloud auth login`
- **`project.yml`**: Fill in competition settings (`competition_name`, `competition_platform`, `is_code_competition`)
- **`.env` file**: Copy from `.env.example` and fill in required values (`PROJECT_ID`, `REGION`)
  - For Kaggle competitions, also set `KAGGLE_USERNAME` and `KAGGLE_KEY`
- **Tools installed**: `gcloud`, `terraform`, `task` (Taskfile), `uv`, `yq`

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

This creates a `backlog/` directory for tracking tasks, milestones, documents, and decisions throughout the competition. Skip if `backlog/` already exists.

### Phase 5: Research Competition Overview

Gather competition information and record it as backlog documents. This is critical — the experiment-workflow skill depends on these documents (Phase 0: Understand the Competition).

#### 5-1. Get the competition page URL

Read `project.yml` and check `metadata.url`. If it is empty, use `AskUserQuestion` to ask the user:

> コンペティションページの URL を教えてください。

Then update `metadata.url` in `project.yml` with the provided URL.

#### 5-2. Fetch and analyze the competition page

Use `WebFetch` (and `WebSearch` if needed) to collect information from the competition page. Extract as much as possible:

- **Competition overview**: What is the goal? What problem are we solving?
- **Meta information**: Deadline, team size limit, submission limits per day, prize, code competition or not, etc.
- **Evaluation metric**: Exact metric name, formula if available, optimization direction (higher/lower is better)
- **Data description**: What files are provided, column descriptions, data types, size
- **Any other useful info**: Rules, external data policy, special constraints, hardware limits, etc.

#### 5-3. Record findings as backlog documents

Create separate backlog documents for each topic, then edit them with the collected content:

```bash
backlog doc create "Competition Overview"
# Edit the created document file with: competition goal, meta info (deadline, team size, submission limits, prizes, code comp flag)

backlog doc create "Evaluation Metric"
# Edit the created document file with: metric name, formula, optimization direction, any edge cases

backlog doc create "Data Description"
# Edit the created document file with: file list, column descriptions, data types, sizes, relationships between files
```

After `backlog doc create`, open and edit the generated markdown file directly (the path is shown in the command output). Write the collected information in a clear, structured format.

If additional useful information was found (e.g., rules about external data, specific constraints), either add it to the relevant document or create additional documents as needed.

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

| File                                             | Purpose                         |
| ------------------------------------------------ | ------------------------------- |
| `project.yml`                                    | Competition settings & metadata |
| `terraform/environments/dev/`                    | Terraform configuration         |
| `docker/Dockerfile.training`                     | Training container image        |
| `docker/entrypoint.sh`                           | Container entrypoint script     |
| `docker/cloudbuild.yaml`                         | Cloud Build configuration       |
| `src/kaggle_ops/vertex.py`                       | Vertex AI job submission        |
| `src/kaggle_ops/scripts/download_competition.py` | GCS download script             |
| `.backlog/`                                      | Project management (Backlog)    |
