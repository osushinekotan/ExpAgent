variable "project_id" {
  type        = string
  description = "The ID of the project in which to deploy resources."
}

variable "account_id" {
  type        = string
  description = "The ID of the service account to create."
}

variable "display_name" {
  type        = string
  description = "The display name of the service account."
}

variable "description" {
  type        = string
  description = "The description of the service account."
  default     = ""
}

variable "roles" {
  type        = list(string)
  description = "The roles to assign to the service account."
  default     = []
}
