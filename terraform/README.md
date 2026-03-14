# Terraform

Provisions GCP resources (GCS bucket, Vertex AI, service account).

Variables are passed via `TF_VAR_*` environment variables from `.env`.

## Setup

```sh
# Authenticate
task auth

# Create state bucket and run terraform init
task init-infra

# Preview changes
task tf-plan

# Apply
task setup-infra

# Destroy
task tf-destroy
```
