# RapidPro API Tools

A set of utilities for extracting data and managing contacts in a RapidPro workspace.

## Run

```bash
python -m parenttext.rapidpro_api_tools --steps <step_name>

```

Available steps:

* `count_flow_runs`: Generate statistics on how many times specific flows have been run and their completion rates.
* `process_deletion_requests`: Permanently delete contacts (and their runs/messages) if they belong to a specific "deletion request" group.
* `export_contacts`: Export a CSV of contacts including group memberships and specific contact fields.

## Configuration

These tools rely on environment variables defined in a `.env` file or the execution environment.

### General Variables

| Variable | Description | How to find it |
| --- | --- | --- |
| `RAPIDPRO_URL` | The base URL of your RapidPro workspace. | This is the URL you use to access the site, e.g., `https://app.rapidpro.io` or `https://rapidpro.idems.international`. |
| `RAPIDPRO_API_TOKEN` | Your personal API Access Token. | In RapidPro, click your user icon (top right) -> **Org Settings** (or click the organization name). Scroll down to the **API Token** section and copy the token. |
| `OUTPUT_FILE` | *(Optional)* path to save the output CSV. | Defaults to `flow_run_stats.csv` or `contacts.csv` depending on the step. |

### Step-Specific Variables

#### `count_flow_runs`

| Variable | Description | How to find it |
| --- | --- | --- |
| `FLOW_NAMES` | Comma-separated list of flow names to analyze. | Go to the **Flows** tab in RapidPro. Copy the exact names of the flows you want to track (e.g., `Registration, Survey 1, Survey 2`). |

#### `process_deletion_requests`

| Variable | Description | How to find it |
| --- | --- | --- |
| `DELETION_REQUEST_GROUP` | Name of the contact group containing users to delete. | Go to **Contacts** in RapidPro to view your groups. The default is `deletion request`. |

#### `export_contacts`

| Variable | Description | How to find it |
| --- | --- | --- |
| `CONTACT_FIELDS` | Comma-separated list of contact field keys to include as columns. | Go to **Contacts** -> **Fields** in RapidPro. Use the **Key** column (e.g., `gender`, `age_years`), not the Label. |
