# CKAN Data Publisher

A tool to automatically upload CSV files to a CKAN data portal. If the target dataset does not exist, the tool will create it (provided an Organization ID is supplied).

## Run

```bash
python -m parenttext.ckan_tools --file <path_to_csv> --dataset <dataset_name> --resource-name <resource_title>

```

* `--file`: Path to the local CSV file you want to upload.
* `--dataset`: The unique name (slug) of the dataset in CKAN (e.g., `deployment-name-stats`).
* `--resource-name`: The title of the resource file as it will appear in the CKAN UI (e.g., `Daily Flow Stats`).

## Configuration

These tools rely on environment variables defined in a `.env` file or the execution environment.


| Variable | Description | How to find it |
| --- | --- | --- |
| `CKAN_URL` | The base URL of your CKAN instance. | The URL of the portal, e.g., `https://data.idems.international`. |
| `CKAN_API_KEY` | Your user API Key for authentication. | Log in to CKAN. Click your user profile link (usually your username at the top right). Look for **API Key** in the left sidebar or at the bottom of the profile details. |
| `CKAN_OWNER_ORG` | *(Required if creating new datasets)* The ID of the organization that will own the dataset. | Go to the **Organizations** page in CKAN. Click on your organization. The ID is usually the slug at the end of the URL (e.g., for `.../organization/my-org`, the ID is `my-org`). |

# Example Workflow

To count flow runs and immediately upload the results to CKAN:

```bash
# 1. Generate the stats
export FLOW_NAMES="Onboarding, Feedback"
export OUTPUT_FILE="runs.csv"
python -m parenttext.rapidpro_api_tools --steps count_flow_runs

# 2. Upload to CKAN
python -m parenttext.ckan_tools \
  --file runs.csv \
  --dataset project-monitoring \
  --resource-name "Flow Run Statistics"

```