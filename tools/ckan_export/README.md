# RapidPro to CKAN Data Export Pipeline

This directory contains the containerization for the automated RapidPro to CKAN data export pipeline. 

---

## Directory Structure

* `Dockerfile`: The container image definition for the export pipeline.

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

## Deployment & Usage

For step-by-step instructions on how to use these tools to deploy the pipeline for a new project, see the full operations guide:
👉 **[Automated RapidPro to CKAN Export Pipeline](../../docs/automated_ckan_export.md)**