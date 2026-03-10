"""
# ckan_tools.py
This script uploads CSV data files to a specified CKAN instance using the ckanapi library.
It allows for:
1. Creating a dataset if it doesn't exist (requires CKAN_OWNER_ORG).
2. Creating or updating a resource (file) within that dataset.
3. Reconciling datasets to preserve historical data that may have been deleted in the source.

Usage:
    python -m parenttext.ckan_tools --file contacts.csv --dataset my-new-dataset-name --resource-name "Contacts Export"
    python -m parenttext.ckan_tools --file contacts.csv --dataset my-new-dataset-name --resource-name "Contacts Export" --reconcile
"""

import argparse
import os
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv
import ckanapi

def get_headers():
    """
    Constructs the authorization headers needed for direct API requests.
    """
    api_key = os.getenv("CKAN_API_KEY")
    if not api_key:
        raise ValueError("CKAN_API_KEY is missing from environment variables.")
    return {
        "Authorization": api_key
    }

def reconcile_datasets(local_file_path, resource_url, reconcile_column, save_intermediary=False):
    """
    Downloads the remote CSV, finds rows where the reconcile_column is not
    present in the local CSV, and appends those rows to the local file.
    """
    print(f"   > Reconciling historical data using column '{reconcile_column}'...")
    
    # 1. Read local CSV to gather existing IDs and headers
    local_ids = set()
    try:
        with open(local_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if not headers or reconcile_column not in headers:
                print(f"   [!] Reconcile column '{reconcile_column}' not found in local CSV. Skipping.")
                return
            for row in reader:
                local_ids.add(row[reconcile_column])
    except Exception as e:
        print(f"   [!] Failed to read local file for reconciliation: {e}")
        return

    # 2. Download and read the existing remote CSV from CKAN
    try:
        req_headers = get_headers()
        response = requests.get(resource_url, headers=req_headers)
        response.raise_for_status()
        
        # Save the raw response to response.csv if requested
        if save_intermediary:
            with open("response.csv", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("   > Saved remote CSV to 'response.csv'")
        
        remote_content = response.text.splitlines()
        remote_reader = csv.DictReader(remote_content)
        
        # We must check the normalized version of the columns in case the reconcile_column itself changed cases
        remote_fields_normalized = [f.lower().replace(' ', '_') for f in (remote_reader.fieldnames or [])]
        if not remote_reader.fieldnames or reconcile_column.lower().replace(' ', '_') not in remote_fields_normalized:
            print(f"   [!] Reconcile column '{reconcile_column}' not found in remote CSV. Skipping.")
            return
            
        # Create a dictionary mapping normalized local headers to their exact remote header counterparts
        header_map = {l_col: r_col for l_col in headers for r_col in remote_reader.fieldnames if l_col.lower().replace(' ', '_') == r_col.lower().replace(' ', '_')}
            
        # 3. Find missing rows
        missing_rows = []
        for row in remote_reader:
            # Look up the ID using the mapped remote column name to handle capitalization/spacing differences
            remote_reconcile_key = header_map.get(reconcile_column, reconcile_column)
            
            if row.get(remote_reconcile_key) not in local_ids:
                # Keep only columns that match the local file's headers using the mapped remote header
                # Falls back to the local key name if it wasn't found in the map
                filtered_row = {k: row.get(header_map.get(k, k), '') for k in headers}
                missing_rows.append(filtered_row)
                local_ids.add(row.get(remote_reconcile_key)) # Add to set to prevent duplicate appends
                
        # Save the missing rows to missing_rows.csv if requested
        if save_intermediary and missing_rows:
            with open("missing_rows.csv", "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(missing_rows)
            print("   > Saved extracted missing rows to 'missing_rows.csv'")

        # 4. Append missing rows to local file
        if missing_rows:
            print(f"   > Found {len(missing_rows)} deleted records to preserve. Appending...")
            with open(local_file_path, 'a', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writerows(missing_rows)
            print("   > Reconciliation complete.")
        else:
            print("   > No missing historical records found.")
            
    except requests.exceptions.RequestException as e:
        print(f"   [!] Failed to download remote resource for reconciliation: {e}")
    except Exception as e:
        print(f"   [!] Error during reconciliation: {e}")

def upload_to_ckan(file_path, dataset_name, resource_name, reconcile_column=None, save_intermediary=False):
    load_dotenv()
    
    ckan_url = os.getenv("CKAN_URL")
    api_key = os.getenv("CKAN_API_KEY")
    owner_org = os.getenv("CKAN_OWNER_ORG") # Required if creating a new dataset

    if not ckan_url or not api_key:
        raise ValueError("CKAN_URL and CKAN_API_KEY must be set in environment variables.")

    # Initialize CKAN client
    ckan = ckanapi.RemoteCKAN(ckan_url, apikey=api_key)

    print(f"🚀 Starting upload to {ckan_url}")
    print(f"   File: {file_path}")
    print(f"   Dataset: {dataset_name}")

    # 1. Get or Create Dataset (Package)
    try:
        print(f"   > Checking for dataset '{dataset_name}'...")
        package = ckan.action.package_show(id=dataset_name)
        print(f"   > Dataset found: {package['title']}")
        
    except ckanapi.NotFound:
        print(f"   > Dataset '{dataset_name}' not found.")
        
        if not owner_org:
            print("   [!] Cannot create new dataset: CKAN_OWNER_ORG is missing from environment.")
            return

        print(f"   > Creating new dataset '{dataset_name}' in organization '{owner_org}'...")
        try:
            package = ckan.action.package_create(
                name=dataset_name,
                title=dataset_name.replace("-", " ").title(),
                owner_org=owner_org,
                notes=f"Dataset created automatically via ParentText Pipeline on {datetime.now().date()}",
                private=True # Default to private for safety
            )
            print("   > Dataset created successfully.")
        except Exception as e:
            print(f"   [!] Failed to create dataset: {e}")
            return

    # 2. Upload (Create or Update) Resource
    existing_resource = None
    for res in package.get("resources", []):
        if res["name"] == resource_name:
            existing_resource = res
            break

    # Trigger reconciliation if resource exists and flag is set
    if existing_resource and reconcile_column:
        reconcile_datasets(file_path, existing_resource['url'], reconcile_column, save_intermediary)

    try:
        if existing_resource:
            print(f"   > Updating existing resource '{resource_name}' (id: {existing_resource['id']})...")
            ckan.action.resource_patch(
                id=existing_resource['id'],
                upload=open(file_path, 'rb'),
                last_modified=datetime.now().isoformat()
            )
        else:
            print(f"   > Creating new resource '{resource_name}'...")
            ckan.action.resource_create(
                package_id=package['id'],
                name=resource_name,
                upload=open(file_path, 'rb'),
                format='CSV',
                description=f"Uploaded via automation on {datetime.now().date()}"
            )
        print("   ✅ Upload successful!")

    except Exception as e:
        print(f"   [!] Error uploading resource: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload CSV to CKAN.")
    parser.add_argument("--file", required=True, help="Path to the CSV file to upload")
    parser.add_argument("--dataset", required=True, help="Unique name (slug) of the CKAN dataset")
    parser.add_argument("--resource-name", required=True, help="Name of the resource to create/update")
    parser.add_argument(
        "--reconcile", 
        nargs='?', 
        const='uuid', 
        default=None, 
        help="Reconcile data to preserve historical rows before uploading. Defaults to 'uuid' column if flag is passed without a value."
    )
    parser.add_argument(
        "--save-intermediary",
        action="store_true",
        help="Saves the downloaded remote file as 'response.csv' and any extracted missing rows as 'missing_rows.csv' for debugging."
    )

    args = parser.parse_args()

    upload_to_ckan(args.file, args.dataset, args.resource_name, args.reconcile, args.save_intermediary)