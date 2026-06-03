#!/bin/bash

set -e

# Default output file if not specified in env
export OUTPUT_FILE=${OUTPUT_FILE:-contacts.csv}

echo "Starting RapidPro export..."
python -m parenttext.rapidpro_api_tools --steps export_contacts

if test -d scripts
then
    echo "Post-export scripts directory found"

    for f in scripts/*.sh
    do
        if test -x $f
        then
            "$f"
            echo "Script execution completed: $f"
        else
            echo "Script skipped because it is not executable: $f"
        fi
    done
else
    echo "Post-export scripts directory not found"
fi

echo "Starting CKAN upload..."
python -m parenttext.ckan_tools \
  --file "$OUTPUT_FILE" \
  --dataset "$CKAN_DATASET" \
  --resource-name "$CKAN_RESOURCE_NAME" \
  --reconcile "uuid"

echo "Pipeline completed successfully!"
