# Automated RapidPro to CKAN Export Pipeline

This guide details how to deploy an automated pipeline that exports contact data from a RapidPro workspace and uploads it to a CKAN data portal. 

It relies on a **Deployer Service Account** to execute the deployment via GitHub Actions, and an isolated **Runner Service Account** to securely access credentials specific to each deployment.

---

## 1. Global Google Cloud Setup (One-Time Admin Task)

If your Google Cloud project is already configured for ParentText automated deployments, you likely already have a Deployer account. If not, an Admin must create one manually.

**Deployer Service Account**
Create a Service Account to be used by GitHub Actions. It requires the following IAM Roles:
* `Cloud Run Admin`
* `Cloud Scheduler Admin`
* `Service Account User` (Required to attach Runner SAs to the Cloud Run Job)

Generate a JSON Service Account Key for this Deployer account.

---

## 2. Setup For a New Deployment (Local Machine)

When setting up a new deployment (e.g. `parenttext-crisis-ukraine-georgia`), an Admin must manually insert the secrets into Google Cloud and use the internal Infrastructure repository to provision the Runner Service Account.

**Step A: Define variables locally**
```bash
export DEPLOYMENT_NAME="parenttext-crisis-ukraine-georgia"

```

**Step B: Store API Tokens in Secret Manager**
Create temporary text files for your tokens to avoid leaking secrets in terminal histories.

1. Create `rp_token.txt` with your RapidPro Token, and `ckan_token.txt` with your CKAN API Key.
2. Run the following commands to securely upload them:

```bash
gcloud secrets delete ${DEPLOYMENT_NAME}-rapidpro-token --quiet || true
gcloud secrets delete ${DEPLOYMENT_NAME}-ckan-token --quiet || true

gcloud secrets create ${DEPLOYMENT_NAME}-rapidpro-token --data-file=rp_token.txt
gcloud secrets create ${DEPLOYMENT_NAME}-ckan-token --data-file=ckan_token.txt

rm rp_token.txt ckan_token.txt
```

**Step C: Create the Isolated Runner Service Account (OpenTofu)**

1. Open the private infrastructure repository.
2. In the `parenttext.tf`, add a new module block for this deployment using the `ckan-runner` template.
3. Run `tofu apply` to create the uniquely hashed Runner Service Account and bind it strictly to the secrets you just created.
4. Copy the `runner_sa_email` outputted by Tofu. You will need this for the GitHub Repository setup.

---

## 3. Setup the Deployment Repository

In the specific deployment's GitHub Repository (e.g., `IDEMSInternational/parenttext-crisis-ukraine-georgia`):

**Step A: Add the Credentials Secret**
Go to **Settings > Secrets and variables > Actions > Secrets** and add:

* `GCP_CREDENTIALS`: The JSON key for your Global Deployer Service Account (from Step 1).

**Step B: Add the Configuration Variables**
Go to **Settings > Secrets and variables > Actions > Variables** and add the following repository variables.

*Note: `CONTAINER_ENV_VARS` is a JSON string. This allows you to safely manage complex environment variables like field allowlists directly from the GitHub UI without modifying pipeline code.*

| Variable | Example Value | Description |
| --- | --- | --- |
| `GCP_PROJECT` | `project-1234` | Your Google Cloud Project ID |
| `GCP_REGION` | `europe-west4` | Target Cloud Region |
| `DEPLOYMENT_NAME` | `parenttext-crisis-ukraine-georgia` | Must match the name used in Step 2 |
| `RUNNER_SA_EMAIL` | `pt-a1b2c3d4-sa@...` | The email of the SA outputted by OpenTofu |
| `CRON_SCHEDULE` | `0 0 * * *` | Cron format for when the job runs (e.g. Midnight UTC) |
| `IMAGE_URL` | `ghcr.io/idemsinternational/parenttext-pipeline-ckan-export:latest` | URL to the pipeline docker image |
| `CONTAINER_ENV_VARS` | *(See JSON block below)* | All container configuration mapped as JSON |

**Example `CONTAINER_ENV_VARS` payload:**

```json
{
  "RAPIDPRO_URL": "[https://app.rapidpro.io](https://app.rapidpro.io)",
  "ALLOWLIST_FIELDS": "uuid,gender,age_years,location",
  "CKAN_URL": "ckan.example.com",
  "CKAN_OWNER_ORG": "your-ckan-org-id",
  "CKAN_DATASET": "parenttext-ukraine-monitoring",
  "CKAN_RESOURCE_NAME": "Contacts Export"
}

```

**Step C: Create the GitHub Action**
Create a new file in your deployment repository at `.github/workflows/deploy-ckan.yml` that invokes the reusable workflow:

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
      deployment_name: ${{ vars.DEPLOYMENT_NAME }}
      runner_sa_email: ${{ vars.RUNNER_SA_EMAIL }}
      cron_schedule: ${{ vars.CRON_SCHEDULE }}
      image_url: ${{ vars.IMAGE_URL }}
      container_env_vars: ${{ vars.CONTAINER_ENV_VARS }}

```

## 4. Run the Deployment

Go to the **Actions** tab in your deployment repository, select **Deploy CKAN Export Infrastructure**, and click **Run Workflow**.

The action will assume the highly restricted Deployer identity, parse your JSON variables, start the Cloud Run Job connected to your Runner identity, and apply the schedule. To add or change script configuration later, edit the `CONTAINER_ENV_VARS` JSON in the repository settings and run the workflow again.
