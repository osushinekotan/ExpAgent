variable "project_id" {
  type        = string
  description = "The ID of the project in which to deploy resources."
}

variable "region" {
  type        = string
  description = "The region in which to deploy resources."
}

variable "bucket_name" {
  type        = string
  description = "The name of the GCS bucket for artifacts."
}
