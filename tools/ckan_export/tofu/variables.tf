variable "project_id" { type = string }
variable "region" { type = string }
variable "deployment_name" { type = string }
variable "cron_schedule" { type = string }
variable "image_url" { type = string }

variable "container_env_vars" { 
  type        = map(string) 
  description = "A JSON map of standard environment variables to pass to the container."
}