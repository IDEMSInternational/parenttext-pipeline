# Automated RapidPro to CKAN Export Pipeline

This guide details how to deploy an automated pipeline that exports contact data from a RapidPro workspace and uploads it to a CKAN data portal. 

It utilizes an Infrastructure-as-Code approach. A GitHub Action executes **OpenTofu** to automatically provision a Google Cloud Run Job, a Cloud Scheduler, and a unique **Runner Service Account** specifically for the deployment.

---

## 1. Global Google Cloud Setup (One-Time Admin Task)

If your Google Cloud project is already configured for ParentText automated deployments, you likely already have a Deployer account and State Bucket. If not, an Admin must set these up once per GCP project using the bootstrap script.

1. Clone the `parenttext-pipeline` repository to your local machine.
2. Navigate to the bootstrap folder: `cd tools/ckan-export/bootstrap-tofu/`
3. Authenticate your CLI: `gcloud auth application-default login`
4. Run the bootstrap: `tofu init` followed by `tofu apply -var "project_id=YOUR_PROJECT_ID`
5. Note the output values for `deployer_sa_email` and `state_bucket_name` for use in future deployments. Create a JSON Service Account Key for the Deployer account to use in GitHub Actions.

---

## 2. Setup For a New Deployment (Local Machine)

We intentionally keep RapidPro and CKAN API tokens *out* of GitHub Actions for security. When setting up a new deployment (e.g. `parenttext-crisis-ukraine-georgia`), you must manually insert these secrets into Google Secret Manager from your local terminal.

**Step A: Define variables locally**
```bash
# The exact name of your deployment (used for the secret names)
export DEPLOYMENT_NAME="parenttext-crisis-ukraine-georgia"

```

**Step B: Create temporary text files**
Create `rp_token.txt` with your RapidPro Token, and `ckan_token.txt` with your CKAN API Key.

**Step C: Create the Secrets in Google Cloud**
We attempt to delete the secrets first to prevent multi-version billing costs if you are updating an existing token.

```bash
gcloud secrets delete ${DEPLOYMENT_NAME}-rapidpro-token --quiet || true
gcloud secrets delete ${DEPLOYMENT_NAME}-ckan-token --quiet || true

gcloud secrets create ${DEPLOYMENT_NAME}-rapidpro-token --data-file=rp_token.txt
gcloud secrets create ${DEPLOYMENT_NAME}-ckan-token --data-file=ckan_token.txt

```

**Step D: Clean Up**
Delete the `.txt` files from your machine to prevent accidental leakage.

---

## 3. Setup the Deployment Repository

In the specific deployment's GitHub Repository (e.g., `IDEMSInternational/parenttext-crisis-ukraine-georgia`):

**Step A: Add the Credentials Secret**
Go to **Settings > Secrets and variables > Actions > Secrets** and add:

* `GCP_CREDENTIALS`: The JSON key for your Global Deployer Service Account.

**Step B: Add the Configuration Variables**
Go to **Settings > Secrets and variables > Actions > Variables** and add the following repository variables.

*Note: `CONTAINER_ENV_VARS` is a JSON string. This allows you to add or modify Python script variables in the future without ever having to touch the underlying OpenTofu code!*

| Variable | Example Value | Description |
| --- | --- | --- |
| `GCP_PROJECT` | `idems-general-123` | Your Google Cloud Project ID |
| `GCP_REGION` | `europe-west4` | Target Cloud Region |
| `TF_STATE_BUCKET` | `idems-general-123-parenttext-tofu-state` | Global bucket name from Step 1 |
| `DEPLOYMENT_NAME` | `parenttext-crisis-ukraine-georgia` | Used to locate your secrets and name resources |
| `CRON_SCHEDULE` | `0 0 * * *` | Cron format for when the job runs (e.g. Midnight UTC) |
| `IMAGE_URL` | `ghcr.io/idemsinternational/parenttext-pipeline-ckan-export:latest` | URL to the pipeline docker image |
| `CONTAINER_ENV_VARS` | *(See JSON block below)* | All container configuration mapped as JSON |

**Example `CONTAINER_ENV_VARS` payload:**

```json
{
  "RAPIDPRO_URL": "[https://app.rapidpro.io](https://app.rapidpro.io)",
  "ALLOWLIST_FIELDS": "uuid,gender,age_years,location",
  "CKAN_URL": "[https://sds.plhdashboard.org/](https://sds.plhdashboard.org/)",
  "CKAN_OWNER_ORG": "your-ckan-org-id",
  "CKAN_DATASET": "parenttext-ukraine-monitoring",
  "CKAN_RESOURCE_NAME": "RapidPro Contacts Export"
}

```

**Step C: Create the GitHub Action**
Create a new file in your deployment repository at `.github/workflows/deploy-ckan.yml` that invokes the reusable IaC workflow:

```yaml
name: Deploy CKAN Export Infrastructure

on:
  workflow_dispatch: # Allows manual trigger from the Actions tab

jobs:
  deploy-infra:
    uses: IDEMSInternational/parenttext-pipeline/.github/workflows/deploy-ckan-job.yml@main
    secrets:
      gcp_credentials: ${{ secrets.GCP_CREDENTIALS }}
    with:
      gcp_project: ${{ vars.GCP_PROJECT }}
      gcp_region: ${{ vars.GCP_REGION }}
      tf_state_bucket: ${{ vars.TF_STATE_BUCKET }}
      deployment_name: ${{ vars.DEPLOYMENT_NAME }}
      cron_schedule: ${{ vars.CRON_SCHEDULE }}
      image_url: ${{ vars.IMAGE_URL }}
      container_env_vars: ${{ vars.CONTAINER_ENV_VARS }}

```

## 4. Run the Deployment

Go to the **Actions** tab in your deployment repository, select **Deploy CKAN Export Infrastructure**, and click **Run Workflow**.

OpenTofu will automatically create a uniquely hashed Runner Service Account, bind it to your secrets, deploy the Cloud Run Job, and activate the Cloud Scheduler. To add a new script variable in the future, simply edit the `CONTAINER_ENV_VARS` JSON in the repository settings and run the workflow again!
