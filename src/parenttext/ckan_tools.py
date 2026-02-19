"""
# ckan_tools.py
This script uploads CSV data files to a specified CKAN instance using the ckanapi library.
It allows for:
1. Creating a dataset if it doesn't exist (requires CKAN_OWNER_ORG).
2. Creating or updating a resource (file) within that dataset.

Usage:
    python -m parenttext.ckan_tools --file contacts.csv --dataset my-new-dataset-name --resource-name "Contacts Export"
"""

import argparse
import os
from datetime import datetime
from dotenv import load_dotenv
import ckanapi

def upload_to_ckan(file_path, dataset_name, resource_name):
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

    args = parser.parse_args()

    upload_to_ckan(args.file, args.dataset, args.resource_name)