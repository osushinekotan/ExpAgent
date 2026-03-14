resource "google_storage_bucket" "this" {
  project       = var.project_id
  name          = var.name
  location      = var.location
  storage_class = var.storage_class

  uniform_bucket_level_access = var.uniform_bucket_level_access
  versioning {
    enabled = var.versioning_enabled
  }
  force_destroy = true
}
