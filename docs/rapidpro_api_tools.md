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
* `upload_contacts_to_group`: Read a CSV of contacts and add them to a group, creating the group if it does not already exist.

Add `--dry-run` (or `-d`) to skip the actions that write to RapidPro (deletions, group creation, adding contacts to a group), e.g.:

```bash
python -m parenttext.rapidpro_api_tools --steps upload_contacts_to_group --dry-run
```

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
| `ALLOWLIST_FIELDS` | Comma-separated list of contact field keys to include as columns. | Go to **Contacts** -> **Fields** in RapidPro. Use the **Key** column (e.g., `gender`, `age_years`), not the Label. |
| `DENYLIST_FIELDS` | Comma-separated list of contact field keys to specifically exclude as columns. | Go to **Contacts** -> **Fields** in RapidPro. Use the **Key** column (e.g., `gender`, `age_years`), not the Label. |
| `IGNORE_CONSENT_COLUMN` | TRUE/FALSE, if the consent column is not present in the deployment or needs to be excluded for another reason | |

#### `upload_contacts_to_group`

| Variable | Description | How to find it |
| --- | --- | --- |
| `UPLOAD_GROUP_NAME` | **Required.** Name of the group the contacts should be added to. | Go to **Contacts** in RapidPro to see the existing groups. If no group with this name exists, it is created. |
| `UPLOAD_FILE` | *(Optional)* path to the CSV of contacts to upload. | Defaults to `upload_contacts.csv` in the working directory. |

The input CSV must have a `uuid` column **or** a `urn` (or `urns`) column. Column
names are matched case-insensitively, and any other columns are ignored:

* `uuid`: the RapidPro contact UUID, as produced by the `export_contacts` step.
* `urn`/`urns`: a contact URN, e.g. `tel:+27123456789` or `whatsapp:27123456789`.

If any row has a non-empty `uuid`, the upload is done by UUID and the URN columns
are ignored; URNs are only used when no UUIDs are present. Contacts are added in
batches of 100. Adding a contact that is already in the group is a no-op, so the
step is safe to re-run.

Example `upload_contacts.csv`:

```csv
uuid
6a53b7a4-3f1b-4b2c-9c2e-1f0a9d1c4e77
b1c9f0d2-8e44-4a1f-9b8a-2c7d5e3f6a10
```
