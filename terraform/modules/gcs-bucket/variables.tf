variable "project_id" {
  type        = string
  description = "The ID of the project in which to deploy resources."
}

variable "name" {
  type        = string
  description = "The name of the bucket to create."
}

variable "location" {
  type        = string
  description = "The location of the bucket to create."
}

variable "versioning_enabled" {
  type        = bool
  description = "Whether to enable versioning for the bucket."
  default     = false
}

variable "storage_class" {
  type        = string
  description = "The storage class of the bucket."
  default     = "STANDARD"
}

variable "uniform_bucket_level_access" {
  type        = bool
  description = "Whether to enable uniform bucket level access for the bucket."
  default     = true
}
