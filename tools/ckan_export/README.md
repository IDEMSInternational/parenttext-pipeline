# RapidPro to CKAN Data Export Pipeline

This directory contains the containerization and Infrastructure-as-Code (IaC) configurations for the automated RapidPro to CKAN data export pipeline. 

The pipeline runs as a scheduled **Google Cloud Run Job**, triggered by **Google Cloud Scheduler**, and securely manages credentials via **Google Secret Manager**. It is designed to be highly reusable across multiple deployments without requiring code changes to the core infrastructure.

---

## Directory Structure

* `Dockerfile`: The container image definition for the export pipeline.
* `tofu/`: The OpenTofu (Terraform) configuration used to provision the resources for a specific deployment.
* `bootstrap-tofu/`: The OpenTofu configuration used *once* per GCP project to set up the global deployment prerequisites.

---

## Container Architecture (`Dockerfile`)

The `Dockerfile` builds a lightweight Python environment capable of executing both the RapidPro data extraction and the CKAN upload scripts.

### Key Technical Details
1. **Base Image & System Dependencies:** Uses `python:3.14-slim`. It explicitly installs `git` because the core pipeline (`pyproject.toml`) relies on fetching a GitHub-hosted dependency (`rapidpro-abtesting`).
2. **Version Resolution Bypass:** Because the Docker build context does not (and should not) include the `.git/` folder, `setuptools-scm` will fail to resolve the package version. We bypass this by injecting `ENV SETUPTOOLS_SCM_PRETEND_VERSION=1.0.0` during the build.
3. **Chained Entrypoint:** Instead of executing a single Python module, the image dynamically generates an `entrypoint.sh` script during the build. This script sequentially runs:
   * `python -m parenttext.rapidpro_api_tools --steps export_contacts`
   * `python -m parenttext.ckan_tools`
4. **Environment-Driven:** The container relies entirely on environment variables passed in at runtime by Cloud Run (e.g., `RAPIDPRO_URL`, `ALLOWLIST_FIELDS`, `CKAN_DATASET`). It does not hardcode any configuration.

---

## Infrastructure as Code (OpenTofu)

The infrastructure relies on two distinct OpenTofu configurations to cleanly separate global project setup from individual deployment resources.

### 1. Project Bootstrap (`bootstrap-tofu/`)
Executed manually by a GCP Administrator once per Google Cloud Project.
* **Tofu State Bucket:** Creates a centralized, versioned GCS bucket to store the state files for all future pipeline deployments.
* **Deployer Service Account:** Creates a highly-privileged Service Account (`github-deployer-sa`) used exclusively by GitHub Actions to provision Cloud Run jobs, SAs, and schedulers.

### 2. Deployment Infrastructure (`tofu/`)
Executed automatically via the `.github/workflows/deploy-ckan-job.yml` reusable GitHub Action when setting up a new chatbot deployment.

**Key Architectural Features:**
* **Dynamic Service Account Hashing:** GCP strictly enforces a 30-character limit on Service Account IDs. To support long repository names (e.g., `parenttext-crisis-ukraine-georgia`), Tofu dynamically generates the runner SA using an MD5 hash of the deployment name (`pt-${substr(md5(var.deployment_name), 0, 8)}-sa`).
* **Least-Privilege Secret Binding:** The generated Runner Service Account is explicitly granted the `Secret Accessor` IAM role *only* for the manually created secrets specific to its deployment (`<deployment_name>-rapidpro-token` and `<deployment_name>-ckan-token`).
* **Dynamic JSON Environment Variables:** To prevent having to rewrite the IaC every time a new Python configuration variable is added, Tofu accepts a single JSON string (`var.container_env_vars`). It uses a `dynamic "env"` block to iterate over this JSON and map each key-value pair directly into the Cloud Run container's environment variables.

---

## Deployment & Usage

For step-by-step instructions on how to use these tools to deploy the pipeline for a new project, see the full operations guide:
👉 **[Automated RapidPro to CKAN Export Pipeline](../../docs/automated_ckan_export.md)**