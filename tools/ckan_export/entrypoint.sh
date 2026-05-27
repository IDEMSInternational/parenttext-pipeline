#!/bin/bash
set -e

# Default output file if not specified in env
export OUTPUT_FILE=${OUTPUT_FILE:-contacts.csv}

echo "Starting RapidPro export..."
python -m parenttext.rapidpro_api_tools --steps export_contacts

echo "Starting CKAN upload..."
python -m parenttext.ckan_tools \\
  --file "$OUTPUT_FILE" \\
  --dataset "$CKAN_DATASET" \\
  --resource-name "$CKAN_RESOURCE_NAME"\\
  --reconcile "uuid"

echo "Pipeline completed successfully!"