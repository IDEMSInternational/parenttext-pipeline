variable "project_id" { default = "YOUR_GCP_PROJECT_ID" } # Change this before running!
variable "region" { default = "europe-west4" }

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Create the Global Tofu State Bucket
resource "google_storage_bucket" "tofu_state" {
  name          = "${var.project_id}-parenttext-tofu-state"
  location      = var.region
  force_destroy = false
  versioning {
    enabled = true
  }
}

# 2. Create the GitHub Actions Deployer Service Account
resource "google_service_account" "deployer" {
  account_id   = "github-deployer-sa"
  display_name = "GitHub Actions Deployer for ParentText"
}

# 3. Grant the Deployer the required roles to provision Cloud Run, SAs, and Secrets
locals {
  deployer_roles = [
    "roles/run.admin",                  # To create Cloud Run Jobs
    "roles/cloudscheduler.admin",       # To create Triggers
    "roles/iam.serviceAccountAdmin",    # To create the Runner SAs
    "roles/iam.serviceAccountUser",     # To attach Runner SAs to Cloud Run
    "roles/secretmanager.admin",        # To grant Runner SAs access to secrets
    "roles/storage.objectAdmin"         # To read/write to the Tofu State bucket
  ]
}

resource "google_project_iam_member" "deployer_permissions" {
  for_each = toset(local.deployer_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.deployer.email}"
}

output "deployer_sa_email" {
  value = google_service_account.deployer.email
}
output "state_bucket_name" {
  value = google_storage_bucket.tofu_state.name
}