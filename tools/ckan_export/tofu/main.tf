terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Dynamically generate the Runner SA
locals {
  # Takes the first 8 characters of an MD5 hash of the deployment name
  # Example output: pt-a1b2c3d4-sa
  runner_sa_id = "pt-${substr(md5(var.deployment_name), 0, 8)}-sa"
}

resource "google_service_account" "runner" {
  account_id   = local.runner_sa_id
  # Use the full, readable name in the description/display name
  display_name = "CKAN Runner for ${var.deployment_name}"
}

# 2. Reference the manually created Secrets
data "google_secret_manager_secret" "rapidpro_token" {
  secret_id = "${var.deployment_name}-rapidpro-token"
}

data "google_secret_manager_secret" "ckan_token" {
  secret_id = "${var.deployment_name}-ckan-token"
}

# 3. Grant the specific Runner SA permission to read THIS deployment's secrets
resource "google_secret_manager_secret_iam_member" "rp_secret_accessor" {
  secret_id = data.google_secret_manager_secret.rapidpro_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runner.email}"
}

resource "google_secret_manager_secret_iam_member" "ckan_secret_accessor" {
  secret_id = data.google_secret_manager_secret.ckan_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runner.email}"
}

# 4. Create the Cloud Run Job
resource "google_cloud_run_v2_job" "ckan_export" {
  name     = "${var.deployment_name}-ckan-export"
  location = var.region

  template {
    template {
      service_account = google_service_account.runner.email
      containers {
        image = var.image_url
        
        dynamic "env" {
          for_each = var.container_env_vars
          content {
            name  = env.key
            value = env.value
          }
        }

        env {
          name = "RAPIDPRO_API_TOKEN"
          value_source {
            secret_key_ref {
              secret  = data.google_secret_manager_secret.rapidpro_token.secret_id
              version = "latest"
            }
          }
        }
        env {
          name = "CKAN_API_KEY"
          value_source {
            secret_key_ref {
              secret  = data.google_secret_manager_secret.ckan_token.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }
  
  depends_on = [
    google_secret_manager_secret_iam_member.rp_secret_accessor,
    google_secret_manager_secret_iam_member.ckan_secret_accessor
  ]
}

# 5. Create the Cloud Scheduler Trigger
resource "google_cloud_scheduler_job" "trigger" {
  name        = "${var.deployment_name}-ckan-schedule"
  description = "Daily trigger for CKAN Export (${var.deployment_name})"
  schedule    = var.cron_schedule
  time_zone   = "UTC"
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.ckan_export.name}:run"

    oauth_token {
      service_account_email = google_service_account.runner.email
    }
  }
}