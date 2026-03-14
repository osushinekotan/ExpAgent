output "service_name" {
  value       = google_project_service.vertex_ai.service
  description = "The name of the enabled service"
}
