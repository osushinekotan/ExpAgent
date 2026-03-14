provider "google" {
  project = var.project_id
  region  = var.region
}

module "service_account" {
  source       = "../../modules/service-account"
  project_id   = var.project_id
  account_id   = "vertex-ai-custom-training-job"
  display_name = "Vertex AI Service Account"
  description  = "Service account for Vertex AI custom training jobs"
  roles = [
    "roles/aiplatform.user",
    "roles/storage.objectAdmin",
  ]
}

output "service_account_email" {
  value = module.service_account.service_account_email
}

module "gcs_bucket" {
  source     = "../../modules/gcs-bucket"
  project_id = var.project_id
  name       = var.bucket_name
  location   = var.region
  storage_class               = "STANDARD"
  versioning_enabled          = true
  uniform_bucket_level_access = true
}

module "vertex_ai" {
  source     = "../../modules/vertex-ai"
  project_id = var.project_id
}

module "artifact_registry" {
  source        = "../../modules/artifact-registry"
  project_id    = var.project_id
  location      = var.region
  repository_id = "training-images"
}
