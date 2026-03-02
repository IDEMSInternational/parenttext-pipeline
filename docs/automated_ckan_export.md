# Google Cloud Run - CKAN Upload of Research Data

To routinely sync research data from RapidPro to CKAN so our partners have access, we need to run custom code which redacts and processes the RapidPro API output, provided by the [RapidPro API Tools].
Due to GDPR constraints on the processing of private data, we do not want to run these in GitHub Actions, and have elected to Google Cloud Run.

This guide details how to deploy an automated, scheduled pipeline that exports contact data from a RapidPro workspace and uploads it to a CKAN data portal. The pipeline is packaged as a Docker container, deployed as a **Google Cloud Run Job**, and triggered by **Google Cloud Scheduler**.

This setup is designed to be easily reproducible for new deployments (e.g., `south-africa-swift`, `romania`, `malaysia`).

---

## 1. Prerequisites and Environment Verification

Before creating resources, ensure your Google Cloud CLI is authenticated and pointing to the correct project. This is crucial if you haven't used `gcloud` recently.

```bash
# 1. Log in to your Google Cloud account
gcloud auth login

# 2. If you don't know the project ID off-hand, get it using the name, for example:
gcloud projects list --filter="name='IDEMS General'" --format="value(projectId)"

# 3. Set the active project, inserting the project ID
gcloud config set project PROJECT_ID_HERE

# 4. Verify the active project is correct
gcloud config get-value project

```

## 2. Define Deployment Variables

To keep naming conventions consistent across multiple deployments, set the following environment variables in your terminal. We will use these throughout the deployment process.

*Note: Use PowerShell, Command Prompt, or Bash to set these depending on your OS. The examples below use Bash/Zsh syntax, which works in macOS, Linux, and Git Bash on Windows. If using PowerShell, use `$env:DEPLOYMENT_NAME="parenttext-swift"`, etc.*

```bash
# The exact name of the deployment repository (e.g., parenttext-swift, parenttext-crisis-ukraine-georgia)
export DEPLOYMENT_NAME="parenttext-crisis-ukraine-georgia"

# The Google Cloud region to deploy resources to, e.g. europe-west4
export REGION="europe-west4"

# The Service Account Name used for all CKAN export jobs
export SA_NAME="parenttext-export-sa"
export SA_EMAIL="${SA_NAME}@$(gcloud config get-value project).iam.gserviceaccount.com"
```

## 3. Securely Store API Tokens

To remain OS-agnostic and avoid leaking secrets in terminal histories, create temporary text files for your tokens, upload them to Google Secret Manager, and then delete the local files.

**Step A: Create temporary text files**
1. Create a file named `rp_token.txt` and paste the **RapidPro API Token** inside.
2. Create a file named `ckan_token.txt` and paste the **CKAN API Key** inside.

**Step B: Create the unique secrets in Google Cloud**
To ensure we aren't billed for keeping outdated versions of secrets (if we are updating an existing deployment), we first attempt to delete any existing secrets before creating fresh ones.
```bash
# 1. Clean up existing secrets to prevent multi-version billing 
# (The '|| true' ensures the script doesn't stop if this is a brand new deployment)
gcloud secrets delete ${DEPLOYMENT_NAME}-rapidpro-token --quiet || true
gcloud secrets delete ${DEPLOYMENT_NAME}-ckan-token --quiet || true

# 2. Create the fresh RapidPro token secret
gcloud secrets create ${DEPLOYMENT_NAME}-rapidpro-token --data-file=rp_token.txt

# 3. Create the fresh CKAN token secret
gcloud secrets create ${DEPLOYMENT_NAME}-ckan-token --data-file=ckan_token.txt
```

**Step C: Clean up**
Delete `rp_token.txt` and `ckan_token.txt` from your local machine to prevent accidental exposure.

## 4. Configure the Shared Service Account

We use a single, shared Service Account for all export jobs to keep IAM permissions clean.

```bash
# 1. Create the Shared Service Account (If it already exists, this safely prints a warning and continues)
gcloud iam service-accounts create $SA_NAME \
  --description="Shared service account for ParentText RapidPro to CKAN exports" \
  --display-name="ParentText CKAN Export SA" || echo "Service account already exists, proceeding..."

# 2. Grant the Shared Service Account permission to read THIS deployment's RapidPro token
gcloud secrets add-iam-policy-binding ${DEPLOYMENT_NAME}-rapidpro-token \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"

# 3. Grant the Shared Service Account permission to read THIS deployment's CKAN token
gcloud secrets add-iam-policy-binding ${DEPLOYMENT_NAME}-ckan-token \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

## 5. Create the Cloud Run Job

Create the Cloud Run Job. This mounts the secrets securely and sets the configuration for the specific deployment.

*Replace the `...` values under `--set-env-vars` with the actual URLs and configurations for the deployment.*

See [RapidPro API Tools] and [CKAN Tools] for configuration guides.

```bash
gcloud run jobs create ${DEPLOYMENT_NAME}-ckan-export \
  --image $IMAGE_URL \
  --region $REGION \
  --service-account $SA_EMAIL \
  --set-env-vars "^|^RAPIDPRO_URL=https://app.rapidpro.io|\
DEPLOYMENT_NAME=${DEPLOYMENT_NAME}|\
ALLOWLIST_FIELDS=uuid,gender,age_years,location|\
CKAN_URL=https://sds.plhdashboard.org/|\
CKAN_OWNER_ORG=your-ckan-org-id|\
CKAN_DATASET=${DEPLOYMENT_NAME}-monitoring|\
CKAN_RESOURCE_NAME=RapidPro Contacts Export" \
  --set-secrets="RAPIDPRO_API_TOKEN=${DEPLOYMENT_NAME}-rapidpro-token:latest,CKAN_API_KEY=${DEPLOYMENT_NAME}-ckan-token:latest"

```

*Note: The `^|^` syntax allows us to safely use commas within the `ALLOWLIST_FIELDS`/`DENYLIST_FIELDS` variable without `gcloud` interpreting it as the end of the variable declaration.*

## 6. Test and Schedule the Pipeline

**Step A: Run a Manual Test**
Trigger the job manually to ensure permissions, secrets, and environment variables are configured correctly.

```bash
gcloud run jobs execute ${DEPLOYMENT_NAME}-ckan-export --region $REGION --wait

```

*Check the Google Cloud Console logs for this job to verify success.*

**Step B: Schedule the Automation**
Once the manual test succeeds, link the job to Google Cloud Scheduler to run automatically (e.g., daily at midnight UTC).

```bash
gcloud scheduler jobs create http ${DEPLOYMENT_NAME}-ckan-schedule \
  --location $REGION \
  --schedule="0 0 * * *" \
  --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$(gcloud config get-value project)/jobs/${DEPLOYMENT_NAME}-ckan-export:run" \
  --http-method POST \
  --oauth-service-account-email=$SA_EMAIL

```

[RapidPro API Tools]: rapidpro_api_tools.md
[CKAN Tools]: ckan_tools.md